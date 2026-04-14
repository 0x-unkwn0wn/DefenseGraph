from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    BASValidation,
    Capability,
    CapabilityRequiredDataSource,
    CapabilitySupportedResponseAction,
    CapabilityTechniqueMap,
    CoverageScope,
    Technique,
    TechniqueRelevantScope,
    Tool,
    ToolCapability,
    ToolCapabilityScope,
    ToolDataSource,
    ToolResponseAction,
)
from app.schemas import (
    BASValidationRead,
    TechniqueCoverageContributionRead,
    TechniqueCoverageRead,
    TechniqueCoverageResponseActionRead,
    ToolCapabilityScopeRead,
    ScopeSummaryRead,
    TechniqueRelevantScopeRead,
)
from app.services.configuration import calculate_configuration_status
from app.services.confidence import CONFIDENCE_RANK, SOURCE_RANK, calculate_confidence


COVERAGE_PRIORITY = {
    "none": 0,
    "detect": 1,
    "block": 2,
    "prevent": 3,
}


@dataclass
class TechniqueContribution:
    tool_id: int
    tool_name: str
    tool_category: str
    tool_types: list[str]
    capability_id: int
    capability_code: str
    capability_name: str
    control_effect: str
    implementation_level: str
    confidence_level: str
    confidence_source: str
    mapping_coverage: str
    dependency_warnings: list[str]
    configuration_status: str | None
    effectively_active: bool
    scopes: list[tuple[str, str]]


@dataclass
class TechniqueResponseAction:
    tool_id: int
    tool_name: str
    action_code: str
    action_name: str
    implementation_level: str


def compute_coverage(db: Session) -> list[TechniqueCoverageRead]:
    statement = (
        select(Technique)
        .options(
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.tool)
            .joinedload(Tool.data_sources)
            .joinedload(ToolDataSource.data_source),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.tool)
            .joinedload(Tool.response_actions)
            .joinedload(ToolResponseAction.response_action),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.required_data_sources)
            .joinedload(CapabilityRequiredDataSource.data_source),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.supported_response_actions)
            .joinedload(CapabilitySupportedResponseAction.response_action),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.assessment_template),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.configuration_questions),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.assessment_answers),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.evidence_items),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.configuration_profile),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.configuration_answers),
            joinedload(Technique.relevant_scopes).joinedload(TechniqueRelevantScope.coverage_scope),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.scopes)
            .joinedload(ToolCapabilityScope.coverage_scope),
            # BAS validations are assurance records, not active control contributions.
            joinedload(Technique.bas_validations).joinedload(BASValidation.bas_tool),
        )
        .order_by(Technique.code)
    )
    techniques = db.execute(statement).unique().scalars().all()
    # A tool is a response tool if "response" is among its types.
    # SQLite JSON: use JSON_EACH or just load all and filter in Python.
    all_tools_with_response = db.execute(
        select(Tool)
        .options(joinedload(Tool.response_actions).joinedload(ToolResponseAction.response_action))
        .order_by(Tool.name)
    ).unique().scalars().all()
    response_tools = [t for t in all_tools_with_response if "response" in t.tool_types]

    return [_build_technique_coverage_row(technique, response_tools) for technique in techniques]


def resolve_effect_for_technique(configured_effect: str, available_effects: list[str]) -> str:
    matching_effects = [
        effect
        for effect in available_effects
        if COVERAGE_PRIORITY[effect] <= COVERAGE_PRIORITY[configured_effect]
    ]
    if not matching_effects:
        return "none"

    return max(matching_effects, key=lambda effect: COVERAGE_PRIORITY[effect])


def _build_technique_coverage_row(technique: Technique, response_tools: list[Tool]) -> TechniqueCoverageRead:
    (
        contributions,
        missing_data_flags,
        unconfigured_flags,
        partially_configured_flags,
    ) = _collect_contributions_for_technique(technique)
    scope_summary = _build_scope_summary(technique, contributions)
    direct_effect = _strongest_effect(contributions)
    if _blocks_effective_coverage(technique, scope_summary):
        direct_effect = "none"
    effective_contributions = [
        contribution
        for contribution in contributions
        if contribution.control_effect == direct_effect
    ]
    tool_count = len({contribution.tool_id for contribution in contributions})
    confidence_level = _aggregate_confidence(effective_contributions)
    response_actions = _collect_response_actions_for_technique(technique, response_tools)
    response_enabled = bool(response_actions) and direct_effect != "none"
    effective_outcome = (
        "detect_with_response"
        if direct_effect == "detect" and response_enabled
        else direct_effect
    )

    is_gap_no_coverage = direct_effect == "none"
    is_gap_detect_only = direct_effect == "detect"
    is_gap_partial = (
        direct_effect != "none"
        and bool(effective_contributions)
        and all(
            contribution.implementation_level == "partial"
            or contribution.mapping_coverage == "partial"
            for contribution in effective_contributions
        )
    )
    is_gap_low_confidence = direct_effect != "none" and confidence_level == "low"
    is_gap_single_tool_dependency = direct_effect != "none" and tool_count == 1
    is_gap_missing_data_sources = bool(missing_data_flags)
    is_gap_detection_without_response = direct_effect == "detect" and not response_enabled
    is_gap_response_without_detection = bool(response_actions) and direct_effect == "none"
    is_gap_unconfigured_control = bool(unconfigured_flags)
    is_gap_partially_configured_control = bool(partially_configured_flags)
    is_gap_scope_missing = bool(scope_summary["missing_scopes"])
    is_gap_scope_partial = bool(scope_summary["partial_scopes"])
    if direct_effect != "none" and (is_gap_scope_missing or is_gap_scope_partial):
        is_gap_partial = True

    dependency_flags = [
        *missing_data_flags,
        *unconfigured_flags,
        *partially_configured_flags,
        *(["Missing scope coverage"] if is_gap_scope_missing else []),
        *(["Partial scope coverage"] if is_gap_scope_partial else []),
        *(["Response enabled"] if response_enabled else []),
        *(["Detection without response"] if is_gap_detection_without_response else []),
        *(["Response without upstream detection"] if is_gap_response_without_detection else []),
    ]

    bas_validation_reads = _build_bas_validations(technique)
    bas_validated = any(v.bas_result != "not_tested" for v in bas_validation_reads)
    # Most recent result — prefer the most recent validation date; fall back to
    # the last entry if no date is recorded.
    latest_bas = (
        max(
            (v for v in bas_validation_reads if v.bas_result != "not_tested"),
            key=lambda v: v.last_validation_date or "",
            default=None,
        )
    )

    return TechniqueCoverageRead(
        technique_id=technique.id,
        technique_code=technique.code,
        technique_name=technique.name,
        attack_url=f"https://attack.mitre.org/techniques/{technique.code.replace('.', '/')}/",
        coverage_type=direct_effect,
        effective_control_effect=direct_effect,
        effective_outcome=effective_outcome,
        tool_count=tool_count,
        confidence_level=confidence_level,
        coverage_status=_build_coverage_status(
            is_gap_no_coverage=is_gap_no_coverage,
            is_gap_detect_only=is_gap_detect_only,
            is_gap_partial=is_gap_partial,
            is_gap_low_confidence=is_gap_low_confidence,
        ),
        response_enabled=response_enabled,
        response_actions=[
            TechniqueCoverageResponseActionRead(
                tool_id=action.tool_id,
                tool_name=action.tool_name,
                action_code=action.action_code,
                action_name=action.action_name,
                implementation_level=action.implementation_level,
            )
            for action in response_actions
        ],
        dependency_flags=dependency_flags,
        contributing_tools=[
            TechniqueCoverageContributionRead(
                tool_id=contribution.tool_id,
                tool_name=contribution.tool_name,
                tool_category=contribution.tool_category,
                tool_types=contribution.tool_types,
                capability_id=contribution.capability_id,
                capability_code=contribution.capability_code,
                capability_name=contribution.capability_name,
                control_effect=contribution.control_effect,
                implementation_level=contribution.implementation_level,
                confidence_level=contribution.confidence_level,
                confidence_source=contribution.confidence_source,
                mapping_coverage=contribution.mapping_coverage,
                dependency_warnings=contribution.dependency_warnings,
                configuration_status=contribution.configuration_status,
                effectively_active=contribution.effectively_active,
                scopes=[
                    ToolCapabilityScopeRead(
                        id=0,
                        tool_capability_id=0,
                        coverage_scope_id=0,
                        status=status,
                        notes="",
                        coverage_scope=_scope_read_from_tuple(scope_code),
                    )
                    for scope_code, status in contribution.scopes
                    if status != "none"
                ],
            )
            for contribution in contributions
        ],
        relevant_scopes=[
            TechniqueRelevantScopeRead(
                coverage_scope_id=link.coverage_scope_id,
                relevance=link.relevance,
                coverage_scope=_scope_read_from_model(link.coverage_scope),
            )
            for link in sorted(technique.relevant_scopes, key=lambda item: (item.relevance, item.coverage_scope.name))
        ],
        scope_summary=ScopeSummaryRead(**scope_summary),
        bas_validations=bas_validation_reads,
        bas_validated=bas_validated,
        bas_result=latest_bas.bas_result if latest_bas else None,
        last_bas_validation_date=latest_bas.last_validation_date if latest_bas else None,
        is_gap_no_coverage=is_gap_no_coverage,
        is_gap_detect_only=is_gap_detect_only,
        is_gap_partial=is_gap_partial,
        is_gap_low_confidence=is_gap_low_confidence,
        is_gap_single_tool_dependency=is_gap_single_tool_dependency,
        is_gap_missing_data_sources=is_gap_missing_data_sources,
        is_gap_detection_without_response=is_gap_detection_without_response,
        is_gap_response_without_detection=is_gap_response_without_detection,
        is_gap_unconfigured_control=is_gap_unconfigured_control,
        is_gap_partially_configured_control=is_gap_partially_configured_control,
        is_gap_scope_missing=is_gap_scope_missing,
        is_gap_scope_partial=is_gap_scope_partial,
    )


def _collect_contributions_for_technique(
    technique: Technique,
) -> tuple[list[TechniqueContribution], list[str], list[str], list[str]]:
    contributions: list[TechniqueContribution] = []
    missing_data_flags: list[str] = []
    unconfigured_flags: list[str] = []
    partially_configured_flags: list[str] = []
    technique_effects_by_capability: dict[int, list[CapabilityTechniqueMap]] = {}

    for capability_map in technique.capability_maps:
        technique_effects_by_capability.setdefault(capability_map.capability_id, []).append(capability_map)

    for capability_maps in technique_effects_by_capability.values():
        capability = capability_maps[0].capability
        available_effects = [entry.control_effect for entry in capability_maps]

        for tool_capability in capability.tool_capabilities:
            if (
                tool_capability.implementation_level == "none"
                or tool_capability.control_effect == "none"
            ):
                continue

            # A tool contributes to active coverage only if it has "control"
            # or "analytics" among its types.  Tools that are purely
            # "response" or "assurance" (BAS) are handled elsewhere.
            tool_types = tool_capability.tool.tool_types
            is_active = any(t in tool_types for t in ("control", "analytics"))
            if not is_active:
                continue

            dependency_warnings: list[str] = []
            configuration_status, configuration_warnings, blocked_by_configuration, degraded_by_configuration = (
                _evaluate_configuration_state(tool_capability, technique.code)
            )
            dependency_warnings.extend(configuration_warnings)
            if blocked_by_configuration:
                unconfigured_flags.extend(configuration_warnings)
                continue
            if configuration_status == "unknown":
                unconfigured_flags.extend(configuration_warnings)
            elif degraded_by_configuration:
                partially_configured_flags.extend(configuration_warnings)

            # If the tool is analytics (and NOT also a control), force "detect".
            # A tool with ["control", "analytics"] uses its configured effect.
            is_analytics_only = "analytics" in tool_types and "control" not in tool_types
            if is_analytics_only:
                dependency_result = _evaluate_analytics_dependencies(tool_capability)
                dependency_warnings.extend(dependency_result["warnings"])
                if dependency_result["blocked"]:
                    missing_data_flags.extend(dependency_result["warnings"])
                    continue
                configured_effect = "detect"
                implementation_level = (
                    "partial"
                    if (
                        dependency_result["degraded"]
                        or degraded_by_configuration
                        or tool_capability.implementation_level == "partial"
                    )
                    else tool_capability.implementation_level
                )
            else:
                configured_effect = tool_capability.control_effect
                implementation_level = (
                    "partial"
                    if degraded_by_configuration or tool_capability.implementation_level == "partial"
                    else tool_capability.implementation_level
                )

            applied_effect = resolve_effect_for_technique(
                configured_effect,
                available_effects,
            )
            if applied_effect == "none":
                continue

            total_questions = (
                len(tool_capability.capability.assessment_template.questions)
                if tool_capability.capability.assessment_template
                else 0
            )
            summary = calculate_confidence(tool_capability, total_questions)
            confidence_level = summary.confidence_level
            confidence_source = summary.confidence_source
            if is_analytics_only and dependency_warnings:
                confidence_level = "low"
                if summary.confidence_source == "declared":
                    confidence_source = "declared"

            best_map = next(
                entry
                for entry in capability_maps
                if entry.control_effect == applied_effect
            )

            contributions.append(
                TechniqueContribution(
                    tool_id=tool_capability.tool_id,
                    tool_name=tool_capability.tool.name,
                    tool_category=tool_capability.tool.category,
                    tool_types=list(tool_capability.tool.tool_types),
                    capability_id=capability.id,
                    capability_code=capability.code,
                    capability_name=capability.name,
                    control_effect=applied_effect,
                    implementation_level=implementation_level,
                    confidence_level=confidence_level,
                    confidence_source=confidence_source,
                    mapping_coverage=best_map.coverage,
                    dependency_warnings=dependency_warnings,
                    configuration_status=configuration_status,
                    effectively_active=not blocked_by_configuration,
                    scopes=[
                        (scope.coverage_scope.code, scope.status)
                        for scope in tool_capability.scopes
                    ],
                )
            )

    return (
        contributions,
        sorted(set(missing_data_flags)),
        sorted(set(unconfigured_flags)),
        sorted(set(partially_configured_flags)),
    )


def _evaluate_analytics_dependencies(tool_capability: ToolCapability) -> dict[str, object]:
    capability = tool_capability.capability
    if not capability.requires_data_sources:
        return {"blocked": False, "degraded": False, "warnings": []}

    tool_data_sources = {
        entry.data_source_id: entry.ingestion_status
        for entry in tool_capability.tool.data_sources
    }
    warnings: list[str] = []
    blocked = False
    degraded = False

    for requirement in capability.required_data_sources:
        status = tool_data_sources.get(requirement.data_source_id, "none")
        if requirement.requirement_level == "required" and status == "none":
            warnings.append(f"Missing {requirement.data_source.name}")
            blocked = True
            continue

        if requirement.requirement_level == "required" and status == "partial":
            warnings.append(f"Partial {requirement.data_source.name}")
            degraded = True
            continue

        if requirement.requirement_level == "recommended" and status in {"none", "partial"}:
            warnings.append(f"Limited {requirement.data_source.name}")
            degraded = True

    return {"blocked": blocked, "degraded": degraded, "warnings": warnings}


def _evaluate_configuration_state(
    tool_capability: ToolCapability,
    technique_code: str,
) -> tuple[str | None, list[str], bool, bool]:
    capability = tool_capability.capability
    if not capability.requires_configuration:
        return None, [], False, False

    summary = calculate_configuration_status(
        tool_capability.configuration_profile,
        len(capability.configuration_questions),
    )
    capability_label = capability.name
    if summary.configuration_status == "unknown":
        return (
            "unknown",
            [f"Unconfigured {capability_label} for {technique_code}"],
            False,
            True,
        )
    if summary.configuration_status == "not_enabled":
        return (
            "not_enabled",
            [f"{capability_label} not enabled for {technique_code}"],
            True,
            False,
        )
    if summary.configuration_status == "partially_enabled":
        return (
            "partially_enabled",
            [f"{capability_label} only partially enabled for {technique_code}"],
            False,
            True,
        )
    return "enabled", [], False, False


def _build_scope_summary(
    technique: Technique,
    contributions: list[TechniqueContribution],
) -> dict[str, list[str]]:
    relevant_scopes = {link.coverage_scope.code: link.relevance for link in technique.relevant_scopes}
    aggregated_statuses = {scope_code: "none" for scope_code in relevant_scopes}

    for contribution in contributions:
        for scope_code, status in contribution.scopes:
            if scope_code not in aggregated_statuses:
                continue
            if _scope_status_rank(status) > _scope_status_rank(aggregated_statuses[scope_code]):
                aggregated_statuses[scope_code] = status

    full_scopes = sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "full")
    partial_scopes = sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "partial")
    missing_scopes = sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "none")

    return {
        "full_scopes": full_scopes,
        "partial_scopes": partial_scopes,
        "missing_scopes": missing_scopes,
    }


def _blocks_effective_coverage(technique: Technique, scope_summary: dict[str, list[str]]) -> bool:
    if not technique.relevant_scopes:
        return False

    primary_scope_codes = {
        link.coverage_scope.code
        for link in technique.relevant_scopes
        if link.relevance == "primary"
    }
    if not primary_scope_codes:
        return not scope_summary["full_scopes"] and not scope_summary["partial_scopes"]

    covered_primary_scopes = primary_scope_codes.intersection(
        set(scope_summary["full_scopes"]) | set(scope_summary["partial_scopes"])
    )
    return not covered_primary_scopes


def _scope_status_rank(status: str) -> int:
    return {"none": 0, "partial": 1, "full": 2}[status]


def _scope_read_from_model(scope: CoverageScope):
    return {
        "id": scope.id,
        "code": scope.code,
        "name": scope.name,
        "description": scope.description,
    }


def _scope_read_from_tuple(scope_code: str):
    scope_names = {
        "endpoint_user_device": "Endpoint / User Device",
        "server": "Server",
        "cloud_workload": "Cloud Workload",
        "identity": "Identity",
        "network": "Network",
        "email": "Email",
        "saas": "SaaS",
        "public_facing_app": "Public-Facing Application",
    }
    return {
        "id": 0,
        "code": scope_code,
        "name": scope_names[scope_code],
        "description": "",
    }


def _collect_response_actions_for_technique(technique: Technique, response_tools: list[Tool]) -> list[TechniqueResponseAction]:
    action_ids_to_names: dict[int, tuple[str, str]] = {}

    for capability_map in technique.capability_maps:
        capability = capability_map.capability
        for action_link in capability.supported_response_actions:
            action_ids_to_names[action_link.response_action_id] = (
                action_link.response_action.code,
                action_link.response_action.name,
            )

    actions: list[TechniqueResponseAction] = []
    for tool in response_tools:
        for action_link in tool.response_actions:
            if (
                action_link.implementation_level == "none"
                or action_link.response_action_id not in action_ids_to_names
            ):
                continue
            action_code, action_name = action_ids_to_names[action_link.response_action_id]
            actions.append(
                TechniqueResponseAction(
                    tool_id=tool.id,
                    tool_name=tool.name,
                    action_code=action_code,
                    action_name=action_name,
                    implementation_level=action_link.implementation_level,
                )
            )

    actions.sort(key=lambda item: (item.tool_name, item.action_name))
    return actions


def _strongest_effect(contributions: list[TechniqueContribution]) -> str:
    strongest = "none"
    for contribution in contributions:
        if COVERAGE_PRIORITY[contribution.control_effect] > COVERAGE_PRIORITY[strongest]:
            strongest = contribution.control_effect
    return strongest


def _aggregate_confidence(contributions: list[TechniqueContribution]) -> str:
    if not contributions:
        return "low"

    return max(
        contributions,
        key=lambda contribution: (
            CONFIDENCE_RANK[contribution.confidence_level],
            SOURCE_RANK[contribution.confidence_source],
        ),
    ).confidence_level


def _build_bas_validations(technique: Technique) -> list[BASValidationRead]:
    """Convert the technique's BAS validation ORM records to schema objects."""
    result: list[BASValidationRead] = []
    for v in technique.bas_validations:
        result.append(
            BASValidationRead(
                id=v.id,
                technique_id=v.technique_id,
                bas_tool_id=v.bas_tool_id,
                bas_tool_name=v.bas_tool.name if v.bas_tool else None,
                bas_result=v.bas_result,
                last_validation_date=v.last_validation_date,
                notes=v.notes,
            )
        )
    return result


def _build_coverage_status(
    *,
    is_gap_no_coverage: bool,
    is_gap_detect_only: bool,
    is_gap_partial: bool,
    is_gap_low_confidence: bool,
) -> str:
    if is_gap_no_coverage:
        return "no_coverage"
    if is_gap_detect_only:
        return "detect_only"
    if is_gap_partial:
        return "partial"
    if is_gap_low_confidence:
        return "low_confidence"
    return "covered"

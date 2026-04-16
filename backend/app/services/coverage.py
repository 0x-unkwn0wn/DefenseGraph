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
    ToolCapabilityTechniqueOverride,
    ToolDataSource,
    ToolResponseAction,
)
from app.schemas import (
    BASValidationRead,
    ScopeSummaryRead,
    TechniqueCoverageContributionRead,
    TechniqueCoverageRead,
    TechniqueCoverageResponseActionRead,
    TechniqueRelevantScopeRead,
    TechniqueTestResultRead,
    ToolCapabilityScopeRead,
)
from app.services.confidence import CONFIDENCE_RANK, SOURCE_RANK, calculate_confidence
from app.services.configuration import calculate_configuration_status
from app.services.test_status import (
    build_test_status_summary,
    normalize_test_status,
    strongest_test_status,
    to_legacy_bas_result,
)
from app.tool_categories import normalize_tool_category
from app.tool_types import normalize_tool_types


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
    capability_domain: str
    control_effect: str
    theoretical_effect: str
    real_effect: str
    configured_effect_default: str
    control_effect_source: str
    override_applied: bool
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
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.scopes)
            .joinedload(ToolCapabilityScope.coverage_scope),
            joinedload(Technique.capability_maps)
            .joinedload(CapabilityTechniqueMap.capability)
            .joinedload(Capability.tool_capabilities)
            .joinedload(ToolCapability.technique_overrides)
            .joinedload(ToolCapabilityTechniqueOverride.technique),
            joinedload(Technique.relevant_scopes).joinedload(TechniqueRelevantScope.coverage_scope),
            joinedload(Technique.bas_validations).joinedload(BASValidation.bas_tool),
        )
        .order_by(Technique.code)
    )
    techniques = db.execute(statement).unique().scalars().all()
    all_tools_with_response = db.execute(
        select(Tool)
        .options(joinedload(Tool.response_actions).joinedload(ToolResponseAction.response_action))
        .order_by(Tool.name)
    ).unique().scalars().all()
    response_tools = [tool for tool in all_tools_with_response if "response" in tool.tool_types]
    return [_build_technique_coverage_row(technique, response_tools) for technique in techniques]


def _build_technique_coverage_row(technique: Technique, response_tools: list[Tool]) -> TechniqueCoverageRead:
    contributions, missing_data_flags, unconfigured_flags, partially_configured_flags = _collect_contributions_for_technique(
        technique
    )
    mapped_capability_count = len({mapping.capability_id for mapping in technique.capability_maps})
    has_capability_mappings = mapped_capability_count > 0
    scope_summary = _build_scope_summary(technique, contributions)
    theoretical_effect = _strongest_effect(contributions, "theoretical_effect")
    real_effect = _strongest_effect(contributions, "real_effect")
    if has_capability_mappings and _blocks_effective_coverage(technique, scope_summary):
        real_effect = "none"
    effective_contributions = [item for item in contributions if item.real_effect == real_effect]
    theoretical_contributions = [item for item in contributions if item.theoretical_effect == theoretical_effect]
    confidence_basis = effective_contributions or theoretical_contributions
    confidence_level = _aggregate_confidence(confidence_basis)
    confidence_source_summary = _aggregate_confidence_sources(confidence_basis)
    available_effects = _collect_available_effects(contributions, "real_effect")
    detection_count = sum(1 for item in contributions if item.real_effect == "detect")
    blocking_count = sum(1 for item in contributions if item.real_effect == "block")
    prevention_count = sum(1 for item in contributions if item.real_effect == "prevent")
    tool_count = len({item.tool_id for item in contributions if item.real_effect != "none"})

    response_actions = _collect_response_actions_for_technique(technique, response_tools)
    response_enabled = bool(response_actions) and real_effect != "none"
    effective_outcome = "detect_with_response" if real_effect == "detect" and response_enabled else real_effect

    is_gap_no_coverage = has_capability_mappings and real_effect == "none"
    is_gap_detect_only = has_capability_mappings and real_effect == "detect"
    is_gap_partial = (
        has_capability_mappings
        and real_effect != "none"
        and bool(effective_contributions)
        and all(
            item.implementation_level == "partial" or item.mapping_coverage == "partial"
            for item in effective_contributions
        )
    )
    is_gap_low_confidence = has_capability_mappings and real_effect != "none" and confidence_level == "low"
    is_gap_single_tool_dependency = has_capability_mappings and real_effect != "none" and tool_count == 1
    is_gap_missing_data_sources = has_capability_mappings and bool(missing_data_flags)
    is_gap_detection_without_response = has_capability_mappings and real_effect == "detect" and not response_enabled
    is_gap_response_without_detection = has_capability_mappings and bool(response_actions) and real_effect == "none"
    is_gap_unconfigured_control = has_capability_mappings and bool(unconfigured_flags)
    is_gap_partially_configured_control = has_capability_mappings and bool(partially_configured_flags)
    is_gap_scope_missing = has_capability_mappings and bool(scope_summary["missing_scopes"])
    is_gap_scope_partial = has_capability_mappings and bool(scope_summary["partial_scopes"])
    if real_effect != "none" and (is_gap_scope_missing or is_gap_scope_partial):
        is_gap_partial = True

    dependency_flags = (
        ["No capability mappings defined for this technique"]
        if not has_capability_mappings
        else [
            *missing_data_flags,
            *unconfigured_flags,
            *partially_configured_flags,
            *(["Missing scope coverage"] if is_gap_scope_missing else []),
            *(["Partial scope coverage"] if is_gap_scope_partial else []),
            *(["Response enabled"] if response_enabled else []),
            *(["Detection without response"] if is_gap_detection_without_response else []),
            *(["Response without upstream detection"] if is_gap_response_without_detection else []),
        ]
    )

    test_results = _build_test_results(technique)
    test_status_values = [item.test_status for item in test_results]
    test_status = strongest_test_status(test_status_values)
    test_status_summary = build_test_status_summary(test_status_values)
    bas_validation_reads = _build_bas_validations(technique)
    bas_validated = test_status != "not_tested"
    latest_test = max(test_results, key=lambda item: item.last_tested_at or "", default=None)
    latest_bas = max(bas_validation_reads, key=lambda item: item.last_validation_date or "", default=None)
    mapped_domains = sorted({mapping.capability.domain for mapping in technique.capability_maps})
    is_gap_tested_failed = has_capability_mappings and test_status == "failed"
    is_gap_detected_not_blocked = has_capability_mappings and test_status == "detected_not_blocked"
    is_gap_untested_critical = has_capability_mappings and test_status == "not_tested" and real_effect in {"block", "prevent"}

    return TechniqueCoverageRead(
        technique_id=technique.id,
        technique_code=technique.code,
        technique_name=technique.name,
        attack_url=technique.attack_url or f"https://attack.mitre.org/techniques/{technique.code.replace('.', '/')}/",
        attack_domain=technique.domain,
        description=technique.description,
        tactics=list(technique.tactics or []),
        primary_tactic=(technique.tactics[0] if technique.tactics else "Execution"),
        platforms=list(technique.platforms or []),
        attack_stix_id=technique.attack_stix_id,
        attack_version=technique.attack_version,
        parent_technique_code=technique.parent_code,
        is_subtechnique=technique.is_subtechnique,
        display_group=technique.display_group,
        revoked=technique.revoked,
        deprecated=technique.deprecated,
        has_capability_mappings=has_capability_mappings,
        mapped_capability_count=mapped_capability_count,
        theoretical_effect=theoretical_effect,
        real_effect=real_effect,
        available_effects=available_effects,
        best_effect=real_effect,
        detection_count=detection_count,
        blocking_count=blocking_count,
        prevention_count=prevention_count,
        coverage_type=real_effect,
        effective_control_effect=real_effect,
        effective_outcome=effective_outcome,
        tool_count=tool_count,
        confidence_level=confidence_level,
        confidence_source_summary=confidence_source_summary,
        coverage_status=_build_coverage_status(
            has_capability_mappings=has_capability_mappings,
            is_gap_no_coverage=is_gap_no_coverage,
            is_gap_detect_only=is_gap_detect_only,
            is_gap_partial=is_gap_partial,
            is_gap_low_confidence=is_gap_low_confidence,
        ),
        mapped_domains=mapped_domains,
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
                capability_domain=contribution.capability_domain,
                control_effect=contribution.control_effect,
                theoretical_effect=contribution.theoretical_effect,
                real_effect=contribution.real_effect,
                configured_effect_default=contribution.configured_effect_default,
                control_effect_source=contribution.control_effect_source,
                override_applied=contribution.override_applied,
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
        test_results=test_results,
        test_status=test_status,
        test_status_summary=test_status_summary,
        bas_validations=bas_validation_reads,
        bas_validated=bas_validated,
        bas_result=latest_bas.bas_result if latest_bas else None,
        last_bas_validation_date=latest_test.last_tested_at if latest_test else None,
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
        is_gap_tested_failed=is_gap_tested_failed,
        is_gap_detected_not_blocked=is_gap_detected_not_blocked,
        is_gap_untested_critical=is_gap_untested_critical,
    )


def _collect_contributions_for_technique(technique: Technique) -> tuple[list[TechniqueContribution], list[str], list[str], list[str]]:
    contributions: list[TechniqueContribution] = []
    missing_data_flags: list[str] = []
    unconfigured_flags: list[str] = []
    partially_configured_flags: list[str] = []
    technique_mappings_by_capability: dict[int, list[CapabilityTechniqueMap]] = {}

    for capability_map in technique.capability_maps:
        technique_mappings_by_capability.setdefault(capability_map.capability_id, []).append(capability_map)

    for capability_maps in technique_mappings_by_capability.values():
        capability = capability_maps[0].capability
        strongest_mapping = max(capability_maps, key=lambda entry: 1 if entry.coverage == "full" else 0)

        for tool_capability in capability.tool_capabilities:
            if tool_capability.implementation_level == "none":
                continue

            tool_types = normalize_tool_types(list(tool_capability.tool.tool_types))
            is_active = any(tool_type in tool_types for tool_type in ("control", "analytics"))
            if not is_active:
                continue

            configured_effect_default, resolved_effect, resolved_implementation_level, control_effect_source = (
                _resolve_tool_capability_behavior(tool_capability, technique.id)
            )
            if resolved_effect == "none":
                continue

            dependency_warnings: list[str] = []
            configuration_status, configuration_warnings, blocked_by_configuration, degraded_by_configuration = (
                _evaluate_configuration_state(tool_capability, technique.code)
            )
            dependency_warnings.extend(configuration_warnings)
            if configuration_status == "unknown":
                unconfigured_flags.extend(configuration_warnings)
            elif blocked_by_configuration:
                unconfigured_flags.extend(configuration_warnings)
            elif degraded_by_configuration:
                partially_configured_flags.extend(configuration_warnings)

            is_analytics_only = "analytics" in tool_types and "control" not in tool_types
            theoretical_effect = "detect" if is_analytics_only else resolved_effect
            real_effect = theoretical_effect

            if is_analytics_only:
                dependency_result = _evaluate_analytics_dependencies(tool_capability)
                dependency_warnings.extend(dependency_result["warnings"])
                if dependency_result["blocked"]:
                    missing_data_flags.extend(dependency_result["warnings"])
                    real_effect = "none"
                implementation_level = (
                    "partial"
                    if (
                        dependency_result["degraded"]
                        or degraded_by_configuration
                        or resolved_implementation_level == "partial"
                    )
                    else resolved_implementation_level
                )
            else:
                implementation_level = (
                    "partial" if degraded_by_configuration or resolved_implementation_level == "partial" else resolved_implementation_level
                )

            if blocked_by_configuration:
                real_effect = "none"

            total_questions = (
                len(tool_capability.capability.assessment_template.questions)
                if tool_capability.capability.assessment_template
                else 0
            )
            summary = calculate_confidence(tool_capability, total_questions)
            confidence_level = summary.confidence_level
            confidence_source = summary.confidence_source
            if real_effect != "none" and confidence_source not in {"validated", "tested"}:
                if configuration_status in {None, "enabled"} and not dependency_warnings:
                    confidence_source = "validated"
                    if CONFIDENCE_RANK[confidence_level] < CONFIDENCE_RANK["medium"]:
                        confidence_level = "medium"
            if is_analytics_only and dependency_warnings:
                confidence_level = "low"
                if summary.confidence_source == "declared":
                    confidence_source = "declared"

            contributions.append(
                TechniqueContribution(
                    tool_id=tool_capability.tool_id,
                    tool_name=tool_capability.tool.name,
                    tool_category=normalize_tool_category(
                        tool_capability.tool.category,
                        list(tool_capability.tool.tool_type_labels),
                    ),
                    tool_types=tool_types,
                    capability_id=capability.id,
                    capability_code=capability.code,
                    capability_name=capability.name,
                    capability_domain=capability.domain,
                    control_effect=real_effect,
                    theoretical_effect=theoretical_effect,
                    real_effect=real_effect,
                    configured_effect_default=configured_effect_default,
                    control_effect_source=control_effect_source,
                    override_applied=control_effect_source == "override",
                    implementation_level=implementation_level,
                    confidence_level=confidence_level,
                    confidence_source=confidence_source,
                    mapping_coverage=strongest_mapping.coverage,
                    dependency_warnings=dependency_warnings,
                    configuration_status=configuration_status,
                    effectively_active=real_effect != "none",
                    scopes=[(scope.coverage_scope.code, scope.status) for scope in tool_capability.scopes],
                )
            )

    return (
        contributions,
        sorted(set(missing_data_flags)),
        sorted(set(unconfigured_flags)),
        sorted(set(partially_configured_flags)),
    )


def _resolve_tool_capability_behavior(tool_capability: ToolCapability, technique_id: int) -> tuple[str, str, str, str]:
    override = next((item for item in tool_capability.technique_overrides if item.technique_id == technique_id), None)
    configured_effect_default = tool_capability.control_effect_default
    if override is None:
        return (
            configured_effect_default,
            configured_effect_default,
            tool_capability.implementation_level,
            "default",
        )
    return (
        configured_effect_default,
        override.control_effect_override,
        override.implementation_level_override or tool_capability.implementation_level,
        "override",
    )


def _evaluate_analytics_dependencies(tool_capability: ToolCapability) -> dict[str, object]:
    capability = tool_capability.capability
    if not capability.requires_data_sources:
        return {"blocked": False, "degraded": False, "warnings": []}

    tool_data_sources = {entry.data_source_id: entry.ingestion_status for entry in tool_capability.tool.data_sources}
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


def _evaluate_configuration_state(tool_capability: ToolCapability, technique_code: str) -> tuple[str | None, list[str], bool, bool]:
    capability = tool_capability.capability
    if not capability.requires_configuration:
        return None, [], False, False

    summary = calculate_configuration_status(
        tool_capability.configuration_profile,
        len(capability.configuration_questions),
    )
    capability_label = capability.name
    if summary.configuration_status == "unknown":
        return "unknown", [f"Unconfigured {capability_label} for {technique_code}"], False, True
    if summary.configuration_status == "not_enabled":
        return "not_enabled", [f"{capability_label} not enabled for {technique_code}"], True, False
    if summary.configuration_status == "partially_enabled":
        return "partially_enabled", [f"{capability_label} only partially enabled for {technique_code}"], False, True
    return "enabled", [], False, False


def _build_scope_summary(technique: Technique, contributions: list[TechniqueContribution]) -> dict[str, list[str]]:
    relevant_scopes = {link.coverage_scope.code: link.relevance for link in technique.relevant_scopes}
    aggregated_statuses = {scope_code: "none" for scope_code in relevant_scopes}
    for contribution in contributions:
        if contribution.real_effect == "none":
            continue
        for scope_code, status in contribution.scopes:
            if scope_code not in aggregated_statuses:
                continue
            if _scope_status_rank(status) > _scope_status_rank(aggregated_statuses[scope_code]):
                aggregated_statuses[scope_code] = status
    return {
        "full_scopes": sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "full"),
        "partial_scopes": sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "partial"),
        "missing_scopes": sorted(scope_code for scope_code, status in aggregated_statuses.items() if status == "none"),
    }


def _blocks_effective_coverage(technique: Technique, scope_summary: dict[str, list[str]]) -> bool:
    if not technique.relevant_scopes:
        return False
    primary_scope_codes = {link.coverage_scope.code for link in technique.relevant_scopes if link.relevance == "primary"}
    if not primary_scope_codes:
        return not scope_summary["full_scopes"] and not scope_summary["partial_scopes"]
    covered_primary_scopes = primary_scope_codes.intersection(
        set(scope_summary["full_scopes"]) | set(scope_summary["partial_scopes"])
    )
    return not covered_primary_scopes


def _scope_status_rank(status: str) -> int:
    return {"none": 0, "partial": 1, "full": 2}[status]


def _scope_read_from_model(scope: CoverageScope) -> dict[str, object]:
    return {
        "id": scope.id,
        "code": scope.code,
        "name": scope.name,
        "description": scope.description,
    }


def _scope_read_from_tuple(scope_code: str) -> dict[str, object]:
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
            if action_link.implementation_level == "none" or action_link.response_action_id not in action_ids_to_names:
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


def _strongest_effect(contributions: list[TechniqueContribution], effect_field: str = "real_effect") -> str:
    strongest = "none"
    for contribution in contributions:
        effect = getattr(contribution, effect_field)
        if COVERAGE_PRIORITY[effect] > COVERAGE_PRIORITY[strongest]:
            strongest = effect
    return strongest


def _collect_available_effects(contributions: list[TechniqueContribution], effect_field: str = "real_effect") -> list[str]:
    return [
        effect
        for effect in ("prevent", "block", "detect")
        if any(getattr(contribution, effect_field) == effect for contribution in contributions)
    ]


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


def _aggregate_confidence_sources(contributions: list[TechniqueContribution]) -> list[str]:
    return sorted(
        {contribution.confidence_source for contribution in contributions},
        key=lambda source: SOURCE_RANK[source],
    )


def _build_bas_validations(technique: Technique) -> list[BASValidationRead]:
    result: list[BASValidationRead] = []
    for item in technique.bas_validations:
        result.append(
            BASValidationRead(
                id=item.id,
                technique_id=item.technique_id,
                bas_tool_id=item.bas_tool_id,
                bas_tool_name=item.bas_tool.name if item.bas_tool else None,
                bas_result=to_legacy_bas_result(item.bas_result),
                test_status=normalize_test_status(item.bas_result),
                last_validation_date=item.last_validation_date,
                notes=item.notes,
            )
        )
    return result


def _build_test_results(technique: Technique) -> list[TechniqueTestResultRead]:
    result: list[TechniqueTestResultRead] = []
    for item in technique.bas_validations:
        result.append(
            TechniqueTestResultRead(
                id=item.id,
                technique_id=item.technique_id,
                linked_tool_id=item.bas_tool_id,
                linked_tool_name=item.bas_tool.name if item.bas_tool else None,
                test_status=normalize_test_status(item.bas_result),
                last_tested_at=item.last_validation_date,
                notes=item.notes,
            )
        )
    return result


def _build_coverage_status(
    *,
    has_capability_mappings: bool,
    is_gap_no_coverage: bool,
    is_gap_detect_only: bool,
    is_gap_partial: bool,
    is_gap_low_confidence: bool,
) -> str:
    if not has_capability_mappings:
        return "unmapped"
    if is_gap_no_coverage:
        return "no_coverage"
    if is_gap_detect_only:
        return "detect_only"
    if is_gap_partial:
        return "partial"
    if is_gap_low_confidence:
        return "low_confidence"
    return "covered"

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Capability, CapabilityCoverageRole, CapabilityTechniqueMap, Tool, ToolCapability, ToolDataSource, ToolResponseAction
from app.schemas import (
    CapabilityTechniqueMapRead,
    CapabilityRead,
    CoverageRoleRead,
    DocsCapabilityMappingRead,
    DocsCapabilityRead,
    DocsMappingRead,
    DocsToolTypeMappingRead,
    DocsToolTypeRead,
)
from app.services.mappings import get_structural_technique_maps
from app.tool_types import normalize_tool_types


def _serialize_capability(capability: Capability) -> CapabilityRead:
    structural_maps = get_structural_technique_maps(capability)
    return CapabilityRead(
        id=capability.id,
        code=capability.code,
        name=capability.name,
        domain=capability.domain,
        description=capability.description,
        requires_data_sources=capability.requires_data_sources,
        supported_by_analytics=capability.supported_by_analytics,
        supported_by_response=capability.supported_by_response,
        requires_configuration=capability.requires_configuration,
        configuration_profile_type=capability.configuration_profile_type,
        coverage_roles=[
            CoverageRoleRead.model_validate(link.coverage_role)
            for link in sorted(capability.coverage_roles, key=lambda item: item.coverage_role.name)
        ],
        related_techniques=[
            CapabilityTechniqueMapRead(
                technique_id=mapping.technique_id,
                technique_code=mapping.technique.code,
                technique_name=mapping.technique.name,
                attack_url=(
                    mapping.technique.attack_url
                    or f"https://attack.mitre.org/techniques/{mapping.technique.code.replace('.', '/')}/"
                ),
                coverage=mapping.coverage,
                technique_tactics=list(mapping.technique.tactics or []),
                technique_domain=mapping.technique.domain,
                display_group=mapping.technique.display_group,
                is_subtechnique=mapping.technique.is_subtechnique,
                parent_technique_code=mapping.technique.parent_code,
            )
            for mapping in structural_maps
        ],
    )


def get_tool_type_docs(db: Session) -> list[DocsToolTypeRead]:
    tools = db.execute(
        select(Tool).options(
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability),
            joinedload(Tool.data_sources).joinedload(ToolDataSource.data_source),
            joinedload(Tool.response_actions).joinedload(ToolResponseAction.response_action),
        )
    ).unique().scalars().all()

    grouped: dict[str, dict[str, object]] = {}
    for tool in tools:
        active_assignments = [
            assignment
            for assignment in tool.capabilities
            if assignment.control_effect_default != "none" and assignment.implementation_level != "none"
        ]
        active_outputs = sorted({assignment.control_effect_default.title() for assignment in active_assignments})
        data_inputs = sorted(
            {
                entry.data_source.name
                for entry in tool.data_sources
                if entry.ingestion_status != "none"
            }
        )
        response_outputs = sorted(
            {
                entry.response_action.name
                for entry in tool.response_actions
                if entry.implementation_level != "none"
            }
        )
        capability_inputs = sorted({assignment.capability.name for assignment in active_assignments})

        for tool_type in normalize_tool_types(list(tool.tool_types)):
            bucket = grouped.setdefault(
                tool_type,
                {
                    "tool_names": [],
                    "capabilities": set(),
                    "inputs": set(),
                    "outputs": set(),
                },
            )
            bucket["tool_names"].append(tool.name)
            bucket["capabilities"].update(capability_inputs)
            bucket["outputs"].update(active_outputs)
            bucket["outputs"].update(response_outputs)
            bucket["inputs"].update(data_inputs or capability_inputs)

    rows: list[DocsToolTypeRead] = []
    for tool_type, payload in sorted(grouped.items()):
        tool_names = sorted(payload["tool_names"])
        capability_count = len(payload["capabilities"])
        rows.append(
            DocsToolTypeRead(
                tool_type=tool_type,
                tool_count=len(tool_names),
                description=(
                    f"{len(tool_names)} tools currently use this type and map to "
                    f"{capability_count} capabilities."
                ),
                inputs=sorted(payload["inputs"]),
                outputs=sorted(payload["outputs"]),
                example_usage=tool_names[:3],
            )
        )
    return rows


def get_capability_docs(db: Session) -> list[DocsCapabilityRead]:
    capabilities = db.execute(
        select(Capability).options(
            joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.tool),
        ).order_by(Capability.name)
    ).unique().scalars().all()

    rows: list[DocsCapabilityRead] = []
    for capability in capabilities:
        structural_maps = get_structural_technique_maps(capability)
        related_techniques = sorted(
            {
                f"{mapping.technique.code} {mapping.technique.name}"
                for mapping in structural_maps
            }
        )
        tool_types = sorted(
            {
                tool_type
                for assignment in capability.tool_capabilities
                for tool_type in normalize_tool_types(list(assignment.tool.tool_types))
            }
        )
        purpose = (
            "Structurally maps this capability to "
            f"{len(related_techniques)} ATT&CK techniques. Actual detect/block/prevent outcomes "
            "come from tool assignments and per-technique overrides."
        )
        rows.append(
            DocsCapabilityRead(
                capability=_serialize_capability(capability),
                purpose=purpose,
                typical_use_cases=related_techniques[:5],
                tool_types=tool_types,
                implementing_tool_count=len({assignment.tool_id for assignment in capability.tool_capabilities}),
                related_techniques=related_techniques,
            )
        )
    return rows


def get_mapping_docs(db: Session) -> DocsMappingRead:
    capabilities = db.execute(
        select(Capability).options(
            joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.tool)
        ).order_by(Capability.name)
    ).unique().scalars().all()

    tool_type_to_capabilities: dict[str, set[int]] = defaultdict(set)
    capability_to_tool_types: dict[int, set[str]] = {capability.id: set() for capability in capabilities}
    capability_by_id = {capability.id: capability for capability in capabilities}

    for capability in capabilities:
        for assignment in capability.tool_capabilities:
            for tool_type in normalize_tool_types(list(assignment.tool.tool_types)):
                capability_to_tool_types[capability.id].add(tool_type)
                tool_type_to_capabilities[tool_type].add(capability.id)

    return DocsMappingRead(
        tool_type_mappings=[
            DocsToolTypeMappingRead(
                tool_type=tool_type,
                capabilities=[
                    _serialize_capability(capability_by_id[capability_id])
                    for capability_id in sorted(
                        capability_ids,
                        key=lambda item: capability_by_id[item].name,
                    )
                ],
            )
            for tool_type, capability_ids in sorted(tool_type_to_capabilities.items())
        ],
        capability_mappings=[
            DocsCapabilityMappingRead(
                capability=_serialize_capability(capability),
                tool_types=sorted(capability_to_tool_types[capability.id]),
            )
            for capability in capabilities
        ],
    )

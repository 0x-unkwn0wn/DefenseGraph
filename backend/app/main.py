from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import BASE_DIR, Base, SessionLocal, engine
from app.migration import migrate_legacy_database
from app.models import (
    BASValidation,
    Capability,
    CapabilityAssessmentTemplate,
    CapabilityCoverageRole,
    CapabilityConfigurationQuestion,
    CapabilityRequiredDataSource,
    CapabilitySupportedResponseAction,
    CapabilityTechniqueMap,
    CoverageRole,
    CoverageScope,
    DataSource,
    ResponseAction,
    Technique,
    Tool,
    ToolCapability,
    ToolCapabilityAssessmentAnswer,
    ToolCapabilityConfigurationAnswer,
    ToolCapabilityConfigurationProfile,
    ToolCapabilityEvidence,
    ToolCapabilityScope,
    ToolCapabilityTechniqueOverride,
    ToolCapabilityTemplate,
    ToolDataSource,
    ToolResponseAction,
    TechniqueRelevantScope,
    Vendor,
)
from app.schemas import (
    AssessmentTemplateRead,
    BASValidationCreate,
    BASValidationRead,
    BASValidationUpdate,
    CapabilityDetailRead,
    CapabilityImplementingToolRead,
    CapabilityRequiredDataSourceRead,
    CapabilityRead,
    CapabilityConfigurationQuestionRead,
    CapabilitySupportedResponseActionRead,
    CapabilityTechniqueMapRead,
    ConfidenceSummaryRead,
    ControlRead,
    CoverageRoleRead,
    CoverageScopeRead,
    ConfigurationSummaryRead,
    DataSourceRead,
    DocsCapabilityRead,
    DocsMappingRead,
    DocsToolTypeRead,
    ResponseActionRead,
    ToolCapabilityAssessmentAnswerRead,
    ToolCapabilityAssessmentSubmission,
    ToolCapabilityConfigurationAnswerRead,
    ToolCapabilityConfigurationProfileCreate,
    ToolCapabilityConfigurationProfileRead,
    ToolCapabilityConfigurationSubmission,
    ToolCapabilityDetailRead,
    ToolCapabilityEvidenceCreate,
    ToolCapabilityEvidenceRead,
    ToolCapabilityRead,
    ToolCapabilityScopeRead,
    ToolCapabilityScopeSubmission,
    ToolCapabilityTechniqueOverrideRead,
    ToolCapabilityTechniqueOverrideSubmission,
    ToolCapabilityTemplateApplyRequest,
    ToolCapabilityTemplateRead,
    ToolCapabilityUpsert,
    ToolCreate,
    ToolDataSourceRead,
    ToolDataSourceUpsert,
    ToolRead,
    ToolTagRead,
    ToolTagsUpdate,
    ToolTypesUpdate,
    ToolResponseActionRead,
    ToolResponseActionUpsert,
    TechniqueRelevantScopeRead,
    VendorRead,
)
from app.seed import seed_reference_data, sync_reference_data
from app.services.configuration import (
    calculate_configuration_status,
    ensure_configuration_profile,
    sync_tool_capability_configuration,
)
from app.services.confidence import sync_tool_capability_confidence
from app.services.confidence import calculate_confidence
from app.services.coverage import compute_coverage
from app.services.docs import get_capability_docs, get_mapping_docs, get_tool_type_docs
from app.services.mappings import get_structural_technique_maps
from app.tool_categories import normalize_tool_category
from app.tool_types import is_validated_tool, normalize_tool_types
from app.services.tool_templates import (
    apply_templates_to_tool,
    get_ranked_templates,
    list_available_tags,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    migrate_legacy_database(BASE_DIR / "defensegraph.db")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        sync_reference_data(db)
        seed_reference_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="DefenseGraph API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_tool_or_404(db: Session, tool_id: int) -> Tool:
    statement = (
        select(Tool)
        .options(
            joinedload(Tool.vendor),
            joinedload(Tool.capabilities)
            .joinedload(ToolCapability.capability)
            .joinedload(Capability.assessment_template)
            .joinedload(CapabilityAssessmentTemplate.questions),
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability).joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability).joinedload(Capability.configuration_questions),
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability).joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique).joinedload(Technique.relevant_scopes).joinedload(TechniqueRelevantScope.coverage_scope),
            joinedload(Tool.capabilities).joinedload(ToolCapability.assessment_answers),
            joinedload(Tool.capabilities).joinedload(ToolCapability.evidence_items),
            joinedload(Tool.capabilities).joinedload(ToolCapability.configuration_profile),
            joinedload(Tool.capabilities).joinedload(ToolCapability.configuration_answers),
            joinedload(Tool.capabilities).joinedload(ToolCapability.scopes).joinedload(ToolCapabilityScope.coverage_scope),
            joinedload(Tool.data_sources).joinedload(ToolDataSource.data_source),
            joinedload(Tool.response_actions).joinedload(ToolResponseAction.response_action),
        )
        .where(Tool.id == tool_id)
    )
    tool = db.execute(statement).unique().scalar_one_or_none()
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


def normalize_tags(tags: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        cleaned = tag.strip()
        if not cleaned:
            continue
        marker = cleaned.casefold()
        if marker in seen:
            continue
        seen.add(marker)
        normalized.append(cleaned)
    return normalized


def get_capability_or_404(db: Session, capability_id: int) -> Capability:
    statement = (
        select(Capability)
        .options(
            joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique),
            joinedload(Capability.assessment_template).joinedload(CapabilityAssessmentTemplate.questions),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.tool).joinedload(Tool.vendor),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.assessment_answers),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.evidence_items),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.configuration_profile),
            joinedload(Capability.tool_capabilities).joinedload(ToolCapability.scopes).joinedload(ToolCapabilityScope.coverage_scope),
            joinedload(Capability.required_data_sources).joinedload(CapabilityRequiredDataSource.data_source),
            joinedload(Capability.supported_response_actions).joinedload(CapabilitySupportedResponseAction.response_action),
            joinedload(Capability.configuration_questions),
            joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique).joinedload(Technique.relevant_scopes).joinedload(TechniqueRelevantScope.coverage_scope),
        )
        .where(Capability.id == capability_id)
    )
    capability = db.execute(statement).unique().scalar_one_or_none()
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")
    return capability


def get_tool_capability_or_404(db: Session, tool_id: int, capability_id: int) -> ToolCapability:
    statement = (
        select(ToolCapability)
        .options(
            joinedload(ToolCapability.tool).joinedload(Tool.vendor),
            joinedload(ToolCapability.capability)
            .joinedload(Capability.assessment_template)
            .joinedload(CapabilityAssessmentTemplate.questions),
            joinedload(ToolCapability.capability).joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(ToolCapability.capability).joinedload(Capability.configuration_questions),
            joinedload(ToolCapability.capability).joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique).joinedload(Technique.relevant_scopes).joinedload(TechniqueRelevantScope.coverage_scope),
            joinedload(ToolCapability.capability)
            .joinedload(Capability.required_data_sources)
            .joinedload(CapabilityRequiredDataSource.data_source),
            joinedload(ToolCapability.capability)
            .joinedload(Capability.supported_response_actions)
            .joinedload(CapabilitySupportedResponseAction.response_action),
            joinedload(ToolCapability.assessment_answers),
            joinedload(ToolCapability.evidence_items),
            joinedload(ToolCapability.configuration_profile),
            joinedload(ToolCapability.configuration_answers),
            joinedload(ToolCapability.scopes).joinedload(ToolCapabilityScope.coverage_scope),
            joinedload(ToolCapability.technique_overrides).joinedload(ToolCapabilityTechniqueOverride.technique),
        )
        .where(
            ToolCapability.tool_id == tool_id,
            ToolCapability.capability_id == capability_id,
        )
    )
    assignment = db.execute(statement).unique().scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=404, detail="Tool capability not found")
    return assignment


def serialize_tool(tool: Tool) -> ToolRead:
    return ToolRead(
        id=tool.id,
        name=tool.name,
        vendor=VendorRead.model_validate(tool.vendor) if tool.vendor else None,
        category=normalize_tool_category(tool.category, list(tool.tool_type_labels)),
        tool_types=normalize_tool_types(list(tool.tool_types)),
        tool_type_labels=list(tool.tool_type_labels),
        tags=tool.tags,
        capabilities=[
            serialize_tool_capability_read(assignment)
            for assignment in sorted(tool.capabilities, key=lambda item: item.capability_id)
        ],
        data_sources=[
            ToolDataSourceRead(
                id=entry.id,
                tool_id=entry.tool_id,
                data_source_id=entry.data_source_id,
                ingestion_status=entry.ingestion_status,
                notes=entry.notes,
                data_source=DataSourceRead.model_validate(entry.data_source),
            )
            for entry in sorted(tool.data_sources, key=lambda item: item.data_source.name)
        ],
        response_actions=[
            ToolResponseActionRead(
                id=entry.id,
                tool_id=entry.tool_id,
                response_action_id=entry.response_action_id,
                implementation_level=entry.implementation_level,
                notes=entry.notes,
                response_action=ResponseActionRead.model_validate(entry.response_action),
            )
            for entry in sorted(tool.response_actions, key=lambda item: item.response_action.name)
        ],
    )


def serialize_capability_read(capability: Capability) -> CapabilityRead:
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
                technique_id=entry.technique_id,
                technique_code=entry.technique.code,
                technique_name=entry.technique.name,
                attack_url=f"https://attack.mitre.org/techniques/{entry.technique.code.replace('.', '/')}/",
                coverage=entry.coverage,
            )
            for entry in structural_maps
        ],
    )


def serialize_tool_capability_read(assignment: ToolCapability) -> ToolCapabilityRead:
    total_questions = (
        len(assignment.capability.assessment_template.questions)
        if assignment.capability.assessment_template
        else 0
    )
    summary = calculate_confidence(assignment, total_questions)
    return ToolCapabilityRead(
        capability_id=assignment.capability_id,
        control_effect_default=assignment.control_effect_default,
        implementation_level=assignment.implementation_level,
        confidence_source=summary.confidence_source,
        confidence_level=summary.confidence_level,
        scopes=[
            serialize_tool_capability_scope(scope)
            for scope in sorted(assignment.scopes, key=lambda item: item.coverage_scope.name)
            if scope.status != "none"
        ],
    )


def serialize_assessment_template(template: CapabilityAssessmentTemplate | None) -> AssessmentTemplateRead | None:
    if template is None:
        return None

    return AssessmentTemplateRead(
        id=template.id,
        capability_id=template.capability_id,
        description=template.description,
        questions=[
            {
                "id": question.id,
                "prompt": question.prompt,
                "position": question.position,
            }
            for question in template.questions
        ],
    )


def serialize_tool_capability_template(template: ToolCapabilityTemplate) -> ToolCapabilityTemplateRead:
    return serialize_ranked_tool_template(template, [], "optional")


def serialize_ranked_tool_template(
    template: ToolCapabilityTemplate,
    matched_tags: list[str],
    suggestion_group: str,
) -> ToolCapabilityTemplateRead:
    return ToolCapabilityTemplateRead(
        id=template.id,
        category=normalize_tool_category(template.category),
        capability_id=template.capability_id,
        optional_tags=template.optional_tags,
        priority=template.priority,
        default_effect=template.default_effect,
        default_implementation_level=template.default_implementation_level,
        confidence_hint=template.confidence_hint,
        description=template.description,
        capability=serialize_capability_read(template.capability),
        matched_tags=matched_tags,
        suggestion_group=suggestion_group,
    )


def serialize_configuration_profile(
    profile: ToolCapabilityConfigurationProfile | None,
) -> ToolCapabilityConfigurationProfileRead | None:
    if profile is None:
        return None

    return ToolCapabilityConfigurationProfileRead(
        id=profile.id,
        tool_id=profile.tool_id,
        capability_id=profile.capability_id,
        profile_type=profile.profile_type,
        configuration_status=profile.configuration_status,
        notes=profile.notes,
        last_updated_at=profile.last_updated_at,
    )


def serialize_tool_capability_scope(scope: ToolCapabilityScope) -> ToolCapabilityScopeRead:
    return ToolCapabilityScopeRead(
        id=scope.id,
        tool_capability_id=scope.tool_capability_id,
        coverage_scope_id=scope.coverage_scope_id,
        status=scope.status,
        notes=scope.notes,
        coverage_scope=CoverageScopeRead.model_validate(scope.coverage_scope),
    )


def serialize_tool_capability_override(
    override: ToolCapabilityTechniqueOverride,
) -> ToolCapabilityTechniqueOverrideRead:
    return ToolCapabilityTechniqueOverrideRead(
        id=override.id,
        tool_capability_id=override.tool_capability_id,
        technique_id=override.technique_id,
        technique_code=override.technique.code,
        technique_name=override.technique.name,
        control_effect_override=override.control_effect_override,
        implementation_level_override=override.implementation_level_override,
        notes=override.notes,
    )


def serialize_technique_relevant_scope(link: TechniqueRelevantScope) -> TechniqueRelevantScopeRead:
    return TechniqueRelevantScopeRead(
        coverage_scope_id=link.coverage_scope_id,
        relevance=link.relevance,
        coverage_scope=CoverageScopeRead.model_validate(link.coverage_scope),
    )


def serialize_assignment_detail(tool_capability: ToolCapability) -> ToolCapabilityDetailRead:
    total_questions = (
        len(tool_capability.capability.assessment_template.questions)
        if tool_capability.capability.assessment_template
        else 0
    )
    summary = calculate_confidence(tool_capability, total_questions)
    configuration_summary = (
        calculate_configuration_status(
            tool_capability.configuration_profile,
            len(tool_capability.capability.configuration_questions),
        )
        if tool_capability.capability.requires_configuration
        else None
    )
    return ToolCapabilityDetailRead(
        capability=serialize_capability_read(tool_capability.capability),
        assignment=ToolCapabilityRead(
            capability_id=tool_capability.capability_id,
            control_effect_default=tool_capability.control_effect_default,
            implementation_level=tool_capability.implementation_level,
            confidence_source=summary.confidence_source,
            confidence_level=summary.confidence_level,
            scopes=[
                serialize_tool_capability_scope(scope)
                for scope in sorted(tool_capability.scopes, key=lambda item: item.coverage_scope.name)
                if scope.status != "none"
            ],
        ),
        confidence=ConfidenceSummaryRead(**summary.__dict__),
        assessment_template=serialize_assessment_template(tool_capability.capability.assessment_template),
        assessment_answers=[
            ToolCapabilityAssessmentAnswerRead(
                question_id=answer.question_id,
                answer=answer.answer,
            )
            for answer in sorted(tool_capability.assessment_answers, key=lambda item: item.question_id)
        ],
        evidence=[
            ToolCapabilityEvidenceRead.model_validate(item)
            for item in sorted(tool_capability.evidence_items, key=lambda evidence: evidence.id)
        ],
        required_data_sources=[
            CapabilityRequiredDataSourceRead(
                data_source_id=entry.data_source_id,
                requirement_level=entry.requirement_level,
                data_source=DataSourceRead.model_validate(entry.data_source),
            )
            for entry in sorted(tool_capability.capability.required_data_sources, key=lambda item: item.data_source.name)
        ],
        supported_response_actions=[
            CapabilitySupportedResponseActionRead(
                response_action_id=entry.response_action_id,
                response_action=ResponseActionRead.model_validate(entry.response_action),
            )
            for entry in sorted(tool_capability.capability.supported_response_actions, key=lambda item: item.response_action.name)
        ],
        configuration_profile=serialize_configuration_profile(tool_capability.configuration_profile),
        configuration_summary=(
            ConfigurationSummaryRead(**configuration_summary.__dict__)
            if configuration_summary is not None
            else None
        ),
        configuration_questions=[
            CapabilityConfigurationQuestionRead(
                id=question.id,
                question=question.question,
                applies_to_profile_type=question.applies_to_profile_type,
            )
            for question in tool_capability.capability.configuration_questions
        ],
        configuration_answers=[
            ToolCapabilityConfigurationAnswerRead(
                question_id=answer.question_id,
                answer=answer.answer,
            )
            for answer in sorted(tool_capability.configuration_answers, key=lambda item: item.question_id)
        ],
        scopes=[
            serialize_tool_capability_scope(scope)
            for scope in sorted(tool_capability.scopes, key=lambda item: item.coverage_scope.name)
            if scope.status != "none"
        ],
        technique_overrides=[
            serialize_tool_capability_override(override)
            for override in sorted(
                tool_capability.technique_overrides,
                key=lambda item: item.technique.code,
            )
        ],
        relevant_scopes=[
            serialize_technique_relevant_scope(scope_link)
            for scope_link in sorted(
                {
                    scope_link.id: scope_link
                    for technique_map in tool_capability.capability.technique_maps
                    for scope_link in technique_map.technique.relevant_scopes
                }.values(),
                key=lambda item: (item.relevance, item.coverage_scope.name),
            )
        ],
    )


def serialize_capability_detail(capability: Capability) -> CapabilityDetailRead:
    structural_maps = get_structural_technique_maps(capability)
    return CapabilityDetailRead(
        capability=serialize_capability_read(capability),
        assessment_template=serialize_assessment_template(capability.assessment_template),
        related_techniques=[
            CapabilityTechniqueMapRead(
                technique_id=entry.technique_id,
                technique_code=entry.technique.code,
                technique_name=entry.technique.name,
                attack_url=f"https://attack.mitre.org/techniques/{entry.technique.code.replace('.', '/')}/",
                coverage=entry.coverage,
            )
            for entry in structural_maps
        ],
        implementing_tools=[
            _serialize_capability_implementing_tool(assignment)
            for assignment in sorted(
                capability.tool_capabilities,
                key=lambda item: (item.tool.name, item.capability_id),
            )
        ],
        required_data_sources=[
            CapabilityRequiredDataSourceRead(
                data_source_id=entry.data_source_id,
                requirement_level=entry.requirement_level,
                data_source=DataSourceRead.model_validate(entry.data_source),
            )
            for entry in sorted(capability.required_data_sources, key=lambda item: item.data_source.name)
        ],
        supported_response_actions=[
            CapabilitySupportedResponseActionRead(
                response_action_id=entry.response_action_id,
                response_action=ResponseActionRead.model_validate(entry.response_action),
            )
            for entry in sorted(capability.supported_response_actions, key=lambda item: item.response_action.name)
        ],
        configuration_questions=[
            CapabilityConfigurationQuestionRead(
                id=question.id,
                question=question.question,
                applies_to_profile_type=question.applies_to_profile_type,
            )
            for question in capability.configuration_questions
        ],
    )


def _serialize_capability_implementing_tool(assignment: ToolCapability) -> CapabilityImplementingToolRead:
    total_questions = (
        len(assignment.capability.assessment_template.questions)
        if assignment.capability.assessment_template
        else 0
    )
    summary = calculate_confidence(assignment, total_questions)
    configuration_status = (
        calculate_configuration_status(
            assignment.configuration_profile,
            len(assignment.capability.configuration_questions),
        ).configuration_status
        if assignment.capability.requires_configuration
        else None
    )
    return CapabilityImplementingToolRead(
        tool_id=assignment.tool_id,
        tool_name=assignment.tool.name,
        vendor=VendorRead.model_validate(assignment.tool.vendor) if assignment.tool.vendor else None,
        tool_category=normalize_tool_category(assignment.tool.category, list(assignment.tool.tool_type_labels)),
        tool_types=normalize_tool_types(list(assignment.tool.tool_types)),
        tool_type_labels=list(assignment.tool.tool_type_labels),
        control_effect_default=assignment.control_effect_default,
        implementation_level=assignment.implementation_level,
        confidence_source=summary.confidence_source,
        confidence_level=summary.confidence_level,
        assessment_answers=[
            ToolCapabilityAssessmentAnswerRead(
                question_id=answer.question_id,
                answer=answer.answer,
            )
            for answer in sorted(assignment.assessment_answers, key=lambda item: item.question_id)
        ],
        configuration_status=configuration_status,
        effectively_active=configuration_status != "not_enabled",
        scopes=[
            serialize_tool_capability_scope(scope)
            for scope in sorted(assignment.scopes, key=lambda item: item.coverage_scope.name)
            if scope.status != "none"
        ],
    )


def get_or_create_vendor(db: Session, vendor_name: str | None) -> Vendor | None:
    if vendor_name is None or not vendor_name.strip():
        return None

    normalized_name = vendor_name.strip()
    vendor = db.scalar(select(Vendor).where(Vendor.name == normalized_name))
    if vendor is not None:
        return vendor

    vendor = Vendor(name=normalized_name)
    db.add(vendor)
    db.flush()
    return vendor


@app.post("/tools", response_model=ToolRead, status_code=201)
def create_tool(payload: ToolCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Tool).where(Tool.name == payload.name.strip()))
    if existing:
        raise HTTPException(status_code=400, detail="Tool already exists")

    vendor = get_or_create_vendor(db, payload.vendor_name)
    tool = Tool(
        name=payload.name.strip(),
        vendor_id=vendor.id if vendor else None,
        category=normalize_tool_category(payload.category, payload.tool_type_labels),
        tool_types=normalize_tool_types(list(dict.fromkeys(payload.tool_types))),
        tool_type_labels=list(dict.fromkeys(item.strip() for item in payload.tool_type_labels if item.strip())),
        tags=normalize_tags(payload.tags),
    )
    db.add(tool)
    db.commit()
    db.refresh(tool)
    return serialize_tool(get_tool_or_404(db, tool.id))


@app.get("/tools", response_model=list[ToolRead])
def list_tools(db: Session = Depends(get_db)):
    statement = (
        select(Tool)
        .options(
            joinedload(Tool.vendor),
            joinedload(Tool.capabilities)
            .joinedload(ToolCapability.capability)
            .joinedload(Capability.assessment_template)
            .joinedload(CapabilityAssessmentTemplate.questions),
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability).joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Tool.capabilities).joinedload(ToolCapability.capability).joinedload(Capability.configuration_questions),
            joinedload(Tool.capabilities).joinedload(ToolCapability.scopes).joinedload(ToolCapabilityScope.coverage_scope),
            joinedload(Tool.capabilities).joinedload(ToolCapability.configuration_profile),
            joinedload(Tool.capabilities).joinedload(ToolCapability.assessment_answers),
            joinedload(Tool.capabilities).joinedload(ToolCapability.evidence_items),
            joinedload(Tool.data_sources).joinedload(ToolDataSource.data_source),
            joinedload(Tool.response_actions).joinedload(ToolResponseAction.response_action),
        )
        .order_by(Tool.name)
    )
    return [serialize_tool(tool) for tool in db.execute(statement).unique().scalars().all()]


@app.get("/tools/{tool_id}", response_model=ToolRead)
def read_tool(tool_id: int, db: Session = Depends(get_db)):
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.put("/tools/{tool_id}/tags", response_model=ToolRead)
def update_tool_tags(tool_id: int, payload: ToolTagsUpdate, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    tool.tags = normalize_tags(payload.tags)
    db.commit()
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.put("/tools/{tool_id}/tool-types", response_model=ToolRead)
def update_tool_types(tool_id: int, payload: ToolTypesUpdate, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    if not payload.tool_types:
        raise HTTPException(status_code=422, detail="At least one tool type is required.")
    tool.tool_types = normalize_tool_types(list(dict.fromkeys(payload.tool_types)))
    db.commit()
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.delete("/tools/{tool_id}", status_code=204)
def delete_tool(tool_id: int, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    db.delete(tool)
    db.commit()


@app.get("/capabilities", response_model=list[CapabilityRead])
def list_capabilities(db: Session = Depends(get_db)):
    statement = (
        select(Capability)
        .options(
            joinedload(Capability.coverage_roles).joinedload(CapabilityCoverageRole.coverage_role),
            joinedload(Capability.technique_maps).joinedload(CapabilityTechniqueMap.technique),
        )
        .order_by(Capability.domain, Capability.name)
    )
    return [
        serialize_capability_read(capability)
        for capability in db.execute(statement).unique().scalars().all()
    ]


@app.get("/capabilities/{capability_id}", response_model=CapabilityDetailRead)
def get_capability_detail(capability_id: int, db: Session = Depends(get_db)):
    capability = get_capability_or_404(db, capability_id)
    return serialize_capability_detail(capability)


@app.get("/assessment-templates", response_model=list[AssessmentTemplateRead])
def list_assessment_templates(db: Session = Depends(get_db)):
    statement = (
        select(CapabilityAssessmentTemplate)
        .options(joinedload(CapabilityAssessmentTemplate.questions))
        .order_by(CapabilityAssessmentTemplate.capability_id)
    )
    return [
        serialize_assessment_template(template)
        for template in db.execute(statement).unique().scalars().all()
    ]


@app.get("/capabilities/{capability_id}/assessment-template", response_model=AssessmentTemplateRead | None)
def get_assessment_template(capability_id: int, db: Session = Depends(get_db)):
    capability = get_capability_or_404(db, capability_id)
    return serialize_assessment_template(capability.assessment_template)


@app.get("/tags", response_model=list[ToolTagRead])
def get_tags():
    return [ToolTagRead(**entry) for entry in list_available_tags()]


@app.get("/data-sources", response_model=list[DataSourceRead])
def list_data_sources(db: Session = Depends(get_db)):
    return db.scalars(select(DataSource).order_by(DataSource.name)).all()


@app.get("/coverage-scopes", response_model=list[CoverageScopeRead])
def list_coverage_scopes(db: Session = Depends(get_db)):
    return db.scalars(select(CoverageScope).order_by(CoverageScope.name)).all()


@app.get("/response-actions", response_model=list[ResponseActionRead])
def list_response_actions(db: Session = Depends(get_db)):
    return db.scalars(select(ResponseAction).order_by(ResponseAction.name)).all()


@app.get("/docs/tool-types", response_model=list[DocsToolTypeRead])
def list_docs_tool_types(db: Session = Depends(get_db)):
    return get_tool_type_docs(db)


@app.get("/docs/capabilities", response_model=list[DocsCapabilityRead])
def list_docs_capabilities(db: Session = Depends(get_db)):
    return get_capability_docs(db)


@app.get("/docs/mappings", response_model=DocsMappingRead)
def list_docs_mappings(db: Session = Depends(get_db)):
    return get_mapping_docs(db)


@app.get("/templates", response_model=list[ToolCapabilityTemplateRead])
def list_tool_capability_templates(
    category: str,
    tags: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
):
    ranked_templates = get_ranked_templates(db, category, tags)
    return [
        serialize_ranked_tool_template(item.template, item.matched_tags, item.suggestion_group)
        for item in ranked_templates
    ]


@app.post("/tools/{tool_id}/capabilities", response_model=ToolRead)
def upsert_tool_capability(tool_id: int, payload: ToolCapabilityUpsert, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    capability = db.get(Capability, payload.capability_id)
    if capability is None:
        raise HTTPException(status_code=404, detail="Capability not found")

    assignment = db.scalar(
        select(ToolCapability).where(
            ToolCapability.tool_id == tool_id,
            ToolCapability.capability_id == payload.capability_id,
        )
    )

    if payload.control_effect_default == "none" and payload.implementation_level == "none":
        if assignment is not None:
            db.delete(assignment)
            db.commit()
        return serialize_tool(get_tool_or_404(db, tool_id))

    if assignment is None:
        assignment = ToolCapability(
            tool_id=tool.id,
            capability_id=capability.id,
            control_effect_default=payload.control_effect_default,
            implementation_level=payload.implementation_level,
        )
        db.add(assignment)
        db.flush()
    else:
        assignment.control_effect_default = payload.control_effect_default
        assignment.implementation_level = payload.implementation_level

    sync_tool_capability_confidence(assignment)
    db.commit()
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.post("/tools/{tool_id}/capabilities/{capability_id}/scopes", response_model=ToolCapabilityDetailRead)
def upsert_tool_capability_scopes(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityScopeSubmission,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    available_scopes = {scope.id: scope for scope in db.scalars(select(CoverageScope)).all()}
    existing_links = {link.coverage_scope_id: link for link in assignment.scopes}

    for item in payload.scopes:
        if item.coverage_scope_id not in available_scopes:
            raise HTTPException(status_code=404, detail="Coverage scope not found")

        existing = existing_links.get(item.coverage_scope_id)
        if item.status == "none":
            if existing is not None:
                db.delete(existing)
            continue

        if existing is None:
            db.add(
                ToolCapabilityScope(
                    tool_capability_id=assignment.id,
                    coverage_scope_id=item.coverage_scope_id,
                    status=item.status,
                    notes=item.notes.strip(),
                )
            )
        else:
            existing.status = item.status
            existing.notes = item.notes.strip()

    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.post(
    "/tools/{tool_id}/capabilities/{capability_id}/technique-overrides",
    response_model=ToolCapabilityDetailRead,
)
def upsert_tool_capability_technique_overrides(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityTechniqueOverrideSubmission,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    related_technique_ids = {
        technique_map.technique_id
        for technique_map in assignment.capability.technique_maps
    }
    existing_overrides = {
        override.technique_id: override
        for override in assignment.technique_overrides
    }

    for item in payload.overrides:
        if item.technique_id not in related_technique_ids:
            raise HTTPException(status_code=404, detail="Technique override target not found for this capability")

        existing = existing_overrides.get(item.technique_id)
        notes = item.notes.strip()
        if (
            item.control_effect_override == "none"
            and item.implementation_level_override is None
            and not notes
        ):
            if existing is not None:
                db.delete(existing)
            continue

        if existing is None:
            db.add(
                ToolCapabilityTechniqueOverride(
                    tool_capability_id=assignment.id,
                    technique_id=item.technique_id,
                    control_effect_override=item.control_effect_override,
                    implementation_level_override=item.implementation_level_override,
                    notes=notes,
                )
            )
            continue

        existing.control_effect_override = item.control_effect_override
        existing.implementation_level_override = item.implementation_level_override
        existing.notes = notes

    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.post("/tools/{tool_id}/data-sources", response_model=ToolRead)
def upsert_tool_data_source(tool_id: int, payload: ToolDataSourceUpsert, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    data_source = db.get(DataSource, payload.data_source_id)
    if data_source is None:
        raise HTTPException(status_code=404, detail="Data source not found")

    assignment = db.scalar(
        select(ToolDataSource).where(
            ToolDataSource.tool_id == tool.id,
            ToolDataSource.data_source_id == payload.data_source_id,
        )
    )

    if payload.ingestion_status == "none":
        if assignment is not None:
            db.delete(assignment)
            db.commit()
        return serialize_tool(get_tool_or_404(db, tool_id))

    if assignment is None:
        assignment = ToolDataSource(
            tool_id=tool.id,
            data_source_id=data_source.id,
            ingestion_status=payload.ingestion_status,
            notes=payload.notes.strip(),
        )
        db.add(assignment)
    else:
        assignment.ingestion_status = payload.ingestion_status
        assignment.notes = payload.notes.strip()

    db.commit()
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.post("/tools/{tool_id}/response-actions", response_model=ToolRead)
def upsert_tool_response_action(tool_id: int, payload: ToolResponseActionUpsert, db: Session = Depends(get_db)):
    tool = get_tool_or_404(db, tool_id)
    action = db.get(ResponseAction, payload.response_action_id)
    if action is None:
        raise HTTPException(status_code=404, detail="Response action not found")

    assignment = db.scalar(
        select(ToolResponseAction).where(
            ToolResponseAction.tool_id == tool.id,
            ToolResponseAction.response_action_id == payload.response_action_id,
        )
    )

    if payload.implementation_level == "none":
        if assignment is not None:
            db.delete(assignment)
            db.commit()
        return serialize_tool(get_tool_or_404(db, tool_id))

    if assignment is None:
        assignment = ToolResponseAction(
            tool_id=tool.id,
            response_action_id=action.id,
            implementation_level=payload.implementation_level,
            notes=payload.notes.strip(),
        )
        db.add(assignment)
    else:
        assignment.implementation_level = payload.implementation_level
        assignment.notes = payload.notes.strip()

    db.commit()
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.post("/tools/{tool_id}/templates", response_model=ToolRead)
def apply_tool_templates(
    tool_id: int,
    payload: ToolCapabilityTemplateApplyRequest,
    db: Session = Depends(get_db),
):
    tool = get_tool_or_404(db, tool_id)
    apply_templates_to_tool(db, tool, payload.selected_templates)
    return serialize_tool(get_tool_or_404(db, tool_id))


@app.get("/tools/{tool_id}/capabilities/{capability_id}", response_model=ToolCapabilityDetailRead)
def get_tool_capability_detail(tool_id: int, capability_id: int, db: Session = Depends(get_db)):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    return serialize_assignment_detail(assignment)


@app.post("/tools/{tool_id}/capabilities/{capability_id}/assessment-answers", response_model=ToolCapabilityDetailRead)
def upsert_tool_capability_assessment(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityAssessmentSubmission,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    template = assignment.capability.assessment_template
    if template is None:
        raise HTTPException(status_code=400, detail="Capability has no assessment template")

    valid_question_ids = {question.id for question in template.questions}
    for item in payload.answers:
        if item.question_id not in valid_question_ids:
            raise HTTPException(status_code=400, detail="Question does not belong to this capability")

        answer = db.get(
            ToolCapabilityAssessmentAnswer,
            {
                "tool_id": tool_id,
                "capability_id": capability_id,
                "question_id": item.question_id,
            },
        )
        if answer is None:
            answer = ToolCapabilityAssessmentAnswer(
                tool_id=tool_id,
                capability_id=capability_id,
                question_id=item.question_id,
                answer=item.answer,
            )
            db.add(answer)
        else:
            answer.answer = item.answer

    sync_tool_capability_confidence(assignment)
    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.post(
    "/tools/{tool_id}/capabilities/{capability_id}/configuration-profile",
    response_model=ToolCapabilityDetailRead,
)
def upsert_tool_capability_configuration_profile(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityConfigurationProfileCreate,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    if not assignment.capability.requires_configuration:
        raise HTTPException(status_code=400, detail="Capability does not require configuration verification")

    profile = ensure_configuration_profile(assignment)
    profile.notes = payload.notes.strip()
    sync_tool_capability_configuration(assignment)
    sync_tool_capability_confidence(assignment)
    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.post(
    "/tools/{tool_id}/capabilities/{capability_id}/configuration-answers",
    response_model=ToolCapabilityDetailRead,
)
def upsert_tool_capability_configuration_answers(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityConfigurationSubmission,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    capability = assignment.capability
    if not capability.requires_configuration:
        raise HTTPException(status_code=400, detail="Capability does not require configuration verification")

    profile = ensure_configuration_profile(assignment)
    valid_question_ids = {question.id for question in capability.configuration_questions}
    for item in payload.answers:
        if item.question_id not in valid_question_ids:
            raise HTTPException(status_code=400, detail="Question does not belong to this capability")

        answer = db.scalar(
            select(ToolCapabilityConfigurationAnswer).where(
                ToolCapabilityConfigurationAnswer.tool_id == tool_id,
                ToolCapabilityConfigurationAnswer.capability_id == capability_id,
                ToolCapabilityConfigurationAnswer.question_id == item.question_id,
            )
        )
        if answer is None:
            answer = ToolCapabilityConfigurationAnswer(
                tool_id=tool_id,
                capability_id=capability_id,
                question_id=item.question_id,
                answer=item.answer,
            )
            db.add(answer)
        else:
            answer.answer = item.answer

    sync_tool_capability_configuration(assignment)
    sync_tool_capability_confidence(assignment)
    profile.profile_type = capability.configuration_profile_type
    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.get("/tools/{tool_id}/capabilities/{capability_id}/evidence", response_model=list[ToolCapabilityEvidenceRead])
def list_tool_capability_evidence(tool_id: int, capability_id: int, db: Session = Depends(get_db)):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    return [
        ToolCapabilityEvidenceRead.model_validate(item)
        for item in sorted(assignment.evidence_items, key=lambda evidence: evidence.id)
    ]


@app.post("/tools/{tool_id}/capabilities/{capability_id}/evidence", response_model=ToolCapabilityDetailRead)
def create_tool_capability_evidence(
    tool_id: int,
    capability_id: int,
    payload: ToolCapabilityEvidenceCreate,
    db: Session = Depends(get_db),
):
    assignment = get_tool_capability_or_404(db, tool_id, capability_id)
    evidence = ToolCapabilityEvidence(
        tool_id=tool_id,
        capability_id=capability_id,
        title=payload.title.strip(),
        evidence_type=payload.evidence_type.strip(),
        note=payload.note.strip(),
        file_name=payload.file_name.strip() if payload.file_name else None,
        recorded_at=payload.recorded_at,
    )
    db.add(evidence)
    db.flush()
    sync_tool_capability_confidence(assignment)
    db.commit()
    return serialize_assignment_detail(get_tool_capability_or_404(db, tool_id, capability_id))


@app.get("/coverage")
def get_coverage(db: Session = Depends(get_db)):
    return compute_coverage(db)


# ---------------------------------------------------------------------------
# Controls endpoint
# Returns only active security control tools (tool_type != "validated").
# BAS tools are excluded by design — they are cross-functional validation
# tools, not active controls.
# ---------------------------------------------------------------------------

CONTROL_EFFECT_PRIORITY = {"none": 0, "detect": 1, "block": 2, "prevent": 3}


def _derive_primary_function(tool: Tool) -> str:
    """Return 'Prevent', 'Detect', or 'Respond' for a tool.

    Priority: if any type is 'control' → look at strongest effect;
    if analytics-only → Detect; if response-only → Respond.
    """
    types = set(tool.tool_types)
    if "control" in types:
        strongest = max(
            (
                tc.control_effect_default
                for tc in tool.capabilities
                if tc.control_effect_default != "none"
            ),
            key=lambda e: CONTROL_EFFECT_PRIORITY[e],
            default=None,
        )
        if strongest in ("block", "prevent"):
            return "Prevent"
        return "Detect"
    if "response" in types:
        return "Respond"
    if "analytics" in types:
        return "Detect"
    return "Prevent"


def _is_active_control(tool: Tool) -> bool:
    """True when the tool has at least one active role (not purely validated)."""
    return any(t in tool.tool_types for t in ("control", "analytics", "response"))


@app.get("/controls", response_model=list[ControlRead])
def list_controls(db: Session = Depends(get_db)):
    """List all active security controls with their primary function and covered TTPs.

    Tools that are ONLY 'validated' are excluded.  A tool with
    tool_types=['control','validated'] IS included because it has an active
    control role in addition to its BAS/validated capability.
    """
    statement = (
        select(Tool)
        .options(
            joinedload(Tool.capabilities)
            .joinedload(ToolCapability.capability)
            .joinedload(Capability.technique_maps)
            .joinedload(CapabilityTechniqueMap.technique),
        )
        .order_by(Tool.name)
    )
    all_tools = db.execute(statement).unique().scalars().all()
    controls: list[ControlRead] = []
    for tool in all_tools:
        if not _is_active_control(tool):
            continue
        ttp_ids: list[str] = sorted(
            {
                technique_map.technique.code
                for tc in tool.capabilities
                for technique_map in tc.capability.technique_maps
                if tc.control_effect_default != "none" and tc.implementation_level != "none"
            }
        )
        controls.append(
            ControlRead(
                tool_id=tool.id,
                tool_name=tool.name,
                primary_category=normalize_tool_category(tool.category, list(tool.tool_type_labels)),
                tool_types=normalize_tool_types(list(tool.tool_types)),
                primary_function=_derive_primary_function(tool),
                covered_ttp_ids=ttp_ids,
            )
        )
    return controls


# ---------------------------------------------------------------------------
# BAS Validation endpoints
# BAS is a cross-functional validated/validation capability — not an active
# control.  These endpoints record BAS test outcomes per technique (TTP).
# ---------------------------------------------------------------------------


def _get_technique_or_404(db: Session, technique_id: int) -> Technique:
    technique = db.get(Technique, technique_id)
    if technique is None:
        raise HTTPException(status_code=404, detail="Technique not found")
    return technique


def _serialize_bas_validation(v: BASValidation) -> BASValidationRead:
    return BASValidationRead(
        id=v.id,
        technique_id=v.technique_id,
        bas_tool_id=v.bas_tool_id,
        bas_tool_name=v.bas_tool.name if v.bas_tool else None,
        bas_result=v.bas_result,
        last_validation_date=v.last_validation_date,
        notes=v.notes,
    )


@app.get("/techniques/{technique_id}/bas-validations", response_model=list[BASValidationRead])
def list_bas_validations(technique_id: int, db: Session = Depends(get_db)):
    """List all BAS validation records for a technique (TTP).

    Returns validated/validation results from BAS tools.  These records do
    NOT affect active coverage — they only reflect whether an adversary
    simulation confirmed or bypassed the existing controls.
    """
    _get_technique_or_404(db, technique_id)
    statement = (
        select(BASValidation)
        .options(joinedload(BASValidation.bas_tool))
        .where(BASValidation.technique_id == technique_id)
        .order_by(BASValidation.last_validation_date.desc(), BASValidation.id.desc())
    )
    return [_serialize_bas_validation(v) for v in db.execute(statement).scalars().all()]


@app.post("/techniques/{technique_id}/bas-validations", response_model=BASValidationRead, status_code=201)
def create_bas_validation(
    technique_id: int,
    payload: BASValidationCreate,
    db: Session = Depends(get_db),
):
    """Record a BAS test result for a specific technique (TTP).

    The bas_tool_id must reference a tool with tool_type == 'validated'.
    Providing a control-type tool ID is rejected to enforce the separation
    between active controls and validated tooling.
    """
    _get_technique_or_404(db, technique_id)
    if payload.bas_tool_id is not None:
        bas_tool = db.get(Tool, payload.bas_tool_id)
        if bas_tool is None:
            raise HTTPException(status_code=404, detail="BAS tool not found")
        if not is_validated_tool(list(bas_tool.tool_types)):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tool '{bas_tool.name}' does not have 'validated' in its tool_types "
                    f"(current: {normalize_tool_types(list(bas_tool.tool_types))}). "
                    "Only tools with 'validated' among their types may be used as BAS tools."
                ),
            )

    validation = BASValidation(
        technique_id=technique_id,
        bas_tool_id=payload.bas_tool_id,
        bas_result=payload.bas_result,
        last_validation_date=payload.last_validation_date,
        notes=payload.notes.strip(),
    )
    db.add(validation)
    db.commit()
    db.refresh(validation)
    # Reload with relationship
    v = db.execute(
        select(BASValidation).options(joinedload(BASValidation.bas_tool)).where(BASValidation.id == validation.id)
    ).scalar_one()
    return _serialize_bas_validation(v)


@app.put("/bas-validations/{validation_id}", response_model=BASValidationRead)
def update_bas_validation(
    validation_id: int,
    payload: BASValidationUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing BAS validation record."""
    validation = db.execute(
        select(BASValidation).options(joinedload(BASValidation.bas_tool)).where(BASValidation.id == validation_id)
    ).scalar_one_or_none()
    if validation is None:
        raise HTTPException(status_code=404, detail="BAS validation not found")

    if payload.bas_tool_id is not None:
        bas_tool = db.get(Tool, payload.bas_tool_id)
        if bas_tool is None:
            raise HTTPException(status_code=404, detail="BAS tool not found")
        if not is_validated_tool(list(bas_tool.tool_types)):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tool '{bas_tool.name}' does not have 'validated' in its tool_types "
                    f"(current: {normalize_tool_types(list(bas_tool.tool_types))}). "
                    "Only tools with 'validated' among their types may be used as BAS tools."
                ),
            )
        validation.bas_tool_id = payload.bas_tool_id

    if payload.bas_result is not None:
        validation.bas_result = payload.bas_result
    if payload.last_validation_date is not None:
        validation.last_validation_date = payload.last_validation_date
    if payload.notes is not None:
        validation.notes = payload.notes.strip()

    db.commit()
    v = db.execute(
        select(BASValidation).options(joinedload(BASValidation.bas_tool)).where(BASValidation.id == validation_id)
    ).scalar_one()
    return _serialize_bas_validation(v)


@app.delete("/bas-validations/{validation_id}", status_code=204)
def delete_bas_validation(validation_id: int, db: Session = Depends(get_db)):
    """Delete a BAS validation record."""
    validation = db.get(BASValidation, validation_id)
    if validation is None:
        raise HTTPException(status_code=404, detail="BAS validation not found")
    db.delete(validation)
    db.commit()

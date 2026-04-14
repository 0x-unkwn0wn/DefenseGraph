from typing import Literal

from pydantic import BaseModel, ConfigDict


CoverageType = Literal["none", "detect", "block", "prevent"]
ImplementationLevel = Literal["none", "partial", "full"]
ControlEffect = Literal["none", "detect", "block", "prevent"]
MappedControlEffect = Literal["detect", "block", "prevent"]
MappingCoverage = Literal["full", "partial"]
ConfidenceSource = Literal["declared", "assessed", "evidenced", "tested"]
ConfidenceLevel = Literal["low", "medium", "high"]
AssessmentAnswerValue = Literal["yes", "no", "partial", "unknown"]
ConfigurationAnswerValue = Literal["yes", "no", "partial", "unknown"]
CoverageStatus = Literal["no_coverage", "detect_only", "partial", "low_confidence", "covered"]

# Active security control categories (prevention, detection, or response tools).
# "BAS" is intentionally excluded from this list — BAS tools are cross-functional
# assurance/validation tools, not active controls.
ActiveControlCategory = Literal["EDR", "PAM", "DLP", "SASE", "DNS", "Email", "Identity", "Security Analytics", "SOAR", "Other"]

# Full category set including BAS for tool registration.
ToolCategory = Literal["EDR", "PAM", "DLP", "SASE", "DNS", "Email", "BAS", "Identity", "Security Analytics", "SOAR", "Other"]

# "assurance" captures BAS and similar validation tools that do NOT contribute
# to active coverage; they only validate whether existing controls hold.
ToolType = Literal["control", "analytics", "response", "assurance"]

# Primary function label exposed in the control output
ControlFunction = Literal["Prevent", "Detect", "Respond"]

# BAS test outcome for a given TTP
BASResult = Literal["blocked", "detected", "not_detected", "not_tested"]

ToolTag = str
TemplatePriority = Literal["core", "secondary", "niche"]
SuggestionGroup = Literal["core", "recommended", "optional"]
IngestionStatus = Literal["none", "partial", "full"]
RequirementLevel = Literal["required", "recommended"]
EffectiveOutcome = Literal["none", "detect", "detect_with_response", "block", "prevent"]
ConfigurationStatus = Literal["unknown", "not_enabled", "partially_enabled", "enabled"]
ScopeStatus = Literal["none", "partial", "full"]
ScopeRelevance = Literal["primary", "secondary"]


class CapabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    domain: str
    description: str
    requires_data_sources: bool
    supported_by_analytics: bool
    supported_by_response: bool
    requires_configuration: bool
    configuration_profile_type: str | None
    related_techniques: list["CapabilityTechniqueMapRead"] = []


class DataSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    category: str
    description: str


class CoverageScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str


class ResponseActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str


class CapabilityRequiredDataSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data_source_id: int
    requirement_level: RequirementLevel
    data_source: DataSourceRead


class CapabilitySupportedResponseActionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    response_action_id: int
    response_action: ResponseActionRead


class CapabilityTechniqueMapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    technique_id: int
    technique_code: str
    technique_name: str
    attack_url: str
    control_effect: MappedControlEffect
    coverage: MappingCoverage


class TechniqueRelevantScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coverage_scope_id: int
    relevance: ScopeRelevance
    coverage_scope: CoverageScopeRead


class AssessmentQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    position: int


class AssessmentTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    capability_id: int
    description: str
    questions: list[AssessmentQuestionRead]


class ToolCapabilityAssessmentAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    answer: AssessmentAnswerValue


class ToolCapabilityAssessmentAnswerUpsert(BaseModel):
    question_id: int
    answer: AssessmentAnswerValue


class ToolCapabilityAssessmentSubmission(BaseModel):
    answers: list[ToolCapabilityAssessmentAnswerUpsert]


class CapabilityConfigurationQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    applies_to_profile_type: str | None


class ToolCapabilityConfigurationAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    answer: ConfigurationAnswerValue


class ToolCapabilityConfigurationAnswerUpsert(BaseModel):
    question_id: int
    answer: ConfigurationAnswerValue


class ToolCapabilityConfigurationSubmission(BaseModel):
    answers: list[ToolCapabilityConfigurationAnswerUpsert]


class ToolCapabilityConfigurationProfileCreate(BaseModel):
    notes: str = ""


class ToolCapabilityConfigurationProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_id: int
    capability_id: int
    profile_type: str | None
    configuration_status: ConfigurationStatus
    notes: str
    last_updated_at: str | None


class ToolCapabilityScopeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_capability_id: int
    coverage_scope_id: int
    status: ScopeStatus
    notes: str
    coverage_scope: CoverageScopeRead


class ToolCapabilityScopeUpsert(BaseModel):
    coverage_scope_id: int
    status: ScopeStatus
    notes: str = ""


class ToolCapabilityScopeSubmission(BaseModel):
    scopes: list[ToolCapabilityScopeUpsert]


class ScopeSummaryRead(BaseModel):
    full_scopes: list[str]
    partial_scopes: list[str]
    missing_scopes: list[str]


class ConfigurationSummaryRead(BaseModel):
    configuration_status: ConfigurationStatus
    answered_questions: int
    total_questions: int
    score: int
    max_score: int


class ToolCapabilityEvidenceCreate(BaseModel):
    title: str
    evidence_type: str
    note: str = ""
    file_name: str | None = None
    recorded_at: str


class ToolCapabilityEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    evidence_type: str
    note: str
    file_name: str | None
    recorded_at: str


class ConfidenceSummaryRead(BaseModel):
    confidence_source: ConfidenceSource
    confidence_level: ConfidenceLevel
    answered_questions: int
    total_questions: int
    score: int
    max_score: int
    evidence_count: int


class ToolCapabilityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    capability_id: int
    control_effect: ControlEffect
    implementation_level: ImplementationLevel
    confidence_source: ConfidenceSource
    confidence_level: ConfidenceLevel
    scopes: list[ToolCapabilityScopeRead] = []


class ToolCapabilityDetailRead(BaseModel):
    capability: CapabilityRead
    assignment: ToolCapabilityRead
    confidence: ConfidenceSummaryRead
    assessment_template: AssessmentTemplateRead | None
    assessment_answers: list[ToolCapabilityAssessmentAnswerRead]
    evidence: list[ToolCapabilityEvidenceRead]
    required_data_sources: list[CapabilityRequiredDataSourceRead]
    supported_response_actions: list[CapabilitySupportedResponseActionRead]
    configuration_profile: ToolCapabilityConfigurationProfileRead | None
    configuration_summary: ConfigurationSummaryRead | None
    configuration_questions: list[CapabilityConfigurationQuestionRead]
    configuration_answers: list[ToolCapabilityConfigurationAnswerRead]
    scopes: list[ToolCapabilityScopeRead]
    relevant_scopes: list[TechniqueRelevantScopeRead]


class ToolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: ToolCategory
    tool_types: list[ToolType]
    tags: list[ToolTag]
    capabilities: list[ToolCapabilityRead]
    data_sources: list["ToolDataSourceRead"]
    response_actions: list["ToolResponseActionRead"]


class ToolCreate(BaseModel):
    name: str
    category: ToolCategory
    tool_types: list[ToolType]
    tags: list[ToolTag] = []


class ToolTagsUpdate(BaseModel):
    tags: list[ToolTag]


class ToolTypesUpdate(BaseModel):
    tool_types: list[ToolType]


class ToolCapabilityUpsert(BaseModel):
    capability_id: int
    control_effect: ControlEffect
    implementation_level: ImplementationLevel


class CapabilityImplementingToolRead(BaseModel):
    tool_id: int
    tool_name: str
    tool_category: ToolCategory
    tool_types: list[ToolType]
    control_effect: ControlEffect
    implementation_level: ImplementationLevel
    confidence_source: ConfidenceSource
    confidence_level: ConfidenceLevel
    assessment_answers: list[ToolCapabilityAssessmentAnswerRead]
    configuration_status: ConfigurationStatus | None
    effectively_active: bool
    scopes: list[ToolCapabilityScopeRead]


class CapabilityDetailRead(BaseModel):
    capability: CapabilityRead
    assessment_template: AssessmentTemplateRead | None
    related_techniques: list[CapabilityTechniqueMapRead]
    implementing_tools: list[CapabilityImplementingToolRead]
    required_data_sources: list[CapabilityRequiredDataSourceRead]
    supported_response_actions: list[CapabilitySupportedResponseActionRead]
    configuration_questions: list[CapabilityConfigurationQuestionRead]


class ToolCapabilityTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: ToolCategory
    capability_id: int
    optional_tags: list[ToolTag]
    priority: TemplatePriority
    default_effect: Literal["detect", "block", "prevent"]
    default_implementation_level: Literal["partial", "full"]
    confidence_hint: str | None
    description: str | None
    capability: CapabilityRead
    matched_tags: list[ToolTag]
    suggestion_group: SuggestionGroup
    # ToolCapabilityTemplateRead references tool category, not tool_types —
    # templates are per-category so this stays as a single value.


class ToolCapabilityTemplateApplyItem(BaseModel):
    template_id: int
    control_effect: Literal["detect", "block", "prevent"] | None = None
    implementation_level: Literal["partial", "full"] | None = None


class ToolCapabilityTemplateApplyRequest(BaseModel):
    selected_templates: list[ToolCapabilityTemplateApplyItem]


class ToolTagRead(BaseModel):
    name: ToolTag
    default_categories: list[ToolCategory]


class ToolTagSuggestionRead(BaseModel):
    category: ToolCategory
    suggested_tags: list[ToolTagRead]


class DocsToolTypeRead(BaseModel):
    tool_type: ToolType
    tool_count: int
    description: str
    inputs: list[str]
    outputs: list[str]
    example_usage: list[str]


class DocsCapabilityRead(BaseModel):
    capability: CapabilityRead
    purpose: str
    typical_use_cases: list[str]
    tool_types: list[ToolType]
    implementing_tool_count: int
    related_techniques: list[str]


class DocsToolTypeMappingRead(BaseModel):
    tool_type: ToolType
    capabilities: list[CapabilityRead]


class DocsCapabilityMappingRead(BaseModel):
    capability: CapabilityRead
    tool_types: list[ToolType]


class DocsMappingRead(BaseModel):
    tool_type_mappings: list[DocsToolTypeMappingRead]
    capability_mappings: list[DocsCapabilityMappingRead]


class ToolDataSourceRead(BaseModel):
    id: int
    tool_id: int
    data_source_id: int
    ingestion_status: IngestionStatus
    notes: str
    data_source: DataSourceRead


class ToolDataSourceUpsert(BaseModel):
    data_source_id: int
    ingestion_status: IngestionStatus
    notes: str = ""


class ToolResponseActionRead(BaseModel):
    id: int
    tool_id: int
    response_action_id: int
    implementation_level: ImplementationLevel
    notes: str
    response_action: ResponseActionRead


class ToolResponseActionUpsert(BaseModel):
    response_action_id: int
    implementation_level: ImplementationLevel
    notes: str = ""


class BASValidationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    technique_id: int
    bas_tool_id: int | None
    bas_tool_name: str | None
    bas_result: BASResult
    last_validation_date: str | None
    notes: str


class BASValidationCreate(BaseModel):
    technique_id: int
    bas_tool_id: int | None = None
    bas_result: BASResult
    last_validation_date: str | None = None
    notes: str = ""


class BASValidationUpdate(BaseModel):
    bas_tool_id: int | None = None
    bas_result: BASResult | None = None
    last_validation_date: str | None = None
    notes: str | None = None


class ControlRead(BaseModel):
    """Structured view of a tool acting as an active security control.

    Tools whose tool_types contains ONLY 'assurance' are excluded.
    A tool with tool_types=['control','assurance'] IS included here because
    it also has an active control role.
    The primary_function is derived from the strongest control effect the
    tool applies across all its capabilities.
    """

    tool_id: int
    tool_name: str
    primary_category: ActiveControlCategory
    tool_types: list[ToolType]
    primary_function: ControlFunction
    covered_ttp_ids: list[str]


class TechniqueCoverageContributionRead(BaseModel):
    tool_id: int
    tool_name: str
    tool_category: ToolCategory
    tool_types: list[ToolType]
    capability_id: int
    capability_code: str
    capability_name: str
    control_effect: CoverageType
    implementation_level: ImplementationLevel
    confidence_level: ConfidenceLevel
    confidence_source: ConfidenceSource
    mapping_coverage: MappingCoverage
    dependency_warnings: list[str]
    configuration_status: ConfigurationStatus | None
    effectively_active: bool
    scopes: list[ToolCapabilityScopeRead]


class TechniqueCoverageResponseActionRead(BaseModel):
    tool_id: int
    tool_name: str
    action_code: str
    action_name: str
    implementation_level: ImplementationLevel


class TechniqueCoverageRead(BaseModel):
    technique_id: int
    technique_code: str
    technique_name: str
    # Direct link to the MITRE ATT&CK page for this technique.
    attack_url: str
    coverage_type: CoverageType
    effective_control_effect: CoverageType
    effective_outcome: EffectiveOutcome
    tool_count: int
    confidence_level: ConfidenceLevel
    coverage_status: CoverageStatus
    response_enabled: bool
    response_actions: list[TechniqueCoverageResponseActionRead]
    dependency_flags: list[str]
    contributing_tools: list[TechniqueCoverageContributionRead]
    relevant_scopes: list[TechniqueRelevantScopeRead]
    scope_summary: ScopeSummaryRead
    # BAS (Breach and Attack Simulation) assurance fields.
    # BAS is a cross-functional validation capability, not an active control.
    bas_validations: list[BASValidationRead]
    bas_validated: bool          # True when at least one non-"not_tested" result exists
    bas_result: BASResult | None # Most recent BAS result, None if never tested
    last_bas_validation_date: str | None
    is_gap_no_coverage: bool
    is_gap_detect_only: bool
    is_gap_partial: bool
    is_gap_low_confidence: bool
    is_gap_single_tool_dependency: bool
    is_gap_missing_data_sources: bool
    is_gap_detection_without_response: bool
    is_gap_response_without_detection: bool
    is_gap_unconfigured_control: bool
    is_gap_partially_configured_control: bool
    is_gap_scope_missing: bool
    is_gap_scope_partial: bool


ToolRead.model_rebuild()
BASValidationRead.model_rebuild()

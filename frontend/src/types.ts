export type ImplementationLevel = "none" | "partial" | "full";
export type CoverageType = "none" | "detect" | "block" | "prevent";
export type MappingCoverage = "full" | "partial";
export type ControlEffect = "none" | "detect" | "block" | "prevent";
export type ConfidenceSource = "declared" | "assessed" | "evidenced" | "tested";
export type ConfidenceLevel = "low" | "medium" | "high";
export type AssessmentAnswerValue = "yes" | "no" | "partial" | "unknown";
export type ConfigurationAnswerValue = "yes" | "no" | "partial" | "unknown";
export type CoverageStatus = "no_coverage" | "detect_only" | "partial" | "low_confidence" | "covered";
export type EffectiveOutcome = "none" | "detect" | "detect_with_response" | "block" | "prevent";
export type ToolCategory =
  | "EDR"
  | "PAM"
  | "DLP"
  | "SASE"
  | "DNS"
  | "Email"
  | "BAS"
  | "Identity"
  | "Security Analytics"
  | "SOAR"
  | "Other";
export type ToolType = "control" | "analytics" | "response";
export type ToolTag = string;
export type TemplatePriority = "core" | "secondary" | "niche";
export type SuggestionGroup = "core" | "recommended" | "optional";
export type TechniqueDisplayGroup = "core" | "extended";
export type IngestionStatus = "none" | "partial" | "full";
export type RequirementLevel = "required" | "recommended";
export type ConfigurationStatus = "unknown" | "not_enabled" | "partially_enabled" | "enabled";
export type ScopeStatus = "none" | "partial" | "full";
export type ScopeRelevance = "primary" | "secondary";
export type TacticName =
  | "Initial Access"
  | "Execution"
  | "Persistence / Privilege Escalation / Defense Evasion"
  | "Credential Access"
  | "Discovery"
  | "Lateral Movement"
  | "Command & Control"
  | "Collection / Exfiltration"
  | "Impact";

export interface Capability {
  id: number;
  code: string;
  name: string;
  domain: string;
  description: string;
  requires_data_sources: boolean;
  supported_by_analytics: boolean;
  supported_by_response: boolean;
  requires_configuration: boolean;
  configuration_profile_type: string | null;
}

export interface DataSource {
  id: number;
  code: string;
  name: string;
  category: string;
  description: string;
}

export interface CoverageScope {
  id: number;
  code: string;
  name: string;
  description: string;
}

export interface ResponseAction {
  id: number;
  code: string;
  name: string;
  description: string;
}

export interface CapabilityRequiredDataSource {
  data_source_id: number;
  requirement_level: RequirementLevel;
  data_source: DataSource;
}

export interface CapabilitySupportedResponseAction {
  response_action_id: number;
  response_action: ResponseAction;
}

export interface TechniqueRelevantScope {
  coverage_scope_id: number;
  relevance: ScopeRelevance;
  coverage_scope: CoverageScope;
}

export interface AssessmentQuestion {
  id: number;
  prompt: string;
  position: number;
}

export interface ConfigurationQuestion {
  id: number;
  question: string;
  applies_to_profile_type: string | null;
}

export interface AssessmentTemplate {
  id: number;
  capability_id: number;
  description: string;
  questions: AssessmentQuestion[];
}

export interface ToolCapabilityAssessmentAnswer {
  question_id: number;
  answer: AssessmentAnswerValue;
}

export interface ToolCapabilityEvidence {
  id: number;
  title: string;
  evidence_type: string;
  note: string;
  file_name: string | null;
  recorded_at: string;
}

export interface ConfidenceSummary {
  confidence_source: ConfidenceSource;
  confidence_level: ConfidenceLevel;
  answered_questions: number;
  total_questions: number;
  score: number;
  max_score: number;
  evidence_count: number;
}

export interface ConfigurationSummary {
  configuration_status: ConfigurationStatus;
  answered_questions: number;
  total_questions: number;
  score: number;
  max_score: number;
}

export interface ToolCapabilityConfigurationProfile {
  id: number;
  tool_id: number;
  capability_id: number;
  profile_type: string | null;
  configuration_status: ConfigurationStatus;
  notes: string;
  last_updated_at: string | null;
}

export interface ToolCapabilityConfigurationAnswer {
  question_id: number;
  answer: ConfigurationAnswerValue;
}

export interface ToolCapabilityScope {
  id: number;
  tool_capability_id: number;
  coverage_scope_id: number;
  status: ScopeStatus;
  notes: string;
  coverage_scope: CoverageScope;
}

export interface ScopeSummary {
  full_scopes: string[];
  partial_scopes: string[];
  missing_scopes: string[];
}

export interface ToolCapability {
  capability_id: number;
  control_effect: ControlEffect;
  implementation_level: ImplementationLevel;
  confidence_source: ConfidenceSource;
  confidence_level: ConfidenceLevel;
  scopes: ToolCapabilityScope[];
}

export interface Tool {
  id: number;
  name: string;
  category: ToolCategory;
  tool_type: ToolType;
  tags: ToolTag[];
  capabilities: ToolCapability[];
  data_sources: ToolDataSource[];
  response_actions: ToolResponseAction[];
}

export interface ToolCapabilityDetail {
  capability: Capability;
  assignment: ToolCapability;
  confidence: ConfidenceSummary;
  assessment_template: AssessmentTemplate | null;
  assessment_answers: ToolCapabilityAssessmentAnswer[];
  evidence: ToolCapabilityEvidence[];
  required_data_sources: CapabilityRequiredDataSource[];
  supported_response_actions: CapabilitySupportedResponseAction[];
  configuration_profile: ToolCapabilityConfigurationProfile | null;
  configuration_summary: ConfigurationSummary | null;
  configuration_questions: ConfigurationQuestion[];
  configuration_answers: ToolCapabilityConfigurationAnswer[];
  scopes: ToolCapabilityScope[];
  relevant_scopes: TechniqueRelevantScope[];
}

export interface CapabilityImplementingTool {
  tool_id: number;
  tool_name: string;
  tool_category: ToolCategory;
  tool_type: ToolType;
  control_effect: ControlEffect;
  implementation_level: ImplementationLevel;
  confidence_source: ConfidenceSource;
  confidence_level: ConfidenceLevel;
  assessment_answers: ToolCapabilityAssessmentAnswer[];
  configuration_status: ConfigurationStatus | null;
  effectively_active: boolean;
  scopes: ToolCapabilityScope[];
}

export interface CapabilityTechniqueLink {
  technique_id: number;
  technique_code: string;
  technique_name: string;
  control_effect: Exclude<ControlEffect, "none">;
  coverage: MappingCoverage;
}

export interface CapabilityDetail {
  capability: Capability;
  assessment_template: AssessmentTemplate | null;
  related_techniques: CapabilityTechniqueLink[];
  implementing_tools: CapabilityImplementingTool[];
  required_data_sources: CapabilityRequiredDataSource[];
  supported_response_actions: CapabilitySupportedResponseAction[];
  configuration_questions: ConfigurationQuestion[];
}

export interface ToolTagDefinition {
  name: ToolTag;
  default_categories: ToolCategory[];
}

export interface ToolDataSource {
  id: number;
  tool_id: number;
  data_source_id: number;
  ingestion_status: IngestionStatus;
  notes: string;
  data_source: DataSource;
}

export interface ToolResponseAction {
  id: number;
  tool_id: number;
  response_action_id: number;
  implementation_level: ImplementationLevel;
  notes: string;
  response_action: ResponseAction;
}

export interface ToolCapabilityTemplate {
  id: number;
  category: ToolCategory;
  capability_id: number;
  optional_tags: ToolTag[];
  priority: TemplatePriority;
  default_effect: Exclude<ControlEffect, "none">;
  default_implementation_level: Exclude<ImplementationLevel, "none">;
  confidence_hint: string | null;
  description: string | null;
  capability: Capability;
  matched_tags: ToolTag[];
  suggestion_group: SuggestionGroup;
}

export interface TechniqueCoverage {
  technique_id: number;
  technique_code: string;
  technique_name: string;
  coverage_type: CoverageType;
  effective_control_effect: CoverageType;
  effective_outcome: EffectiveOutcome;
  tool_count: number;
  confidence_level: ConfidenceLevel;
  coverage_status: CoverageStatus;
  response_enabled: boolean;
  response_actions: TechniqueResponseAction[];
  dependency_flags: string[];
  contributing_tools: TechniqueCoverageContribution[];
  relevant_scopes: TechniqueRelevantScope[];
  scope_summary: ScopeSummary;
  is_gap_no_coverage: boolean;
  is_gap_detect_only: boolean;
  is_gap_partial: boolean;
  is_gap_low_confidence: boolean;
  is_gap_single_tool_dependency: boolean;
  is_gap_missing_data_sources: boolean;
  is_gap_detection_without_response: boolean;
  is_gap_response_without_detection: boolean;
  is_gap_unconfigured_control: boolean;
  is_gap_partially_configured_control: boolean;
  is_gap_scope_missing: boolean;
  is_gap_scope_partial: boolean;
}

export interface CapabilityContribution {
  capabilityId: number;
  capabilityCode: string;
  capabilityName: string;
  toolId: number;
  toolName: string;
  controlEffect: CoverageType;
  configuredEffect: ControlEffect;
  implementationLevel: ImplementationLevel;
  mappingCoverage: MappingCoverage;
  confidenceSource: ConfidenceSource;
  confidenceLevel: ConfidenceLevel;
  toolCategory: ToolCategory;
  toolType: ToolType;
  dependencyWarnings: string[];
  configurationStatus: ConfigurationStatus | null;
  effectivelyActive: boolean;
  scopes: ToolCapabilityScope[];
}

export interface TechniqueCoverageContribution {
  tool_id: number;
  tool_name: string;
  tool_category: ToolCategory;
  tool_type: ToolType;
  capability_id: number;
  capability_code: string;
  capability_name: string;
  control_effect: CoverageType;
  implementation_level: ImplementationLevel;
  confidence_level: ConfidenceLevel;
  confidence_source: ConfidenceSource;
  mapping_coverage: MappingCoverage;
  dependency_warnings: string[];
  configuration_status: ConfigurationStatus | null;
  effectively_active: boolean;
  scopes: ToolCapabilityScope[];
}

export interface TechniqueResponseAction {
  tool_id: number;
  tool_name: string;
  action_code: string;
  action_name: string;
  implementation_level: ImplementationLevel;
}

export interface DerivedTechnique extends TechniqueCoverage {
  tactic: TacticName;
  display_group: TechniqueDisplayGroup;
  contributions: CapabilityContribution[];
}

export interface ToolCoverageSummary {
  id: number | "all";
  name: string;
}

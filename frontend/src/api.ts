import type {
  AssessmentAnswerValue,
  BASResult,
  BASValidation,
  Capability,
  CapabilityDetail,
  ControlRead,
  CoverageScope,
  ConfigurationAnswerValue,
  ControlEffect,
  DataSource,
  DocsCapability,
  DocsMapping,
  DocsToolType,
  ImplementationLevel,
  ResponseAction,
  TechniqueCoverage,
  Tool,
  ToolCapabilityDetail,
  ToolCapabilityEvidence,
  ToolCategory,
  ToolTagDefinition,
  ToolCapabilityTemplate,
  ToolType,
  IngestionStatus,
  ScopeStatus,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail ?? "Request failed");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function listTools() {
  return request<Tool[]>("/tools");
}

export function createTool(name: string, category: ToolCategory, toolTypes: ToolType[], tags: string[]) {
  return request<Tool>("/tools", {
    method: "POST",
    body: JSON.stringify({ name, category, tool_types: toolTypes, tags }),
  });
}

export function deleteTool(toolId: number) {
  return request<void>(`/tools/${toolId}`, {
    method: "DELETE",
  });
}

export function listCapabilities() {
  return request<Capability[]>("/capabilities");
}

export function getCapabilityDetail(capabilityId: number) {
  return request<CapabilityDetail>(`/capabilities/${capabilityId}`);
}

export function listTags() {
  return request<ToolTagDefinition[]>("/tags");
}

export function listDataSources() {
  return request<DataSource[]>("/data-sources");
}

export function listCoverageScopes() {
  return request<CoverageScope[]>("/coverage-scopes");
}

export function listResponseActions() {
  return request<ResponseAction[]>("/response-actions");
}

export function listDocsToolTypes() {
  return request<DocsToolType[]>("/docs/tool-types");
}

export function listDocsCapabilities() {
  return request<DocsCapability[]>("/docs/capabilities");
}

export function getDocsMappings() {
  return request<DocsMapping>("/docs/mappings");
}

export function updateToolTags(toolId: number, tags: string[]) {
  return request<Tool>(`/tools/${toolId}/tags`, {
    method: "PUT",
    body: JSON.stringify({ tags }),
  });
}

export function updateToolTypes(toolId: number, toolTypes: ToolType[]) {
  return request<Tool>(`/tools/${toolId}/tool-types`, {
    method: "PUT",
    body: JSON.stringify({ tool_types: toolTypes }),
  });
}

export function listToolTemplates(category: ToolCategory, tags: string[]) {
  const query = new URLSearchParams({ category });
  for (const tag of tags) {
    query.append("tags", tag);
  }
  return request<ToolCapabilityTemplate[]>(`/templates?${query.toString()}`);
}

export function setToolCapability(
  toolId: number,
  capabilityId: number,
  controlEffect: ControlEffect,
  implementationLevel: ImplementationLevel,
) {
  return request<Tool>(`/tools/${toolId}/capabilities`, {
    method: "POST",
    body: JSON.stringify({
      capability_id: capabilityId,
      control_effect: controlEffect,
      implementation_level: implementationLevel,
    }),
  });
}

export function setToolDataSource(
  toolId: number,
  dataSourceId: number,
  ingestionStatus: IngestionStatus,
  notes: string,
) {
  return request<Tool>(`/tools/${toolId}/data-sources`, {
    method: "POST",
    body: JSON.stringify({
      data_source_id: dataSourceId,
      ingestion_status: ingestionStatus,
      notes,
    }),
  });
}

export function setToolResponseAction(
  toolId: number,
  responseActionId: number,
  implementationLevel: Exclude<ImplementationLevel, "none"> | "none",
  notes: string,
) {
  return request<Tool>(`/tools/${toolId}/response-actions`, {
    method: "POST",
    body: JSON.stringify({
      response_action_id: responseActionId,
      implementation_level: implementationLevel,
      notes,
    }),
  });
}

export function applyToolTemplates(
  toolId: number,
  selectedTemplates: Array<{
    template_id: number;
    control_effect?: Exclude<ControlEffect, "none">;
    implementation_level?: Exclude<ImplementationLevel, "none">;
  }>,
) {
  return request<Tool>(`/tools/${toolId}/templates`, {
    method: "POST",
    body: JSON.stringify({ selected_templates: selectedTemplates }),
  });
}

export function getToolCapabilityDetail(toolId: number, capabilityId: number) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}`);
}

export function saveToolCapabilityAssessment(
  toolId: number,
  capabilityId: number,
  answers: Array<{ question_id: number; answer: AssessmentAnswerValue }>,
) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}/assessment-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function saveToolCapabilityConfigurationProfile(
  toolId: number,
  capabilityId: number,
  notes: string,
) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}/configuration-profile`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
}

export function saveToolCapabilityConfigurationAnswers(
  toolId: number,
  capabilityId: number,
  answers: Array<{ question_id: number; answer: ConfigurationAnswerValue }>,
) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}/configuration-answers`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function saveToolCapabilityScopes(
  toolId: number,
  capabilityId: number,
  scopes: Array<{ coverage_scope_id: number; status: ScopeStatus; notes: string }>,
) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}/scopes`, {
    method: "POST",
    body: JSON.stringify({ scopes }),
  });
}

export function addToolCapabilityEvidence(
  toolId: number,
  capabilityId: number,
  payload: {
    title: string;
    evidence_type: string;
    note: string;
    file_name: string | null;
    recorded_at: string;
  },
) {
  return request<ToolCapabilityDetail>(`/tools/${toolId}/capabilities/${capabilityId}/evidence`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listToolCapabilityEvidence(toolId: number, capabilityId: number) {
  return request<ToolCapabilityEvidence[]>(`/tools/${toolId}/capabilities/${capabilityId}/evidence`);
}

export function listCoverage() {
  return request<TechniqueCoverage[]>("/coverage");
}

// ---------------------------------------------------------------------------
// Controls — active security controls (excludes BAS / assurance tools)
// ---------------------------------------------------------------------------

export function listControls() {
  return request<ControlRead[]>("/controls");
}

// ---------------------------------------------------------------------------
// BAS Validations
// BAS is a cross-functional assurance/validation capability.  These calls
// record and retrieve BAS test outcomes per technique (TTP).  BAS results
// do NOT affect the active coverage computation — they only reflect whether
// adversary simulation confirmed or bypassed the existing controls.
// ---------------------------------------------------------------------------

export function listBASValidations(techniqueId: number) {
  return request<BASValidation[]>(`/techniques/${techniqueId}/bas-validations`);
}

export function createBASValidation(
  techniqueId: number,
  payload: {
    bas_tool_id: number | null;
    bas_result: BASResult;
    last_validation_date: string | null;
    notes?: string;
  },
) {
  return request<BASValidation>(`/techniques/${techniqueId}/bas-validations`, {
    method: "POST",
    body: JSON.stringify({ technique_id: techniqueId, ...payload }),
  });
}

export function updateBASValidation(
  validationId: number,
  payload: {
    bas_tool_id?: number | null;
    bas_result?: BASResult;
    last_validation_date?: string | null;
    notes?: string;
  },
) {
  return request<BASValidation>(`/bas-validations/${validationId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function deleteBASValidation(validationId: number) {
  return request<void>(`/bas-validations/${validationId}`, {
    method: "DELETE",
  });
}

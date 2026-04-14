import { useEffect, useMemo, useState } from "react";

import { getToolCapabilityDetail } from "../api";
import { Card } from "../components/Card";
import type {
  AssessmentAnswerValue,
  Capability,
  CoverageScope,
  ConfigurationAnswerValue,
  DataSource,
  ScopeStatus,
  Tool,
  ToolTag,
  ToolCapabilityDetail,
  ControlEffect,
  ImplementationLevel,
  ResponseAction,
  ToolDataSource,
  ToolResponseAction,
  ToolType,
} from "../types";

interface ToolDetailPageProps {
  toolId: number;
  tools: Tool[];
  capabilities: Capability[];
  dataSources: DataSource[];
  coverageScopes: CoverageScope[];
  responseActions: ResponseAction[];
  onDeleteTool: (tool: Tool) => Promise<void>;
  onSetCapability: (
    toolId: number,
    capabilityId: number,
    controlEffect: ControlEffect,
    implementationLevel: ImplementationLevel,
  ) => Promise<void>;
  onSaveAssessment: (
    toolId: number,
    capabilityId: number,
    answers: Array<{ question_id: number; answer: AssessmentAnswerValue }>,
  ) => Promise<void>;
  onAddEvidence: (
    toolId: number,
    capabilityId: number,
    payload: {
      title: string;
      evidence_type: string;
      note: string;
      file_name: string | null;
      recorded_at: string;
    },
  ) => Promise<void>;
  onSaveConfigurationProfile: (toolId: number, capabilityId: number, notes: string) => Promise<void>;
  onSaveConfigurationAnswers: (
    toolId: number,
    capabilityId: number,
    answers: Array<{ question_id: number; answer: ConfigurationAnswerValue }>,
  ) => Promise<void>;
  onSaveCapabilityScopes: (
    toolId: number,
    capabilityId: number,
    scopes: Array<{ coverage_scope_id: number; status: ScopeStatus; notes: string }>,
  ) => Promise<void>;
  onSetToolDataSource: (
    toolId: number,
    dataSourceId: number,
    ingestionStatus: "none" | "partial" | "full",
    notes: string,
  ) => Promise<void>;
  onSetToolResponseAction: (
    toolId: number,
    responseActionId: number,
    implementationLevel: "none" | "partial" | "full",
    notes: string,
  ) => Promise<void>;
  onUpdateTags: (toolId: number, tags: ToolTag[]) => Promise<void>;
  onUpdateToolTypes: (toolId: number, toolTypes: ToolType[]) => Promise<void>;
}

const assessmentOptions: AssessmentAnswerValue[] = ["yes", "partial", "no", "unknown"];
const configurationOptions: ConfigurationAnswerValue[] = ["yes", "partial", "no", "unknown"];

export function ToolDetailPage({
  toolId,
  tools,
  capabilities,
  dataSources,
  coverageScopes,
  responseActions,
  onDeleteTool,
  onSetCapability,
  onSetToolDataSource,
  onSetToolResponseAction,
  onSaveAssessment,
  onAddEvidence,
  onSaveConfigurationProfile,
  onSaveConfigurationAnswers,
  onSaveCapabilityScopes,
  onUpdateTags,
  onUpdateToolTypes,
}: ToolDetailPageProps) {
  const tool = tools.find((entry) => entry.id === toolId);
  const [expandedCapabilityId, setExpandedCapabilityId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ToolCapabilityDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [assessmentDraft, setAssessmentDraft] = useState<Record<number, AssessmentAnswerValue>>({});
  const [configurationDraft, setConfigurationDraft] = useState<Record<number, ConfigurationAnswerValue>>({});
  const [configurationNotes, setConfigurationNotes] = useState("");
  const [scopeDraft, setScopeDraft] = useState<Record<number, ScopeStatus>>({});
  const [scopeNotes, setScopeNotes] = useState<Record<number, string>>({});
  const [tagDraft, setTagDraft] = useState<ToolTag[]>(tool?.tags ?? []);
  const [toolTypesDraft, setToolTypesDraft] = useState<ToolType[]>(tool?.tool_types ?? []);
  const [dataSourceNotes, setDataSourceNotes] = useState<Record<number, string>>({});
  const [responseActionNotes, setResponseActionNotes] = useState<Record<number, string>>({});
  const [customTag, setCustomTag] = useState("");
  const [evidenceDraft, setEvidenceDraft] = useState({
    title: "",
    evidence_type: "",
    note: "",
    file_name: "",
    recorded_at: new Date().toISOString().slice(0, 10),
  });

  useEffect(() => {
    setTagDraft(tool?.tags ?? []);
    setToolTypesDraft(tool?.tool_types ?? []);
  }, [tool]);

  useEffect(() => {
    setDataSourceNotes(
      Object.fromEntries((tool?.data_sources ?? []).map((item) => [item.data_source_id, item.notes])),
    );
    setResponseActionNotes(
      Object.fromEntries((tool?.response_actions ?? []).map((item) => [item.response_action_id, item.notes])),
    );
  }, [tool]);

  useEffect(() => {
    if (!tool || expandedCapabilityId === null) {
      setDetail(null);
      return;
    }

    const assignment = tool.capabilities.find((item) => item.capability_id === expandedCapabilityId);
    if (!assignment || assignment.control_effect === "none" || assignment.implementation_level === "none") {
      setDetail(null);
      return;
    }

    setDetailLoading(true);
    void getToolCapabilityDetail(tool.id, expandedCapabilityId)
      .then((payload) => {
        setDetail(payload);
        setAssessmentDraft(
          Object.fromEntries((payload.assessment_answers ?? []).map((answer) => [answer.question_id, answer.answer])),
        );
        setConfigurationDraft(
          Object.fromEntries((payload.configuration_answers ?? []).map((answer) => [answer.question_id, answer.answer])),
        );
        setConfigurationNotes(payload.configuration_profile?.notes ?? "");
        setScopeDraft(
          Object.fromEntries((payload.scopes ?? []).map((scope) => [scope.coverage_scope_id, scope.status])),
        );
        setScopeNotes(
          Object.fromEntries((payload.scopes ?? []).map((scope) => [scope.coverage_scope_id, scope.notes])),
        );
      })
      .finally(() => setDetailLoading(false));
  }, [expandedCapabilityId, tool]);

  const assignments = useMemo(
    () => new Map(tool?.capabilities.map((capability) => [capability.capability_id, capability]) ?? []),
    [tool],
  );
  const dataSourceAssignments = useMemo(
    () => new Map(tool?.data_sources.map((entry) => [entry.data_source_id, entry]) ?? []),
    [tool],
  );
  const responseActionAssignments = useMemo(
    () => new Map(tool?.response_actions.map((entry) => [entry.response_action_id, entry]) ?? []),
    [tool],
  );

  if (!tool) {
    return (
      <Card title="Tool not found" subtitle="Tool detail">
        <h2>Tool not found</h2>
        <a href="#/tools" className="back-link">
          Return to tools
        </a>
      </Card>
    );
  }

  const activeTool = tool;

  async function saveTags() {
    await onUpdateTags(activeTool.id, tagDraft);
  }

  const ALL_TOOL_TYPES: ToolType[] = ["control", "analytics", "response", "assurance"];
  const TOOL_TYPE_LABEL: Record<ToolType, string> = {
    control: "control",
    analytics: "analytics",
    response: "response",
    assurance: "Validated",
  };

  function toggleToolType(type: ToolType) {
    setToolTypesDraft((current) =>
      current.includes(type) ? current.filter((t) => t !== type) : [...current, type],
    );
  }

  async function saveToolTypes() {
    if (toolTypesDraft.length === 0) {
      return;
    }
    await onUpdateToolTypes(activeTool.id, toolTypesDraft);
  }

  async function submitAssessment() {
    if (!detail?.assessment_template) {
      return;
    }

    const answers = detail.assessment_template.questions.map((question) => ({
      question_id: question.id,
      answer: assessmentDraft[question.id] ?? "unknown",
    }));

    await onSaveAssessment(activeTool.id, detail.capability.id, answers);
    const refreshed = await getToolCapabilityDetail(activeTool.id, detail.capability.id);
    setDetail(refreshed);
    setAssessmentDraft(
      Object.fromEntries(refreshed.assessment_answers.map((answer) => [answer.question_id, answer.answer])),
    );
  }

  async function submitConfiguration() {
    if (!detail?.capability.requires_configuration) {
      return;
    }

    await onSaveConfigurationProfile(activeTool.id, detail.capability.id, configurationNotes);
    if (detail.configuration_questions.length > 0) {
      await onSaveConfigurationAnswers(
        activeTool.id,
        detail.capability.id,
        detail.configuration_questions.map((question) => ({
          question_id: question.id,
          answer: configurationDraft[question.id] ?? "unknown",
        })),
      );
    }

    const refreshed = await getToolCapabilityDetail(activeTool.id, detail.capability.id);
    setDetail(refreshed);
    setConfigurationDraft(
      Object.fromEntries(refreshed.configuration_answers.map((answer) => [answer.question_id, answer.answer])),
    );
    setConfigurationNotes(refreshed.configuration_profile?.notes ?? "");
  }

  async function submitEvidence() {
    if (!detail) {
      return;
    }

    await onAddEvidence(activeTool.id, detail.capability.id, {
      title: evidenceDraft.title,
      evidence_type: evidenceDraft.evidence_type,
      note: evidenceDraft.note,
      file_name: evidenceDraft.file_name.trim() || null,
      recorded_at: evidenceDraft.recorded_at,
    });
    const refreshed = await getToolCapabilityDetail(activeTool.id, detail.capability.id);
    setDetail(refreshed);
    setEvidenceDraft((current) => ({
      ...current,
      title: "",
      evidence_type: "",
      note: "",
      file_name: "",
    }));
  }

  async function submitScopes() {
    if (!detail) {
      return;
    }

    await onSaveCapabilityScopes(
      activeTool.id,
      detail.capability.id,
      coverageScopes.map((scope) => ({
        coverage_scope_id: scope.id,
        status: scopeDraft[scope.id] ?? "none",
        notes: scopeNotes[scope.id] ?? "",
      })),
    );

    const refreshed = await getToolCapabilityDetail(activeTool.id, detail.capability.id);
    setDetail(refreshed);
    setScopeDraft(
      Object.fromEntries(refreshed.scopes.map((scope) => [scope.coverage_scope_id, scope.status])),
    );
    setScopeNotes(
      Object.fromEntries(refreshed.scopes.map((scope) => [scope.coverage_scope_id, scope.notes])),
    );
  }

  return (
    <div className="stack page-stack">
      <Card
        title={tool.name}
        subtitle="Tool detail"
        actions={
          <>
            <span className="count-chip">{tool.category}</span>
            <button
              type="button"
              className="danger-button"
              onClick={() => void onDeleteTool(tool)}
            >
              Delete tool
            </button>
            <a href="#/tools" className="back-link">
              Back to tools
            </a>
          </>
        }
      >
        <p className="section-copy">
          Configure one capability per control area, then improve confidence with an assessment or evidence.
        </p>
      </Card>

      <Card title="Classification" subtitle="Category and tags">
        <div className="workspace-section-header">
          <div>
            <p className="section-copy">
              Primary category stays simple. Tags capture hybrid behavior like Active Directory or Password Security.
            </p>
          </div>
          <div className="workspace-badges">
            <span className="count-chip">{activeTool.category}</span>
          </div>
        </div>

        <div className="workspace-section">
          <div className="workspace-section-header">
            <div>
              <p className="eyebrow">Tool types</p>
              <strong className="workspace-title">Select all roles this tool fulfills</strong>
            </div>
            <button
              type="button"
              className="primary-button"
              disabled={toolTypesDraft.length === 0}
              onClick={() => void saveToolTypes()}
            >
              Save types
            </button>
          </div>
          <div className="tag-chip-row">
            {ALL_TOOL_TYPES.map((type) => (
              <label key={type} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={toolTypesDraft.includes(type)}
                  onChange={() => toggleToolType(type)}
                />
                {TOOL_TYPE_LABEL[type]}
              </label>
            ))}
          </div>
        </div>

        <div className="custom-tag-row">
          <input
            className="text-input"
            placeholder="Add tag"
            value={customTag}
            onChange={(event) => setCustomTag(event.target.value)}
          />
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              const nextTag = customTag.trim();
              if (!nextTag || tagDraft.includes(nextTag)) {
                return;
              }
              setTagDraft((current) => [...current, nextTag]);
              setCustomTag("");
            }}
          >
            Add tag
          </button>
          <button type="button" className="primary-button" onClick={() => void saveTags()}>
            Save tags
          </button>
        </div>
        <div className="tag-chip-row">
          {tagDraft.length === 0 ? (
            <span className="muted">No tags yet.</span>
          ) : (
            tagDraft.map((tag) => (
              <button
                key={tag}
                type="button"
                className="tag-chip"
                onClick={() => setTagDraft((current) => current.filter((entry) => entry !== tag))}
              >
                {tag}
              </button>
            ))
          )}
        </div>
      </Card>

      {activeTool.tool_types.includes("analytics") ? (
        <Card title="Data Sources" subtitle="Analytics dependencies">
          <p className="section-copy">
            Analytics tools only contribute credible coverage when the required data sources are actually ingested.
          </p>
          <div className="capability-list">
            {dataSources.map((dataSource) => {
              const assignment = dataSourceAssignments.get(dataSource.id);
              const ingestionStatus = assignment?.ingestion_status ?? "none";
              return (
                <div key={dataSource.id} className="capability-card">
                  <div className="capability-card-main">
                    <div>
                      <strong className="capability-title">{dataSource.name}</strong>
                      <p className="muted">{dataSource.description}</p>
                    </div>
                    <span className="domain-pill">{dataSource.category}</span>
                  </div>
                  <div className="capability-controls">
                    <label className="implementation-control">
                      <span>Ingestion</span>
                      <select
                        className="level-select"
                        value={ingestionStatus}
                        onChange={(event) =>
                          void onSetToolDataSource(
                            activeTool.id,
                            dataSource.id,
                            event.target.value as "none" | "partial" | "full",
                            dataSourceNotes[dataSource.id] ?? "",
                          )
                        }
                      >
                        <option value="none">None</option>
                        <option value="partial">Partial</option>
                        <option value="full">Full</option>
                      </select>
                    </label>
                    <label className="implementation-control notes-control">
                      <span>Notes</span>
                      <input
                        className="text-input"
                        placeholder="Optional note"
                        value={dataSourceNotes[dataSource.id] ?? ""}
                        onChange={(event) =>
                          setDataSourceNotes((current) => ({ ...current, [dataSource.id]: event.target.value }))
                        }
                        onBlur={() =>
                          void onSetToolDataSource(
                            activeTool.id,
                            dataSource.id,
                            ingestionStatus,
                            dataSourceNotes[dataSource.id] ?? "",
                          )
                        }
                      />
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      ) : null}

      {activeTool.tool_types.includes("response") ? (
        <Card title="Response Actions" subtitle="Operational response">
          <p className="section-copy">
            Response tools do not detect anything by themselves. They only strengthen coverage when upstream detections exist.
          </p>
          <div className="capability-list">
            {responseActions.map((action) => {
              const assignment = responseActionAssignments.get(action.id);
              const implementationLevel = assignment?.implementation_level ?? "none";
              return (
                <div key={action.id} className="capability-card">
                  <div className="capability-card-main">
                    <div>
                      <strong className="capability-title">{action.name}</strong>
                      <p className="muted">{action.description}</p>
                    </div>
                    <span className="domain-pill">response</span>
                  </div>
                  <div className="capability-controls">
                    <label className="implementation-control">
                      <span>Implementation</span>
                      <select
                        className="level-select"
                        value={implementationLevel}
                        onChange={(event) =>
                          void onSetToolResponseAction(
                            activeTool.id,
                            action.id,
                            event.target.value as "none" | "partial" | "full",
                            responseActionNotes[action.id] ?? "",
                          )
                        }
                      >
                        <option value="none">None</option>
                        <option value="partial">Partial</option>
                        <option value="full">Full</option>
                      </select>
                    </label>
                    <label className="implementation-control notes-control">
                      <span>Notes</span>
                      <input
                        className="text-input"
                        placeholder="Optional note"
                        value={responseActionNotes[action.id] ?? ""}
                        onChange={(event) =>
                          setResponseActionNotes((current) => ({ ...current, [action.id]: event.target.value }))
                        }
                        onBlur={() =>
                          void onSetToolResponseAction(
                            activeTool.id,
                            action.id,
                            implementationLevel,
                            responseActionNotes[action.id] ?? "",
                          )
                        }
                      />
                    </label>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      ) : null}

      {activeTool.capabilities.length < 2 ? (
        <Card title="Coverage hint" subtitle="Onboarding">
          <p className="section-copy">
            This tool currently has very few capabilities assigned. Add more if the product covers additional areas.
          </p>
        </Card>
      ) : null}

      {activeTool.capabilities.length > 0 &&
      activeTool.capabilities.every((capability) => capability.control_effect === "detect") ? (
        <Card title="Coverage hint" subtitle="Control posture">
          <p className="section-copy">
            This tool is only detecting threats right now, not blocking or preventing them.
          </p>
        </Card>
      ) : null}

      <Card title="Capabilities" subtitle="Assignments">
        <p className="section-copy">
          Each capability carries an effect, implementation level, and confidence state.
        </p>

        <div className="capability-list">
          {capabilities.map((capability) => {
            const assignment = assignments.get(capability.id);
            const effect = assignment?.control_effect ?? "none";
            const level = assignment?.implementation_level ?? "none";
            const enabled = effect !== "none" && level !== "none";
            const isExpanded = expandedCapabilityId === capability.id;

            return (
              <div key={capability.id} className={`capability-card ${isExpanded ? "expanded" : ""}`.trim()}>
                <div className="capability-card-main">
                  <div>
                    <a href={`#/capabilities/${capability.id}`} className="capability-link">
                      <strong className="capability-title">{capability.name}</strong>
                    </a>
                    <p className="muted">{capability.description}</p>
                    {capability.requires_configuration ? (
                      <p className="muted">Requires configuration verification.</p>
                    ) : null}
                    <div className="capability-meta-row">
                      <span className="muted">{capability.code}</span>
                      {assignment ? (
                        <>
                          <span className={`coverage-pill ${assignment.control_effect}`}>
                            {assignment.control_effect}
                          </span>
                          <span className="count-chip">{assignment.implementation_level}</span>
                          <span className={`coverage-pill ${assignment.confidence_level}`}>
                            {assignment.confidence_source} / {assignment.confidence_level}
                          </span>
                          {detail?.capability.id === capability.id && detail.configuration_summary ? (
                            <span className="count-chip">
                              config / {detail.configuration_summary.configuration_status}
                            </span>
                          ) : capability.requires_configuration ? (
                            <span className="count-chip">config pending</span>
                          ) : null}
                          {detail?.capability.id === capability.id && (detail.scopes?.length ?? 0) > 0 ? (
                            <span className="count-chip">
                              scope / {(detail.scopes ?? []).map((scope) => `${scope.coverage_scope.code}:${scope.status}`).join(", ")}
                            </span>
                          ) : null}
                        </>
                      ) : (
                        <span className="count-chip">Unassigned</span>
                      )}
                    </div>
                  </div>
                  <span className="domain-pill">{capability.domain}</span>
                </div>

                <div className="capability-controls">
                  <label className="implementation-control">
                    <span>Effect</span>
                    <select
                      className="level-select"
                      value={effect}
                      onChange={(event) => {
                        const nextEffect = event.target.value as ControlEffect;
                        void onSetCapability(
                          tool.id,
                          capability.id,
                          nextEffect,
                          nextEffect === "none" ? "none" : enabled ? level : "partial",
                        );
                      }}
                    >
                      <option value="none">None</option>
                      <option value="detect">Detect</option>
                      {activeTool.tool_types.includes("control") ? <option value="block">Block</option> : null}
                      {activeTool.tool_types.includes("control") ? <option value="prevent">Prevent</option> : null}
                    </select>
                  </label>

                  <label className="implementation-control">
                    <span>Implementation</span>
                    <select
                      className="level-select"
                      disabled={effect === "none"}
                      value={enabled ? level : "partial"}
                      onChange={(event) =>
                        void onSetCapability(
                          tool.id,
                          capability.id,
                          effect,
                          event.target.value as ImplementationLevel,
                        )
                      }
                    >
                      <option value="partial">Partial</option>
                      <option value="full">Full</option>
                    </select>
                  </label>

                  <div className="capability-action-group">
                    <button
                      type="button"
                      className="secondary-button"
                      disabled={!enabled}
                      onClick={() =>
                        setExpandedCapabilityId((current) =>
                          current === capability.id ? null : capability.id,
                        )
                      }
                    >
                      {isExpanded
                        ? "Close workspace"
                        : capability.requires_configuration
                          ? "Verify configuration"
                          : "Open workspace"}
                    </button>
                    <a href={`#/capabilities/${capability.id}`} className="secondary-link">
                      View capability
                    </a>
                  </div>
                </div>

                {isExpanded ? (
                  <div className="capability-detail-workspace">
                    {detailLoading ? (
                      <div className="empty-state compact">
                        <p>Loading assessment and evidence...</p>
                      </div>
                    ) : detail ? (
                      <>
                        <div className="workspace-section">
                          <div className="workspace-section-header">
                            <div>
                              <p className="eyebrow">Confidence</p>
                              <strong className="workspace-title">
                                {detail.confidence.confidence_source} / {detail.confidence.confidence_level}
                              </strong>
                            </div>
                            <div className="workspace-badges">
                              <span className="count-chip">
                                {detail.confidence.answered_questions}/{detail.confidence.total_questions} answered
                              </span>
                              <span className="count-chip">{detail.confidence.evidence_count} evidence</span>
                            </div>
                          </div>
                          <p className="muted">
                            Score {detail.confidence.score} / {detail.confidence.max_score}. Declared starts low,
                            assessments raise confidence by score, and evidence upgrades the source to evidenced.
                          </p>
                          {detail.required_data_sources.length > 0 ? (
                            <p className="muted">
                              Depends on data sources:{" "}
                              {detail.required_data_sources
                                .map((entry) => `${entry.data_source.name} (${entry.requirement_level})`)
                                .join(", ")}
                            </p>
                          ) : null}
                          {detail.supported_response_actions.length > 0 ? (
                            <p className="muted">
                              Response capable via:{" "}
                              {detail.supported_response_actions
                                .map((entry) => entry.response_action.name)
                                .join(", ")}
                            </p>
                          ) : null}
                          {detail.scopes.length > 0 ? (
                            <p className="muted">
                              Assigned scope: {detail.scopes.map((scope) => `${scope.coverage_scope.name} (${scope.status})`).join(", ")}
                            </p>
                          ) : (
                            <p className="muted">No scope assigned yet. Coverage without scope is treated as weak or missing.</p>
                          )}
                        </div>

                        <div className="workspace-section">
                          <div className="workspace-section-header">
                            <div>
                              <p className="eyebrow">Coverage Scope</p>
                              <strong className="workspace-title">Where this capability applies</strong>
                            </div>
                            <button type="button" className="primary-button" onClick={() => void submitScopes()}>
                              Save scope
                            </button>
                          </div>
                          <div className="assessment-list">
                            {coverageScopes.map((scope) => (
                              <div key={scope.id} className="assessment-question">
                                <span>{scope.name}</span>
                                <div className="capability-controls">
                                  <select
                                    className="level-select"
                                    value={scopeDraft[scope.id] ?? "none"}
                                    onChange={(event) =>
                                      setScopeDraft((current) => ({
                                        ...current,
                                        [scope.id]: event.target.value as ScopeStatus,
                                      }))
                                    }
                                  >
                                    <option value="none">None</option>
                                    <option value="partial">Partial</option>
                                    <option value="full">Full</option>
                                  </select>
                                  <input
                                    className="text-input"
                                    placeholder="Optional note"
                                    value={scopeNotes[scope.id] ?? ""}
                                    onChange={(event) =>
                                      setScopeNotes((current) => ({
                                        ...current,
                                        [scope.id]: event.target.value,
                                      }))
                                    }
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {detail.capability.requires_configuration ? (
                          <div className="workspace-section">
                            <div className="workspace-section-header">
                              <div>
                                <p className="eyebrow">Configuration</p>
                                <strong className="workspace-title">Verification checklist</strong>
                              </div>
                              <button type="button" className="primary-button" onClick={() => void submitConfiguration()}>
                                Save verification
                              </button>
                            </div>
                            <p className="muted">
                              Status {detail.configuration_summary?.configuration_status ?? "unknown"}.
                              Installed tool is not treated as effective coverage until configuration is verified.
                            </p>
                            <div className="evidence-form">
                              <textarea
                                className="text-area"
                                placeholder="Configuration notes"
                                value={configurationNotes}
                                onChange={(event) => setConfigurationNotes(event.target.value)}
                              />
                            </div>
                            {detail.configuration_questions.length > 0 ? (
                              <div className="assessment-list">
                                {detail.configuration_questions.map((question) => (
                                  <label key={question.id} className="assessment-question">
                                    <span>{question.question}</span>
                                    <select
                                      className="level-select"
                                      value={configurationDraft[question.id] ?? "unknown"}
                                      onChange={(event) =>
                                        setConfigurationDraft((current) => ({
                                          ...current,
                                          [question.id]: event.target.value as ConfigurationAnswerValue,
                                        }))
                                      }
                                    >
                                      {configurationOptions.map((option) => (
                                        <option key={option} value={option}>
                                          {option}
                                        </option>
                                      ))}
                                    </select>
                                  </label>
                                ))}
                              </div>
                            ) : (
                              <div className="empty-state compact">
                                <p>No configuration checklist is defined for this capability.</p>
                              </div>
                            )}
                          </div>
                        ) : null}

                        <div className="workspace-section">
                          <div className="workspace-section-header">
                            <div>
                              <p className="eyebrow">Assessment</p>
                              <strong className="workspace-title">Guided questionnaire</strong>
                            </div>
                            <button type="button" className="primary-button" onClick={() => void submitAssessment()}>
                              Save assessment
                            </button>
                          </div>
                          {detail.assessment_template ? (
                            <div className="assessment-list">
                              {detail.assessment_template.questions.map((question) => (
                                <label key={question.id} className="assessment-question">
                                  <span>{question.prompt}</span>
                                  <select
                                    className="level-select"
                                    value={assessmentDraft[question.id] ?? "unknown"}
                                    onChange={(event) =>
                                      setAssessmentDraft((current) => ({
                                        ...current,
                                        [question.id]: event.target.value as AssessmentAnswerValue,
                                      }))
                                    }
                                  >
                                    {assessmentOptions.map((option) => (
                                      <option key={option} value={option}>
                                        {option}
                                      </option>
                                    ))}
                                  </select>
                                </label>
                              ))}
                            </div>
                          ) : (
                            <div className="empty-state compact">
                              <p>No assessment template is available for this capability.</p>
                            </div>
                          )}
                        </div>

                        <div className="workspace-section">
                          <div className="workspace-section-header">
                            <div>
                              <p className="eyebrow">Evidence</p>
                              <strong className="workspace-title">Manual evidence</strong>
                            </div>
                            <button type="button" className="primary-button" onClick={() => void submitEvidence()}>
                              Add evidence
                            </button>
                          </div>

                          <div className="evidence-form">
                            <input
                              className="text-input"
                              placeholder="Title"
                              value={evidenceDraft.title}
                              onChange={(event) =>
                                setEvidenceDraft((current) => ({ ...current, title: event.target.value }))
                              }
                            />
                            <input
                              className="text-input"
                              placeholder="Type"
                              value={evidenceDraft.evidence_type}
                              onChange={(event) =>
                                setEvidenceDraft((current) => ({ ...current, evidence_type: event.target.value }))
                              }
                            />
                            <input
                              className="text-input"
                              placeholder="Optional file name"
                              value={evidenceDraft.file_name}
                              onChange={(event) =>
                                setEvidenceDraft((current) => ({ ...current, file_name: event.target.value }))
                              }
                            />
                            <input
                              className="text-input"
                              type="date"
                              value={evidenceDraft.recorded_at}
                              onChange={(event) =>
                                setEvidenceDraft((current) => ({ ...current, recorded_at: event.target.value }))
                              }
                            />
                            <textarea
                              className="text-area"
                              placeholder="Evidence note"
                              value={evidenceDraft.note}
                              onChange={(event) =>
                                setEvidenceDraft((current) => ({ ...current, note: event.target.value }))
                              }
                            />
                          </div>

                          <div className="detail-list">
                            {detail.evidence.length === 0 ? (
                              <div className="detail-item">
                                <span className="muted">No evidence added yet.</span>
                              </div>
                            ) : (
                              detail.evidence.map((evidence) => (
                                <div key={evidence.id} className="detail-item stacked">
                                  <div className="detail-row">
                                    <span>{evidence.title}</span>
                                    <span className="count-chip">{evidence.evidence_type}</span>
                                  </div>
                                  <p className="muted">
                                    {evidence.recorded_at}
                                    {evidence.file_name ? ` | ${evidence.file_name}` : ""}
                                  </p>
                                  <p className="muted">{evidence.note}</p>
                                </div>
                              ))
                            )}
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="empty-state compact">
                        <p>Assign the capability first to access assessment and evidence.</p>
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

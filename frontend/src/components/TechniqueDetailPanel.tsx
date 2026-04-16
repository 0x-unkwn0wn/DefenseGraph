import { useState } from "react";

import { createTechniqueTestResult, deleteTechniqueTestResult } from "../api";
import type { DerivedTechnique, TestStatus, Tool, ToolType } from "../types";

const TOOL_TYPE_LABEL: Record<ToolType, string> = {
  control: "control",
  analytics: "analytics",
  response: "response",
  validated: "Validated",
  assurance: "Validated",
};

interface TechniqueDetailPanelProps {
  technique: DerivedTechnique | null;
  tools?: Tool[];
  onClose: () => void;
  onRefreshCoverage?: () => Promise<void> | void;
}

export function TechniqueDetailPanel({ technique, tools = [], onClose, onRefreshCoverage }: TechniqueDetailPanelProps) {
  const [testStatus, setTestStatus] = useState<TestStatus>("not_tested");
  const [linkedToolId, setLinkedToolId] = useState<string>("none");
  const [lastTestedAt, setLastTestedAt] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  if (!technique) {
    return null;
  }

  const currentTechnique = technique;
  const techniqueTactics = currentTechnique.tactics?.length
    ? currentTechnique.tactics
    : [currentTechnique.tactic];
  const validationTools = tools.filter((tool) => tool.tool_types.includes("validated") || tool.tool_types.includes("assurance"));
  const currentTestStatus = currentTechnique.test_status ?? "not_tested";
  const testResults = currentTechnique.test_results ?? [];
  const testStatusSummary = currentTechnique.test_status_summary ?? {
    not_tested: 1,
    passed: 0,
    partial: 0,
    failed: 0,
    detected_not_blocked: 0,
  };

  async function handleCreateTestResult(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSaving(true);
    setError(null);
    try {
      await createTechniqueTestResult(currentTechnique.technique_id, {
        linked_tool_id: linkedToolId === "none" ? null : Number(linkedToolId),
        test_status: testStatus,
        last_tested_at: lastTestedAt || null,
        notes,
      });
      setTestStatus("not_tested");
      setLinkedToolId("none");
      setLastTestedAt("");
      setNotes("");
      await onRefreshCoverage?.();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Failed to save test result");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteTestResult(testResultId: number) {
    setError(null);
    try {
      await deleteTechniqueTestResult(testResultId);
      await onRefreshCoverage?.();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Failed to delete test result");
    }
  }

  return (
    <aside className="technique-detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="eyebrow">Technique detail</p>
          <h3>
            {currentTechnique.technique_code} {currentTechnique.technique_name}
          </h3>
        </div>
        <button type="button" className="panel-close-button" onClick={onClose} aria-label="Close detail panel">
          Close
        </button>
      </div>

      <div className="detail-panel-section">
        <div className="detail-kv">
          <span className="detail-label">Technique ID</span>
          <a href={currentTechnique.attack_url} target="_blank" rel="noreferrer noopener" className="attack-link">
            {currentTechnique.technique_code} ↗
          </a>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Tactics</span>
          <strong>{techniqueTactics.join(" | ")}</strong>
        </div>
        {currentTechnique.parent_technique_code ? (
          <div className="detail-kv">
            <span className="detail-label">Parent technique</span>
            <strong>{currentTechnique.parent_technique_code}</strong>
          </div>
        ) : null}
        <div className="detail-kv">
          <span className="detail-label">Model status</span>
          <strong>{currentTechnique.has_capability_mappings === false ? "Unmapped" : `${currentTechnique.mapped_capability_count ?? 0} capability mappings`}</strong>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Confidence</span>
          <span className={`coverage-pill ${currentTechnique.confidence_level}`}>{currentTechnique.confidence_level}</span>
        </div>
      </div>

      {currentTechnique.description ? (
        <div className="detail-panel-section">
          <p className="muted">{currentTechnique.description}</p>
        </div>
      ) : null}

      {currentTechnique.has_capability_mappings === false ? (
        <div className="detail-panel-section">
          <p className="muted">
            This technique is excluded from gap counts until the model is extended with capability mappings.
          </p>
        </div>
      ) : null}

      <div className="detail-panel-section">
        <span className="detail-label">Theoretical coverage</span>
        <div className="detail-kv">
          <span>Expected effect</span>
          <span className={`coverage-pill ${currentTechnique.theoretical_effect ?? "none"}`}>{currentTechnique.theoretical_effect ?? "none"}</span>
        </div>
        <div className="detail-list">
          {currentTechnique.contributions.map((contribution) => (
            <div key={`${contribution.toolId}-${contribution.capabilityId}-theoretical`} className="detail-item stacked">
              <div className="detail-row">
                <strong>{contribution.toolName}</strong>
                <span className={`coverage-pill ${contribution.theoreticalEffect ?? contribution.controlEffect}`}>
                  {contribution.theoreticalEffect ?? contribution.controlEffect}
                </span>
              </div>
              <p className="muted">
                {contribution.capabilityName} | {contribution.toolTypes.map((type) => TOOL_TYPE_LABEL[type]).join(", ")} | {contribution.controlEffectSource}
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Real coverage</span>
        <div className="detail-kv">
          <span>Resolved effect</span>
          <span className={`coverage-pill ${currentTechnique.real_effect ?? currentTechnique.coverage_type}`}>{currentTechnique.real_effect ?? currentTechnique.coverage_type}</span>
        </div>
        {currentTechnique.dependency_flags.length > 0 ? <p className="muted">{currentTechnique.dependency_flags.join(" | ")}</p> : null}
        <div className="detail-list">
          {currentTechnique.contributions.map((contribution) => (
            <div key={`${contribution.toolId}-${contribution.capabilityId}-real`} className="detail-item stacked">
              <div className="detail-row">
                <strong>{contribution.toolName}</strong>
                <div className="workspace-badges">
                  <span className={`coverage-pill ${contribution.realEffect ?? contribution.controlEffect}`}>
                    {contribution.realEffect ?? contribution.controlEffect}
                  </span>
                  <span className="count-chip">{contribution.controlEffectSource}</span>
                </div>
              </div>
              <p className="muted">
                {contribution.capabilityName} | {contribution.toolTypes.map((type) => TOOL_TYPE_LABEL[type]).join(", ")} | default {contribution.configuredEffectDefault} | {contribution.implementationLevel} implementation
              </p>
            </div>
          ))}
        </div>
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Response tools</span>
        {currentTechnique.response_actions.length === 0 ? (
          <p className="muted">No linked response action is available for this technique.</p>
        ) : (
          <div className="detail-list">
            {currentTechnique.response_actions.map((action) => (
              <div key={`${action.tool_id}-${action.action_code}`} className="detail-item stacked">
                <div className="detail-row">
                  <strong>{action.tool_name}</strong>
                  <span className="count-chip">response</span>
                </div>
                <p className="muted">
                  {action.action_name} | {action.implementation_level}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Tested status</span>
        <div className="detail-kv">
          <span>Current status</span>
          <span className="count-chip">{formatTestStatus(currentTestStatus)}</span>
        </div>
        <p className="muted">
          {testStatusSummary.passed} passed | {testStatusSummary.partial} partial | {testStatusSummary.failed} failed | {testStatusSummary.detected_not_blocked} detected not blocked
        </p>
        <div className="detail-list">
          {testResults.map((result) => (
            <div key={result.id} className="detail-item stacked">
              <div className="detail-row">
                <strong>{result.linked_tool_name ?? "Manual validation"}</strong>
                <div className="workspace-badges">
                  <span className="count-chip">{formatTestStatus(result.test_status)}</span>
                  <button type="button" className="panel-close-button" onClick={() => void handleDeleteTestResult(result.id)}>
                    Delete
                  </button>
                </div>
              </div>
              <p className="muted">{result.last_tested_at || "No date"} | {result.notes || "No notes"}</p>
            </div>
          ))}
        </div>

        <form className="technique-test-form" onSubmit={handleCreateTestResult}>
          <div className="workspace-field">
            <label htmlFor="test-status">Test status</label>
            <select
              id="test-status"
              className="level-select"
              value={testStatus}
              onChange={(event) => setTestStatus(event.target.value as TestStatus)}
            >
              <option value="not_tested">Not tested</option>
              <option value="passed">Passed</option>
              <option value="partial">Partial</option>
              <option value="failed">Failed</option>
              <option value="detected_not_blocked">Detected not blocked</option>
            </select>
          </div>
          <div className="workspace-field">
            <label htmlFor="linked-tool">Linked tool</label>
            <select
              id="linked-tool"
              className="level-select"
              value={linkedToolId}
              onChange={(event) => setLinkedToolId(event.target.value)}
            >
              <option value="none">No linked tool</option>
              {validationTools.map((tool) => (
                <option key={tool.id} value={tool.id}>
                  {tool.name}
                </option>
              ))}
            </select>
          </div>
          <div className="workspace-field">
            <label htmlFor="last-tested">Last tested</label>
            <input
              id="last-tested"
              className="text-input"
              type="datetime-local"
              value={lastTestedAt}
              onChange={(event) => setLastTestedAt(event.target.value)}
            />
          </div>
          <div className="workspace-field workspace-field--full">
            <label htmlFor="test-notes">Notes</label>
            <textarea
              id="test-notes"
              className="text-area"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={3}
            />
          </div>
          <div className="technique-test-actions">
            {error ? <p className="error-text">{error}</p> : <span className="muted">Add an optional tested result for this technique.</span>}
            <button type="submit" className="secondary-button" disabled={isSaving}>
              {isSaving ? "Saving..." : "Save test result"}
            </button>
          </div>
        </form>
      </div>
    </aside>
  );
}

function formatTestStatus(value: string) {
  return value.replace(/_/g, " ");
}

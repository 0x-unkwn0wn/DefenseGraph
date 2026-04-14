import type { DerivedTechnique } from "../types";

interface TechniqueDetailPanelProps {
  technique: DerivedTechnique | null;
  onClose: () => void;
}

export function TechniqueDetailPanel({ technique, onClose }: TechniqueDetailPanelProps) {
  if (!technique) {
    return null;
  }

  const uniqueTools = Array.from(
    new Map(
      technique.contributions.map((contribution) => [
        contribution.toolId,
        { id: contribution.toolId, name: contribution.toolName },
      ]),
    ).values(),
  );

  const coverageSummary =
    technique.coverage_type === "prevent"
      ? "At least one tool prevents this technique."
      : technique.coverage_type === "block"
        ? "At least one tool blocks this technique, but none prevent it."
        : technique.coverage_type === "detect"
          ? "The current scope detects this technique but does not block it."
          : "No tool currently contributes coverage for this technique.";

  return (
    <aside className="technique-detail-panel">
      <div className="detail-panel-header">
        <div>
          <p className="eyebrow">Technique detail</p>
          <h3>
            {technique.technique_code} {technique.technique_name}
          </h3>
        </div>
        <button type="button" className="panel-close-button" onClick={onClose} aria-label="Close detail panel">
          Close
        </button>
      </div>

      <div className="detail-panel-section">
        <div className="detail-kv">
          <span className="detail-label">Technique ID</span>
          <strong>{technique.technique_code}</strong>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Catalog scope</span>
          <strong>{technique.display_group}</strong>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Tactic</span>
          <strong>{technique.tactic}</strong>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Coverage</span>
          <span className={`coverage-pill ${technique.coverage_type}`}>{technique.coverage_type}</span>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Outcome</span>
          <strong>{technique.effective_outcome}</strong>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Confidence</span>
          <span className={`coverage-pill ${technique.confidence_level}`}>{technique.confidence_level}</span>
        </div>
        <div className="detail-kv">
          <span className="detail-label">Tools covering it</span>
          <strong>{technique.tool_count}</strong>
        </div>
        {technique.is_gap_partial ? (
          <div className="detail-kv">
            <span className="detail-label">Coverage quality</span>
            <span className="partial-badge">Partial</span>
          </div>
        ) : null}
        {technique.is_gap_single_tool_dependency ? (
          <div className="detail-kv">
            <span className="detail-label">Dependency</span>
            <span className="partial-badge">Single tool</span>
          </div>
        ) : null}
        {technique.response_enabled ? (
          <div className="detail-kv">
            <span className="detail-label">Response</span>
            <span className="partial-badge">Enabled</span>
          </div>
        ) : null}
        {technique.is_gap_unconfigured_control ? (
          <div className="detail-kv">
            <span className="detail-label">Configuration</span>
            <span className="partial-badge">Unverified</span>
          </div>
        ) : null}
        {technique.is_gap_partially_configured_control ? (
          <div className="detail-kv">
            <span className="detail-label">Configuration</span>
            <span className="partial-badge">Partial</span>
          </div>
        ) : null}
        {technique.is_gap_scope_missing ? (
          <div className="detail-kv">
            <span className="detail-label">Scope</span>
            <span className="partial-badge">Missing</span>
          </div>
        ) : null}
        {technique.is_gap_scope_partial ? (
          <div className="detail-kv">
            <span className="detail-label">Scope</span>
            <span className="partial-badge">Partial</span>
          </div>
        ) : null}
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Summary</span>
        <p className="muted">{coverageSummary}</p>
        <p className="muted">
          {technique.is_gap_no_coverage
            ? "This technique is currently uncovered."
            : technique.is_gap_detect_only
              ? "Coverage is limited to detection and should be strengthened."
              : technique.is_gap_partial
                ? "The best available control path is still partial."
                : technique.is_gap_low_confidence
                  ? "Coverage exists but confidence remains low."
                  : "Coverage is present without an immediate weak-point flag."}
        </p>
        {technique.dependency_flags.length > 0 ? (
          <p className="muted">{technique.dependency_flags.join(" | ")}</p>
        ) : null}
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Relevant scopes</span>
        {technique.relevant_scopes.length === 0 ? (
          <p className="muted">No explicit scope mapping exists for this technique yet.</p>
        ) : (
          <div className="detail-list">
            {technique.relevant_scopes.map((scope) => {
              const status = technique.scope_summary.full_scopes.includes(scope.coverage_scope.code)
                ? "full"
                : technique.scope_summary.partial_scopes.includes(scope.coverage_scope.code)
                  ? "partial"
                  : "none";
              return (
                <div key={`${scope.coverage_scope_id}-${scope.relevance}`} className="detail-item stacked">
                  <div className="detail-row">
                    <span>{scope.coverage_scope.name}</span>
                    <div className="workspace-badges">
                      <span className="count-chip">{scope.relevance}</span>
                      <span className={`coverage-pill ${status === "none" ? "none" : "detect"}`}>{status}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Detection and control tools</span>
        {uniqueTools.length === 0 ? (
          <p className="muted">No tools currently cover this technique.</p>
        ) : (
          <div className="detail-list">
            {Array.from(
              new Map(
                technique.contributions.map((contribution) => [
                  contribution.toolId,
                  {
                    id: contribution.toolId,
                    name: contribution.toolName,
                    type: contribution.toolTypes.join(", "),
                  },
                ]),
              ).values(),
            ).map((tool) => (
              <div key={tool.id} className="detail-item">
                <div className="detail-row">
                  <span>{tool.name}</span>
                  <span className="count-chip">{tool.type}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="detail-panel-section">
        <span className="detail-label">Response tools</span>
        {technique.response_actions.length === 0 ? (
          <p className="muted">No linked response action is available for this technique.</p>
        ) : (
          <div className="detail-list">
            {technique.response_actions.map((action) => (
              <div key={`${action.tool_id}-${action.action_code}`} className="detail-item stacked">
                <div className="detail-row">
                  <span>{action.tool_name}</span>
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
        <span className="detail-label">Capabilities</span>
        {technique.contributions.length === 0 ? (
          <p className="muted">No capability mappings are currently contributing.</p>
        ) : (
          <div className="detail-list">
            {technique.contributions.map((contribution) => (
              <div
                key={`${contribution.toolId}-${contribution.capabilityId}-${contribution.controlEffect}`}
                className="detail-item stacked"
              >
                <div className="detail-row">
                  <span>{contribution.capabilityName}</span>
                  <span className={`coverage-pill ${contribution.controlEffect}`}>
                    {contribution.controlEffect}
                  </span>
                </div>
                <p className="muted">
                  {contribution.toolName} | {contribution.toolTypes.join(", ")} | configured {contribution.configuredEffect} |{" "}
                  {contribution.implementationLevel} implementation | {contribution.confidenceLevel} confidence |{" "}
                  {contribution.mappingCoverage} mapping
                  {contribution.configurationStatus ? ` | config ${contribution.configurationStatus}` : ""}
                </p>
                {contribution.dependencyWarnings.length > 0 ? (
                  <p className="muted">{contribution.dependencyWarnings.join(" | ")}</p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

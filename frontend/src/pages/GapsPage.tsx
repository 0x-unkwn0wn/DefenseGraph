import { useState } from "react";

import { Card } from "../components/Card";
import {
  buildDisplayGroupCounters,
  buildTechniqueStates,
  buildToolOptions,
  filterTechniquesByDisplayGroup,
} from "../coverageHelpers";
import type {
  Capability,
  DerivedTechnique,
  TechniqueCoverage,
  TechniqueDisplayGroup,
  Tool,
} from "../types";

interface GapsPageProps {
  capabilities: Capability[];
  coverage: TechniqueCoverage[];
  tools: Tool[];
}

interface GapSectionProps {
  description: string;
  rows: DerivedTechnique[];
  title: string;
}

function GapSection({ description, rows, title }: GapSectionProps) {
  return (
    <Card title={title} subtitle="Gap category" actions={<span className="count-chip">{rows.length}</span>}>
      <p className="section-copy compact-copy">{description}</p>

      <div className="gap-card-list">
        {rows.length === 0 ? (
          <div className="empty-state compact">
            <p>No techniques in this category for the current filter.</p>
          </div>
        ) : (
          rows.map((row) => (
            <div key={row.technique_code} className="gap-row-card">
              <div className="gap-row-main">
                <strong>
                  {row.technique_code} - {row.technique_name}
                </strong>
                <p className="muted">{row.tactic}</p>
              </div>
              <div className="gap-badges">
                <span className={`coverage-pill ${row.coverage_type}`}>{row.coverage_type}</span>
                <span className={`coverage-pill ${row.confidence_level}`}>{row.confidence_level}</span>
                {row.is_gap_partial ? <span className="partial-badge">partial</span> : null}
                {row.is_gap_single_tool_dependency ? <span className="partial-badge">1 tool</span> : null}
                {row.is_gap_unconfigured_control ? <span className="partial-badge">unconfigured</span> : null}
                {row.is_gap_partially_configured_control ? <span className="partial-badge">config partial</span> : null}
                {row.is_gap_scope_missing ? <span className="partial-badge">scope missing</span> : null}
                {row.is_gap_scope_partial ? <span className="partial-badge">scope partial</span> : null}
              </div>
              <span className="gap-tool-count">{row.tool_count} tools</span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}

export function GapsPage({ capabilities, coverage, tools }: GapsPageProps) {
  const [selectedToolId, setSelectedToolId] = useState<number | "all">("all");
  const [selectedDisplayGroup, setSelectedDisplayGroup] = useState<TechniqueDisplayGroup | "all">("all");
  const techniqueStates = buildTechniqueStates({
    coverageRows: coverage,
    tools,
    selectedToolId,
  });
  const displayScopedTechniques = filterTechniquesByDisplayGroup(techniqueStates, selectedDisplayGroup);
  const groupCounters = buildDisplayGroupCounters(techniqueStates);
  const toolOptions = buildToolOptions(tools);

  const criticalRows = displayScopedTechniques.filter((technique) => technique.is_gap_no_coverage);
  const detectRows = displayScopedTechniques.filter((technique) => technique.is_gap_detect_only);
  const partialRows = displayScopedTechniques.filter((technique) => technique.is_gap_partial);
  const lowConfidenceRows = displayScopedTechniques.filter((technique) => technique.is_gap_low_confidence);
  const dependencyRows = displayScopedTechniques.filter((technique) => technique.is_gap_single_tool_dependency);
  const missingDataRows = displayScopedTechniques.filter((technique) => technique.is_gap_missing_data_sources);
  const unconfiguredRows = displayScopedTechniques.filter((technique) => technique.is_gap_unconfigured_control);
  const partiallyConfiguredRows = displayScopedTechniques.filter(
    (technique) => technique.is_gap_partially_configured_control,
  );
  const missingScopeRows = displayScopedTechniques.filter((technique) => technique.is_gap_scope_missing);
  const partialScopeRows = displayScopedTechniques.filter((technique) => technique.is_gap_scope_partial);
  const noResponseRows = displayScopedTechniques.filter((technique) => technique.is_gap_detection_without_response);
  const orphanResponseRows = displayScopedTechniques.filter((technique) => technique.is_gap_response_without_detection);

  return (
    <div className="stack page-stack">
      <Card title="Coverage gaps by severity" subtitle="Gaps">
        <div className="counter-grid compact-counter-grid">
          <div className="counter-card compact">
            <span>Core techniques covered</span>
            <strong>
              {groupCounters.coreCovered}/{groupCounters.coreTotal}
            </strong>
          </div>
          <div className="counter-card compact">
            <span>Core gaps</span>
            <strong>{groupCounters.coreGaps}</strong>
          </div>
          <div className="counter-card compact">
            <span>Extended techniques covered</span>
            <strong>
              {groupCounters.extendedCovered}/{groupCounters.extendedTotal}
            </strong>
          </div>
          <div className="counter-card compact">
            <span>Extended gaps</span>
            <strong>{groupCounters.extendedGaps}</strong>
          </div>
        </div>

        <div className="section-heading">
          <p className="section-copy compact-copy">Filter by tool to isolate operational weaknesses.</p>
          <div className="section-heading-controls">
            <label className="filter-field compact">
              <span>Tool</span>
              <select
                className="text-input"
                value={selectedToolId}
                onChange={(event) =>
                  setSelectedToolId(event.target.value === "all" ? "all" : Number(event.target.value))
                }
              >
                {toolOptions.map((tool) => (
                  <option key={tool.id} value={tool.id}>
                    {tool.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="filter-group compact-filter-group">
              <span className="filter-label">Catalog scope</span>
              <div className="filter-chips">
                {(["all", "core", "extended"] as const).map((scope) => (
                  <button
                    key={scope}
                    type="button"
                    className={selectedDisplayGroup === scope ? "filter-chip active" : "filter-chip"}
                    onClick={() => setSelectedDisplayGroup(scope)}
                  >
                    {scope}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Card>

      <GapSection
        title="Critical gaps"
        description="No tool currently maps to these techniques."
        rows={criticalRows}
      />
      <GapSection
        title="Detect only"
        description="These techniques are only detected and still lack block or prevent controls."
        rows={detectRows}
      />
      <GapSection
        title="Partial paths"
        description="The best available control path is still partial."
        rows={partialRows}
      />
      <GapSection
        title="Low confidence"
        description="Coverage exists, but confidence remains weak."
        rows={lowConfidenceRows}
      />
      <GapSection
        title="Single-tool dependency"
        description="Only one tool currently covers these techniques."
        rows={dependencyRows}
      />
      <GapSection
        title="Missing data sources"
        description="Analytics coverage is configured but the required upstream data is missing or incomplete."
        rows={missingDataRows}
      />
      <GapSection
        title="Unconfigured controls"
        description="A tool is mapped, but the relevant control has not been verified as enabled."
        rows={unconfiguredRows}
      />
      <GapSection
        title="Partially configured controls"
        description="The control exists, but configuration is only partially enabled in production."
        rows={partiallyConfiguredRows}
      />
      <GapSection
        title="Missing scope"
        description="A capability is mapped, but the required operating scope is not covered."
        rows={missingScopeRows}
      />
      <GapSection
        title="Partial scope"
        description="Some relevant scopes are covered, but the technique is not covered everywhere it matters."
        rows={partialScopeRows}
      />
      <GapSection
        title="Detection without response"
        description="These techniques are detected but no linked response action is available."
        rows={noResponseRows}
      />
      <GapSection
        title="Response without detection"
        description="Response actions exist, but there is no upstream detection to trigger them."
        rows={orphanResponseRows}
      />
    </div>
  );
}

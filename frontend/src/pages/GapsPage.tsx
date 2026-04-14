import { useEffect, useMemo, useState } from "react";

import { Card } from "../components/Card";
import { AttackMatrix } from "../components/AttackMatrix";
import { TechniqueDetailPanel } from "../components/TechniqueDetailPanel";
import {
  buildDisplayGroupCounters,
  buildScopeOptions,
  buildTechniqueStates,
  buildToolOptions,
  filterTechniquesByDisplayGroup,
} from "../coverageHelpers";
import type { Capability, DerivedTechnique, TechniqueCoverage, TechniqueDisplayGroup, Tool } from "../types";

interface GapsPageProps {
  capabilities: Capability[];
  coverage: TechniqueCoverage[];
  tools: Tool[];
}

type GapCategoryKey =
  | "critical"
  | "detect_only"
  | "partial"
  | "low_confidence"
  | "single_tool_dependency"
  | "missing_data_sources"
  | "unconfigured_control"
  | "partially_configured_control"
  | "scope_missing"
  | "scope_partial"
  | "detection_without_response"
  | "response_without_detection";

interface GapCategoryDefinition {
  description: string;
  key: GapCategoryKey;
  label: string;
  matches: (technique: DerivedTechnique) => boolean;
}

const gapCategoryDefinitions: GapCategoryDefinition[] = [
  {
    key: "critical",
    label: "Critical gaps",
    description: "No effective coverage exists for the technique.",
    matches: (technique) => technique.is_gap_no_coverage,
  },
  {
    key: "detect_only",
    label: "Detect only",
    description: "Coverage is limited to detection and still lacks block or prevent controls.",
    matches: (technique) => technique.is_gap_detect_only,
  },
  {
    key: "partial",
    label: "Partial paths",
    description: "The strongest available control path is still partial.",
    matches: (technique) => technique.is_gap_partial,
  },
  {
    key: "low_confidence",
    label: "Low confidence",
    description: "Coverage exists, but the confidence model remains weak.",
    matches: (technique) => technique.is_gap_low_confidence,
  },
  {
    key: "single_tool_dependency",
    label: "Single-tool dependency",
    description: "Only one tool currently covers the technique.",
    matches: (technique) => technique.is_gap_single_tool_dependency,
  },
  {
    key: "missing_data_sources",
    label: "Missing data sources",
    description: "Analytics coverage depends on upstream data that is missing or incomplete.",
    matches: (technique) => technique.is_gap_missing_data_sources,
  },
  {
    key: "unconfigured_control",
    label: "Unconfigured controls",
    description: "A mapped control exists, but it has not been verified as enabled.",
    matches: (technique) => technique.is_gap_unconfigured_control,
  },
  {
    key: "partially_configured_control",
    label: "Partially configured",
    description: "A mapped control exists, but it is only partially enabled in production.",
    matches: (technique) => technique.is_gap_partially_configured_control,
  },
  {
    key: "scope_missing",
    label: "Missing scope",
    description: "The required operating scope is not covered.",
    matches: (technique) => technique.is_gap_scope_missing,
  },
  {
    key: "scope_partial",
    label: "Partial scope",
    description: "Some relevant scopes are covered, but not all of them.",
    matches: (technique) => technique.is_gap_scope_partial,
  },
  {
    key: "detection_without_response",
    label: "Detection without response",
    description: "The technique is detected but there is no linked response path.",
    matches: (technique) => technique.is_gap_detection_without_response,
  },
  {
    key: "response_without_detection",
    label: "Response without detection",
    description: "A response action exists, but nothing upstream is detecting the technique.",
    matches: (technique) => technique.is_gap_response_without_detection,
  },
];

const allGapCategoryKeys = gapCategoryDefinitions.map((category) => category.key);

export function GapsPage({ capabilities: _capabilities, coverage, tools }: GapsPageProps) {
  const [selectedToolId, setSelectedToolId] = useState<number | "all">("all");
  const [selectedDisplayGroup, setSelectedDisplayGroup] = useState<TechniqueDisplayGroup | "all">("all");
  const [selectedScope, setSelectedScope] = useState<string>("all");
  const [selectedTechniqueCode, setSelectedTechniqueCode] = useState<string | null>(null);
  const [selectedGapCategories, setSelectedGapCategories] = useState<GapCategoryKey[]>(allGapCategoryKeys);

  const techniqueStates = buildTechniqueStates({
    coverageRows: coverage,
    tools,
    selectedToolId,
  });
  const displayScopedTechniques = filterTechniquesByDisplayGroup(techniqueStates, selectedDisplayGroup);
  const scopeOptions = buildScopeOptions(coverage);
  const toolOptions = buildToolOptions(tools);
  const groupCounters = buildDisplayGroupCounters(techniqueStates);

  const scopeFilteredTechniques = displayScopedTechniques.filter(
    (technique) =>
      selectedScope === "all" ||
      technique.relevant_scopes.some((scope) => scope.coverage_scope.code === selectedScope),
  );

  const visibleTechniques = scopeFilteredTechniques.filter((technique) =>
    gapCategoryDefinitions.some(
      (category) => selectedGapCategories.includes(category.key) && category.matches(technique),
    ),
  );

  const activeTechnique =
    visibleTechniques.find((technique) => technique.technique_code === selectedTechniqueCode) ?? null;

  useEffect(() => {
    if (
      selectedTechniqueCode &&
      !visibleTechniques.some((technique) => technique.technique_code === selectedTechniqueCode)
    ) {
      setSelectedTechniqueCode(null);
    }
  }, [selectedTechniqueCode, visibleTechniques]);

  const gapCategoryCounts = useMemo(
    () =>
      Object.fromEntries(
        gapCategoryDefinitions.map((category) => [
          category.key,
          scopeFilteredTechniques.filter((technique) => category.matches(technique)).length,
        ]),
      ) as Record<GapCategoryKey, number>,
    [scopeFilteredTechniques],
  );

  const activeCategorySummary = gapCategoryDefinitions
    .filter((category) => selectedGapCategories.includes(category.key))
    .map((category) => category.label)
    .join(", ");

  function handleSelectTechnique(technique: DerivedTechnique) {
    setSelectedTechniqueCode((current) =>
      current === technique.technique_code ? null : technique.technique_code,
    );
  }

  function toggleGapCategory(key: GapCategoryKey) {
    setSelectedGapCategories((current) => {
      if (current.length === allGapCategoryKeys.length) {
        return [key];
      }
      if (current.includes(key)) {
        return current.length === 1 ? current : current.filter((entry) => entry !== key);
      }
      return [...current, key];
    });
  }

  return (
    <div className={`coverage-layout ${activeTechnique ? "detail-open" : ""}`.trim()}>
      <Card title="Gap matrix" subtitle="ATT&CK gaps" className="matrix-card">
        <p className="section-copy">
          Review ATT&CK weak points with the same matrix view used in Coverage, filtered down to gap conditions only.
        </p>

        <div className="counter-grid">
          <div className="counter-card">
            <span>Visible gap techniques</span>
            <strong>{visibleTechniques.length}</strong>
          </div>
          <div className="counter-card">
            <span>Critical gaps</span>
            <strong>{gapCategoryCounts.critical}</strong>
          </div>
          <div className="counter-card">
            <span>Detect only</span>
            <strong>{gapCategoryCounts.detect_only}</strong>
          </div>
          <div className="counter-card">
            <span>Scope-related gaps</span>
            <strong>{gapCategoryCounts.scope_missing + gapCategoryCounts.scope_partial}</strong>
          </div>
        </div>

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

        <div className="filters-card">
          <div className="filters-grid">
            <label className="filter-field">
              <span>Tool</span>
              <select
                className="text-input"
                value={selectedToolId}
                onChange={(event) =>
                  setSelectedToolId(
                    event.target.value === "all" ? "all" : Number(event.target.value),
                  )
                }
              >
                {toolOptions.map((tool) => (
                  <option key={tool.id} value={tool.id}>
                    {tool.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="filter-field">
              <span>Scope</span>
              <select
                className="text-input"
                value={selectedScope}
                onChange={(event) => setSelectedScope(event.target.value)}
              >
                {scopeOptions.map((scope) => (
                  <option key={scope.code} value={scope.code}>
                    {scope.name}
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

          <div className="filter-group">
            <div className="filter-group-heading">
              <span className="filter-label">Gap categories</span>
              <button
                type="button"
                className="filter-chip"
                onClick={() => setSelectedGapCategories(allGapCategoryKeys)}
              >
                reset
              </button>
            </div>
            <div className="filter-chips">
              {gapCategoryDefinitions.map((category) => (
                <button
                  key={category.key}
                  type="button"
                  className={selectedGapCategories.includes(category.key) ? "filter-chip active" : "filter-chip"}
                  onClick={() => toggleGapCategory(category.key)}
                  title={category.description}
                >
                  {category.label}
                </button>
              ))}
            </div>
          </div>

          <div className="legend">
            <div className="legend-item">
              <span className="legend-swatch none" />
              <span>No coverage</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch detect" />
              <span>Detect only</span>
            </div>
            <div className="legend-item">
              <span className="legend-border critical" />
              <span>Critical gap</span>
            </div>
            <div className="legend-item">
              <span className="legend-border weak" />
              <span>Weak gap</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" />
              <span>Partial path</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">LC</span>
              <span>Low confidence</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">1T</span>
              <span>Single-tool dependency</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">DS</span>
              <span>Missing data</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">CFG</span>
              <span>Unconfigured control</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">SM</span>
              <span>Scope missing</span>
            </div>
          </div>
        </div>

        <div className="matrix-toolbar">
          <p className="section-copy compact-copy">
            {activeTechnique
              ? `Inspecting ${activeTechnique.technique_code}. Click the selected cell again to close detail.`
              : visibleTechniques.length === 0
                ? "No techniques match the current gap filters."
                : `Showing ${visibleTechniques.length} techniques across: ${activeCategorySummary}.`}
          </p>
        </div>

        <AttackMatrix
          hideEmptyTactics
          techniques={visibleTechniques}
          selectedTechniqueCode={selectedTechniqueCode}
          onSelect={handleSelectTechnique}
        />
      </Card>

      <TechniqueDetailPanel technique={activeTechnique} onClose={() => setSelectedTechniqueCode(null)} />
    </div>
  );
}

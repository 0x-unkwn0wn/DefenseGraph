import { useEffect, useMemo, useState } from "react";

import { Card } from "../components/Card";
import { AttackMatrix } from "../components/AttackMatrix";
import { TechniqueDetailPanel } from "../components/TechniqueDetailPanel";
import {
  buildCounters,
  buildDisplayGroupCounters,
  buildScopeOptions,
  buildTechniqueStates,
  buildToolOptions,
  filterTechniqueStates,
  filterTechniquesByDisplayGroup,
} from "../coverageHelpers";
import type {
  Capability,
  CoverageType,
  DerivedTechnique,
  TechniqueCoverage,
  TechniqueDisplayGroup,
  Tool,
} from "../types";

type CoverageWorkspaceView = "coverage" | "gaps";
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
  | "response_without_detection"
  | "tested_failed"
  | "detected_not_blocked"
  | "untested_critical";

interface CoveragePageProps {
  capabilities: Capability[];
  coverage: TechniqueCoverage[];
  tools: Tool[];
  viewMode?: CoverageWorkspaceView;
  onChangeViewMode?: (view: CoverageWorkspaceView) => void;
  onRefreshCoverage?: () => Promise<void> | void;
}

interface GapCategoryDefinition {
  description: string;
  key: GapCategoryKey;
  label: string;
  matches: (technique: DerivedTechnique) => boolean;
}

const coverageOptions: CoverageType[] = ["none", "detect", "block", "prevent"];
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
  {
    key: "tested_failed",
    label: "Tested failed",
    description: "A validation run disproved the expected coverage path.",
    matches: (technique) => technique.is_gap_tested_failed ?? false,
  },
  {
    key: "detected_not_blocked",
    label: "Detected not blocked",
    description: "Testing showed the technique was seen but not stopped.",
    matches: (technique) => technique.is_gap_detected_not_blocked ?? false,
  },
  {
    key: "untested_critical",
    label: "Untested critical",
    description: "A blocking or prevention claim still lacks validation evidence.",
    matches: (technique) => technique.is_gap_untested_critical ?? false,
  },
];
const allGapCategoryKeys = gapCategoryDefinitions.map((category) => category.key);

export function CoveragePage({
  capabilities: _capabilities,
  coverage,
  tools,
  viewMode = "coverage",
  onChangeViewMode,
  onRefreshCoverage,
}: CoveragePageProps) {
  const [activeView, setActiveView] = useState<CoverageWorkspaceView>(viewMode);
  const [selectedToolId, setSelectedToolId] = useState<number | "all">("all");
  const [selectedCoverage, setSelectedCoverage] = useState<CoverageType[]>(coverageOptions);
  const [selectedScope, setSelectedScope] = useState<string>("all");
  const [showOnlyCriticalGaps, setShowOnlyCriticalGaps] = useState(false);
  const [showExtendedTechniques, setShowExtendedTechniques] = useState(false);
  const [showUnmappedTechniques, setShowUnmappedTechniques] = useState(true);
  const [selectedDisplayGroup, setSelectedDisplayGroup] = useState<TechniqueDisplayGroup | "all">("all");
  const [selectedGapCategories, setSelectedGapCategories] = useState<GapCategoryKey[]>(allGapCategoryKeys);
  const [selectedTechniqueCode, setSelectedTechniqueCode] = useState<string | null>(null);

  useEffect(() => {
    setActiveView(viewMode);
  }, [viewMode]);

  const techniqueStates = buildTechniqueStates({
    coverageRows: coverage,
    tools,
    selectedToolId,
  });
  const uniqueTechniqueStates = useMemo(
    () => Array.from(new Map(techniqueStates.map((technique) => [technique.technique_code, technique])).values()),
    [techniqueStates],
  );
  const mappedTechniqueStates = useMemo(
    () => techniqueStates.filter((technique) => technique.has_capability_mappings !== false),
    [techniqueStates],
  );
  const uniqueMappedTechniqueStates = useMemo(
    () => Array.from(new Map(mappedTechniqueStates.map((technique) => [technique.technique_code, technique])).values()),
    [mappedTechniqueStates],
  );
  const coverageTechniqueStates = showUnmappedTechniques ? techniqueStates : mappedTechniqueStates;
  const uniqueCoverageTechniqueStates = showUnmappedTechniques
    ? uniqueTechniqueStates
    : uniqueMappedTechniqueStates;
  const toolOptions = buildToolOptions(tools);
  const scopeOptions = buildScopeOptions(coverage);
  const groupCounters = buildDisplayGroupCounters(uniqueCoverageTechniqueStates);

  const visibleTechniques =
    activeView === "coverage"
      ? filterTechniqueStates(
          coverageTechniqueStates.filter(
            (technique) =>
              showExtendedTechniques ||
              technique.display_group === "core" ||
              !technique.has_capability_mappings,
          ),
          selectedCoverage,
          showOnlyCriticalGaps,
          selectedScope,
        )
      : filterTechniquesByDisplayGroup(techniqueStates, selectedDisplayGroup)
          .filter(
            (technique) =>
              selectedScope === "all" ||
              technique.relevant_scopes.some((scope) => scope.coverage_scope.code === selectedScope),
          )
          .filter((technique) =>
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

  const coverageCounters = buildCounters(
    uniqueCoverageTechniqueStates.filter(
      (technique) =>
        showExtendedTechniques || technique.display_group === "core" || !technique.has_capability_mappings,
    ),
  );
  const gapCategoryCounts = useMemo(
    () =>
      Object.fromEntries(
        gapCategoryDefinitions.map((category) => [
          category.key,
          uniqueMappedTechniqueStates.filter((technique) => category.matches(technique)).length,
        ]),
      ) as Record<GapCategoryKey, number>,
    [uniqueMappedTechniqueStates],
  );

  function handleSelectTechnique(technique: DerivedTechnique) {
    setSelectedTechniqueCode((current) =>
      current === technique.technique_code ? null : technique.technique_code,
    );
  }

  function handleChangeView(nextView: CoverageWorkspaceView) {
    setActiveView(nextView);
    onChangeViewMode?.(nextView);
  }

  function toggleCoverageFilter(nextCoverage: CoverageType) {
    setSelectedCoverage((current) => {
      if (current.includes(nextCoverage)) {
        return current.length === 1 ? current : current.filter((entry) => entry !== nextCoverage);
      }
      return [...current, nextCoverage];
    });
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

  const activeGapCategorySummary = gapCategoryDefinitions
    .filter((category) => selectedGapCategories.includes(category.key))
    .map((category) => category.label)
    .join(", ");

  return (
    <div className={`coverage-layout ${activeTechnique ? "detail-open" : ""}`.trim()}>
      <Card
        title="Coverage"
        subtitle={activeView === "coverage" ? "ATT&CK workspace" : "ATT&CK workspace / gaps mode"}
        className="matrix-card"
      >
        <p className="section-copy">
          {activeView === "coverage"
            ? "Coverage state by tactic, technique, and selected tool scope."
            : "Gap-focused ATT&CK view using the same matrix, detail panel, and filters as the main coverage workspace."}
        </p>

        <div className="filter-group view-mode-group">
          <div className="filter-group-heading">
            <span className="filter-label">Workspace view</span>
          </div>
          <div className="filter-chips">
            {(["coverage", "gaps"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                className={activeView === mode ? "filter-chip active" : "filter-chip"}
                onClick={() => handleChangeView(mode)}
              >
                {mode}
              </button>
            ))}
          </div>
        </div>

        {activeView === "coverage" ? (
          <div className="counter-grid">
            <div className="counter-card">
              <span>
                {showExtendedTechniques
                  ? showUnmappedTechniques
                    ? "Visible techniques"
                    : "Mapped techniques"
                  : showUnmappedTechniques
                    ? "Core techniques"
                    : "Mapped core techniques"}
              </span>
              <strong>{coverageCounters.total}</strong>
            </div>
            <div className="counter-card">
              <span>Covered</span>
              <strong>{coverageCounters.covered}</strong>
            </div>
            <div className="counter-card">
              <span>Gaps</span>
              <strong>{coverageCounters.gaps}</strong>
            </div>
            <div className="counter-card">
              <span>Detect only</span>
              <strong>{coverageCounters.detectOnly}</strong>
            </div>
          </div>
        ) : (
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
        )}

        <div className="counter-grid compact-counter-grid">
          <div className="counter-card compact">
            <span>Core covered</span>
            <strong>
              {groupCounters.coreCovered}/{groupCounters.coreTotal}
            </strong>
          </div>
          <div className="counter-card compact">
            <span>Core gaps</span>
            <strong>{groupCounters.coreGaps}</strong>
          </div>
          <div className="counter-card compact">
            <span>Extended covered</span>
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

            {activeView === "coverage" ? (
              <>
                <label className="filter-toggle">
                  <input
                    type="checkbox"
                    checked={showOnlyCriticalGaps}
                    onChange={(event) => setShowOnlyCriticalGaps(event.target.checked)}
                  />
                  <span>Show only critical gaps</span>
                </label>

                <label className="filter-toggle">
                  <input
                    type="checkbox"
                    checked={showExtendedTechniques}
                    onChange={(event) => setShowExtendedTechniques(event.target.checked)}
                  />
                  <span>Show extended techniques</span>
                </label>

                <label className="filter-toggle">
                  <input
                    type="checkbox"
                    checked={showUnmappedTechniques}
                    onChange={(event) => setShowUnmappedTechniques(event.target.checked)}
                  />
                  <span>Show unmapped ATT&amp;CK techniques</span>
                </label>
              </>
            ) : (
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
            )}
          </div>

          {activeView === "coverage" ? (
            <div className="filter-group">
              <span className="filter-label">Coverage filter</span>
              <div className="filter-chips">
                {coverageOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={selectedCoverage.includes(option) ? "filter-chip active" : "filter-chip"}
                    onClick={() => toggleCoverageFilter(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          ) : (
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
          )}

          <div className="legend">
            <div className="legend-item">
              <span className="legend-swatch none" />
              <span>No coverage</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">UM</span>
              <span>Unmapped technique</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch detect" />
              <span>{activeView === "coverage" ? "Detect" : "Detect only"}</span>
            </div>
            {activeView === "coverage" ? (
              <>
                <div className="legend-item">
                  <span className="legend-swatch block" />
                  <span>Block</span>
                </div>
                <div className="legend-item">
                  <span className="legend-swatch prevent" />
                  <span>Prevent</span>
                </div>
              </>
            ) : null}
            <div className="legend-item">
              <span className="legend-border critical" />
              <span>Critical gap</span>
            </div>
            <div className="legend-item">
              <span className="legend-border weak" />
              <span>{activeView === "coverage" ? "Detect only" : "Weak gap"}</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" />
              <span>{activeView === "coverage" ? "Partial coverage" : "Partial path"}</span>
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
              <span className="legend-flag">PC</span>
              <span>Partially configured</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">SM</span>
              <span>Scope missing</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">SP</span>
              <span>Scope partial</span>
            </div>
            <div className="legend-item">
              <span className="legend-flag">R</span>
              <span>Response enabled</span>
            </div>
          </div>
        </div>

        <div className="matrix-toolbar">
          <p className="section-copy compact-copy">
            {activeTechnique
              ? `Inspecting ${activeTechnique.technique_code}. Click the selected cell again to close detail.`
              : activeView === "coverage"
                ? showOnlyCriticalGaps
                  ? "Showing only techniques with no effective coverage. Detect-only and partial techniques are hidden in this mode."
                  : showExtendedTechniques
                    ? showUnmappedTechniques
                      ? "Showing the full ATT&CK catalog in the current modeled scope, including unmapped techniques."
                      : "Showing all mapped Core and Extended techniques. Switch to Gaps view for weakness-first analysis."
                    : showUnmappedTechniques
                      ? "Showing Core techniques across the current ATT&CK catalog, including unmapped entries."
                      : "Showing mapped Core techniques by default. Enable Extended for the full modeled set."
                : visibleTechniques.length === 0
                  ? "No techniques match the current gap filters."
                  : `Showing ${visibleTechniques.length} techniques across: ${activeGapCategorySummary}.`}
          </p>
        </div>

        <AttackMatrix
          hideEmptyTactics={
            activeView === "coverage"
              ? showOnlyCriticalGaps ||
                selectedScope !== "all" ||
                selectedToolId !== "all" ||
                selectedCoverage.length !== coverageOptions.length
              : true
          }
          techniques={visibleTechniques}
          selectedTechniqueCode={selectedTechniqueCode}
          onSelect={handleSelectTechnique}
        />
      </Card>

      <TechniqueDetailPanel
        technique={activeTechnique}
        tools={tools}
        onClose={() => setSelectedTechniqueCode(null)}
        onRefreshCoverage={onRefreshCoverage}
      />
    </div>
  );
}

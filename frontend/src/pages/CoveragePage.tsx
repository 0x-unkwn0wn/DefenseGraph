import { useEffect, useState } from "react";

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
} from "../coverageHelpers";
import type { Capability, CoverageType, DerivedTechnique, TechniqueCoverage, Tool } from "../types";

interface CoveragePageProps {
  capabilities: Capability[];
  coverage: TechniqueCoverage[];
  tools: Tool[];
}

const coverageOptions: CoverageType[] = ["none", "detect", "block", "prevent"];

export function CoveragePage({ capabilities, coverage, tools }: CoveragePageProps) {
  const [selectedToolId, setSelectedToolId] = useState<number | "all">("all");
  const [selectedCoverage, setSelectedCoverage] = useState<CoverageType[]>(coverageOptions);
  const [selectedScope, setSelectedScope] = useState<string>("all");
  const [showOnlyGaps, setShowOnlyGaps] = useState(false);
  const [showExtendedTechniques, setShowExtendedTechniques] = useState(false);
  const [selectedTechniqueCode, setSelectedTechniqueCode] = useState<string | null>(null);

  const techniqueStates = buildTechniqueStates({
    coverageRows: coverage,
    tools,
    selectedToolId,
  });
  const scopedTechniques = techniqueStates.filter(
    (technique) => showExtendedTechniques || technique.display_group === "core",
  );
  const visibleTechniques = filterTechniqueStates(
    scopedTechniques,
    selectedCoverage,
    showOnlyGaps,
    selectedScope,
  );
  const counters = buildCounters(scopedTechniques);
  const groupCounters = buildDisplayGroupCounters(techniqueStates);
  const toolOptions = buildToolOptions(tools);
  const scopeOptions = buildScopeOptions(coverage);
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

  function toggleCoverageFilter(nextCoverage: CoverageType) {
    setSelectedCoverage((current) => {
      if (current.includes(nextCoverage)) {
        return current.length === 1 ? current : current.filter((entry) => entry !== nextCoverage);
      }
      return [...current, nextCoverage];
    });
  }

  function handleSelectTechnique(technique: DerivedTechnique) {
    setSelectedTechniqueCode((current) =>
      current === technique.technique_code ? null : technique.technique_code,
    );
  }

  return (
    <div className={`coverage-layout ${activeTechnique ? "detail-open" : ""}`.trim()}>
      <Card title="Coverage matrix" subtitle="ATT&CK coverage" className="matrix-card">
        <p className="section-copy">Coverage state by tactic, technique, and selected tool scope.</p>

        <div className="counter-grid">
          <div className="counter-card">
            <span>{showExtendedTechniques ? "Visible techniques" : "Core techniques"}</span>
            <strong>{counters.total}</strong>
          </div>
          <div className="counter-card">
            <span>Covered</span>
            <strong>{counters.covered}</strong>
          </div>
          <div className="counter-card">
            <span>Gaps</span>
            <strong>{counters.gaps}</strong>
          </div>
          <div className="counter-card">
            <span>Detect only</span>
            <strong>{counters.detectOnly}</strong>
          </div>
        </div>

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

            <label className="filter-toggle">
              <input
                type="checkbox"
                checked={showOnlyGaps}
                onChange={(event) => setShowOnlyGaps(event.target.checked)}
              />
              <span>Show only gaps</span>
            </label>

            <label className="filter-toggle">
              <input
                type="checkbox"
                checked={showExtendedTechniques}
                onChange={(event) => setShowExtendedTechniques(event.target.checked)}
              />
              <span>Show extended techniques</span>
            </label>
          </div>

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

          <div className="legend">
            <div className="legend-item">
              <span className="legend-swatch none" />
              <span>No coverage</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch detect" />
              <span>Detect</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch block" />
              <span>Block</span>
            </div>
            <div className="legend-item">
              <span className="legend-swatch prevent" />
              <span>Prevent</span>
            </div>
            <div className="legend-item">
              <span className="legend-border critical" />
              <span>Critical gap</span>
            </div>
            <div className="legend-item">
              <span className="legend-border weak" />
              <span>Detect only</span>
            </div>
            <div className="legend-item">
              <span className="legend-dot" />
              <span>Partial coverage</span>
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
              : showExtendedTechniques
                ? "Showing Core and Extended techniques. Select a technique to inspect its coverage path, tools, and capabilities."
                : "Showing Core techniques by default. Enable the Extended toggle for deeper coverage review."}
          </p>
        </div>

        <AttackMatrix
          hideEmptyTactics={
            showOnlyGaps || selectedScope !== "all" || selectedToolId !== "all" || selectedCoverage.length !== coverageOptions.length
          }
          techniques={visibleTechniques}
          selectedTechniqueCode={selectedTechniqueCode}
          onSelect={handleSelectTechnique}
        />
      </Card>

      <TechniqueDetailPanel technique={activeTechnique} onClose={() => setSelectedTechniqueCode(null)} />
    </div>
  );
}

import type { DerivedTechnique } from "../types";

interface TechniqueCellProps {
  technique: DerivedTechnique;
  isActive: boolean;
  onSelect: (technique: DerivedTechnique) => void;
}

export function TechniqueCell({ technique, isActive, onSelect }: TechniqueCellProps) {
  const isUnmapped = technique.has_capability_mappings === false;
  const gapClass =
    technique.is_gap_no_coverage
      ? "gap-critical"
      : technique.is_gap_detect_only
        ? "gap-weak"
        : "";

  return (
    <button
      type="button"
      className={[
        "matrix-cell",
        technique.coverage_type,
        technique.tool_count > 1 ? "multi-tool" : "",
        technique.is_gap_partial ? "partial" : "",
        technique.is_gap_low_confidence ? "low-confidence" : "",
        technique.is_gap_single_tool_dependency ? "single-tool" : "",
        technique.is_gap_unconfigured_control ? "unconfigured-control" : "",
        technique.is_gap_partially_configured_control ? "partially-configured-control" : "",
        isUnmapped ? "unmapped-model" : "",
        gapClass,
        isActive ? "active" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-pressed={isActive}
      onClick={() => onSelect(technique)}
    >
      <div className="matrix-cell-topline">
        <span className="matrix-cell-code">{technique.technique_code}</span>
        <span className={`matrix-cell-scope ${technique.display_group}`}>{technique.display_group}</span>
      </div>
      <strong className="matrix-cell-title">{technique.technique_name}</strong>
      <span className="matrix-cell-meta">
        {technique.tool_count} {technique.tool_count === 1 ? "tool" : "tools"}
      </span>
      <span className="matrix-cell-flags">
        {isUnmapped ? <span className="cell-flag">unmapped</span> : null}
        {technique.is_gap_partial ? <span className="cell-flag">partial</span> : null}
        {technique.is_gap_missing_data_sources ? <span className="cell-flag">data</span> : null}
        {technique.is_gap_unconfigured_control ? <span className="cell-flag">config</span> : null}
        {technique.is_gap_partially_configured_control ? <span className="cell-flag">config partial</span> : null}
        {technique.is_gap_scope_missing ? <span className="cell-flag">scope</span> : null}
        {technique.is_gap_scope_partial ? <span className="cell-flag">scope partial</span> : null}
        {technique.is_gap_low_confidence ? <span className="cell-flag">low conf</span> : null}
        {technique.is_gap_single_tool_dependency ? <span className="cell-flag">1 tool</span> : null}
        {technique.response_enabled ? <span className="cell-flag">response</span> : null}
      </span>
      {technique.is_gap_partial ? <span className="partial-indicator" aria-hidden="true" /> : null}
    </button>
  );
}

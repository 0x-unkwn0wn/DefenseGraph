import { legacyTechniqueDisplayGroups, legacyTechniqueTactics, tacticOrder } from "./attackConfig";
import type {
  CapabilityContribution,
  ConfidenceLevel,
  CoverageStatus,
  CoverageType,
  CoverageScope,
  DerivedTechnique,
  TechniqueCoverage,
  TechniqueDisplayGroup,
  TechniqueResponseAction,
  Tool,
  ToolCoverageSummary,
} from "./types";

const coverageRank: Record<CoverageType, number> = {
  none: 0,
  detect: 1,
  block: 2,
  prevent: 3,
};

const confidenceRank: Record<ConfidenceLevel, number> = {
  low: 0,
  medium: 1,
  high: 2,
};

interface BuildTechniqueStateArgs {
  coverageRows: TechniqueCoverage[];
  tools: Tool[];
  selectedToolId: number | "all";
}

export function buildTechniqueStates({
  coverageRows,
  tools,
  selectedToolId,
}: BuildTechniqueStateArgs): DerivedTechnique[] {
  return coverageRows
    .flatMap((row) => {
      const tactics = row.tactics?.length
        ? row.tactics
        : [row.primary_tactic ?? legacyTechniqueTactics[row.technique_code] ?? "Execution"];
      const displayGroup = row.display_group ?? legacyTechniqueDisplayGroups[row.technique_code] ?? "extended";
      const allContributions = mapCoverageContributions(row);
      const hasCapabilityMappings = row.has_capability_mappings ?? true;
      const localCoverage =
        selectedToolId === "all"
          ? summarizeCoverage(allContributions, row.response_actions, row.relevant_scopes, hasCapabilityMappings)
          : summarizeCoverageForSelectedTool(row, selectedToolId);

      return tactics.map<DerivedTechnique>((tactic) => ({
        ...row,
        ...localCoverage,
        technique_id: row.technique_id,
        technique_code: row.technique_code,
        technique_name: row.technique_name,
        // Preserve API-sourced fields that localCoverage would overwrite with defaults.
        attack_url: row.attack_url,
        attack_domain: row.attack_domain ?? "enterprise-attack",
        description: row.description ?? "",
        tactics,
        primary_tactic: row.primary_tactic ?? tactics[0] ?? tactic,
        platforms: row.platforms ?? [],
        attack_stix_id: row.attack_stix_id ?? null,
        attack_version: row.attack_version ?? null,
        parent_technique_code: row.parent_technique_code ?? null,
        is_subtechnique: row.is_subtechnique ?? false,
        revoked: row.revoked ?? false,
        deprecated: row.deprecated ?? false,
        has_capability_mappings: hasCapabilityMappings,
        mapped_capability_count: row.mapped_capability_count ?? 0,
        theoretical_effect: localCoverage.theoretical_effect,
        real_effect: localCoverage.real_effect,
        confidence_source_summary: localCoverage.confidence_source_summary,
        mapped_domains: row.mapped_domains ?? [],
        test_results: row.test_results ?? [],
        test_status: row.test_status ?? "not_tested",
        test_status_summary:
          row.test_status_summary ??
          {
            not_tested: 1,
            passed: 0,
            partial: 0,
            failed: 0,
            detected_not_blocked: 0,
          },
        bas_validations: row.bas_validations,
        bas_validated: row.bas_validated,
        bas_result: row.bas_result,
        last_bas_validation_date: row.last_bas_validation_date,
        is_gap_tested_failed: row.is_gap_tested_failed ?? false,
        is_gap_detected_not_blocked: row.is_gap_detected_not_blocked ?? false,
        is_gap_untested_critical: row.is_gap_untested_critical ?? false,
        tactic,
        display_group: displayGroup,
        contributions: localCoverage.contributions,
      }));
    })
    .sort((left, right) => {
      const leftTacticIndex = tacticOrder.indexOf(left.tactic);
      const rightTacticIndex = tacticOrder.indexOf(right.tactic);
      const tacticDelta =
        (leftTacticIndex === -1 ? tacticOrder.length : leftTacticIndex) -
        (rightTacticIndex === -1 ? tacticOrder.length : rightTacticIndex);
      if (tacticDelta !== 0) {
        return tacticDelta;
      }
      return left.technique_code.localeCompare(right.technique_code);
    });
}

function summarizeCoverageForSelectedTool(
  row: TechniqueCoverage,
  selectedToolId: number,
): TechniqueCoverage & { contributions: CapabilityContribution[] } {
  const contributions = mapCoverageContributions(row).filter(
    (contribution) => contribution.toolId === selectedToolId,
  );
  const responseActions = row.response_actions.filter((action) => action.tool_id === selectedToolId);

  return summarizeCoverage(
    contributions,
    responseActions,
    row.relevant_scopes,
    row.has_capability_mappings ?? true,
  );
}

function mapCoverageContributions(row: TechniqueCoverage): CapabilityContribution[] {
  return row.contributing_tools.map<CapabilityContribution>((contribution) => ({
    capabilityId: contribution.capability_id,
    capabilityCode: contribution.capability_code,
    capabilityName: contribution.capability_name,
    capabilityDomain: contribution.capability_domain ?? contribution.capability_name,
    toolId: contribution.tool_id,
    toolName: contribution.tool_name,
    toolCategory: contribution.tool_category,
    toolTypes: contribution.tool_types,
    controlEffect: contribution.control_effect,
    theoreticalEffect: contribution.theoretical_effect ?? contribution.control_effect,
    realEffect: contribution.real_effect ?? contribution.control_effect,
    configuredEffectDefault: contribution.configured_effect_default ?? contribution.control_effect,
    controlEffectSource: contribution.control_effect_source ?? "default",
    overrideApplied: contribution.override_applied ?? false,
    implementationLevel: contribution.implementation_level,
    mappingCoverage: contribution.mapping_coverage,
    confidenceSource: contribution.confidence_source,
    confidenceLevel: contribution.confidence_level,
    dependencyWarnings: contribution.dependency_warnings,
    configurationStatus: contribution.configuration_status,
    effectivelyActive: contribution.effectively_active,
    scopes: contribution.scopes,
  }));
}

export function filterTechniqueStates(
  techniques: DerivedTechnique[],
  coverageFilters: CoverageType[],
  showOnlyGaps: boolean,
  scopeFilter: string = "all",
) {
  return techniques.filter((technique) => {
    const matchesCoverage = coverageFilters.includes(technique.coverage_type);
    const matchesGap = !showOnlyGaps || isCriticalGap(technique);
    const matchesScope =
      scopeFilter === "all" ||
      technique.relevant_scopes.some((scope) => scope.coverage_scope.code === scopeFilter);
    return matchesCoverage && matchesGap && matchesScope;
  });
}

export function filterTechniquesByDisplayGroup(
  techniques: DerivedTechnique[],
  displayGroup: TechniqueDisplayGroup | "all",
) {
  if (displayGroup === "all") {
    return techniques;
  }

  return techniques.filter((technique) => technique.display_group === displayGroup);
}

export function summarizeCoverage(
  contributions: CapabilityContribution[],
  responseActions: TechniqueResponseAction[] = [],
  relevantScopes: TechniqueCoverage["relevant_scopes"] = [],
  hasCapabilityMappings: boolean = true,
): TechniqueCoverage & { contributions: CapabilityContribution[] } {
  const effectiveControlEffect = strongestEffect(contributions);
  const theoreticalEffect = strongestTheoreticalEffect(contributions);
  const effectiveContributions = contributions.filter(
    (contribution) => contribution.controlEffect === effectiveControlEffect,
  );
  const theoreticalContributions = contributions.filter(
    (contribution) => contribution.theoreticalEffect === theoreticalEffect,
  );
  const toolIds = new Set(
    contributions.filter((contribution) => contribution.controlEffect !== "none").map((contribution) => contribution.toolId),
  );
  const confidenceBasis = effectiveContributions.length ? effectiveContributions : theoreticalContributions;
  const confidenceLevel = confidenceBasis.length
    ? confidenceBasis
        .sort((left, right) => confidenceRank[right.confidenceLevel] - confidenceRank[left.confidenceLevel])[0]
        .confidenceLevel
    : "low";
  const confidenceSourceSummary = Array.from(
    new Set(confidenceBasis.map((contribution) => contribution.confidenceSource)),
  );
  const responseEnabled = responseActions.length > 0 && effectiveControlEffect !== "none";
  const effectiveOutcome =
    effectiveControlEffect === "detect" && responseEnabled ? "detect_with_response" : effectiveControlEffect;
  const dependencyFlags = Array.from(
    new Set([
      ...(hasCapabilityMappings ? [] : ["No capability mappings defined for this technique"]),
      ...effectiveContributions.flatMap((contribution) => contribution.dependencyWarnings),
      ...(responseEnabled ? ["Response enabled"] : []),
      ...(effectiveControlEffect === "detect" && !responseEnabled ? ["Detection without response"] : []),
      ...(effectiveControlEffect === "none" && responseActions.length > 0
        ? ["Response without upstream detection"]
        : []),
    ]),
  );

  const isGapNoCoverage = hasCapabilityMappings && effectiveControlEffect === "none";
  const isGapDetectOnly = hasCapabilityMappings && effectiveControlEffect === "detect";
  const isGapPartial =
    hasCapabilityMappings &&
    effectiveControlEffect !== "none" &&
    effectiveContributions.length > 0 &&
    effectiveContributions.every(
      (contribution) =>
        contribution.implementationLevel === "partial" || contribution.mappingCoverage === "partial",
    );
  const isGapLowConfidence = hasCapabilityMappings && effectiveControlEffect !== "none" && confidenceLevel === "low";
  const isGapSingleToolDependency = hasCapabilityMappings && effectiveControlEffect !== "none" && toolIds.size === 1;
  const isGapMissingDataSources =
    hasCapabilityMappings && dependencyFlags.some((flag) => flag.toLowerCase().includes("missing"));
  const isGapDetectionWithoutResponse = hasCapabilityMappings && effectiveControlEffect === "detect" && !responseEnabled;
  const isGapResponseWithoutDetection =
    hasCapabilityMappings && effectiveControlEffect === "none" && responseActions.length > 0;
  const isGapUnconfiguredControl =
    hasCapabilityMappings && dependencyFlags.some((flag) => flag.toLowerCase().includes("unconfigured"));
  const isGapPartiallyConfiguredControl =
    hasCapabilityMappings && dependencyFlags.some((flag) => flag.toLowerCase().includes("partially enabled"));
  const scopeSummary = summarizeScopes(relevantScopes, contributions);
  const isGapScopeMissing = hasCapabilityMappings && scopeSummary.missing_scopes.length > 0;
  const isGapScopePartial = hasCapabilityMappings && scopeSummary.partial_scopes.length > 0;
  const finalIsGapPartial =
    isGapPartial || (hasCapabilityMappings && effectiveControlEffect !== "none" && (isGapScopeMissing || isGapScopePartial));

  return {
    technique_id: 0,
    technique_code: "",
    technique_name: "",
    attack_url: "",
    has_capability_mappings: hasCapabilityMappings,
    mapped_capability_count: 0,
    theoretical_effect: theoreticalEffect,
    real_effect: effectiveControlEffect,
    bas_validations: [],
    bas_validated: false,
    bas_result: null,
    last_bas_validation_date: null,
    confidence_source_summary: confidenceSourceSummary,
    mapped_domains: [],
    test_results: [],
    test_status: "not_tested",
    test_status_summary: {
      not_tested: 1,
      passed: 0,
      partial: 0,
      failed: 0,
      detected_not_blocked: 0,
    },
    available_effects: (["prevent", "block", "detect"] as const).filter((effect) =>
      contributions.some((contribution) => contribution.controlEffect === effect),
    ),
    best_effect: effectiveControlEffect,
    detection_count: contributions.filter((contribution) => contribution.controlEffect === "detect").length,
    blocking_count: contributions.filter((contribution) => contribution.controlEffect === "block").length,
    prevention_count: contributions.filter((contribution) => contribution.controlEffect === "prevent").length,
    coverage_type: effectiveControlEffect,
    effective_control_effect: effectiveControlEffect,
    effective_outcome: effectiveOutcome,
    tool_count: toolIds.size,
    confidence_level: confidenceLevel,
    coverage_status: buildCoverageStatus({
      hasCapabilityMappings,
      isGapNoCoverage,
      isGapDetectOnly,
      isGapPartial,
      isGapLowConfidence,
    }),
    response_enabled: responseEnabled,
    response_actions: responseActions,
    dependency_flags: dependencyFlags,
    contributing_tools: [],
    relevant_scopes: relevantScopes,
    scope_summary: scopeSummary,
    is_gap_no_coverage: isGapNoCoverage,
    is_gap_detect_only: isGapDetectOnly,
    is_gap_partial: finalIsGapPartial,
    is_gap_low_confidence: isGapLowConfidence,
    is_gap_single_tool_dependency: isGapSingleToolDependency,
    is_gap_missing_data_sources: isGapMissingDataSources,
    is_gap_detection_without_response: isGapDetectionWithoutResponse,
    is_gap_response_without_detection: isGapResponseWithoutDetection,
    is_gap_unconfigured_control: isGapUnconfiguredControl,
    is_gap_partially_configured_control: isGapPartiallyConfiguredControl,
    is_gap_scope_missing: isGapScopeMissing,
    is_gap_scope_partial: isGapScopePartial,
    is_gap_tested_failed: false,
    is_gap_detected_not_blocked: false,
    is_gap_untested_critical: false,
    contributions,
  };
}

export function isGap(technique: DerivedTechnique) {
  return (
    technique.is_gap_no_coverage ||
    technique.is_gap_detect_only ||
    technique.is_gap_partial ||
    technique.is_gap_low_confidence ||
    technique.is_gap_single_tool_dependency ||
    technique.is_gap_missing_data_sources ||
    technique.is_gap_detection_without_response ||
    technique.is_gap_response_without_detection ||
    technique.is_gap_unconfigured_control ||
    technique.is_gap_partially_configured_control ||
    technique.is_gap_scope_missing ||
    technique.is_gap_scope_partial ||
    technique.is_gap_tested_failed ||
    technique.is_gap_detected_not_blocked ||
    technique.is_gap_untested_critical
  );
}

export function isCriticalGap(technique: DerivedTechnique) {
  return technique.is_gap_no_coverage;
}

export function buildCounters(techniques: DerivedTechnique[]) {
  return {
    total: techniques.length,
    covered: techniques.filter((technique) => technique.coverage_type !== "none").length,
    gaps: techniques.filter((technique) => isGap(technique)).length,
    detectOnly: techniques.filter((technique) => technique.is_gap_detect_only).length,
  };
}

export function buildDisplayGroupCounters(techniques: DerivedTechnique[]) {
  const uniqueTechniques = Array.from(
    new Map(techniques.map((technique) => [technique.technique_code, technique])).values(),
  );
  const coreTechniques = uniqueTechniques.filter((technique) => technique.display_group === "core");
  const extendedTechniques = uniqueTechniques.filter((technique) => technique.display_group === "extended");

  return {
    coreTotal: coreTechniques.length,
    coreCovered: coreTechniques.filter((technique) => technique.coverage_type !== "none").length,
    coreGaps: coreTechniques.filter((technique) => isGap(technique)).length,
    extendedTotal: extendedTechniques.length,
    extendedCovered: extendedTechniques.filter((technique) => technique.coverage_type !== "none").length,
    extendedGaps: extendedTechniques.filter((technique) => isGap(technique)).length,
  };
}

export function buildToolOptions(tools: Tool[]): ToolCoverageSummary[] {
  return [
    { id: "all", name: "All tools" },
    ...tools.map((tool) => ({ id: tool.id, name: tool.name })),
  ];
}

export function buildScopeOptions(techniques: TechniqueCoverage[]) {
  const seen = new Map<string, CoverageScope>();

  for (const technique of techniques) {
    for (const scope of technique.relevant_scopes) {
      if (!seen.has(scope.coverage_scope.code)) {
        seen.set(scope.coverage_scope.code, scope.coverage_scope);
      }
    }
  }

  return [
    { code: "all", name: "All scopes" },
    ...Array.from(seen.values())
      .sort((left, right) => left.name.localeCompare(right.name))
      .map((scope) => ({ code: scope.code, name: scope.name })),
  ];
}

function strongestEffect(contributions: CapabilityContribution[]) {
  let coverageType: CoverageType = "none";

  for (const contribution of contributions) {
    if (coverageRank[contribution.controlEffect] > coverageRank[coverageType]) {
      coverageType = contribution.controlEffect;
    }
  }

  return coverageType;
}

function strongestTheoreticalEffect(contributions: CapabilityContribution[]) {
  let coverageType: CoverageType = "none";

  for (const contribution of contributions) {
    const nextEffect = contribution.theoreticalEffect ?? contribution.controlEffect;
    if (coverageRank[nextEffect] > coverageRank[coverageType]) {
      coverageType = nextEffect;
    }
  }

  return coverageType;
}

function buildCoverageStatus(flags: {
  hasCapabilityMappings: boolean;
  isGapNoCoverage: boolean;
  isGapDetectOnly: boolean;
  isGapPartial: boolean;
  isGapLowConfidence: boolean;
}): CoverageStatus {
  if (!flags.hasCapabilityMappings) {
    return "unmapped";
  }
  if (flags.isGapNoCoverage) {
    return "no_coverage";
  }
  if (flags.isGapDetectOnly) {
    return "detect_only";
  }
  if (flags.isGapPartial) {
    return "partial";
  }
  if (flags.isGapLowConfidence) {
    return "low_confidence";
  }
  return "covered";
}

function summarizeScopes(
  relevantScopes: TechniqueCoverage["relevant_scopes"],
  contributions: CapabilityContribution[],
): TechniqueCoverage["scope_summary"] {
  const scopeStatus = new Map<string, "none" | "partial" | "full">(
    (relevantScopes ?? []).map((scope) => [scope.coverage_scope.code, "none"]),
  );

  for (const contribution of contributions) {
    for (const scope of contribution.scopes ?? []) {
      const current = scopeStatus.get(scope.coverage_scope.code);
      if (!current) {
        continue;
      }
      const next = scope.status;
      if ((next === "full" && current !== "full") || (next === "partial" && current === "none")) {
        scopeStatus.set(scope.coverage_scope.code, next);
      }
    }
  }

  return {
    full_scopes: Array.from(scopeStatus.entries())
      .filter(([, status]) => status === "full")
      .map(([code]) => code),
    partial_scopes: Array.from(scopeStatus.entries())
      .filter(([, status]) => status === "partial")
      .map(([code]) => code),
    missing_scopes: Array.from(scopeStatus.entries())
      .filter(([, status]) => status === "none")
      .map(([code]) => code),
  };
}

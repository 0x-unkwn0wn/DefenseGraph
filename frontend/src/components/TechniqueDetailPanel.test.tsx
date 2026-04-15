import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TechniqueDetailPanel } from "./TechniqueDetailPanel";

describe("TechniqueDetailPanel", () => {
  it("shows whether each contribution uses the default effect or an override", () => {
    render(
      <TechniqueDetailPanel
        technique={{
          technique_id: 401,
          technique_code: "T1041",
          technique_name: "Exfiltration Over C2 Channel",
          attack_url: "https://attack.mitre.org/techniques/T1041/",
          available_effects: ["block", "detect"],
          best_effect: "block",
          detection_count: 1,
          blocking_count: 1,
          prevention_count: 0,
          coverage_type: "block",
          effective_control_effect: "block",
          effective_outcome: "block",
          tool_count: 2,
          confidence_level: "medium",
          coverage_status: "covered",
          response_enabled: false,
          response_actions: [],
          dependency_flags: [],
          contributing_tools: [],
          relevant_scopes: [],
          scope_summary: {
            full_scopes: ["server"],
            partial_scopes: [],
            missing_scopes: [],
          },
          bas_validations: [],
          bas_validated: false,
          bas_result: null,
          last_bas_validation_date: null,
          is_gap_no_coverage: false,
          is_gap_detect_only: false,
          is_gap_partial: false,
          is_gap_low_confidence: false,
          is_gap_single_tool_dependency: false,
          is_gap_missing_data_sources: false,
          is_gap_detection_without_response: false,
          is_gap_response_without_detection: false,
          is_gap_unconfigured_control: false,
          is_gap_partially_configured_control: false,
          is_gap_scope_missing: false,
          is_gap_scope_partial: false,
          tactic: "Collection / Exfiltration",
          display_group: "extended",
          contributions: [
            {
              capabilityId: 7,
              capabilityCode: "CAP-007",
              capabilityName: "Data Exfiltration Protection",
              toolId: 11,
              toolName: "DLP",
              toolCategory: "DLP",
              toolTypes: ["control"],
              controlEffect: "detect",
              configuredEffectDefault: "block",
              controlEffectSource: "override",
              overrideApplied: true,
              implementationLevel: "full",
              mappingCoverage: "full",
              confidenceSource: "declared",
              confidenceLevel: "medium",
              dependencyWarnings: [],
              configurationStatus: null,
              effectivelyActive: true,
              scopes: [],
            },
            {
              capabilityId: 30,
              capabilityCode: "CAP-030",
              capabilityName: "Security Event Correlation",
              toolId: 12,
              toolName: "QRadar",
              toolCategory: "Security Analytics",
              toolTypes: ["analytics"],
              controlEffect: "detect",
              configuredEffectDefault: "detect",
              controlEffectSource: "default",
              overrideApplied: false,
              implementationLevel: "full",
              mappingCoverage: "full",
              confidenceSource: "declared",
              confidenceLevel: "medium",
              dependencyWarnings: [],
              configurationStatus: null,
              effectivelyActive: true,
              scopes: [],
            },
          ],
        }}
        onClose={() => undefined}
      />,
    );

    expect(screen.getByText("override")).toBeInTheDocument();
    expect(screen.getByText("default")).toBeInTheDocument();
    expect(screen.getByText(/Data Exfiltration Protection \| control \| default block \| full implementation/i)).toBeInTheDocument();
    expect(screen.getByText(/Security Event Correlation \| analytics \| default detect \| full implementation/i)).toBeInTheDocument();
  });
});

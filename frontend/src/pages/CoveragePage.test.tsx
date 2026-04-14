import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CoveragePage } from "./CoveragePage";

describe("CoveragePage", () => {
  it("shows core techniques by default and reveals extended techniques on toggle", async () => {
    const user = userEvent.setup();

    render(
      <CoveragePage
        capabilities={[]}
        coverage={[
          {
            technique_id: 1,
            technique_code: "T1133",
            technique_name: "External Remote Services",
            coverage_type: "none",
            effective_control_effect: "none",
            effective_outcome: "none",
            tool_count: 0,
            confidence_level: "low",
            coverage_status: "no_coverage",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [],
            relevant_scopes: [],
            scope_summary: { full_scopes: [], partial_scopes: [], missing_scopes: [] },
            is_gap_no_coverage: true,
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
          },
          {
            technique_id: 2,
            technique_code: "T1190",
            technique_name: "Exploit Public-Facing Application",
            coverage_type: "none",
            effective_control_effect: "none",
            effective_outcome: "none",
            tool_count: 0,
            confidence_level: "low",
            coverage_status: "no_coverage",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [],
            relevant_scopes: [],
            scope_summary: { full_scopes: [], partial_scopes: [], missing_scopes: [] },
            is_gap_no_coverage: true,
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
          },
        ]}
        tools={[]}
      />,
    );

    expect(screen.getByText("External Remote Services")).toBeInTheDocument();
    expect(screen.queryByText("Exploit Public-Facing Application")).not.toBeInTheDocument();

    await user.click(screen.getByLabelText(/show extended techniques/i));

    expect(screen.getByText("Exploit Public-Facing Application")).toBeInTheDocument();
    expect(screen.getAllByText(/extended/i).length).toBeGreaterThan(0);
  });

  it("shows dependency and response indicators in the technique detail panel", async () => {
    const user = userEvent.setup();

    render(
      <CoveragePage
        capabilities={[]}
        coverage={[
          {
            technique_id: 1,
            technique_code: "T1078",
            technique_name: "Valid Accounts",
            coverage_type: "detect",
            effective_control_effect: "detect",
            effective_outcome: "detect_with_response",
            tool_count: 1,
            confidence_level: "low",
            coverage_status: "detect_only",
            response_enabled: true,
            response_actions: [
              {
                tool_id: 2,
                tool_name: "XSOAR",
                action_code: "RA-002",
                action_name: "Disable Account",
                implementation_level: "full",
              },
            ],
            dependency_flags: ["Missing Active Directory Logs", "Response enabled"],
            contributing_tools: [
              {
                tool_id: 1,
                tool_name: "QRadar",
                tool_category: "Security Analytics",
                tool_type: "analytics",
                capability_id: 9,
                capability_code: "CAP-009",
                capability_name: "Identity Misuse Detection",
                control_effect: "detect",
                implementation_level: "partial",
                confidence_level: "low",
                confidence_source: "declared",
                mapping_coverage: "partial",
                dependency_warnings: ["Missing Active Directory Logs"],
                configuration_status: null,
                effectively_active: true,
                scopes: [
                  {
                    id: 1,
                    tool_capability_id: 1,
                    coverage_scope_id: 4,
                    status: "full",
                    notes: "",
                    coverage_scope: {
                      id: 4,
                      code: "identity",
                      name: "Identity",
                      description: "Identity systems",
                    },
                  },
                ],
              },
            ],
            relevant_scopes: [
              {
                coverage_scope_id: 4,
                relevance: "primary",
                coverage_scope: {
                  id: 4,
                  code: "identity",
                  name: "Identity",
                  description: "Identity systems",
                },
              },
            ],
            scope_summary: { full_scopes: ["identity"], partial_scopes: [], missing_scopes: [] },
            is_gap_no_coverage: false,
            is_gap_detect_only: true,
            is_gap_partial: true,
            is_gap_low_confidence: true,
            is_gap_single_tool_dependency: true,
            is_gap_missing_data_sources: true,
            is_gap_detection_without_response: false,
            is_gap_response_without_detection: false,
            is_gap_unconfigured_control: false,
            is_gap_partially_configured_control: false,
            is_gap_scope_missing: false,
            is_gap_scope_partial: false,
          },
        ]}
        tools={[
          {
            id: 1,
            name: "QRadar",
            category: "Security Analytics",
            tool_type: "analytics",
            tags: [],
            capabilities: [],
            data_sources: [],
            response_actions: [],
          },
          {
            id: 2,
            name: "XSOAR",
            category: "SOAR",
            tool_type: "response",
            tags: [],
            capabilities: [],
            data_sources: [],
            response_actions: [],
          },
        ]}
      />,
    );

    await user.click(screen.getByRole("button", { name: /T1078/i }));

    expect(screen.getAllByText(/Missing Active Directory Logs/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Disable Account/i)).toBeInTheDocument();
    expect(screen.getAllByText(/response/i).length).toBeGreaterThan(0);
  });
});

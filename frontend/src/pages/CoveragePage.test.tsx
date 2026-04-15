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
            attack_url: "https://attack.mitre.org/techniques/T1133/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
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
            attack_url: "https://attack.mitre.org/techniques/T1190/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
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

  it("treats unmapped techniques as out of model instead of critical gaps", async () => {
    const user = userEvent.setup();

    render(
      <CoveragePage
        capabilities={[]}
        coverage={[
          {
            technique_id: 1,
            technique_code: "T9000",
            technique_name: "Unmapped Technique",
            has_capability_mappings: false,
            mapped_capability_count: 0,
            coverage_type: "none",
            effective_control_effect: "none",
            effective_outcome: "none",
            tool_count: 0,
            confidence_level: "low",
            coverage_status: "unmapped",
            response_enabled: false,
            response_actions: [],
            dependency_flags: ["No capability mappings defined for this technique"],
            contributing_tools: [],
            relevant_scopes: [],
            scope_summary: { full_scopes: [], partial_scopes: [], missing_scopes: [] },
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
            attack_url: "https://attack.mitre.org/techniques/T9000/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
          {
            technique_id: 2,
            technique_code: "T1133",
            technique_name: "External Remote Services",
            has_capability_mappings: true,
            mapped_capability_count: 1,
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
            attack_url: "https://attack.mitre.org/techniques/T1133/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[]}
      />,
    );

    await user.click(screen.getByRole("button", { name: "gaps" }));

    expect(screen.getByText("External Remote Services")).toBeInTheDocument();
    expect(screen.queryByText("Unmapped Technique")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "coverage" }));
    await user.click(screen.getByLabelText(/show extended techniques/i));
    await user.click(screen.getByRole("button", { name: /T9000/i }));

    expect(screen.getByText("Unmapped")).toBeInTheDocument();
    expect(
      screen.getByText(/excluded from gap counts until the model is extended/i),
    ).toBeInTheDocument();
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
                tool_types: ["analytics"],
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
            attack_url: "https://attack.mitre.org/techniques/T1078/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[
          {
            id: 1,
            name: "QRadar",
            category: "Security Analytics",
            tool_types: ["analytics"],
            tags: [],
            capabilities: [],
            data_sources: [],
            response_actions: [],
          },
          {
            id: 2,
            name: "XSOAR",
            category: "SOAR",
            tool_types: ["response"],
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

  it("filters the matrix when show only critical gaps is enabled", async () => {
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
            attack_url: "https://attack.mitre.org/techniques/T1133/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
          {
            technique_id: 2,
            technique_code: "T1059",
            technique_name: "Command and Scripting Interpreter",
            coverage_type: "block",
            effective_control_effect: "block",
            effective_outcome: "block",
            tool_count: 2,
            confidence_level: "high",
            coverage_status: "covered",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [
              {
                tool_id: 1,
                tool_name: "EDR A",
                tool_category: "EDR",
                tool_types: ["control"],
                capability_id: 1,
                capability_code: "CAP-001",
                capability_name: "Script Execution Control",
                control_effect: "block",
                implementation_level: "full",
                confidence_level: "high",
                confidence_source: "evidenced",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: null,
                effectively_active: true,
                scopes: [],
              },
              {
                tool_id: 2,
                tool_name: "EDR B",
                tool_category: "EDR",
                tool_types: ["control"],
                capability_id: 1,
                capability_code: "CAP-001",
                capability_name: "Script Execution Control",
                control_effect: "block",
                implementation_level: "full",
                confidence_level: "high",
                confidence_source: "tested",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: null,
                effectively_active: true,
                scopes: [],
              },
            ],
            relevant_scopes: [],
            scope_summary: { full_scopes: [], partial_scopes: [], missing_scopes: [] },
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
            attack_url: "https://attack.mitre.org/techniques/T1059/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[]}
      />,
    );

    expect(screen.getByText("External Remote Services")).toBeInTheDocument();
    expect(screen.getByText("Command and Scripting Interpreter")).toBeInTheDocument();

    await user.click(screen.getByLabelText(/show only critical gaps/i));

    expect(screen.getByText("External Remote Services")).toBeInTheDocument();
    expect(screen.queryByText("Command and Scripting Interpreter")).not.toBeInTheDocument();
  });

  it("filters the matrix by scope", async () => {
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
            effective_outcome: "detect",
            tool_count: 1,
            confidence_level: "medium",
            coverage_status: "detect_only",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [
              {
                tool_id: 1,
                tool_name: "Identity Control",
                tool_category: "Identity",
                tool_types: ["control"],
                capability_id: 9,
                capability_code: "CAP-009",
                capability_name: "Identity Misuse Detection",
                control_effect: "detect",
                implementation_level: "full",
                confidence_level: "medium",
                confidence_source: "assessed",
                mapping_coverage: "full",
                dependency_warnings: [],
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
            is_gap_partial: false,
            is_gap_low_confidence: false,
            is_gap_single_tool_dependency: true,
            is_gap_missing_data_sources: false,
            is_gap_detection_without_response: true,
            is_gap_response_without_detection: false,
            is_gap_unconfigured_control: false,
            is_gap_partially_configured_control: false,
            is_gap_scope_missing: false,
            is_gap_scope_partial: false,
            attack_url: "https://attack.mitre.org/techniques/T1078/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
          {
            technique_id: 2,
            technique_code: "T1071.004",
            technique_name: "DNS",
            coverage_type: "block",
            effective_control_effect: "block",
            effective_outcome: "block",
            tool_count: 2,
            confidence_level: "high",
            coverage_status: "covered",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [
              {
                tool_id: 2,
                tool_name: "DNS Control",
                tool_category: "DNS",
                tool_types: ["control"],
                capability_id: 6,
                capability_code: "CAP-006",
                capability_name: "DNS C2 Control",
                control_effect: "block",
                implementation_level: "full",
                confidence_level: "high",
                confidence_source: "tested",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: null,
                effectively_active: true,
                scopes: [
                  {
                    id: 2,
                    tool_capability_id: 2,
                    coverage_scope_id: 5,
                    status: "full",
                    notes: "",
                    coverage_scope: {
                      id: 5,
                      code: "network",
                      name: "Network",
                      description: "Network controls",
                    },
                  },
                ],
              },
              {
                tool_id: 3,
                tool_name: "DNS Control B",
                tool_category: "DNS",
                tool_types: ["control"],
                capability_id: 6,
                capability_code: "CAP-006",
                capability_name: "DNS C2 Control",
                control_effect: "block",
                implementation_level: "full",
                confidence_level: "high",
                confidence_source: "evidenced",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: null,
                effectively_active: true,
                scopes: [
                  {
                    id: 3,
                    tool_capability_id: 3,
                    coverage_scope_id: 5,
                    status: "full",
                    notes: "",
                    coverage_scope: {
                      id: 5,
                      code: "network",
                      name: "Network",
                      description: "Network controls",
                    },
                  },
                ],
              },
            ],
            relevant_scopes: [
              {
                coverage_scope_id: 5,
                relevance: "secondary",
                coverage_scope: {
                  id: 5,
                  code: "network",
                  name: "Network",
                  description: "Network controls",
                },
              },
            ],
            scope_summary: { full_scopes: ["network"], partial_scopes: [], missing_scopes: [] },
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
            attack_url: "https://attack.mitre.org/techniques/T1071.004/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[]}
      />,
    );

    expect(screen.getByText("Valid Accounts")).toBeInTheDocument();
    expect(screen.getByText("DNS")).toBeInTheDocument();

    await user.selectOptions(screen.getByRole("combobox", { name: /scope/i }), "identity");

    expect(screen.getByText("Valid Accounts")).toBeInTheDocument();
    expect(screen.queryByText("DNS")).not.toBeInTheDocument();
  });
});

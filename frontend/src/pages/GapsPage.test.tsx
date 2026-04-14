import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { GapsPage } from "./GapsPage";

describe("GapsPage", () => {
  it("shows low confidence and single-tool dependency gaps", () => {
    render(
      <GapsPage
        capabilities={[
          {
            id: 6,
            code: "CAP-006",
            name: "DNS C2 Control",
            domain: "network",
            description: "Detects or blocks C2 over DNS.",
            requires_data_sources: true,
            supported_by_analytics: true,
            supported_by_response: true,
            requires_configuration: true,
            configuration_profile_type: "dns_security",
          },
        ]}
        coverage={[
          {
            technique_id: 10,
            technique_code: "T1071.004",
            technique_name: "DNS",
            coverage_type: "detect",
            effective_control_effect: "detect",
            effective_outcome: "detect",
            tool_count: 1,
            confidence_level: "low",
            coverage_status: "detect_only",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [
              {
                tool_id: 1,
                tool_name: "Resolver Control",
                tool_category: "DNS",
                tool_types: ["control"],
                capability_id: 6,
                capability_code: "CAP-006",
                capability_name: "DNS C2 Control",
                control_effect: "detect",
                implementation_level: "full",
                confidence_level: "low",
                confidence_source: "declared",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: "partially_enabled",
                effectively_active: true,
                scopes: [
                  {
                    id: 1,
                    tool_capability_id: 1,
                    coverage_scope_id: 1,
                    status: "full",
                    notes: "",
                    coverage_scope: {
                      id: 1,
                      code: "endpoint_user_device",
                      name: "Endpoint / User Device",
                      description: "Managed endpoints",
                    },
                  },
                ],
              },
            ],
            relevant_scopes: [
              {
                coverage_scope_id: 1,
                relevance: "primary",
                coverage_scope: {
                  id: 1,
                  code: "endpoint_user_device",
                  name: "Endpoint / User Device",
                  description: "Managed endpoints",
                },
              },
            ],
            scope_summary: { full_scopes: ["endpoint_user_device"], partial_scopes: [], missing_scopes: [] },
            is_gap_no_coverage: false,
            is_gap_detect_only: true,
            is_gap_partial: false,
            is_gap_low_confidence: true,
            is_gap_single_tool_dependency: true,
            is_gap_missing_data_sources: false,
            is_gap_detection_without_response: true,
            is_gap_response_without_detection: false,
            is_gap_unconfigured_control: false,
            is_gap_partially_configured_control: true,
            is_gap_scope_missing: false,
            is_gap_scope_partial: false,
            attack_url: "https://attack.mitre.org/techniques/T1071/004/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[
          {
            id: 1,
            name: "Resolver Control",
            category: "DNS",
            tool_types: ["control"],
            tags: ["DNS"],
            capabilities: [
              {
                capability_id: 6,
                control_effect: "detect",
                implementation_level: "full",
                confidence_source: "declared",
                confidence_level: "low",
                scopes: [],
              },
            ],
            data_sources: [],
            response_actions: [],
          },
        ]}
      />,
    );

    expect(screen.getByText("Low confidence")).toBeInTheDocument();
    expect(screen.getByText("Single-tool dependency")).toBeInTheDocument();
    expect(screen.getByText("Core techniques covered")).toBeInTheDocument();
    expect(screen.getByText("Extended gaps")).toBeInTheDocument();
    expect(screen.getAllByText("1 tool").length).toBeGreaterThan(0);
  });

  it("filters gaps by core and extended catalog scope", async () => {
    const user = userEvent.setup();

    render(
      <GapsPage
        capabilities={[
          {
            id: 6,
            code: "CAP-006",
            name: "DNS C2 Control",
            domain: "network",
            description: "Detects or blocks C2 over DNS.",
            requires_data_sources: true,
            supported_by_analytics: true,
            supported_by_response: true,
            requires_configuration: true,
            configuration_profile_type: "dns_security",
          },
          {
            id: 25,
            code: "CAP-025",
            name: "Public-Facing Service Protection",
            domain: "network",
            description: "Protects exposed services.",
            requires_data_sources: true,
            supported_by_analytics: true,
            supported_by_response: false,
            requires_configuration: true,
            configuration_profile_type: "firewall",
          },
        ]}
        coverage={[
          {
            technique_id: 10,
            technique_code: "T1071.004",
            technique_name: "DNS",
            coverage_type: "detect",
            effective_control_effect: "detect",
            effective_outcome: "detect",
            tool_count: 1,
            confidence_level: "low",
            coverage_status: "detect_only",
            response_enabled: false,
            response_actions: [],
            dependency_flags: [],
            contributing_tools: [
              {
                tool_id: 1,
                tool_name: "Resolver Control",
                tool_category: "DNS",
                tool_types: ["control"],
                capability_id: 6,
                capability_code: "CAP-006",
                capability_name: "DNS C2 Control",
                control_effect: "detect",
                implementation_level: "full",
                confidence_level: "low",
                confidence_source: "declared",
                mapping_coverage: "full",
                dependency_warnings: [],
                configuration_status: "enabled",
                effectively_active: true,
                scopes: [
                  {
                    id: 1,
                    tool_capability_id: 1,
                    coverage_scope_id: 1,
                    status: "full",
                    notes: "",
                    coverage_scope: {
                      id: 1,
                      code: "endpoint_user_device",
                      name: "Endpoint / User Device",
                      description: "Managed endpoints",
                    },
                  },
                ],
              },
            ],
            relevant_scopes: [
              {
                coverage_scope_id: 1,
                relevance: "primary",
                coverage_scope: {
                  id: 1,
                  code: "endpoint_user_device",
                  name: "Endpoint / User Device",
                  description: "Managed endpoints",
                },
              },
            ],
            scope_summary: { full_scopes: ["endpoint_user_device"], partial_scopes: [], missing_scopes: [] },
            is_gap_no_coverage: false,
            is_gap_detect_only: true,
            is_gap_partial: false,
            is_gap_low_confidence: true,
            is_gap_single_tool_dependency: true,
            is_gap_missing_data_sources: false,
            is_gap_detection_without_response: true,
            is_gap_response_without_detection: false,
            is_gap_unconfigured_control: false,
            is_gap_partially_configured_control: false,
            is_gap_scope_missing: false,
            is_gap_scope_partial: false,
            attack_url: "https://attack.mitre.org/techniques/T1071/004/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
          {
            technique_id: 11,
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
            relevant_scopes: [
              {
                coverage_scope_id: 8,
                relevance: "primary",
                coverage_scope: {
                  id: 8,
                  code: "public_facing_app",
                  name: "Public-Facing Application",
                  description: "Internet-facing applications",
                },
              },
            ],
            scope_summary: { full_scopes: [], partial_scopes: [], missing_scopes: ["public_facing_app"] },
            is_gap_no_coverage: true,
            is_gap_detect_only: false,
            is_gap_partial: false,
            is_gap_low_confidence: false,
            is_gap_single_tool_dependency: false,
            is_gap_missing_data_sources: false,
            is_gap_detection_without_response: false,
            is_gap_response_without_detection: false,
            is_gap_unconfigured_control: true,
            is_gap_partially_configured_control: false,
            is_gap_scope_missing: true,
            is_gap_scope_partial: false,
            attack_url: "https://attack.mitre.org/techniques/T1190/",
            bas_validations: [],
            bas_validated: false,
            bas_result: null,
            last_bas_validation_date: null,
          },
        ]}
        tools={[
          {
            id: 1,
            name: "Resolver Control",
            category: "DNS",
            tool_types: ["control"],
            tags: ["DNS"],
            capabilities: [
              {
                capability_id: 6,
                control_effect: "detect",
                implementation_level: "full",
                confidence_source: "declared",
                confidence_level: "low",
                scopes: [],
              },
            ],
            data_sources: [],
            response_actions: [],
          },
        ]}
      />,
    );

    expect(screen.getAllByText(/Exploit Public-Facing Application/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "core" }));

    expect(screen.queryByText(/Exploit Public-Facing Application/i)).not.toBeInTheDocument();
    expect(screen.getAllByText(/T1071\.004 - DNS/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "extended" }));

    expect(screen.getAllByText(/Exploit Public-Facing Application/i).length).toBeGreaterThan(0);
    expect(screen.queryByText(/T1071\.004 - DNS/i)).not.toBeInTheDocument();
  });
});

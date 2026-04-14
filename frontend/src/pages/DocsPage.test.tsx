import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DocsPage } from "./DocsPage";

vi.mock("../api", () => ({
  listTools: vi.fn().mockResolvedValue([
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
  ]),
  listDocsToolTypes: vi.fn().mockResolvedValue([
    {
      tool_type: "analytics",
      tool_count: 1,
      description: "1 tools currently use this type and map to 1 capabilities.",
      inputs: ["Active Directory Logs"],
      outputs: ["Detect"],
      example_usage: ["QRadar"],
    },
  ]),
  listDocsCapabilities: vi.fn().mockResolvedValue([
    {
      capability: {
        id: 9,
        code: "CAP-009",
        name: "Identity Misuse Detection",
        domain: "identity",
        description: "Detect suspicious identity misuse.",
        requires_data_sources: true,
        supported_by_analytics: true,
        supported_by_response: true,
        requires_configuration: false,
        configuration_profile_type: null,
      },
      purpose: "Supports detect coverage across 2 ATT&CK techniques.",
      typical_use_cases: ["T1078 Valid Accounts"],
      tool_types: ["analytics"],
      implementing_tool_count: 1,
      related_techniques: ["T1078 Valid Accounts"],
    },
  ]),
  getDocsMappings: vi.fn().mockResolvedValue({
    tool_type_mappings: [
      {
        tool_type: "analytics",
        capabilities: [
          {
            id: 9,
            code: "CAP-009",
            name: "Identity Misuse Detection",
            domain: "identity",
            description: "Detect suspicious identity misuse.",
            requires_data_sources: true,
            supported_by_analytics: true,
            supported_by_response: true,
            requires_configuration: false,
            configuration_profile_type: null,
          },
        ],
      },
    ],
    capability_mappings: [
      {
        capability: {
          id: 9,
          code: "CAP-009",
          name: "Identity Misuse Detection",
          domain: "identity",
          description: "Detect suspicious identity misuse.",
          requires_data_sources: true,
          supported_by_analytics: true,
          supported_by_response: true,
          requires_configuration: false,
          configuration_profile_type: null,
        },
        tool_types: ["analytics"],
      },
    ],
  }),
}));

describe("DocsPage", () => {
  it("renders dynamic documentation sections from backend data", async () => {
    const user = userEvent.setup();

    render(<DocsPage />);

    await waitFor(() => {
      expect(screen.getByText("How DefenseGraph models coverage")).toBeInTheDocument();
    });

    expect(screen.getByText("QRadar")).toBeInTheDocument();
    expect(screen.getAllByText("Identity Misuse Detection").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Tool types/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: "Capabilities" }));
    await user.click(screen.getAllByRole("button", { name: "Collapse" })[0]);
  });
});

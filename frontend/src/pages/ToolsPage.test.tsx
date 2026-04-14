import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ToolsPage } from "./ToolsPage";

vi.mock("../api", () => ({
  listTags: vi.fn().mockResolvedValue([
    { name: "Active Directory", default_categories: ["Identity", "PAM"] },
    { name: "Password Security", default_categories: ["Identity"] },
    { name: "Authentication", default_categories: ["Identity", "SASE"] },
  ]),
  listToolTemplates: vi.fn().mockResolvedValue([
    {
      id: 1,
      category: "EDR",
      capability_id: 1,
      optional_tags: ["Endpoint Protection"],
      priority: "core",
      default_effect: "detect",
      default_implementation_level: "partial",
      confidence_hint: "declared",
      description: "Common baseline for endpoint execution visibility.",
      matched_tags: [],
      suggestion_group: "core",
      capability: {
        id: 1,
        code: "CAP-001",
        name: "Script Execution Control",
        domain: "endpoint",
        description: "Monitors script execution.",
      },
    },
    {
      id: 2,
      category: "EDR",
      capability_id: 3,
      optional_tags: ["Monitoring"],
      priority: "secondary",
      default_effect: "detect",
      default_implementation_level: "partial",
      confidence_hint: "declared",
      description: "Optional beaconing visibility.",
      matched_tags: [],
      suggestion_group: "optional",
      capability: {
        id: 3,
        code: "CAP-003",
        name: "Credential Dumping Protection",
        domain: "endpoint",
        description: "Detects credential dumping.",
      },
    },
  ]),
}));

describe("ToolsPage", () => {
  it("shows template selection step grouped into common and additional", async () => {
    const user = userEvent.setup();

    render(<ToolsPage tools={[]} onCreateTool={vi.fn()} onDeleteTool={vi.fn()} />);

    await user.type(screen.getByPlaceholderText(/new tool/i), "Test EDR");
    await user.selectOptions(screen.getByLabelText(/primary category/i), "EDR");
    await user.click(screen.getByRole("button", { name: /continue/i }));

    await waitFor(() => {
      expect(screen.getByText(/accept suggested tags/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("button", { name: /generate capability suggestions/i }));

    await waitFor(() => {
      expect(screen.getByText(/core for this category/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/additional capabilities/i)).toBeInTheDocument();
    expect(screen.getByText("Script Execution Control")).toBeInTheDocument();
    expect(screen.getByText("Credential Dumping Protection")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /skip suggestions/i })).toBeInTheDocument();
  });
});

import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { CapabilityDetailPage } from "./CapabilityDetailPage";

vi.mock("../api", () => ({
  getCapabilityDetail: vi.fn().mockResolvedValue({
    capability: {
      id: 30,
      code: "CAP-030",
      name: "Remote Access Abuse Detection",
      domain: "identity",
      description: "Detects suspicious remote access use that may indicate compromised external access paths.",
      requires_data_sources: true,
      supported_by_analytics: true,
      supported_by_response: true,
      requires_configuration: false,
      configuration_profile_type: null,
      related_techniques: [
        {
          technique_id: 24,
          technique_code: "T1078",
          technique_name: "Valid Accounts",
          attack_url: "https://attack.mitre.org/techniques/T1078/",
          control_effect: "detect",
          coverage: "full",
        },
        {
          technique_id: 23,
          technique_code: "T1021",
          technique_name: "Remote Services",
          attack_url: "https://attack.mitre.org/techniques/T1021/",
          control_effect: "detect",
          coverage: "full",
        },
      ],
    },
    assessment_template: null,
    related_techniques: [
      {
        technique_id: 24,
        technique_code: "T1078",
        technique_name: "Valid Accounts",
        attack_url: "https://attack.mitre.org/techniques/T1078/",
        control_effect: "detect",
        coverage: "full",
      },
      {
        technique_id: 23,
        technique_code: "T1021",
        technique_name: "Remote Services",
        attack_url: "https://attack.mitre.org/techniques/T1021/",
        control_effect: "detect",
        coverage: "full",
      },
    ],
    implementing_tools: [],
    required_data_sources: [],
    supported_response_actions: [],
    configuration_questions: [],
  }),
}));

describe("CapabilityDetailPage", () => {
  it("renders all mapped ATT&CK techniques for a capability", async () => {
    render(<CapabilityDetailPage capabilityId={30} />);

    await waitFor(() => {
      expect(screen.getByText("Remote Access Abuse Detection")).toBeInTheDocument();
    });

    expect(screen.getByRole("link", { name: /T1078 - Valid Accounts/i })).toHaveAttribute(
      "href",
      "https://attack.mitre.org/techniques/T1078/",
    );
    expect(screen.getByRole("link", { name: /T1021 - Remote Services/i })).toHaveAttribute(
      "href",
      "https://attack.mitre.org/techniques/T1021/",
    );
  });
});

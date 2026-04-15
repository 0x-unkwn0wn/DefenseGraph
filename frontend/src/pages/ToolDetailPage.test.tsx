import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ToolDetailPage } from "./ToolDetailPage";

vi.mock("../api", () => ({
  getToolCapabilityDetail: vi.fn().mockResolvedValue({
    capability: {
      id: 4,
      code: "CAP-004",
      name: "Email Phishing Protection",
      domain: "email",
      description: "Protects inbound mail flows.",
      requires_data_sources: false,
      supported_by_analytics: false,
      supported_by_response: false,
      requires_configuration: true,
      configuration_profile_type: "phishing_email",
      related_techniques: [
        {
          technique_id: 401,
          technique_code: "T1204",
          technique_name: "User Execution",
          attack_url: "https://attack.mitre.org/techniques/T1204/",
          coverage: "full",
        },
        {
          technique_id: 402,
          technique_code: "T1566",
          technique_name: "Phishing",
          attack_url: "https://attack.mitre.org/techniques/T1566/",
          coverage: "full",
        },
      ],
    },
    assignment: {
      capability_id: 4,
      control_effect_default: "prevent",
      implementation_level: "full",
      confidence_source: "declared",
      confidence_level: "low",
      scopes: [
        {
          id: 1,
          tool_capability_id: 1,
          coverage_scope_id: 6,
          status: "full",
          notes: "",
          coverage_scope: {
            id: 6,
            code: "email",
            name: "Email",
            description: "Email systems",
          },
        },
      ],
    },
    confidence: {
      confidence_source: "declared",
      confidence_level: "low",
      answered_questions: 0,
      total_questions: 4,
      score: 0,
      max_score: 8,
      evidence_count: 0,
    },
    assessment_template: {
      id: 1,
      capability_id: 4,
      description: "Mail controls",
      questions: [
        {
          id: 101,
          prompt: "Is URL rewriting enabled?",
          position: 1,
        },
      ],
    },
    assessment_answers: [],
    evidence: [],
    required_data_sources: [],
    supported_response_actions: [],
    configuration_profile: null,
    configuration_summary: {
      configuration_status: "unknown",
      answered_questions: 0,
      total_questions: 3,
      score: 0,
      max_score: 6,
    },
    configuration_questions: [
      {
        id: 201,
        question: "Is inbound phishing protection enabled?",
        applies_to_profile_type: "phishing_email",
      },
    ],
    configuration_answers: [],
    scopes: [
      {
        id: 1,
        tool_capability_id: 1,
        coverage_scope_id: 6,
        status: "full",
        notes: "",
        coverage_scope: {
          id: 6,
          code: "email",
          name: "Email",
          description: "Email systems",
        },
      },
    ],
    technique_overrides: [
      {
        id: 1,
        tool_capability_id: 1,
        technique_id: 401,
        technique_code: "T1204",
        technique_name: "User Execution",
        control_effect_override: "detect",
        implementation_level_override: null,
        notes: "",
      },
    ],
    relevant_scopes: [
      {
        id: 1,
        technique_id: 1,
        relevance: "primary",
        coverage_scope: {
          id: 6,
          code: "email",
          name: "Email",
          description: "Email systems",
        },
      },
    ],
  }),
}));

describe("ToolDetailPage", () => {
  it("shows confidence and opens the assessment workspace", async () => {
    const user = userEvent.setup();

    render(
      <ToolDetailPage
        toolId={1}
        tools={[
          {
            id: 1,
            name: "Mail Gateway",
            category: "Email",
            tool_types: ["control"],
            tags: ["Email Security", "Phishing"],
            capabilities: [
              {
                capability_id: 4,
                control_effect_default: "prevent",
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
        capabilities={[
          {
            id: 4,
            code: "CAP-004",
            name: "Email Phishing Protection",
            domain: "email",
            description: "Protects inbound mail flows.",
            requires_data_sources: false,
            supported_by_analytics: false,
            supported_by_response: false,
            requires_configuration: true,
            configuration_profile_type: "phishing_email",
          },
        ]}
        dataSources={[]}
        coverageScopes={[
          {
            id: 6,
            code: "email",
            name: "Email",
            description: "Email systems",
          },
        ]}
        responseActions={[]}
        onDeleteTool={vi.fn()}
        onSetCapability={vi.fn()}
        onSetToolDataSource={vi.fn()}
        onSetToolResponseAction={vi.fn()}
        onSaveAssessment={vi.fn()}
        onAddEvidence={vi.fn()}
        onSaveConfigurationProfile={vi.fn()}
        onSaveConfigurationAnswers={vi.fn()}
        onSaveCapabilityScopes={vi.fn()}
        onSaveTechniqueOverrides={vi.fn()}
        onUpdateTags={vi.fn()}
        onUpdateToolTypes={vi.fn()}
      />,
    );

    expect(screen.getByText("declared / low")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /verify configuration/i }));

    await waitFor(() => {
      expect(screen.getByText(/guided questionnaire/i)).toBeInTheDocument();
    });
    expect(screen.getByText("Is URL rewriting enabled?")).toBeInTheDocument();
    expect(screen.getByText(/verification checklist/i)).toBeInTheDocument();
  });

  it("renders ATT&CK overrides and falls back to the default effect when absent", async () => {
    const user = userEvent.setup();

    render(
      <ToolDetailPage
        toolId={1}
        tools={[
          {
            id: 1,
            name: "Mail Gateway",
            category: "Email",
            tool_types: ["control"],
            tags: ["Email Security", "Phishing"],
            capabilities: [
              {
                capability_id: 4,
                control_effect_default: "prevent",
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
        capabilities={[
          {
            id: 4,
            code: "CAP-004",
            name: "Email Phishing Protection",
            domain: "email",
            description: "Protects inbound mail flows.",
            requires_data_sources: false,
            supported_by_analytics: false,
            supported_by_response: false,
            requires_configuration: true,
            configuration_profile_type: "phishing_email",
          },
        ]}
        dataSources={[]}
        coverageScopes={[]}
        responseActions={[]}
        onDeleteTool={vi.fn()}
        onSetCapability={vi.fn()}
        onSetToolDataSource={vi.fn()}
        onSetToolResponseAction={vi.fn()}
        onSaveAssessment={vi.fn()}
        onAddEvidence={vi.fn()}
        onSaveConfigurationProfile={vi.fn()}
        onSaveConfigurationAnswers={vi.fn()}
        onSaveCapabilityScopes={vi.fn()}
        onSaveTechniqueOverrides={vi.fn()}
        onUpdateTags={vi.fn()}
        onUpdateToolTypes={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /verify configuration/i }));
    await waitFor(() => {
      expect(screen.getByText(/ATT&CK Behavior/i)).toBeInTheDocument();
    });

    expect(screen.getByText("2 techniques")).toBeInTheDocument();
    expect(screen.getByText("1 overrides")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Refine per technique/i }));

    expect(screen.getByText(/T1204 User Execution/i)).toBeInTheDocument();
    expect(screen.getByText(/T1566 Phishing/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("Detect")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Use default")).toBeInTheDocument();
  });

  it("renders analytics data sources and response actions for specialized tool types", () => {
    const { rerender } = render(
      <ToolDetailPage
        toolId={2}
        tools={[
          {
            id: 2,
            name: "QRadar",
            category: "Security Analytics",
            tool_types: ["analytics"],
            tags: ["Log Analytics"],
            capabilities: [],
            data_sources: [
              {
                id: 1,
                tool_id: 2,
                data_source_id: 1,
                ingestion_status: "partial",
                notes: "",
                data_source: {
                  id: 1,
                  code: "DS-001",
                  name: "Active Directory Logs",
                  category: "identity",
                  description: "Directory logs",
                },
              },
            ],
            response_actions: [],
          },
        ]}
        capabilities={[]}
        dataSources={[
          {
            id: 1,
            code: "DS-001",
            name: "Active Directory Logs",
            category: "identity",
            description: "Directory logs",
          },
        ]}
        coverageScopes={[]}
        responseActions={[
          {
            id: 1,
            code: "RA-002",
            name: "Disable Account",
            description: "Disable account",
          },
        ]}
        onDeleteTool={vi.fn()}
        onSetCapability={vi.fn()}
        onSetToolDataSource={vi.fn()}
        onSetToolResponseAction={vi.fn()}
        onSaveAssessment={vi.fn()}
        onAddEvidence={vi.fn()}
        onSaveConfigurationProfile={vi.fn()}
        onSaveConfigurationAnswers={vi.fn()}
        onSaveCapabilityScopes={vi.fn()}
        onSaveTechniqueOverrides={vi.fn()}
        onUpdateTags={vi.fn()}
        onUpdateToolTypes={vi.fn()}
      />,
    );

    expect(screen.getByText("Data Sources")).toBeInTheDocument();
    expect(screen.getByText("Active Directory Logs")).toBeInTheDocument();

    rerender(
      <ToolDetailPage
        toolId={3}
        tools={[
          {
            id: 3,
            name: "XSOAR",
            category: "SOAR",
            tool_types: ["response"],
            tags: ["Incident Response"],
            capabilities: [],
            data_sources: [],
            response_actions: [
              {
                id: 1,
                tool_id: 3,
                response_action_id: 1,
                implementation_level: "full",
                notes: "",
                response_action: {
                  id: 1,
                  code: "RA-002",
                  name: "Disable Account",
                  description: "Disable account",
                },
              },
            ],
          },
        ]}
        capabilities={[]}
        dataSources={[]}
        coverageScopes={[]}
        responseActions={[
          {
            id: 1,
            code: "RA-002",
            name: "Disable Account",
            description: "Disable account",
          },
        ]}
        onDeleteTool={vi.fn()}
        onSetCapability={vi.fn()}
        onSetToolDataSource={vi.fn()}
        onSetToolResponseAction={vi.fn()}
        onSaveAssessment={vi.fn()}
        onAddEvidence={vi.fn()}
        onSaveConfigurationProfile={vi.fn()}
        onSaveConfigurationAnswers={vi.fn()}
        onSaveCapabilityScopes={vi.fn()}
        onSaveTechniqueOverrides={vi.fn()}
        onUpdateTags={vi.fn()}
        onUpdateToolTypes={vi.fn()}
      />,
    );

    expect(screen.getByText("Response Actions")).toBeInTheDocument();
    expect(screen.getAllByText("Disable Account").length).toBeGreaterThan(0);
  });
});

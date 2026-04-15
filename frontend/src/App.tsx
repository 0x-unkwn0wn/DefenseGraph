import { useEffect, useState } from "react";

import {
  addToolCapabilityEvidence,
  applyToolTemplates,
  createTool,
  deleteTool,
  listCoverageScopes,
  listDataSources,
  listCapabilities,
  listCoverage,
  listResponseActions,
  listTools,
  saveToolCapabilityAssessment,
  saveToolCapabilityConfigurationAnswers,
  saveToolCapabilityConfigurationProfile,
  saveToolCapabilityScopes,
  saveToolCapabilityTechniqueOverrides,
  setToolCapability,
  setToolDataSource,
  setToolResponseAction,
  updateToolTags,
  updateToolTypes,
} from "./api";
import { AppShell } from "./components/AppShell";
import { CapabilityDetailPage } from "./pages/CapabilityDetailPage";
import { CoveragePage } from "./pages/CoveragePage";
import { DocsPage } from "./pages/DocsPage";
import { ToolDetailPage } from "./pages/ToolDetailPage";
import { ToolsPage } from "./pages/ToolsPage";
import type {
  AssessmentAnswerValue,
  Capability,
  ConfigurationAnswerValue,
  ControlEffect,
  CoverageScope,
  DataSource,
  ImplementationLevel,
  ResponseAction,
  ScopeStatus,
  TechniqueCoverage,
  Tool,
  ToolCapabilityTemplate,
  ToolCategory,
  ToolTag,
  ToolType,
} from "./types";

type Route =
  | { page: "tools" }
  | { page: "tool-detail"; toolId: number }
  | { page: "capability-detail"; capabilityId: number }
  | { page: "coverage"; view: "coverage" | "gaps" }
  | { page: "docs" };

function parseRoute(hash: string): Route {
  const toolMatch = hash.match(/^#\/tools\/(\d+)$/);
  if (toolMatch) {
    return { page: "tool-detail", toolId: Number(toolMatch[1]) };
  }

  const capabilityMatch = hash.match(/^#\/capabilities\/(\d+)$/);
  if (capabilityMatch) {
    return { page: "capability-detail", capabilityId: Number(capabilityMatch[1]) };
  }

  if (hash.startsWith("#/coverage")) {
    const [, queryString = ""] = hash.split("?");
    const params = new URLSearchParams(queryString);
    return {
      page: "coverage",
      view: params.get("view") === "gaps" ? "gaps" : "coverage",
    };
  }

  if (hash === "#/gaps") {
    return { page: "coverage", view: "gaps" };
  }

  if (hash === "#/docs") {
    return { page: "docs" };
  }

  return { page: "tools" };
}

function buildCoverageHash(view: "coverage" | "gaps") {
  return view === "gaps" ? "#/coverage?view=gaps" : "#/coverage";
}

export default function App() {
  const [route, setRoute] = useState<Route>(parseRoute(window.location.hash));
  const [tools, setTools] = useState<Tool[]>([]);
  const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [coverageScopes, setCoverageScopes] = useState<CoverageScope[]>([]);
  const [responseActions, setResponseActions] = useState<ResponseAction[]>([]);
  const [coverage, setCoverage] = useState<TechniqueCoverage[]>([]);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(() => {
    const stored = window.localStorage.getItem("defensegraph.sidebarCollapsed");
    return stored === "true";
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!window.location.hash) {
      window.location.hash = "#/tools";
    }

    const onHashChange = () => setRoute(parseRoute(window.location.hash));
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    void refreshAll();
  }, []);

  useEffect(() => {
    window.localStorage.setItem("defensegraph.sidebarCollapsed", String(isSidebarCollapsed));
  }, [isSidebarCollapsed]);

  async function refreshAll() {
    setIsLoading(true);
    setError(null);
    try {
      const [toolRows, capabilityRows, dataSourceRows, coverageScopeRows, responseActionRows, coverageRows] = await Promise.all([
        listTools(),
        listCapabilities(),
        listDataSources(),
        listCoverageScopes(),
        listResponseActions(),
        listCoverage(),
      ]);
      setTools(toolRows);
      setCapabilities(capabilityRows);
      setDataSources(dataSourceRows);
      setCoverageScopes(coverageScopeRows);
      setResponseActions(responseActionRows);
      setCoverage(coverageRows);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }

  async function refreshToolsAndCoverage() {
    const [toolRows, coverageRows] = await Promise.all([listTools(), listCoverage()]);
    setTools(toolRows);
    setCoverage(coverageRows);
  }

  async function handleCreateTool(
    name: string,
    vendorName: string,
    category: ToolCategory,
    toolTypes: ToolType[],
    toolTypeLabels: string[],
    tags: ToolTag[],
    selectedTemplates: Array<{
      template: ToolCapabilityTemplate;
      controlEffect: Exclude<ControlEffect, "none">;
    }>,
  ) {
    setError(null);
    try {
      const tool = await createTool(name, vendorName, category, toolTypes, toolTypeLabels, tags);
      if (selectedTemplates.length > 0) {
        await applyToolTemplates(
          tool.id,
          selectedTemplates.map((item) => ({
            template_id: item.template.id,
            control_effect: item.controlEffect,
            implementation_level: item.template.default_implementation_level,
          })),
        );
      }
      await refreshToolsAndCoverage();
      window.location.hash = `#/tools/${tool.id}`;
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to create tool");
      throw actionError;
    }
  }

  async function handleUpdateToolTags(toolId: number, tags: ToolTag[]) {
    setError(null);
    try {
      const updatedTool = await updateToolTags(toolId, tags);
      setTools((currentTools) =>
        currentTools
          .map((tool) => (tool.id === updatedTool.id ? updatedTool : tool))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update tags");
      throw actionError;
    }
  }

  async function handleUpdateToolTypes(toolId: number, toolTypes: ToolType[]) {
    setError(null);
    try {
      const updatedTool = await updateToolTypes(toolId, toolTypes);
      setTools((currentTools) =>
        currentTools
          .map((tool) => (tool.id === updatedTool.id ? updatedTool : tool))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
      setCoverage(await listCoverage());
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update tool types");
      throw actionError;
    }
  }

  async function handleDeleteTool(tool: Tool) {
    const confirmed = window.confirm(`Delete "${tool.name}"?`);
    if (!confirmed) {
      return;
    }

    setError(null);
    try {
      await deleteTool(tool.id);
      await refreshToolsAndCoverage();

      if (route.page === "tool-detail" && route.toolId === tool.id) {
        window.location.hash = "#/tools";
      }
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to delete tool");
    }
  }

  async function handleSetCapability(
    toolId: number,
    capabilityId: number,
    controlEffect: ControlEffect,
    implementationLevel: ImplementationLevel,
  ) {
    setError(null);
    try {
      const updatedTool = await setToolCapability(
        toolId,
        capabilityId,
        controlEffect,
        implementationLevel,
      );
      setTools((currentTools) =>
        currentTools
          .map((tool) => (tool.id === updatedTool.id ? updatedTool : tool))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
      setCoverage(await listCoverage());
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update capability");
      throw actionError;
    }
  }

  async function handleSaveAssessment(
    toolId: number,
    capabilityId: number,
    answers: Array<{ question_id: number; answer: AssessmentAnswerValue }>,
  ) {
    setError(null);
    try {
      await saveToolCapabilityAssessment(toolId, capabilityId, answers);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to save assessment");
      throw actionError;
    }
  }

  async function handleAddEvidence(
    toolId: number,
    capabilityId: number,
    payload: {
      title: string;
      evidence_type: string;
      note: string;
      file_name: string | null;
      recorded_at: string;
    },
  ) {
    setError(null);
    try {
      await addToolCapabilityEvidence(toolId, capabilityId, payload);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to add evidence");
      throw actionError;
    }
  }

  async function handleSaveConfigurationProfile(toolId: number, capabilityId: number, notes: string) {
    setError(null);
    try {
      await saveToolCapabilityConfigurationProfile(toolId, capabilityId, notes);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to save configuration profile");
      throw actionError;
    }
  }

  async function handleSaveConfigurationAnswers(
    toolId: number,
    capabilityId: number,
    answers: Array<{ question_id: number; answer: ConfigurationAnswerValue }>,
  ) {
    setError(null);
    try {
      await saveToolCapabilityConfigurationAnswers(toolId, capabilityId, answers);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to save configuration verification");
      throw actionError;
    }
  }

  async function handleSaveCapabilityScopes(
    toolId: number,
    capabilityId: number,
    scopes: Array<{ coverage_scope_id: number; status: ScopeStatus; notes: string }>,
  ) {
    setError(null);
    try {
      await saveToolCapabilityScopes(toolId, capabilityId, scopes);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to save coverage scope");
      throw actionError;
    }
  }

  async function handleSaveTechniqueOverrides(
    toolId: number,
    capabilityId: number,
    overrides: Array<{
      technique_id: number;
      control_effect_override: ControlEffect;
      implementation_level_override: Exclude<ImplementationLevel, "none"> | null;
      notes: string;
    }>,
  ) {
    setError(null);
    try {
      await saveToolCapabilityTechniqueOverrides(toolId, capabilityId, overrides);
      await refreshToolsAndCoverage();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to save ATT&CK behavior");
      throw actionError;
    }
  }

  async function handleSetToolDataSource(
    toolId: number,
    dataSourceId: number,
    ingestionStatus: "none" | "partial" | "full",
    notes: string,
  ) {
    setError(null);
    try {
      const updatedTool = await setToolDataSource(toolId, dataSourceId, ingestionStatus, notes);
      setTools((currentTools) =>
        currentTools
          .map((tool) => (tool.id === updatedTool.id ? updatedTool : tool))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
      setCoverage(await listCoverage());
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update data source");
      throw actionError;
    }
  }

  async function handleSetToolResponseAction(
    toolId: number,
    responseActionId: number,
    implementationLevel: "none" | "partial" | "full",
    notes: string,
  ) {
    setError(null);
    try {
      const updatedTool = await setToolResponseAction(toolId, responseActionId, implementationLevel, notes);
      setTools((currentTools) =>
        currentTools
          .map((tool) => (tool.id === updatedTool.id ? updatedTool : tool))
          .sort((left, right) => left.name.localeCompare(right.name)),
      );
      setCoverage(await listCoverage());
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to update response action");
      throw actionError;
    }
  }

  const currentNav =
    route.page === "tool-detail" || route.page === "capability-detail" ? "tools" : route.page;

  const pageMeta = (() => {
    switch (route.page) {
      case "tools":
        return {
          title: "Tools",
          description: "Tool inventory, onboarding presets, and capability state.",
        };
      case "tool-detail": {
        const tool = tools.find((entry) => entry.id === route.toolId);
        return {
          title: tool?.name ?? "Tool detail",
          description: "Capability assignment, confidence, assessment, and evidence.",
        };
      }
      case "capability-detail": {
        const capability = capabilities.find((entry) => entry.id === route.capabilityId);
        return {
          title: capability?.name ?? "Capability detail",
          description: "Capability-centric detail across implementing tools and ATT&CK coverage.",
        };
      }
      case "coverage":
        return {
          title: "Coverage",
          description:
            route.view === "gaps"
              ? "Unified ATT&CK workspace in gaps mode, focused on weaknesses, confidence issues, and dependencies."
              : "Unified ATT&CK workspace for coverage analysis, confidence review, and gap inspection.",
        };
      case "docs":
        return {
          title: "Status & Docs",
          description: "Current workspace status plus in-app documentation for the DefenseGraph model.",
        };
    }
  })();

  return (
    <AppShell
      current={currentNav}
      description={pageMeta.description}
      isSidebarCollapsed={isSidebarCollapsed}
      onToggleSidebar={() => setIsSidebarCollapsed((current) => !current)}
      title={pageMeta.title}
    >
      {error ? <div className="error-banner">{error}</div> : null}
      {isLoading ? <div className="card">Loading data...</div> : null}

      {!isLoading && route.page === "tools" ? (
        <ToolsPage tools={tools} onCreateTool={handleCreateTool} onDeleteTool={handleDeleteTool} />
      ) : null}

      {!isLoading && route.page === "tool-detail" ? (
        <ToolDetailPage
          toolId={route.toolId}
          tools={tools}
          capabilities={capabilities}
          dataSources={dataSources}
          coverageScopes={coverageScopes}
          responseActions={responseActions}
          onDeleteTool={handleDeleteTool}
          onSetCapability={handleSetCapability}
          onSetToolDataSource={handleSetToolDataSource}
          onSetToolResponseAction={handleSetToolResponseAction}
          onSaveAssessment={handleSaveAssessment}
          onAddEvidence={handleAddEvidence}
          onSaveConfigurationProfile={handleSaveConfigurationProfile}
          onSaveConfigurationAnswers={handleSaveConfigurationAnswers}
          onSaveCapabilityScopes={handleSaveCapabilityScopes}
          onSaveTechniqueOverrides={handleSaveTechniqueOverrides}
          onUpdateTags={handleUpdateToolTags}
          onUpdateToolTypes={handleUpdateToolTypes}
        />
      ) : null}

      {!isLoading && route.page === "capability-detail" ? (
        <CapabilityDetailPage capabilityId={route.capabilityId} />
      ) : null}

      {!isLoading && route.page === "coverage" ? (
        <CoveragePage
          coverage={coverage}
          tools={tools}
          capabilities={capabilities}
          viewMode={route.view}
          onChangeViewMode={(view) => {
            const nextHash = buildCoverageHash(view);
            if (window.location.hash !== nextHash) {
              window.location.hash = nextHash;
            }
          }}
        />
      ) : null}

      {!isLoading && route.page === "docs" ? (
        <DocsPage />
      ) : null}
    </AppShell>
  );
}

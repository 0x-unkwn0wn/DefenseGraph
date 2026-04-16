import { useEffect, useMemo, useState } from "react";

import { getDocsMappings, listDocsCapabilities, listDocsToolTypes, listTools } from "../api";
import { DocsSection } from "../components/DocsSection";
import { DocsSidebarNav } from "../components/DocsSidebarNav";
import type { DocsCapability, DocsMapping, DocsToolType, Tool } from "../types";

type DocsView = "status" | "documentation";

const statusSections = [
  { id: "status-overview", label: "Overview" },
  { id: "tool-types", label: "Tool Types" },
  { id: "capabilities", label: "Capabilities" },
  { id: "mapping", label: "Mappings" },
] as const;

const documentationSections = [
  { id: "model-overview", label: "Model" },
  { id: "how-to-use", label: "How to Use" },
] as const;

export function DocsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolTypes, setToolTypes] = useState<DocsToolType[]>([]);
  const [capabilities, setCapabilities] = useState<DocsCapability[]>([]);
  const [mappings, setMappings] = useState<DocsMapping | null>(null);
  const [activeView, setActiveView] = useState<DocsView>("status");
  const [activeSection, setActiveSection] = useState<string>("status-overview");
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    void Promise.all([listTools(), listDocsToolTypes(), listDocsCapabilities(), getDocsMappings()])
      .then(([toolRows, toolTypeRows, capabilityRows, mappingRows]) => {
        setTools(toolRows);
        setToolTypes(toolTypeRows);
        setCapabilities(capabilityRows);
        setMappings(mappingRows);
      })
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : "Failed to load documentation");
      })
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(
    () => ({
      tools: tools.length,
      toolTypes: toolTypes.length,
      capabilities: capabilities.length,
      mappings: mappings?.tool_type_mappings.reduce((count, item) => count + item.capabilities.length, 0) ?? 0,
    }),
    [capabilities.length, mappings, toolTypes.length, tools.length],
  );

  const currentSections = activeView === "status" ? [...statusSections] : [...documentationSections];

  useEffect(() => {
    const firstSection = currentSections[0]?.id ?? "";
    setActiveSection(firstSection);
  }, [activeView]);

  function toggleSection(sectionId: string) {
    setCollapsedSections((current) => ({ ...current, [sectionId]: !current[sectionId] }));
  }

  function jumpToSection(sectionId: string) {
    setActiveSection(sectionId);
    const target = document.getElementById(sectionId);
    if (target && typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  if (loading) {
    return <div className="card">Loading documentation…</div>;
  }

  if (error) {
    return <div className="error-banner">{error}</div>;
  }

  return (
    <div className="docs-page-stack">
      <div className="filter-group view-mode-group docs-view-group" role="tablist" aria-label="Reference view">
        {(["status", "documentation"] as const).map((view) => (
          <button
            key={view}
            type="button"
            role="tab"
            aria-selected={activeView === view}
            className={activeView === view ? "filter-chip active" : "filter-chip"}
            onClick={() => setActiveView(view)}
          >
            {view === "status" ? "Status" : "Documentation"}
          </button>
        ))}
      </div>

      <div className="docs-layout">
        <DocsSidebarNav
          activeSection={activeSection}
          sections={currentSections}
          title={activeView === "status" ? "Status" : "Documentation"}
          onSelect={jumpToSection}
        />

        <div className="docs-content">
          {activeView === "status" ? (
            <>
              <DocsSection
                id="status-overview"
                subtitle="Status"
                title="Current workspace state"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("status-overview")}>
                    {collapsedSections["status-overview"] ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections["status-overview"] ? (
                  <div className="stack">
                    <div className="counter-grid compact-counter-grid">
                      <div className="counter-card compact">
                        <span>Tools</span>
                        <strong>{stats.tools}</strong>
                      </div>
                      <div className="counter-card compact">
                        <span>Tool types</span>
                        <strong>{stats.toolTypes}</strong>
                      </div>
                      <div className="counter-card compact">
                        <span>Capabilities</span>
                        <strong>{stats.capabilities}</strong>
                      </div>
                      <div className="counter-card compact">
                        <span>Mappings</span>
                        <strong>{stats.mappings}</strong>
                      </div>
                    </div>
                    <p className="section-copy">
                      This tab reflects the current workspace state generated from live tool, capability, and mapping
                      data.
                    </p>
                    <div className="docs-grid two-column">
                      <div className="docs-panel-block">
                        <p className="eyebrow">Current inventory</p>
                        <ul className="docs-list">
                          <li>{stats.tools} tools currently loaded in the workspace.</li>
                          <li>{stats.toolTypes} tool types inferred from current tool definitions.</li>
                          <li>{stats.capabilities} capabilities available for assignment and review.</li>
                          <li>{stats.mappings} active tool-type-to-capability links observed in current data.</li>
                        </ul>
                      </div>
                      <div className="docs-panel-block">
                        <p className="eyebrow">What this tab is for</p>
                        <ul className="docs-list">
                          <li>Check what is currently modeled and populated.</li>
                          <li>Review which tool roles and capabilities exist right now.</li>
                          <li>Inspect current mappings before interpreting coverage and gaps.</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : null}
              </DocsSection>

              <DocsSection
                id="tool-types"
                subtitle="Status"
                title="Operational roles currently present"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("tool-types")}>
                    {collapsedSections["tool-types"] ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections["tool-types"] ? (
                  toolTypes.length > 0 ? (
                    <div className="docs-grid">
                      {toolTypes.map((toolType) => (
                        <article key={toolType.tool_type} className="docs-card">
                          <div className="docs-card-head">
                            <strong>{toolType.tool_type}</strong>
                            <span className="count-chip">{toolType.tool_count} tools</span>
                          </div>
                          <p className="muted">{toolType.description}</p>
                          <div className="docs-chip-row">
                            <span className="eyebrow">Inputs</span>
                            {toolType.inputs.length > 0 ? toolType.inputs.map((item) => <span key={item} className="count-chip">{item}</span>) : <span className="count-chip">No inputs documented</span>}
                          </div>
                          <div className="docs-chip-row">
                            <span className="eyebrow">Outputs</span>
                            {toolType.outputs.length > 0 ? toolType.outputs.map((item) => <span key={item} className="count-chip">{item}</span>) : <span className="count-chip">No outputs documented</span>}
                          </div>
                          <div className="docs-chip-row">
                            <span className="eyebrow">Examples</span>
                            {toolType.example_usage.length > 0 ? toolType.example_usage.map((item) => <span key={item} className="count-chip">{item}</span>) : <span className="count-chip">No examples yet</span>}
                          </div>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="muted">No tool types are populated yet. Add tools to generate this section.</p>
                  )
                ) : null}
              </DocsSection>

              <DocsSection
                id="capabilities"
                subtitle="Status"
                title="Current defensive capability catalog"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("capabilities")}>
                    {collapsedSections.capabilities ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections.capabilities ? (
                  <div className="docs-grid">
                    {capabilities.map((item) => (
                      <details key={item.capability.id} className="docs-card docs-accordion">
                        <summary>
                          <strong>{item.capability.name}</strong>
                          <span className="count-chip">{item.implementing_tool_count} tools</span>
                        </summary>
                        {item.capability.family ? (
                          <div className="docs-chip-row">
                            <span className="eyebrow">Family</span>
                            <span className="count-chip">{item.capability.family}</span>
                          </div>
                        ) : null}
                        <p className="muted">{item.capability.description}</p>
                        <p>{item.purpose}</p>
                        <div className="docs-chip-row">
                          <span className="eyebrow">Tool types</span>
                          {item.tool_types.length > 0 ? item.tool_types.map((toolType) => <span key={toolType} className="count-chip">{toolType}</span>) : <span className="count-chip">Not assigned yet</span>}
                        </div>
                        <div className="docs-chip-row">
                          <span className="eyebrow">Typical use cases</span>
                          {item.typical_use_cases.length > 0 ? item.typical_use_cases.map((useCase) => <span key={useCase} className="count-chip">{useCase}</span>) : <span className="count-chip">No mapped techniques yet</span>}
                        </div>
                      </details>
                    ))}
                  </div>
                ) : null}
              </DocsSection>

              <DocsSection
                id="mapping"
                subtitle="Status"
                title="Current mapping state"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("mapping")}>
                    {collapsedSections.mapping ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections.mapping && mappings ? (
                  <div className="docs-grid two-column">
                    <div className="docs-panel-block">
                      <p className="eyebrow">Tool Type to Capabilities</p>
                      <div className="docs-table-list">
                        {mappings.tool_type_mappings.map((entry) => (
                          <div key={entry.tool_type} className="docs-table-row">
                            <strong>{entry.tool_type}</strong>
                            <div className="docs-chip-row">
                              {entry.capabilities.length > 0 ? entry.capabilities.map((capability) => <span key={capability.id} className="count-chip">{capability.name}</span>) : <span className="count-chip">No linked capabilities</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="docs-panel-block">
                      <p className="eyebrow">Capability to Tool Types</p>
                      <div className="docs-table-list">
                        {mappings.capability_mappings.map((entry) => (
                          <div key={entry.capability.id} className="docs-table-row">
                            <strong>{entry.capability.name}</strong>
                            <div className="docs-chip-row">
                              {entry.tool_types.length > 0 ? entry.tool_types.map((toolType) => <span key={toolType} className="count-chip">{toolType}</span>) : <span className="count-chip">No linked tool types</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : null}
              </DocsSection>
            </>
          ) : (
            <>
              <DocsSection
                id="model-overview"
                subtitle="Documentation"
                title="How DefenseGraph models coverage"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("model-overview")}>
                    {collapsedSections["model-overview"] ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections["model-overview"] ? (
                  <div className="stack">
                    <p className="section-copy">
                      DefenseGraph models tools as nodes, attaches capabilities to them, and then translates those
                      relationships into ATT&CK coverage and gaps.
                    </p>
                    <div className="docs-grid two-column">
                      <div className="docs-panel-block">
                        <p className="eyebrow">Core concepts</p>
                        <ul className="docs-list">
                          <li>Nodes: tools and capabilities linked through assignments.</li>
                          <li>Tools: inventory items with categories, types, tags, and implementation state.</li>
                          <li>Capabilities: defensive outcomes mapped to ATT&CK techniques.</li>
                          <li>Relationships: tool types, capabilities, scopes, data sources, and response actions.</li>
                        </ul>
                      </div>
                      <div className="docs-panel-block">
                        <p className="eyebrow">Coverage semantics</p>
                        <ul className="docs-list">
                          <li>Mappings decide whether a capability is relevant to a technique.</li>
                          <li>Actual effect comes from the assigned tool capability and any per-technique override.</li>
                          <li>Coverage and gaps are computed from current assignments, confidence, scope, and dependencies.</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                ) : null}
              </DocsSection>

              <DocsSection
                id="how-to-use"
                subtitle="Documentation"
                title="Suggested workflow"
                actions={
                  <button type="button" className="sidebar-toggle" onClick={() => toggleSection("how-to-use")}>
                    {collapsedSections["how-to-use"] ? "Expand" : "Collapse"}
                  </button>
                }
              >
                {!collapsedSections["how-to-use"] ? (
                  <ol className="docs-steps">
                    <li>Create tools and assign their category, tool types, and any relevant tags.</li>
                    <li>Map capabilities to each tool, then verify configuration, confidence, and scope where required.</li>
                    <li>Use the Status tab to confirm what is actually populated in the workspace.</li>
                    <li>Review the current catalog of {stats.capabilities} capabilities before interpreting ATT&CK results.</li>
                    <li>Interpret ATT&CK coverage and gaps after assignments and overrides are updated.</li>
                  </ol>
                ) : null}
              </DocsSection>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

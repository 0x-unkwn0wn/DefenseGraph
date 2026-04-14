import { useEffect, useMemo, useState } from "react";

import { getDocsMappings, listDocsCapabilities, listDocsToolTypes, listTools } from "../api";
import { DocsSection } from "../components/DocsSection";
import { DocsSidebarNav } from "../components/DocsSidebarNav";
import type { DocsCapability, DocsMapping, DocsToolType, Tool } from "../types";

const sections = [
  { id: "overview", label: "Overview" },
  { id: "tool-types", label: "Tool Types" },
  { id: "capabilities", label: "Capabilities" },
  { id: "mapping", label: "Mapping" },
  { id: "how-to-use", label: "How to Use" },
] as const;

export function DocsPage() {
  const [tools, setTools] = useState<Tool[]>([]);
  const [toolTypes, setToolTypes] = useState<DocsToolType[]>([]);
  const [capabilities, setCapabilities] = useState<DocsCapability[]>([]);
  const [mappings, setMappings] = useState<DocsMapping | null>(null);
  const [activeSection, setActiveSection] = useState<string>("overview");
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
    <div className="docs-layout">
      <DocsSidebarNav activeSection={activeSection} sections={[...sections]} onSelect={jumpToSection} />

      <div className="docs-content">
        <DocsSection
          id="overview"
          subtitle="Overview"
          title="How DefenseGraph models coverage"
          actions={
            <button type="button" className="sidebar-toggle" onClick={() => toggleSection("overview")}>
              {collapsedSections.overview ? "Expand" : "Collapse"}
            </button>
          }
        >
          {!collapsedSections.overview ? (
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
                DefenseGraph models tools as nodes, attaches capabilities to them, and then translates those
                relationships into ATT&CK coverage and gaps. This view is generated from the current database state.
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
                  <p className="eyebrow">Current state</p>
                  <ul className="docs-list">
                    <li>{stats.tools} tools currently documented in the workspace.</li>
                    <li>{stats.capabilities} capabilities available for assignment and analysis.</li>
                    <li>{stats.toolTypes} tool types inferred from current tool definitions.</li>
                    <li>{stats.mappings} active tool-type-to-capability links observed in current data.</li>
                  </ul>
                </div>
              </div>
            </div>
          ) : null}
        </DocsSection>

        <DocsSection
          id="tool-types"
          subtitle="Tool Types"
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
          subtitle="Capabilities"
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
          subtitle="Mapping"
          title="Tool types and capabilities"
          actions={
            <button type="button" className="sidebar-toggle" onClick={() => toggleSection("mapping")}>
              {collapsedSections.mapping ? "Expand" : "Collapse"}
            </button>
          }
        >
          {!collapsedSections.mapping && mappings ? (
            <div className="docs-grid two-column">
              <div className="docs-panel-block">
                <p className="eyebrow">Tool Type → Capabilities</p>
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
                <p className="eyebrow">Capability → Tool Types</p>
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

        <DocsSection
          id="how-to-use"
          subtitle="How to Use"
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
              <li>Review the current catalog of {stats.capabilities} capabilities to understand what each tool can claim.</li>
              <li>Use the mapping view to confirm how current tool types translate into capability coverage.</li>
              <li>Interpret ATT&CK coverage and gaps using the coverage and gaps screens after assignments are updated.</li>
            </ol>
          ) : null}
        </DocsSection>
      </div>
    </div>
  );
}

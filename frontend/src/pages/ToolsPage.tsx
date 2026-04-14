import { FormEvent, useEffect, useMemo, useState } from "react";

import { listTags, listToolTemplates } from "../api";
import { Card } from "../components/Card";
import type {
  ControlEffect,
  Tool,
  ToolCapabilityTemplate,
  ToolCategory,
  ToolTag,
  ToolTagDefinition,
  ToolType,
} from "../types";

interface ToolsPageProps {
  tools: Tool[];
  onCreateTool: (
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
  ) => Promise<void>;
  onDeleteTool: (tool: Tool) => Promise<void>;
}

const toolCategories: ToolCategory[] = [
  "EDR",
  "PAM",
  "DLP",
  "SASE",
  "DNS",
  "Email",
  "BAS",
  "Identity",
  "Security Analytics",
  "SOAR",
  "Other",
];

const ALL_TOOL_TYPES: ToolType[] = ["control", "analytics", "response", "assurance"];
const PRODUCT_TYPE_OPTIONS = [
  "DLP",
  "Information Protection",
  "Encryption",
  "WAF / API Security",
  "UEM / MDM",
  "Policy Enforcement / Hardening",
  "AD Security Assessment",
  "Credential Exposure Monitoring",
  "Password Policy Enforcement",
  "Password Audit / Assessment",
  "IAM Administration / Automation",
  "PAM",
  "MFA",
  "Identity Threat Protection",
  "Vulnerability Assessment",
  "AD Audit / Monitoring",
  "SIEM",
  "NAC / Visibility Platform",
] as const;

const TOOL_TYPE_LABEL: Record<ToolType, string> = {
  control: "control",
  analytics: "analytics",
  response: "response",
  assurance: "Validated",
};

const defaultToolTypesByCategory: Record<ToolCategory, ToolType[]> = {
  EDR: ["control"],
  PAM: ["control"],
  DLP: ["control"],
  SASE: ["control"],
  DNS: ["control"],
  Email: ["control"],
  BAS: ["assurance"],
  Identity: ["control"],
  "Security Analytics": ["analytics"],
  SOAR: ["response"],
  Other: ["control"],
};

export function ToolsPage({ tools, onCreateTool, onDeleteTool }: ToolsPageProps) {
  const [name, setName] = useState("");
  const [vendorName, setVendorName] = useState("");
  const [category, setCategory] = useState<ToolCategory>("Other");
  const [toolTypes, setToolTypes] = useState<ToolType[]>(["control"]);
  const [toolTypeLabels, setToolTypeLabels] = useState<string[]>([]);
  const [tagCatalog, setTagCatalog] = useState<ToolTagDefinition[]>([]);
  const [selectedTags, setSelectedTags] = useState<ToolTag[]>([]);
  const [customTag, setCustomTag] = useState("");
  const [templates, setTemplates] = useState<ToolCapabilityTemplate[] | null>(null);
  const [selectedTemplates, setSelectedTemplates] = useState<Record<number, boolean>>({});
  const [templateEffects, setTemplateEffects] = useState<Record<number, Exclude<ControlEffect, "none">>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [step, setStep] = useState<"form" | "tags" | "templates">("form");

  useEffect(() => {
    void listTags().then(setTagCatalog).catch(() => setTagCatalog([]));
  }, []);

  const suggestedTags = useMemo(
    () => tagCatalog.filter((tag) => tag.default_categories.includes(category)),
    [category, tagCatalog],
  );
  const coreTemplates = useMemo(
    () => (templates ?? []).filter((template) => template.suggestion_group === "core"),
    [templates],
  );
  const recommendedTemplates = useMemo(
    () => (templates ?? []).filter((template) => template.suggestion_group === "recommended"),
    [templates],
  );
  const optionalTemplates = useMemo(
    () => (templates ?? []).filter((template) => template.suggestion_group === "optional"),
    [templates],
  );

  function resetWizard() {
    setName("");
    setVendorName("");
    setCategory("Other");
    setToolTypes(["control"]);
    setToolTypeLabels([]);
    setSelectedTags([]);
    setCustomTag("");
    setTemplates(null);
    setSelectedTemplates({});
    setTemplateEffects({});
    setTemplateError(null);
    setStep("form");
  }

  function seedSuggestedTags(nextCategory: ToolCategory) {
    const suggested = tagCatalog
      .filter((tag) => tag.default_categories.includes(nextCategory))
      .map((tag) => tag.name);
    setSelectedTags(suggested);
  }

  async function handleStart(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }
    seedSuggestedTags(category);
    setStep("tags");
  }

  async function handleLoadTemplates() {
    setTemplateError(null);
    setIsLoadingTemplates(true);
    try {
      const nextTemplates = await listToolTemplates(category, selectedTags);
      setTemplates(nextTemplates);
      setSelectedTemplates(
        Object.fromEntries(
          nextTemplates.map((template) => [
            template.id,
            template.suggestion_group === "core" || template.suggestion_group === "recommended",
          ]),
        ),
      );
      setTemplateEffects(
        Object.fromEntries(nextTemplates.map((template) => [template.id, template.default_effect])),
      );
      setStep("templates");
    } catch (loadError) {
      setTemplateError(loadError instanceof Error ? loadError.message : "Failed to load templates");
    } finally {
      setIsLoadingTemplates(false);
    }
  }

  async function handleCreateFromSelection() {
    setIsSubmitting(true);
    try {
      const selected = (templates ?? [])
        .filter((template) => selectedTemplates[template.id])
        .map((template) => ({
          template,
          controlEffect: templateEffects[template.id] ?? template.default_effect,
        }));

      await onCreateTool(name.trim(), vendorName.trim(), category, toolTypes, toolTypeLabels, selectedTags, selected);
      resetWizard();
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleSkipSuggestions() {
    setIsSubmitting(true);
    try {
      await onCreateTool(name.trim(), vendorName.trim(), category, toolTypes, toolTypeLabels, selectedTags, []);
      resetWizard();
    } finally {
      setIsSubmitting(false);
    }
  }

  function addCustomTag() {
    const nextTag = customTag.trim();
    if (!nextTag || selectedTags.includes(nextTag)) {
      return;
    }
    setSelectedTags((current) => [...current, nextTag]);
    setCustomTag("");
  }

  function selectAllCommon() {
    setSelectedTemplates((current) => ({
      ...current,
      ...Object.fromEntries(coreTemplates.map((template) => [template.id, true])),
    }));
  }

  function startWithMinimal() {
    setSelectedTemplates(
      Object.fromEntries((templates ?? []).map((template) => [template.id, template.suggestion_group === "core"])),
    );
  }

  return (
    <div className="page-grid tools-layout">
      <Card title="Create tool" subtitle="Inventory" className="tool-create-card">
        {step === "form" ? (
          <>
            <p className="section-copy">
              Start with a primary category and tool type. Tags and capability suggestions come next.
            </p>
            <form className="stack" onSubmit={handleStart}>
              <input
                className="text-input"
                placeholder="New Tool"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
              <input
                className="text-input"
                placeholder="Vendor (optional)"
                value={vendorName}
                onChange={(event) => setVendorName(event.target.value)}
              />
              <label className="filter-field">
                <span>Primary category</span>
                <select
                  className="text-input"
                  value={category}
                  onChange={(event) => {
                    const nextCategory = event.target.value as ToolCategory;
                    setCategory(nextCategory);
                    setToolTypes(defaultToolTypesByCategory[nextCategory]);
                  }}
                >
                  {toolCategories.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </label>
              <div className="filter-field">
                <span>Tool types (select all that apply)</span>
                <div className="tag-chip-row">
                  {ALL_TOOL_TYPES.map((t) => (
                    <label key={t} className="tag-chip" style={{ cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={toolTypes.includes(t)}
                        onChange={(event) => {
                          setToolTypes((prev) =>
                            event.target.checked
                              ? [...prev, t]
                              : prev.filter((x) => x !== t),
                          );
                        }}
                        style={{ marginRight: "4px" }}
                      />
                      {TOOL_TYPE_LABEL[t]}
                    </label>
                  ))}
                </div>
              </div>
              <div className="filter-field">
                <span>Product types</span>
                <div className="tag-chip-row">
                  {PRODUCT_TYPE_OPTIONS.map((label) => (
                    <label key={label} className="tag-chip" style={{ cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={toolTypeLabels.includes(label)}
                        onChange={(event) => {
                          setToolTypeLabels((prev) =>
                            event.target.checked
                              ? [...prev, label]
                              : prev.filter((item) => item !== label),
                          );
                        }}
                        style={{ marginRight: "4px" }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
              <button className="primary-button" type="submit">
                Continue
              </button>
            </form>
          </>
        ) : null}

        {step === "tags" ? (
          <div className="stack">
            <p className="section-copy">
              Add tags so hybrid tools can be classified more accurately. Nothing is enforced later.
            </p>

            <div className="template-top-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => seedSuggestedTags(category)}
              >
                Accept suggested tags
              </button>
              <button type="button" className="secondary-button" onClick={() => setSelectedTags([])}>
                Clear tags
              </button>
              <button type="button" className="secondary-button" onClick={() => setStep("form")}>
                Back
              </button>
            </div>

            <div className="tag-selection-grid">
              {tagCatalog.map((tag) => {
                const suggested = tag.default_categories.includes(category);
                return (
                  <label key={tag.name} className={`tag-option ${suggested ? "suggested" : ""}`.trim()}>
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag.name)}
                      onChange={() =>
                        setSelectedTags((current) =>
                          current.includes(tag.name)
                            ? current.filter((entry) => entry !== tag.name)
                            : [...current, tag.name],
                        )
                      }
                    />
                    <span>{tag.name}</span>
                  </label>
                );
              })}
            </div>

            <div className="custom-tag-row">
              <input
                className="text-input"
                placeholder="Add custom tag"
                value={customTag}
                onChange={(event) => setCustomTag(event.target.value)}
              />
              <button type="button" className="secondary-button" onClick={addCustomTag}>
                Add tag
              </button>
            </div>

            <div className="tag-chip-row">
              {selectedTags.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  className="tag-chip"
                  onClick={() => setSelectedTags((current) => current.filter((entry) => entry !== tag))}
                >
                  {tag}
                </button>
              ))}
            </div>

            <button
              type="button"
              className="primary-button"
              disabled={isLoadingTemplates}
              onClick={() => void handleLoadTemplates()}
            >
              {isLoadingTemplates ? "Generating suggestions..." : "Generate capability suggestions"}
            </button>
          </div>
        ) : null}

        {step === "templates" ? (
          <div className="stack">
            <p className="section-copy">
              Suggestions combine the primary category with the selected tags. You can accept all, accept some, or ignore them.
            </p>

            <div className="template-top-actions">
              <button type="button" className="secondary-button" onClick={selectAllCommon}>
                Select all common
              </button>
              <button type="button" className="secondary-button" onClick={startWithMinimal}>
                Start with minimal
              </button>
              <button type="button" className="secondary-button" onClick={() => setStep("tags")}>
                Back to tags
              </button>
            </div>

            {templateError ? <div className="error-banner">{templateError}</div> : null}

            <TemplateGroup
              title="Core for this category"
              templates={coreTemplates}
              selectedTemplates={selectedTemplates}
              templateEffects={templateEffects}
              onToggle={(templateId) =>
                setSelectedTemplates((current) => ({
                  ...current,
                  [templateId]: !current[templateId],
                }))
              }
              onChangeEffect={(templateId, effect) =>
                setTemplateEffects((current) => ({ ...current, [templateId]: effect }))
              }
            />

            <TemplateGroup
              title="Recommended for selected tags"
              templates={recommendedTemplates}
              selectedTemplates={selectedTemplates}
              templateEffects={templateEffects}
              onToggle={(templateId) =>
                setSelectedTemplates((current) => ({
                  ...current,
                  [templateId]: !current[templateId],
                }))
              }
              onChangeEffect={(templateId, effect) =>
                setTemplateEffects((current) => ({ ...current, [templateId]: effect }))
              }
            />

            <TemplateGroup
              title="Additional capabilities"
              templates={optionalTemplates}
              selectedTemplates={selectedTemplates}
              templateEffects={templateEffects}
              onToggle={(templateId) =>
                setSelectedTemplates((current) => ({
                  ...current,
                  [templateId]: !current[templateId],
                }))
              }
              onChangeEffect={(templateId, effect) =>
                setTemplateEffects((current) => ({ ...current, [templateId]: effect }))
              }
            />

            <div className="template-footer-actions">
              <button
                type="button"
                className="primary-button"
                disabled={isSubmitting}
                onClick={() => void handleCreateFromSelection()}
              >
                {isSubmitting ? "Creating..." : "Create with selected templates"}
              </button>
              <button
                type="button"
                className="secondary-button"
                disabled={isSubmitting}
                onClick={() => void handleSkipSuggestions()}
              >
                Skip suggestions
              </button>
            </div>
          </div>
        ) : null}
      </Card>

      <Card
        title="Tool inventory"
        subtitle="Configured tools"
        actions={<span className="count-chip">{tools.length}</span>}
      >
        <p className="section-copy">Select a tool to inspect assignments, tags, confidence, assessments, and evidence.</p>

        <div className="tool-grid">
          {tools.length === 0 ? (
            <div className="empty-state">
              <p>No tools yet. Create one to start assigning capabilities.</p>
            </div>
          ) : (
            tools.map((tool) => (
              <div key={tool.id} className="tool-card">
                <div className="tool-card-indicator" aria-hidden="true" />
                <div className="tool-card-content">
                  <a href={`#/tools/${tool.id}`} className="tool-card-link">
                    <div>
                      <strong className="tool-card-title">{tool.name}</strong>
                      <p className="muted">
                        {tool.vendor ? `${tool.vendor.name} | ` : ""}
                        {tool.category} | {tool.tool_types.map((t) => TOOL_TYPE_LABEL[t]).join(", ")}
                      </p>
                      {(tool.tool_type_labels ?? []).length > 0 ? (
                        <div className="tag-chip-row compact">
                          {(tool.tool_type_labels ?? []).slice(0, 2).map((label) => (
                            <span key={label} className="tag-chip static">
                              {label}
                            </span>
                          ))}
                        </div>
                      ) : null}
                      {tool.tags.length > 0 ? (
                        <div className="tag-chip-row compact">
                          {tool.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="tag-chip static">
                              {tag}
                            </span>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </a>
                  <div className="tool-card-meta">
                    <span className="tool-card-count">{tool.capabilities.length}</span>
                    <a href={`#/tools/${tool.id}`} className="tool-card-open">
                      Open
                    </a>
                    <button
                      type="button"
                      className="danger-button"
                      onClick={() => void onDeleteTool(tool)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  );
}

interface TemplateGroupProps {
  title: string;
  templates: ToolCapabilityTemplate[];
  selectedTemplates: Record<number, boolean>;
  templateEffects: Record<number, Exclude<ControlEffect, "none">>;
  onToggle: (templateId: number) => void;
  onChangeEffect: (templateId: number, effect: Exclude<ControlEffect, "none">) => void;
}

function TemplateGroup({
  title,
  templates,
  selectedTemplates,
  templateEffects,
  onToggle,
  onChangeEffect,
}: TemplateGroupProps) {
  return (
    <div className="template-group">
      <div className="workspace-section-header">
        <div>
          <p className="eyebrow">Templates</p>
          <strong className="workspace-title">{title}</strong>
        </div>
        <span className="count-chip">{templates.length}</span>
      </div>

      {templates.length === 0 ? (
        <div className="empty-state compact">
          <p>No templates in this group.</p>
        </div>
      ) : (
        <div className="template-list">
          {templates.map((template) => (
            <label key={template.id} className="template-item">
              <div className="template-item-main">
                <input
                  type="checkbox"
                  checked={Boolean(selectedTemplates[template.id])}
                  onChange={() => onToggle(template.id)}
                />
                <div>
                  <strong className="capability-title">{template.capability.name}</strong>
                  <p className="muted">{template.description ?? template.capability.description}</p>
                  {template.matched_tags.length > 0 ? (
                    <div className="tag-chip-row compact">
                      {template.matched_tags.map((tag) => (
                        <span key={tag} className="tag-chip static">
                          {tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
              <div className="template-item-meta">
                <select
                  className="level-select"
                  value={templateEffects[template.id] ?? template.default_effect}
                  onChange={(event) =>
                    onChangeEffect(template.id, event.target.value as Exclude<ControlEffect, "none">)
                  }
                >
                  <option value="detect">Detect</option>
                  <option value="block">Block</option>
                  <option value="prevent">Prevent</option>
                </select>
                <span className="count-chip">{template.default_implementation_level}</span>
              </div>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

interface DocsSidebarNavProps {
  activeSection: string;
  sections: Array<{ id: string; label: string }>;
  onSelect: (sectionId: string) => void;
}

export function DocsSidebarNav({ activeSection, sections, onSelect }: DocsSidebarNavProps) {
  return (
    <aside className="docs-sidebar-nav">
      <p className="eyebrow">Documentation</p>
      <div className="docs-sidebar-links">
        {sections.map((section) => (
          <button
            key={section.id}
            type="button"
            className={activeSection === section.id ? "docs-nav-link active" : "docs-nav-link"}
            onClick={() => onSelect(section.id)}
          >
            {section.label}
          </button>
        ))}
      </div>
    </aside>
  );
}

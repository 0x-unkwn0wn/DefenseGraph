interface DocsSidebarNavProps {
  activeSection: string;
  sections: Array<{ id: string; label: string }>;
  onSelect: (sectionId: string) => void;
  title: string;
}

export function DocsSidebarNav({ activeSection, sections, onSelect, title }: DocsSidebarNavProps) {
  return (
    <aside className="docs-sidebar-nav">
      <p className="eyebrow">{title}</p>
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

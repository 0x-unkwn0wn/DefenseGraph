import sidebarLogo from "../../images/favicon.png";

interface SidebarProps {
  collapsed: boolean;
  current: "dashboard" | "tools" | "coverage" | "docs";
  onToggle: () => void;
}

const links = [
  {
    href: "#/dashboard",
    key: "dashboard",
    label: "Dashboard",
    hint: "Current security state",
    icon: "dashboard",
  },
  {
    href: "#/tools",
    key: "tools",
    label: "Tools",
    hint: "Inventory and capability mapping",
    icon: "tools",
  },
  {
    href: "#/coverage",
    key: "coverage",
    label: "Coverage",
    hint: "ATT&CK matrix view",
    icon: "coverage",
  },
  {
    href: "#/docs",
    key: "docs",
    label: "Status & Docs",
    hint: "Workspace status and reference",
    icon: "docs",
  },
] as const;

function NavIcon({ type }: { type: (typeof links)[number]["icon"] }) {
  if (type === "dashboard") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 12.5V8.5M8 12.5V3.5M13 12.5V6.5" />
      </svg>
    );
  }

  if (type === "tools") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M2.5 4.5h11M2.5 8h11M2.5 11.5h11" />
      </svg>
    );
  }

  if (type === "coverage") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M2.5 12.5V3.5M7.5 12.5V6M12.5 12.5V8.5" />
      </svg>
    );
  }

  if (type === "docs") {
    return (
      <svg viewBox="0 0 16 16" aria-hidden="true">
        <path d="M3 2.5h8l2 2v9H3zM5 6h6M5 8.5h6M5 11h4" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M2.5 3.5h11v9h-11zM5.5 6.5h5M5.5 9h3" />
    </svg>
  );
}

export function Sidebar({ collapsed, current, onToggle }: SidebarProps) {
  return (
    <aside className={`sidebar ${collapsed ? "collapsed" : ""}`.trim()}>
      <div className="sidebar-head">
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <img src={sidebarLogo} alt="DefenseGraph logo" className="sidebar-logo-image" />
          </div>
          <div className="sidebar-brand-copy">
            <p className="eyebrow">DefenseGraph</p>
            <h1>Cyber defense coverage</h1>
          </div>
        </div>
        <button
          type="button"
          className="sidebar-toggle"
          onClick={onToggle}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? ">>" : "<<"}
        </button>
      </div>

      <nav className="sidebar-nav">
        {links.map((link) => (
          <a
            key={link.key}
            href={link.href}
            className={current === link.key ? "sidebar-link active" : "sidebar-link"}
            title={collapsed ? link.label : undefined}
          >
            <span className="sidebar-link-icon" aria-hidden="true">
              <NavIcon type={link.icon} />
            </span>
            <span className="sidebar-link-copy">
              <strong>{link.label}</strong>
              <span>{link.hint}</span>
            </span>
          </a>
        ))}
      </nav>

      <div className="sidebar-footer">
        <p className="eyebrow">MVP</p>
        <p>{"Tool -> capability -> ATT&CK -> coverage -> gaps"}</p>
      </div>
    </aside>
  );
}

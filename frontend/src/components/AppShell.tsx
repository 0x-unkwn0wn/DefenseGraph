import type { PropsWithChildren } from "react";

import { Sidebar } from "./Sidebar";

interface AppShellProps extends PropsWithChildren {
  current: "tools" | "coverage" | "gaps";
  description: string;
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  title: string;
}

export function AppShell({
  children,
  current,
  description,
  isSidebarCollapsed,
  onToggleSidebar,
  title,
}: AppShellProps) {
  return (
    <div className={`dashboard-shell ${isSidebarCollapsed ? "sidebar-collapsed" : ""}`.trim()}>
      <Sidebar
        collapsed={isSidebarCollapsed}
        current={current}
        onToggle={onToggleSidebar}
      />

      <main className="main-shell">
        <header className="topbar">
          <div>
            <p className="eyebrow">DefenseGraph</p>
            <h2 className="page-title">{title}</h2>
            <p className="page-description">{description}</p>
          </div>
        </header>

        {children}
      </main>
    </div>
  );
}

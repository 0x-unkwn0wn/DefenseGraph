import type { PropsWithChildren, ReactNode } from "react";

interface DocsSectionProps extends PropsWithChildren {
  actions?: ReactNode;
  id: string;
  subtitle?: string;
  title: string;
}

export function DocsSection({ actions, children, id, subtitle, title }: DocsSectionProps) {
  return (
    <section id={id} className="card docs-section">
      <div className="card-header">
        <div>
          {subtitle ? <p className="eyebrow">{subtitle}</p> : null}
          <h2>{title}</h2>
        </div>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}

import type { PropsWithChildren, ReactNode } from "react";

interface CardProps extends PropsWithChildren {
  actions?: ReactNode;
  className?: string;
  subtitle?: string;
  title?: string;
}

export function Card({ actions, children, className = "", subtitle, title }: CardProps) {
  return (
    <section className={`card ${className}`.trim()}>
      {title || subtitle || actions ? (
        <div className="card-header">
          <div>
            {subtitle ? <p className="eyebrow">{subtitle}</p> : null}
            {title ? <h2>{title}</h2> : null}
          </div>
          {actions ? <div className="card-actions">{actions}</div> : null}
        </div>
      ) : null}
      {children}
    </section>
  );
}

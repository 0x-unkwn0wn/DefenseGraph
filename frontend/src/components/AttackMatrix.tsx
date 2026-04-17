import { useState } from "react";
import { tacticOrder } from "../attackConfig";
import type { DerivedTechnique } from "../types";

import { TechniqueCell } from "./TechniqueCell";

interface AttackMatrixProps {
  hideEmptyTactics?: boolean;
  selectedTechniqueCode: string | null;
  techniques: DerivedTechnique[];
  onSelect: (technique: DerivedTechnique) => void;
}

export function AttackMatrix({
  hideEmptyTactics = false,
  selectedTechniqueCode,
  techniques,
  onSelect,
}: AttackMatrixProps) {
  const [expandedParents, setExpandedParents] = useState<Set<string>>(new Set());

  const toggleExpand = (code: string) => {
    setExpandedParents((prev) => {
      const next = new Set(prev);
      if (next.has(code)) {
        next.delete(code);
      } else {
        next.add(code);
      }
      return next;
    });
  };

  const tacticSet = new Set(techniques.map((technique) => technique.tactic));
  const orderedTactics = tacticOrder.filter((tactic) => tacticSet.has(tactic));
  const extraTactics = Array.from(tacticSet).filter((tactic) => !tacticOrder.includes(tactic)).sort();
  const visibleTactics = [...orderedTactics, ...extraTactics].filter((tactic) =>
    !hideEmptyTactics || techniques.some((technique) => technique.tactic === tactic),
  );

  return (
    <div className="matrix-scroll">
      <div
        className="matrix-grid"
        style={{
          gridTemplateColumns: `repeat(${Math.max(visibleTactics.length, 1)}, minmax(200px, 1fr))`,
          minWidth: `${Math.max(visibleTactics.length, 1) * 206}px`,
        }}
      >
        {visibleTactics.length === 0 ? (
          <div className="matrix-global-empty">No techniques match the current filters.</div>
        ) : null}
        {visibleTactics.map((tactic) => {
          const tacticTechniques = techniques.filter((technique) => technique.tactic === tactic);
          const parentCodes = new Set(
            tacticTechniques
              .filter((technique) => !technique.is_subtechnique)
              .map((technique) => technique.technique_code),
          );
          const childTechniquesByParent = new Map<string, DerivedTechnique[]>();
          const standaloneTechniques: DerivedTechnique[] = [];

          for (const technique of tacticTechniques) {
            if (
              technique.is_subtechnique &&
              technique.parent_technique_code &&
              parentCodes.has(technique.parent_technique_code)
            ) {
              const existingChildren = childTechniquesByParent.get(technique.parent_technique_code) ?? [];
              existingChildren.push(technique);
              childTechniquesByParent.set(technique.parent_technique_code, existingChildren);
              continue;
            }
            standaloneTechniques.push(technique);
          }

          return (
            <section key={tactic} className="matrix-column">
              <header className="matrix-column-header">
                <h3>{tactic}</h3>
                <span>{tacticTechniques.length}</span>
              </header>

              <div className="matrix-column-body">
                {tacticTechniques.length === 0 ? (
                  <div className="matrix-empty">No techniques in view.</div>
                ) : (
                  standaloneTechniques.map((technique) => {
                    const children = childTechniquesByParent.get(technique.technique_code) ?? [];
                    const isExpanded = expandedParents.has(technique.technique_code);

                    return (
                      <div key={`${technique.technique_code}:${tactic}`} className="matrix-technique-group">
                        <TechniqueCell
                          technique={technique}
                          isActive={selectedTechniqueCode === technique.technique_code}
                          onSelect={onSelect}
                          subtechniqueCount={children.length > 0 ? children.length : undefined}
                          isExpanded={children.length > 0 ? isExpanded : undefined}
                          onToggleExpand={
                            children.length > 0
                              ? (e) => {
                                  e.stopPropagation();
                                  toggleExpand(technique.technique_code);
                                }
                              : undefined
                          }
                        />
                        {children.length > 0 && isExpanded ? (
                          <div className="matrix-subtechniques">
                            {children.map((child) => (
                              <TechniqueCell
                                key={`${child.technique_code}:${tactic}`}
                                technique={child}
                                isActive={selectedTechniqueCode === child.technique_code}
                                isSubtechnique
                                onSelect={onSelect}
                              />
                            ))}
                          </div>
                        ) : null}
                      </div>
                    );
                  })
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

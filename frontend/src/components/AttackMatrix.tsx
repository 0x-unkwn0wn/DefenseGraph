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
  const visibleTactics = tacticOrder.filter((tactic) =>
    !hideEmptyTactics || techniques.some((technique) => technique.tactic === tactic),
  );

  return (
    <div className="matrix-scroll">
      <div className="matrix-grid">
        {visibleTactics.length === 0 ? (
          <div className="matrix-global-empty">No techniques match the current filters.</div>
        ) : null}
        {visibleTactics.map((tactic) => {
          const tacticTechniques = techniques.filter((technique) => technique.tactic === tactic);

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
                  tacticTechniques.map((technique) => (
                    <TechniqueCell
                      key={technique.technique_code}
                      technique={technique}
                      isActive={selectedTechniqueCode === technique.technique_code}
                      onSelect={onSelect}
                    />
                  ))
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}

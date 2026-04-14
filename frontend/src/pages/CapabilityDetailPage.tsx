import { useEffect, useState } from "react";

import { getCapabilityDetail } from "../api";
import { Card } from "../components/Card";
import type { CapabilityDetail } from "../types";

interface CapabilityDetailPageProps {
  capabilityId: number;
}

export function CapabilityDetailPage({ capabilityId }: CapabilityDetailPageProps) {
  const [detail, setDetail] = useState<CapabilityDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setIsLoading(true);
    setError(null);
    void getCapabilityDetail(capabilityId)
      .then(setDetail)
      .catch((loadError) =>
        setError(loadError instanceof Error ? loadError.message : "Failed to load capability detail"),
      )
      .finally(() => setIsLoading(false));
  }, [capabilityId]);

  if (isLoading) {
    return <div className="card">Loading capability detail...</div>;
  }

  if (error || !detail) {
    return (
      <Card title="Capability detail" subtitle="Capability">
        <p className="muted">{error ?? "Capability not found."}</p>
        <a href="#/tools" className="back-link">
          Back to tools
        </a>
      </Card>
    );
  }

  return (
    <div className="stack page-stack">
      <Card
        title={detail.capability.name}
        subtitle="Capability detail"
        actions={
          <>
            <span className="domain-pill">{detail.capability.domain}</span>
            <a href="#/tools" className="back-link">
              Back to tools
            </a>
          </>
        }
      >
        <p className="section-copy">{detail.capability.description}</p>
        {(detail.capability.coverage_roles ?? []).length > 0 ? (
          <div className="tag-chip-row compact">
            {(detail.capability.coverage_roles ?? []).map((role) => (
              <span key={role.code} className="tag-chip static">
                {role.code}
              </span>
            ))}
          </div>
        ) : null}
        <p className="muted">
          {detail.capability.requires_configuration
            ? `Requires configuration verification (${detail.capability.configuration_profile_type ?? "generic"}).`
            : "No explicit configuration verification is required for this capability."}
        </p>
      </Card>

      <Card title="Implementing tools" subtitle="Capability view">
        <div className="detail-list">
          {detail.implementing_tools.length === 0 ? (
            <div className="detail-item">
              <span className="muted">No tools implement this capability yet.</span>
            </div>
          ) : (
            detail.implementing_tools.map((tool) => (
              <div key={tool.tool_id} className="detail-item stacked">
                <div className="detail-row">
                  <a href={`#/tools/${tool.tool_id}`} className="capability-link">
                    {tool.tool_name}
                  </a>
                  <div className="workspace-badges">
                    <span className={`coverage-pill ${tool.control_effect}`}>{tool.control_effect}</span>
                    <span className="count-chip">{tool.implementation_level}</span>
                    <span className={`coverage-pill ${tool.confidence_level}`}>
                      {tool.confidence_source} / {tool.confidence_level}
                    </span>
                    {tool.configuration_status ? (
                      <span className="count-chip">config / {tool.configuration_status}</span>
                    ) : null}
                  </div>
                </div>
                <p className="muted">
                  {tool.vendor ? `${tool.vendor.name} | ` : ""}
                  {tool.tool_category}
                </p>
                {(tool.tool_type_labels ?? []).length > 0 ? (
                  <div className="tag-chip-row compact">
                    {(tool.tool_type_labels ?? []).map((label) => (
                      <span key={label} className="tag-chip static">
                        {label}
                      </span>
                    ))}
                  </div>
                ) : null}
                <p className="muted">
                  {tool.effectively_active
                    ? "Capability is currently active for this tool."
                    : "Capability is currently inactive until configuration is enabled."}
                </p>
                {tool.scopes.length > 0 ? (
                  <p className="muted">
                    Scope: {tool.scopes.map((scope) => `${scope.coverage_scope.name} (${scope.status})`).join(", ")}
                  </p>
                ) : (
                  <p className="muted">No scope assigned yet.</p>
                )}
                {tool.assessment_answers.length > 0 ? (
                  <p className="muted">{tool.assessment_answers.length} assessment answers recorded.</p>
                ) : (
                  <p className="muted">No assessment responses recorded yet.</p>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      <Card title="Assessment template" subtitle="Guided assessment">
        {detail.assessment_template ? (
          <div className="assessment-list">
            {detail.assessment_template.questions.map((question) => (
              <div key={question.id} className="assessment-question read-only">
                <span>{question.prompt}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact">
            <p>No guided assessment is defined for this capability.</p>
          </div>
        )}
      </Card>

      <Card title="Configuration checklist" subtitle="Activation rules">
        {detail.configuration_questions.length > 0 ? (
          <div className="assessment-list">
            {detail.configuration_questions.map((question) => (
              <div key={question.id} className="assessment-question read-only">
                <span>{question.question}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact">
            <p>No configuration verification checklist is defined for this capability.</p>
          </div>
        )}
      </Card>

      <Card title="Related ATT&CK techniques" subtitle="Mappings">
        <div className="detail-list">
          {detail.related_techniques.map((technique) => (
            <div key={`${technique.technique_code}-${technique.control_effect}`} className="detail-item">
              <div className="detail-row">
                <a href={technique.attack_url} target="_blank" rel="noreferrer" className="capability-link">
                  {technique.technique_code} - {technique.technique_name}
                </a>
                <div className="workspace-badges">
                  <span className={`coverage-pill ${technique.control_effect}`}>{technique.control_effect}</span>
                  <span className="count-chip">{technique.coverage}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

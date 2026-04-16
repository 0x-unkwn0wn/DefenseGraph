import { useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  createCoverageSnapshot,
  getDashboardByDomain,
  getDashboardByScope,
  getDashboardDelta,
  getDashboardSummary,
  getDashboardTestStatus,
  getDashboardTopRisks,
  listCoverageSnapshots,
} from "../api";
import { Card } from "../components/Card";
import type {
  CoverageSnapshot,
  DashboardDelta,
  DashboardDomainRow,
  DashboardScopeRow,
  DashboardSummary,
  DashboardTestStatusSummary,
  DashboardTopRisk,
} from "../types";

interface DashboardPageProps {
  refreshKey?: number;
}

const EMPTY_SUMMARY: DashboardSummary = {
  total_techniques: 0,
  theoretical_coverage_pct: 0,
  real_coverage_pct: 0,
  tested_coverage_pct: 0,
  critical_gap_count: 0,
  detect_only_count: 0,
  low_confidence_count: 0,
};

export function DashboardPage({ refreshKey = 0 }: DashboardPageProps) {
  const [summary, setSummary] = useState<DashboardSummary>(EMPTY_SUMMARY);
  const [topRisks, setTopRisks] = useState<DashboardTopRisk[]>([]);
  const [domainRows, setDomainRows] = useState<DashboardDomainRow[]>([]);
  const [scopeRows, setScopeRows] = useState<DashboardScopeRow[]>([]);
  const [testStatus, setTestStatus] = useState<DashboardTestStatusSummary>({
    passed: 0,
    partial: 0,
    failed: 0,
    detected_not_blocked: 0,
    not_tested: 0,
  });
  const [snapshots, setSnapshots] = useState<CoverageSnapshot[]>([]);
  const [delta, setDelta] = useState<DashboardDelta | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreatingSnapshot, setIsCreatingSnapshot] = useState(false);

  useEffect(() => {
    void loadDashboard();
  }, [refreshKey]);

  async function loadDashboard() {
    setIsLoading(true);
    setError(null);
    try {
      const [summaryRow, riskRows, domainBreakdown, scopeBreakdown, testStatusBreakdown, snapshotRows, deltaRow] =
        await Promise.all([
          getDashboardSummary(),
          getDashboardTopRisks(10),
          getDashboardByDomain(),
          getDashboardByScope(),
          getDashboardTestStatus(),
          listCoverageSnapshots(),
          getDashboardDelta(),
        ]);
      setSummary(summaryRow);
      setTopRisks(riskRows);
      setDomainRows(domainBreakdown);
      setScopeRows(scopeBreakdown);
      setTestStatus(testStatusBreakdown);
      setSnapshots(snapshotRows);
      setDelta(deltaRow);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load dashboard");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateSnapshot() {
    const defaultName = `Baseline ${new Date().toISOString().slice(0, 10)}`;
    const name = window.prompt("Snapshot name", defaultName)?.trim();
    if (!name) {
      return;
    }
    setIsCreatingSnapshot(true);
    setError(null);
    try {
      await createCoverageSnapshot({ name });
      await loadDashboard();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Failed to create snapshot");
    } finally {
      setIsCreatingSnapshot(false);
    }
  }

  const kpis = useMemo(
    () => [
      { label: "Theoretical Coverage", value: `${summary.theoretical_coverage_pct}%` },
      { label: "Real Coverage", value: `${summary.real_coverage_pct}%` },
      { label: "Tested Coverage", value: `${summary.tested_coverage_pct}%` },
      { label: "Critical Gaps", value: String(summary.critical_gap_count) },
      { label: "Detect-Only Techniques", value: String(summary.detect_only_count) },
      { label: "Low Confidence", value: String(summary.low_confidence_count) },
    ],
    [summary],
  );

  if (isLoading) {
    return <Card title="Dashboard" subtitle="State of security">Loading dashboard...</Card>;
  }

  return (
    <div className="dashboard-page">
      <Card
        title="Dashboard"
        subtitle="State of security"
        actions={
          <div className="toolbar-inline">
            <button type="button" className="secondary-button" onClick={handleCreateSnapshot} disabled={isCreatingSnapshot}>
              {isCreatingSnapshot ? "Creating..." : "Create baseline snapshot"}
            </button>
            <a className="secondary-button" href={`${API_BASE_URL}/reports/executive`} target="_blank" rel="noreferrer">
              Executive PDF
            </a>
            <a className="secondary-button" href={`${API_BASE_URL}/reports/technical`} target="_blank" rel="noreferrer">
              Technical PDF
            </a>
            <a className="secondary-button" href={`${API_BASE_URL}/reports/gaps.csv`} target="_blank" rel="noreferrer">
              Gaps CSV
            </a>
          </div>
        }
      >
        <p className="section-copy">
          Current tenant posture from ATT&CK coverage, real-world degradations, confidence, testing, scope, and dependency health.
        </p>
        {error ? <p className="error-text">{error}</p> : null}
        <div className="dashboard-kpi-grid">
          {kpis.map((item) => (
            <div key={item.label} className="dashboard-kpi-card">
              <span className="detail-label">{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      </Card>

      <div className="dashboard-columns">
        <Card title="Top Risks" subtitle="Priority gaps">
          <div className="detail-list">
            {topRisks.map((item) => (
              <div key={item.technique_id} className="detail-item stacked">
                <div className="detail-row">
                  <strong>
                    {item.technique_code} {item.technique_name}
                  </strong>
                  <span className={`count-chip severity-${item.severity}`}>{item.severity}</span>
                </div>
                <p className="muted">{item.reason}</p>
                <p className="muted">{item.summary}</p>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Snapshots" subtitle="Change vs baseline">
          {snapshots.length === 0 ? (
            <p className="muted">No snapshots yet. Create a baseline to track change over time.</p>
          ) : (
            <>
              <div className="detail-list">
                {snapshots.slice(0, 5).map((snapshot) => (
                  <div key={snapshot.id} className="detail-item stacked">
                    <div className="detail-row">
                      <strong>{snapshot.name}</strong>
                      <span className="count-chip">{new Date(snapshot.created_at).toLocaleDateString()}</span>
                    </div>
                    <p className="muted">
                      Real {snapshot.summary_json.real_coverage_pct}% | Tested {snapshot.summary_json.tested_coverage_pct}% | Critical gaps{" "}
                      {snapshot.summary_json.critical_gap_count}
                    </p>
                  </div>
                ))}
              </div>
              {delta ? (
                <div className="dashboard-delta-grid">
                  <div className="dashboard-kpi-card">
                    <span className="detail-label">Real Coverage Delta</span>
                    <strong>{formatSigned(delta.real_coverage_pct_change)}%</strong>
                  </div>
                  <div className="dashboard-kpi-card">
                    <span className="detail-label">Tested Coverage Delta</span>
                    <strong>{formatSigned(delta.tested_coverage_pct_change)}%</strong>
                  </div>
                  <div className="dashboard-kpi-card">
                    <span className="detail-label">Critical Gaps Delta</span>
                    <strong>{formatSigned(delta.critical_gap_count_change)}</strong>
                  </div>
                </div>
              ) : null}
            </>
          )}
        </Card>
      </div>

      <div className="dashboard-columns">
        <Card title="Coverage by Domain" subtitle="Mapped defensive domains">
          <div className="dashboard-bar-list">
            {domainRows.map((row) => (
              <div key={row.domain} className="dashboard-bar-row">
                <div className="detail-row">
                  <strong>{row.domain}</strong>
                  <span className="count-chip">{row.critical_gap_count} critical gaps</span>
                </div>
                <div className="dashboard-bar-track">
                  <span className="dashboard-bar theoretical" style={{ width: `${row.theoretical_coverage_pct}%` }} />
                  <span className="dashboard-bar real" style={{ width: `${row.real_coverage_pct}%` }} />
                </div>
                <p className="muted">
                  Theoretical {row.theoretical_coverage_pct}% | Real {row.real_coverage_pct}% | Techniques {row.technique_count}
                </p>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Validation / Tested Status" subtitle="Technique-level test state">
          <div className="dashboard-kpi-grid compact">
            <div className="dashboard-kpi-card">
              <span className="detail-label">Passed</span>
              <strong>{testStatus.passed}</strong>
            </div>
            <div className="dashboard-kpi-card">
              <span className="detail-label">Partial</span>
              <strong>{testStatus.partial}</strong>
            </div>
            <div className="dashboard-kpi-card">
              <span className="detail-label">Failed</span>
              <strong>{testStatus.failed}</strong>
            </div>
            <div className="dashboard-kpi-card">
              <span className="detail-label">Detected not blocked</span>
              <strong>{testStatus.detected_not_blocked}</strong>
            </div>
            <div className="dashboard-kpi-card">
              <span className="detail-label">Not tested</span>
              <strong>{testStatus.not_tested}</strong>
            </div>
          </div>
        </Card>
      </div>

      <Card title="Coverage by Scope" subtitle="Real coverage split by operating scope">
        <div className="dashboard-scope-table">
          {scopeRows.map((row) => (
            <div key={row.scope_code} className="dashboard-scope-row">
              <strong>{row.scope_name}</strong>
              <span>Covered {row.covered_count}</span>
              <span>Partial {row.partial_count}</span>
              <span>Missing {row.missing_count}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function formatSigned(value: number) {
  return value > 0 ? `+${value}` : String(value);
}

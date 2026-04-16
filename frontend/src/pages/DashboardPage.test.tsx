import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DashboardPage } from "./DashboardPage";

vi.mock("../api", () => ({
  API_BASE_URL: "http://127.0.0.1:8000",
  createCoverageSnapshot: vi.fn(),
  getDashboardSummary: vi.fn().mockResolvedValue({
    total_techniques: 10,
    theoretical_coverage_pct: 80,
    real_coverage_pct: 60,
    tested_coverage_pct: 30,
    critical_gap_count: 4,
    detect_only_count: 2,
    low_confidence_count: 1,
  }),
  getDashboardTopRisks: vi.fn().mockResolvedValue([
    {
      technique_id: 1,
      technique_code: "T1190",
      technique_name: "Exploit Public-Facing Application",
      severity: "critical",
      reason: "No real coverage",
      summary: "No current tool provides real coverage after scope and configuration checks.",
      score: 90,
    },
  ]),
  getDashboardByDomain: vi.fn().mockResolvedValue([
    {
      domain: "Endpoint",
      technique_count: 4,
      theoretical_coverage_pct: 75,
      real_coverage_pct: 50,
      critical_gap_count: 1,
    },
  ]),
  getDashboardByScope: vi.fn().mockResolvedValue([
    {
      scope_code: "identity",
      scope_name: "Identity",
      covered_count: 2,
      missing_count: 1,
      partial_count: 1,
    },
  ]),
  getDashboardTestStatus: vi.fn().mockResolvedValue({
    passed: 1,
    partial: 1,
    failed: 1,
    detected_not_blocked: 1,
    not_tested: 6,
  }),
  getDashboardDelta: vi.fn().mockResolvedValue({
    real_coverage_pct_change: 4,
    tested_coverage_pct_change: 2,
    critical_gap_count_change: -1,
  }),
  listCoverageSnapshots: vi.fn().mockResolvedValue([
    {
      id: 1,
      tenant_id: 1,
      name: "Baseline",
      created_at: "2026-04-16T09:00:00",
      metadata_json: null,
      summary_json: {
        real_coverage_pct: 56,
        tested_coverage_pct: 28,
        critical_gap_count: 5,
      },
    },
  ]),
}));

describe("DashboardPage", () => {
  it("renders KPIs, risks, and snapshot delta", async () => {
    render(<DashboardPage />);

    await waitFor(() => expect(screen.getByText("Theoretical Coverage")).toBeInTheDocument());

    expect(screen.getByText("80%")).toBeInTheDocument();
    expect(screen.getByText(/Exploit Public-Facing Application/i)).toBeInTheDocument();
    expect(screen.getByText(/Real Coverage Delta/i)).toBeInTheDocument();
    expect(screen.getByText("+4%")).toBeInTheDocument();
    expect(screen.getByText("Baseline")).toBeInTheDocument();
  });
});

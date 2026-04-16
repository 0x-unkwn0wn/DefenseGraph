from app.schemas import (
    DashboardDomainRead,
    DashboardScopeRead,
    DashboardSummaryRead,
    DashboardTestStatusRead,
    DashboardTopRiskRead,
    TechniqueCoverageRead,
)


SCOPE_LABELS = {
    "endpoint_user_device": "Endpoint / User Device",
    "server": "Server",
    "cloud_workload": "Cloud Workload",
    "identity": "Identity",
    "network": "Network",
    "email": "Email",
    "saas": "SaaS",
    "public_facing_app": "Public-Facing Application",
}


def build_dashboard_summary(rows: list[TechniqueCoverageRead]) -> DashboardSummaryRead:
    total = len(rows) or 1
    mapped_rows = [row for row in rows if row.has_capability_mappings]
    return DashboardSummaryRead(
        total_techniques=len(rows),
        theoretical_coverage_pct=_pct(sum(1 for row in rows if row.theoretical_effect != "none"), total),
        real_coverage_pct=_pct(sum(1 for row in rows if row.real_effect != "none"), total),
        tested_coverage_pct=_pct(sum(1 for row in rows if row.test_status != "not_tested"), total),
        critical_gap_count=sum(
            1
            for row in mapped_rows
            if row.real_effect == "none" or row.test_status == "failed" or row.is_gap_scope_missing
        ),
        detect_only_count=sum(
            1 for row in mapped_rows if row.best_effect == "detect" and set(row.available_effects) <= {"detect"}
        ),
        low_confidence_count=sum(
            1 for row in mapped_rows if row.real_effect != "none" and row.confidence_level == "low"
        ),
    )


def build_top_risks(rows: list[TechniqueCoverageRead], limit: int = 10) -> list[DashboardTopRiskRead]:
    ranked = sorted(
        ((_risk_score(row), row) for row in rows if row.has_capability_mappings and _risk_score(row) > 0),
        key=lambda item: (-item[0], item[1].technique_code),
    )
    result: list[DashboardTopRiskRead] = []
    for score, row in ranked[:limit]:
        severity = "critical" if score >= 90 else "high" if score >= 60 else "medium"
        reason, summary = _risk_reason(row)
        result.append(
            DashboardTopRiskRead(
                technique_id=row.technique_id,
                technique_code=row.technique_code,
                technique_name=row.technique_name,
                severity=severity,
                reason=reason,
                summary=summary,
                score=score,
            )
        )
    return result


def build_domain_breakdown(rows: list[TechniqueCoverageRead]) -> list[DashboardDomainRead]:
    grouped: dict[str, list[TechniqueCoverageRead]] = {}
    for row in rows:
        domains = row.mapped_domains or ["Other"]
        for domain in {_normalize_domain(domain) for domain in domains}:
            grouped.setdefault(domain, []).append(row)

    result: list[DashboardDomainRead] = []
    for domain, domain_rows in sorted(grouped.items()):
        total = len(domain_rows) or 1
        result.append(
            DashboardDomainRead(
                domain=domain,
                technique_count=len(domain_rows),
                theoretical_coverage_pct=_pct(sum(1 for row in domain_rows if row.theoretical_effect != "none"), total),
                real_coverage_pct=_pct(sum(1 for row in domain_rows if row.real_effect != "none"), total),
                critical_gap_count=sum(
                    1
                    for row in domain_rows
                    if row.has_capability_mappings
                    and (row.real_effect == "none" or row.test_status == "failed" or row.is_gap_scope_missing)
                ),
            )
        )
    return result


def build_scope_breakdown(rows: list[TechniqueCoverageRead]) -> list[DashboardScopeRead]:
    result: list[DashboardScopeRead] = []
    for scope_code, scope_name in SCOPE_LABELS.items():
        relevant_rows = [
            row for row in rows if any(scope.coverage_scope.code == scope_code for scope in row.relevant_scopes)
        ]
        covered_count = sum(
            1
            for row in relevant_rows
            if scope_code in row.scope_summary.full_scopes and row.real_effect != "none"
        )
        partial_count = sum(
            1
            for row in relevant_rows
            if scope_code in row.scope_summary.partial_scopes and row.real_effect != "none"
        )
        missing_count = sum(
            1
            for row in relevant_rows
            if scope_code in row.scope_summary.missing_scopes or row.real_effect == "none"
        )
        result.append(
            DashboardScopeRead(
                scope_code=scope_code,
                scope_name=scope_name,
                covered_count=covered_count,
                missing_count=missing_count,
                partial_count=partial_count,
            )
        )
    return result


def build_test_status_breakdown(rows: list[TechniqueCoverageRead]) -> DashboardTestStatusRead:
    return DashboardTestStatusRead(
        passed=sum(1 for row in rows if row.test_status == "passed"),
        partial=sum(1 for row in rows if row.test_status == "partial"),
        failed=sum(1 for row in rows if row.test_status == "failed"),
        detected_not_blocked=sum(1 for row in rows if row.test_status == "detected_not_blocked"),
        not_tested=sum(1 for row in rows if row.test_status == "not_tested"),
    )


def build_snapshot_summary(rows: list[TechniqueCoverageRead]) -> dict:
    summary = build_dashboard_summary(rows)
    return {
        "total_techniques": summary.total_techniques,
        "theoretical_coverage_pct": summary.theoretical_coverage_pct,
        "real_coverage_pct": summary.real_coverage_pct,
        "tested_coverage_pct": summary.tested_coverage_pct,
        "critical_gap_count": summary.critical_gap_count,
        "low_confidence_count": summary.low_confidence_count,
        "detect_only_count": summary.detect_only_count,
    }


def build_snapshot_delta(current_summary: dict, previous_summary: dict | None) -> dict | None:
    if previous_summary is None:
        return None
    return {
        "real_coverage_pct_change": round(current_summary["real_coverage_pct"] - previous_summary.get("real_coverage_pct", 0), 1),
        "tested_coverage_pct_change": round(current_summary["tested_coverage_pct"] - previous_summary.get("tested_coverage_pct", 0), 1),
        "critical_gap_count_change": current_summary["critical_gap_count"] - previous_summary.get("critical_gap_count", 0),
    }


def current_gap_rows(rows: list[TechniqueCoverageRead]) -> list[TechniqueCoverageRead]:
    return [
        row
        for row in rows
        if (
            row.is_gap_no_coverage
            or row.is_gap_detect_only
            or row.is_gap_partial
            or row.is_gap_low_confidence
            or row.is_gap_scope_missing
            or row.is_gap_scope_partial
            or row.is_gap_missing_data_sources
            or row.is_gap_unconfigured_control
            or row.is_gap_partially_configured_control
            or row.is_gap_detection_without_response
            or row.is_gap_response_without_detection
            or row.is_gap_single_tool_dependency
            or row.is_gap_tested_failed
            or row.is_gap_detected_not_blocked
            or row.is_gap_untested_critical
        )
    ]


def _pct(value: int, total: int) -> float:
    return round((value / total) * 100, 1)


def _normalize_domain(domain: str) -> str:
    value = domain.lower()
    if "endpoint" in value:
        return "Endpoint"
    if "identity" in value or "credential" in value or "session" in value:
        return "Identity"
    if "network" in value:
        return "Network"
    if "email" in value:
        return "Email"
    if "data" in value or "exfil" in value:
        return "Data"
    if "application" in value or "public" in value or "web" in value or "api" in value:
        return "Public-Facing Apps / App Security"
    if "cloud" in value:
        return "Cloud"
    return domain


def _risk_score(row: TechniqueCoverageRead) -> int:
    score = 0
    if row.test_status == "failed":
        score += 100
    if row.real_effect == "none":
        score += 90
    if row.is_gap_scope_missing:
        score += 80
    if row.test_status == "detected_not_blocked":
        score += 70
    if row.confidence_level == "low" and row.real_effect != "none":
        score += 50
    if row.is_gap_detect_only:
        score += 40
    if row.is_gap_single_tool_dependency:
        score += 30
    if row.is_gap_untested_critical:
        score += 20
    return score


def _risk_reason(row: TechniqueCoverageRead) -> tuple[str, str]:
    if row.test_status == "failed":
        return "Tested and failed", "Validated control path did not hold during testing."
    if row.real_effect == "none":
        return "No real coverage", "No current tool provides real coverage after scope and configuration checks."
    if row.is_gap_scope_missing:
        return "Missing critical scope", "Coverage exists in the model, but the primary operating scope is not covered."
    if row.test_status == "detected_not_blocked":
        return "Detected but not blocked", "Testing confirmed visibility without a blocking or prevention outcome."
    if row.confidence_level == "low":
        return "Low confidence", "Coverage exists, but the supporting evidence or validation confidence remains low."
    if row.is_gap_detect_only:
        return "Detect only", "The technique is visible, but there is no blocking or prevention path."
    if row.is_gap_single_tool_dependency:
        return "Single-tool dependency", "Only one tool currently carries the technique coverage."
    return "Gap", "This technique still has meaningful residual weakness."

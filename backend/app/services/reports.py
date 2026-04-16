import csv
import io
from datetime import datetime, timezone

from app.schemas import DashboardSummaryRead, DashboardTopRiskRead, TechniqueCoverageRead
from app.services.dashboard import current_gap_rows


def build_executive_report_pdf(
    summary: DashboardSummaryRead,
    top_risks: list[DashboardTopRiskRead],
    scope_rows: list[dict],
    test_status: dict,
) -> bytes:
    lines = [
        "DefenseGraph Executive Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Theoretical Coverage: {summary.theoretical_coverage_pct}%",
        f"Real Coverage: {summary.real_coverage_pct}%",
        f"Tested Coverage: {summary.tested_coverage_pct}%",
        f"Critical Gaps: {summary.critical_gap_count}",
        f"Low Confidence: {summary.low_confidence_count}",
        "",
        "Top Risks:",
        *[f"- {item.technique_code} {item.technique_name}: {item.reason}" for item in top_risks[:5]],
        "",
        "Scope Coverage:",
        *[
            f"- {row['scope_name']}: covered {row['covered_count']}, partial {row['partial_count']}, missing {row['missing_count']}"
            for row in scope_rows[:8]
        ],
        "",
        "Validation Summary:",
        f"- Passed: {test_status['passed']}",
        f"- Partial: {test_status['partial']}",
        f"- Failed: {test_status['failed']}",
        f"- Detected Not Blocked: {test_status['detected_not_blocked']}",
        f"- Not Tested: {test_status['not_tested']}",
        "",
        "Recommended Focus Areas:",
        "- Close no-coverage and failed-test techniques first.",
        "- Expand testing on high-value blocking and prevention techniques.",
        "- Reduce low-confidence and single-tool dependencies in critical paths.",
    ]
    return _build_simple_pdf(lines)


def build_technical_report_pdf(
    summary: DashboardSummaryRead,
    top_risks: list[DashboardTopRiskRead],
    coverage_rows: list[TechniqueCoverageRead],
) -> bytes:
    gap_rows = current_gap_rows(coverage_rows)
    lines = [
        "DefenseGraph Technical Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        f"Theoretical Coverage: {summary.theoretical_coverage_pct}%",
        f"Real Coverage: {summary.real_coverage_pct}%",
        f"Tested Coverage: {summary.tested_coverage_pct}%",
        f"Critical Gaps: {summary.critical_gap_count}",
        "",
        "Top Risks:",
        *[
            f"- {item.technique_code} {item.technique_name}: {item.reason} | {item.summary}"
            for item in top_risks
        ],
        "",
        "Current Gaps:",
        *[
            f"- {row.technique_code} {row.technique_name}: real={row.real_effect}, theoretical={row.theoretical_effect}, confidence={row.confidence_level}, test={row.test_status}"
            for row in gap_rows[:25]
        ],
    ]
    return _build_simple_pdf(lines)


def build_gap_csv(rows: list[TechniqueCoverageRead]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "technique_code",
            "technique_name",
            "theoretical_effect",
            "real_effect",
            "confidence_level",
            "test_status",
            "coverage_status",
            "dependency_flags",
        ]
    )
    for row in current_gap_rows(rows):
        writer.writerow(
            [
                row.technique_code,
                row.technique_name,
                row.theoretical_effect,
                row.real_effect,
                row.confidence_level,
                row.test_status,
                row.coverage_status,
                " | ".join(row.dependency_flags),
            ]
        )
    return output.getvalue()


def _build_simple_pdf(lines: list[str]) -> bytes:
    escaped_lines = [_escape_pdf_text(line) for line in lines]
    content_lines = ["BT", "/F1 12 Tf", "50 780 Td"]
    for index, line in enumerate(escaped_lines):
        if index == 0:
            content_lines.append(f"({line}) Tj")
        else:
            content_lines.append("0 -16 Td")
            content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content_stream)} >>\nstream\n".encode("latin-1") + content_stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("latin-1")
    )
    return bytes(pdf)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

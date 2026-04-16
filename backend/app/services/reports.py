import csv
import io
from datetime import datetime, timezone

from fpdf import FPDF  # pip install fpdf2


# Replace unicode chars that Helvetica (latin-1) cannot encode
_UNICODE_MAP = str.maketrans({
    "\u2014": "--", "\u2013": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"',  "\u201d": '"', "\u2026": "...", "\u2022": "*",
    "\u00b7": "*",  "\u2192": "->", "\u2190": "<-", "\u00a0": " ",
})


def _safe(text: str) -> str:
    """Strip/replace chars outside latin-1 so Helvetica renders cleanly."""
    return text.translate(_UNICODE_MAP).encode("latin-1", errors="replace").decode("latin-1")

from app.schemas import DashboardSummaryRead, DashboardTopRiskRead, TechniqueCoverageRead
from app.services.dashboard import current_gap_rows

# ── Brand colours (dark theme palette) ────────────────────────────────────────
DARK_BG = (18, 18, 35)          # page background
PANEL = (30, 30, 55)            # card / header band
ACCENT = (99, 102, 241)         # indigo accent
ACCENT_LIGHT = (139, 142, 255)  # lighter accent for sub-text
WHITE = (255, 255, 255)
MUTED = (160, 160, 190)
CRITICAL = (239, 68, 68)        # red
WARN = (245, 158, 11)           # amber
OK = (52, 211, 153)             # green
TEXT_BODY = (220, 220, 240)


class _DGReport(FPDF):
    """Shared base for DefenseGraph PDF reports."""

    report_title: str = "DefenseGraph Report"
    report_subtitle: str = ""

    def __init__(self) -> None:
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.add_page()
        self._draw_cover_band()

    # ── PDF chrome ────────────────────────────────────────────────────────────

    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_fill_color(*PANEL)
        self.rect(0, 0, 210, 14, style="F")
        self.set_xy(10, 4)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*ACCENT_LIGHT)
        self.cell(0, 6, self.report_title.upper(), align="L")
        self.set_xy(0, 4)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(200, 6, f"Page {self.page_no()}", align="R")
        self.ln(14)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MUTED)
        self.cell(0, 6, "DefenseGraph  ·  Confidential", align="C")

    # ── Cover band (page 1) ───────────────────────────────────────────────────

    def _draw_cover_band(self) -> None:
        # background
        self.set_fill_color(*DARK_BG)
        self.rect(0, 0, 210, 297, style="F")
        # top accent band
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, 210, 2, style="F")
        # header panel
        self.set_fill_color(*PANEL)
        self.rect(0, 2, 210, 42, style="F")
        # title
        self.set_xy(12, 10)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*WHITE)
        self.cell(0, 10, self.report_title)
        # subtitle
        self.set_xy(12, 22)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(*ACCENT_LIGHT)
        self.cell(0, 8, self.report_subtitle)
        # timestamp
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d  %H:%M UTC")
        self.set_xy(12, 34)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"Generated: {ts}")
        self.set_y(54)

    # ── Section heading ───────────────────────────────────────────────────────

    def section_heading(self, title: str) -> None:
        self.ln(4)
        self.set_fill_color(*PANEL)
        self.rect(10, self.get_y(), 190, 9, style="F")
        # left accent bar
        self.set_fill_color(*ACCENT)
        self.rect(10, self.get_y(), 3, 9, style="F")
        self.set_xy(16, self.get_y() + 1)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*WHITE)
        self.cell(0, 7, _safe(title).upper())
        self.ln(13)

    # ── KPI grid ──────────────────────────────────────────────────────────────

    def kpi_grid(self, items: list[tuple[str, str, tuple]]) -> None:
        """Render a row of KPI tiles. items = [(label, value, colour), ...]"""
        cols = len(items)
        w = 186 / cols
        x0 = 12
        y0 = self.get_y()
        for i, (label, value, colour) in enumerate(items):
            x = x0 + i * (w + 2)
            self.set_fill_color(*PANEL)
            self.rect(x, y0, w, 20, style="F")
            self.set_fill_color(*colour)
            self.rect(x, y0, w, 2, style="F")
            self.set_xy(x + 2, y0 + 4)
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*colour)
            self.cell(w - 4, 7, value, align="C")
            self.set_xy(x + 2, y0 + 12)
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*MUTED)
            self.cell(w - 4, 5, label, align="C")
        self.ln(26)

    # ── Body text ─────────────────────────────────────────────────────────────

    def body_text(self, text: str, indent: int = 12) -> None:
        self.set_x(indent)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_BODY)
        self.multi_cell(186, 5, _safe(text))

    # ── Risk item ─────────────────────────────────────────────────────────────

    def risk_item(
        self,
        index: int,
        code: str,
        name: str,
        reason: str,
        summary: str = "",
        severity: str = "high",
    ) -> None:
        colour = CRITICAL if severity == "critical" else (WARN if severity == "high" else OK)
        y = self.get_y()
        self.set_fill_color(*PANEL)
        self.rect(12, y, 186, 1, style="F")  # top border line
        self.set_fill_color(*colour)
        self.rect(12, y, 3, 18 if summary else 13, style="F")
        # index badge
        self.set_fill_color(*PANEL)
        self.set_xy(17, y + 1)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*colour)
        self.cell(14, 6, f"#{index}", align="C")
        # code
        self.set_xy(31, y + 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*WHITE)
        self.cell(22, 6, _safe(code))
        # name
        self.set_xy(54, y + 1)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*TEXT_BODY)
        self.cell(0, 6, _safe(name))
        # reason
        self.set_xy(17, y + 8)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MUTED)
        self.multi_cell(181, 4.5, _safe(reason))
        if summary:
            self.set_x(17)
            self.set_font("Helvetica", "I", 7.5)
            self.set_text_color(*ACCENT_LIGHT)
            self.multi_cell(181, 4, _safe(summary))
        self.ln(3)

    # ── Table helpers ─────────────────────────────────────────────────────────

    def table_header(self, cols: list[tuple[str, int]]) -> None:
        """cols = [(label, width_mm), ...]"""
        self.set_fill_color(*ACCENT)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        x0 = 12
        for label, w in cols:
            self.set_xy(x0, self.get_y())
            self.cell(w, 7, label, fill=True, border=0)
            x0 += w
        self.ln(8)

    def table_row(self, cols: list[tuple[str, int]], even: bool = False) -> None:
        fill_col = (24, 24, 45) if even else DARK_BG
        self.set_fill_color(*fill_col)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(*TEXT_BODY)
        x0 = 12
        y = self.get_y()
        row_h = 6
        for value, w in cols:
            self.set_xy(x0, y)
            self.cell(w, row_h, _safe(str(value))[:42], fill=True, border=0)
            x0 += w
        self.ln(row_h)


# ── Executive report ──────────────────────────────────────────────────────────


def build_executive_report_pdf(
    summary: DashboardSummaryRead,
    top_risks: list[DashboardTopRiskRead],
    scope_rows: list[dict],
    test_status: dict,
) -> bytes:
    class _PDF(_DGReport):
        report_title = "DefenseGraph Executive Report"
        report_subtitle = "Security Posture Overview"

    pdf = _PDF()
    pdf.set_fill_color(*DARK_BG)

    # ── Coverage KPIs ─────────────────────────────────────────────────────────
    pdf.section_heading("Coverage Summary")
    pdf.kpi_grid([
        ("Theoretical Coverage", f"{summary.theoretical_coverage_pct}%", ACCENT),
        ("Real Coverage",        f"{summary.real_coverage_pct}%",        OK),
        ("Tested Coverage",      f"{summary.tested_coverage_pct}%",      WARN),
        ("Critical Gaps",        str(summary.critical_gap_count),        CRITICAL),
        ("Low Confidence",       str(summary.low_confidence_count),      WARN),
    ])

    # ── Top risks ─────────────────────────────────────────────────────────────
    pdf.section_heading("Top Priority Risks")
    for i, item in enumerate(top_risks[:8], start=1):
        pdf.risk_item(
            index=i,
            code=item.technique_code,
            name=item.technique_name,
            reason=item.reason,
            severity=getattr(item, "severity", "high"),
        )

    # ── Scope coverage ────────────────────────────────────────────────────────
    pdf.section_heading("Coverage by Scope")
    cols = [("Scope", 70), ("Covered", 30), ("Partial", 30), ("Missing", 30), ("Total", 26)]
    pdf.table_header(cols)
    for idx, row in enumerate(scope_rows[:12]):
        total = row["covered_count"] + row["partial_count"] + row["missing_count"]
        pdf.table_row([
            (row["scope_name"],      70),
            (row["covered_count"],   30),
            (row["partial_count"],   30),
            (row["missing_count"],   30),
            (total,                  26),
        ], even=idx % 2 == 0)

    # ── Validation summary ────────────────────────────────────────────────────
    pdf.section_heading("Validation / Test Status")
    pdf.kpi_grid([
        ("Passed",              str(test_status["passed"]),               OK),
        ("Partial",             str(test_status["partial"]),              WARN),
        ("Failed",              str(test_status["failed"]),               CRITICAL),
        ("Detected Not Blocked",str(test_status["detected_not_blocked"]), WARN),
        ("Not Tested",          str(test_status["not_tested"]),           MUTED),
    ])

    # ── Recommendations ───────────────────────────────────────────────────────
    pdf.section_heading("Recommended Focus Areas")
    bullets = [
        "1. Close no-coverage and failed-test techniques first - these represent the highest exploitable risk.",
        "2. Expand BAS / validation testing on high-value blocking and prevention techniques.",
        "3. Reduce low-confidence and single-tool dependencies in critical ATT&CK paths.",
        "4. Improve real-world coverage for any technique with theoretical > real gap > 20 pp.",
        "5. Review detect-only techniques and determine if prevention uplift is feasible.",
    ]
    for b in bullets:
        pdf.body_text(b)
        pdf.ln(2)

    return bytes(pdf.output())


# ── Technical report ──────────────────────────────────────────────────────────


def build_technical_report_pdf(
    summary: DashboardSummaryRead,
    top_risks: list[DashboardTopRiskRead],
    coverage_rows: list[TechniqueCoverageRead],
) -> bytes:
    gap_rows = current_gap_rows(coverage_rows)

    class _PDF(_DGReport):
        report_title = "DefenseGraph Technical Report"
        report_subtitle = "Detailed Coverage & Gap Analysis"

    pdf = _PDF()
    pdf.set_fill_color(*DARK_BG)

    # ── Coverage KPIs ─────────────────────────────────────────────────────────
    pdf.section_heading("Coverage Metrics")
    pdf.kpi_grid([
        ("Theoretical Coverage", f"{summary.theoretical_coverage_pct}%", ACCENT),
        ("Real Coverage",        f"{summary.real_coverage_pct}%",        OK),
        ("Tested Coverage",      f"{summary.tested_coverage_pct}%",      WARN),
        ("Critical Gaps",        str(summary.critical_gap_count),        CRITICAL),
    ])

    # ── Top risks (full detail) ───────────────────────────────────────────────
    pdf.section_heading("Top Risks - Full Detail")
    for i, item in enumerate(top_risks, start=1):
        pdf.risk_item(
            index=i,
            code=item.technique_code,
            name=item.technique_name,
            reason=item.reason,
            summary=getattr(item, "summary", ""),
            severity=getattr(item, "severity", "high"),
        )

    # ── Gap table ─────────────────────────────────────────────────────────────
    pdf.section_heading("Current Gaps - Technique Detail")
    cols = [
        ("Technique",    38),
        ("Name",         58),
        ("Real Effect",  28),
        ("Theoretical",  28),
        ("Confidence",   24),
        ("Test Status",  24),
    ]
    pdf.table_header(cols)
    for idx, row in enumerate(gap_rows):
        pdf.table_row([
            (row.technique_code,       38),
            (row.technique_name,       58),
            (row.real_effect,          28),
            (row.theoretical_effect,   28),
            (row.confidence_level,     24),
            (row.test_status,          24),
        ], even=idx % 2 == 0)

    return bytes(pdf.output())


# ── CSV gap export (unchanged) ────────────────────────────────────────────────


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

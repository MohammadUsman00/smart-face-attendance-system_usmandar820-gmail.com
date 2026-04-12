"""Minimal PDF report for analytics (fpdf2)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict


def build_analytics_pdf_summary(analytics_data: Dict[str, Any]) -> bytes:
    """Return PDF bytes with overview + key metrics (no charts)."""
    from fpdf import FPDF

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.cell(0, 10, "Attendance analytics report", ln=True)
            self.set_font("Helvetica", "", 9)
            self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
            self.ln(4)

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    overview = analytics_data.get("overview") or {}
    na = "n/a"
    lines = [
        f"Total students: {overview.get('total_students', na)}",
        f"Present today: {overview.get('present_today', na)}",
        f"Absent today: {overview.get('absent_today', na)}",
        f"Attendance rate today (%): {overview.get('attendance_rate_today', na)}",
        f"Avg weekly rate (%): {overview.get('avg_weekly_rate', na)}",
        "",
        f"Daily trend rows: {len(analytics_data.get('daily_trends') or [])}",
        f"Student performance rows: {len(analytics_data.get('student_performance') or [])}",
        f"Course rows: {len(analytics_data.get('course_analytics') or [])}",
        f"Alerts: {len(analytics_data.get('alerts') or [])}",
    ]
    for line in lines:
        pdf.cell(0, 6, line or " ", ln=True)

    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(
        0,
        5,
        "Charts stay in the web app; this PDF is a short text summary for archiving.",
        ln=True,
    )

    raw = pdf.output(dest="S")
    if isinstance(raw, str):
        return raw.encode("latin-1")
    return bytes(raw)

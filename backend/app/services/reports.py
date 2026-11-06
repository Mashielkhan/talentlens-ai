from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_report(results: list[dict], title="Qualification analysis"):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#4338ca")
    content = [Paragraph("TalentLens AI", styles["Title"]), Paragraph(escape(title), styles["Heading2"])]
    for result in results:
        content.extend(
            [
                Spacer(1, 16),
                Paragraph(escape(result["job_title"]), styles["Heading2"]),
                Paragraph(escape(result["resume_filename"]), styles["Normal"]),
                Paragraph(
                    f"Compatibility Index: {result['compatibility_index']:.1f} / 100", styles["Heading3"]
                ),
            ]
        )
        rows = [["Component", "Index", "Effective weight"]]
        for key, value in result["score_breakdown"].items():
            rows.append(
                [
                    key.replace("_", " ").title(),
                    f"{value:.1f}" if value is not None else "Unknown / N/A",
                    f"{result['effective_weights'][key]:.1%}",
                ]
            )
        table = Table(rows, colWidths=[2.7 * inch, 1.4 * inch, 1.4 * inch], repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        content.append(table)
        for label, values in [
            ("Documented required skills", result["matched_skills"]),
            ("Required skills not documented", result["not_documented_required_skills"]),
            ("Preferred skills not documented", result["not_documented_preferred_skills"]),
            ("Uncertainty", result["uncertainties"]),
        ]:
            content.extend(
                [
                    Paragraph(label, styles["Heading3"]),
                    Paragraph(escape("; ".join(values) or "None"), styles["Normal"]),
                ]
            )
        for evidence in result["evidence"]:
            content.append(
                Paragraph(
                    escape(f"{evidence['name']} ({evidence['source_section']}): {evidence['evidence']}"),
                    styles["Normal"],
                )
            )
        content.append(Paragraph("Learning and evidence plan", styles["Heading3"]))
        for item in result["recommendations"]:
            content.append(
                Paragraph(
                    escape(item["action"] + (" " + item["url"] if item["url"] else "")), styles["Normal"]
                )
            )
        content.extend(
            [
                Spacer(1, 12),
                Paragraph(escape(result["disclaimer"]), styles["Normal"]),
                Paragraph(
                    escape(
                        f"Model: {result['model_version']} | Scoring: {result['scoring_version']} | Experience as of: {result['as_of_date']}"
                    ),
                    styles["Normal"],
                ),
            ]
        )
    SimpleDocTemplate(buffer, title=title, author="TalentLens AI", rightMargin=40, leftMargin=40).build(
        content
    )
    return buffer.getvalue()

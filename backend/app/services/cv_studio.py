"""Conservative editing assistance and exports of explicitly approved content."""

import re
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.nlp.taxonomy import extract_skills
from app.schemas.beta import CvContent

SECTIONS = ("summary", "skills", "experience", "education", "projects", "certifications")


def prepare_draft(parsed, target):
    contact, sections = parsed.get("contact", {}), parsed.get("sections", {})
    links = contact.get("links", [])
    content = CvContent(
        name=contact.get("name", ""),
        email=contact.get("email", ""),
        phone=contact.get("phone", ""),
        links="\n".join(links) if isinstance(links, list) else str(links),
        **{key: sections.get(key, "") for key in SECTIONS},
    ).model_dump()
    if not content["skills"]:
        content["skills"] = ", ".join(s["name"] for s in parsed.get("skills", []))
    documented = {s["name"].casefold() for s in parsed.get("skills", [])}
    target_skills = [s["name"] for s in extract_skills({"description": target})]
    suggestions = []
    for section in ("summary", "experience", "projects"):
        for line in content[section].splitlines():
            original = line.strip()
            replacement = re.sub(r"\bin order to\b", "to", original, flags=re.I)
            replacement = re.sub(r"\butilized\b", "used", replacement, flags=re.I)
            replacement = re.sub(
                r"^I (?=(?:built|developed|designed|implemented|tested|managed|created)\b)",
                "",
                replacement,
                flags=re.I,
            )
            if replacement:
                replacement = replacement[0].upper() + replacement[1:]
            if replacement != original:
                suggestions.append(
                    {
                        "id": len(suggestions),
                        "section": section,
                        "original": original,
                        "replacement": replacement,
                        "reason": "Use direct, concise wording while preserving the supplied facts.",
                    }
                )
    prompts = [
        "For each project, describe your contribution and a result you can support. Add numbers only when you can verify them."
    ]
    if not content["summary"]:
        prompts.append(
            "Add a short summary of your actual role, strongest documented skills and target work."
        )
    if not target_skills:
        prompts.append(
            "No catalogued IT skills were recognized in this job description. Review its requirements manually."
        )
    return content, {
        "method": "Conservative editing rules and the IT skill taxonomy; no generative rewrite.",
        "suggestions": suggestions[:50],
        "prompts": prompts,
        "documented_target_skills": [s for s in target_skills if s.casefold() in documented],
        "not_documented_target_skills": [s for s in target_skills if s.casefold() not in documented],
    }


def render_cv(content, kind):
    content = CvContent.model_validate(content).model_dump()
    buffer = BytesIO()
    if kind == "docx":
        document = Document()
        section = document.sections[0]
        section.top_margin = section.bottom_margin = Inches(0.65)
        section.page_width, section.page_height = Inches(8.27), Inches(11.69)
        for style in ("Title", "Heading 1", "Normal"):
            document.styles[style].font.color.rgb = RGBColor(0, 0, 0)
        normal = document.styles["Normal"]
        normal.font.name, normal.font.size = "Calibri", Pt(10)
        document.add_heading(content["name"], 0)
        for key in ("email", "phone", "links"):
            if content[key]:
                document.add_paragraph(content[key])
        for key in SECTIONS:
            if content[key]:
                document.add_heading(key.title(), 1)
                for line in content[key].splitlines():
                    if line.strip():
                        document.add_paragraph(line.strip())
        document.core_properties.title = "Curriculum Vitae"
        document.core_properties.author = content["name"]
        document.save(buffer)
    else:
        # Bundled Bitstream Vera provides accented Latin support without host fonts.
        font_dir = Path(reportlab.__file__).parent / "fonts"
        if "CVVera" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("CVVera", str(font_dir / "Vera.ttf")))
            pdfmetrics.registerFont(TTFont("CVVeraBold", str(font_dir / "VeraBd.ttf")))
        supported = pdfmetrics.getFont("CVVera").face.charToGlyph
        if any(ord(c) not in supported for value in content.values() for c in value if not c.isspace()):
            raise ValueError("This PDF font cannot render some characters. Use DOCX export for this CV.")
        styles = getSampleStyleSheet()
        body = ParagraphStyle(
            "CVBody", fontName="CVVera", fontSize=10, leading=15, spaceAfter=5, splitLongWords=True
        )
        heading = ParagraphStyle(
            "CVHeading",
            parent=body,
            fontName="CVVeraBold",
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True,
            textColor=colors.HexColor("#312e81"),
        )
        title = ParagraphStyle(
            "CVTitle", parent=styles["Title"], fontName="CVVeraBold", fontSize=22, leading=28, alignment=0
        )
        story = [Paragraph(escape(content["name"]), title)]
        for key in ("email", "phone", "links"):
            for line in content[key].splitlines():
                story.append(Paragraph(escape(line), body))
        story.append(Spacer(1, 8))
        for key in SECTIONS:
            if content[key]:
                story.append(Paragraph(key.title(), heading))
                for line in content[key].splitlines():
                    if line.strip():
                        story.append(Paragraph(escape(line.strip()), body))
        SimpleDocTemplate(
            buffer,
            title="Curriculum Vitae",
            author=content["name"],
            leftMargin=45,
            rightMargin=45,
            topMargin=42,
            bottomMargin=42,
        ).build(story)
    return buffer.getvalue()

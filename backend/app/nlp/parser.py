import re
from datetime import date
from functools import lru_cache

import spacy

from app.core.config import settings
from app.nlp.taxonomy import CATEGORIES, canonical_name, extract_skills

HEADINGS = {
    "summary": ["summary", "profile", "professional summary", "objective", "about me"],
    "skills": ["skills", "technical skills", "technologies", "core competencies", "technical expertise"],
    "experience": [
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "employment history",
    ],
    "education": ["education", "academic background", "academic qualifications"],
    "projects": ["projects", "selected projects", "personal projects"],
    "certifications": ["certifications", "certificates", "licenses"],
}
MONTHS = {
    name: i
    for i, name in enumerate(
        ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1
    )
}
DATE = r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[ .]+)?(?:19|20)\d{2}"
RANGES = re.compile(rf"({DATE})\s*(?:[-–—]|to)\s*({DATE}|present|current|now)\b", re.I)


@lru_cache
def ner_model():
    # Missing models are explicit worker failures, never silently replaced with fake NER.
    return spacy.load(settings().spacy_model)


def split_sections(text: str):
    output = {"contact": []}
    active = "contact"
    lookup = {heading: key for key, headings in HEADINGS.items() for heading in headings}
    for line in text.splitlines():
        heading = line.strip().strip(":").casefold()
        if heading in lookup:
            active = lookup[heading]
            output.setdefault(active, [])
        else:
            output[active].append(line)
    return {key: "\n".join(lines).strip() for key, lines in output.items() if any(lines)}


def month_number(value: str, today: date):
    if value.lower() in {"present", "current", "now"}:
        return today.year * 12 + today.month - 1, False
    year = int(re.search(r"\d{4}", value)[0])
    month = MONTHS.get(value[:3].lower())
    return year * 12 + (month or 1) - 1, month is None


def union_months(intervals):
    merged = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def experience_entries(text: str, today: date):
    matches = list(RANGES.finditer(text))
    entries = []
    for i, match in enumerate(matches):
        start, approx_start = month_number(match[1], today)
        end, approx_end = month_number(match[2], today)
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        evidence = text[max(0, text.rfind("\n", 0, match.start())) : next_start].strip()
        entries.append(
            {
                "start_month": start,
                "end_month": min(end, today.year * 12 + today.month - 1),
                "approximate": approx_start or approx_end,
                "evidence": evidence,
                "skills": [s["name"] for s in extract_skills({"experience": evidence})],
            }
        )
    return entries


def parse_resume(text: str, corrections: dict | None = None, today: date | None = None, nlp=None):
    today = today or date.today()
    corrections = corrections or {}
    sections = split_sections(text)
    sections.update(corrections.get("sections", {}))
    doc = (nlp or ner_model())(text)
    entities = [
        {"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char}
        for e in doc.ents
        if e.label_ in {"PERSON", "ORG", "GPE", "DATE"}
    ]
    email = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    phone = re.search(r"(?<!\w)(?:\+\d{1,3}[ -]?)?(?:\(?\d{3}\)?[ -])\d{3}[ -]\d{4}(?!\w)", text)
    links = re.findall(r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in/|github\.com/)[A-Za-z0-9_.%/-]+", text)
    people = [e["text"] for e in entities if e["label"] == "PERSON" and e["start"] < 180]
    contact = {
        "name": people[0] if people else "",
        "email": email[0] if email else "",
        "phone": phone[0] if phone else "",
        "links": links,
    }
    contact.update(corrections.get("contact", {}))
    qualifications = {k: v for k, v in sections.items() if k != "contact"}
    skills = extract_skills(qualifications)
    if "skills" in corrections:
        skills = [
            {
                "name": canonical_name(s),
                "category": CATEGORIES.get(canonical_name(s), "Other"),
                "source_section": "user correction",
                "evidence": "Applicant-confirmed; not independently verified",
                "method": "manual",
                "user_verified": True,
            }
            for s in dict.fromkeys(corrections["skills"])
        ]
    experience = experience_entries(sections.get("experience", ""), today)
    uncertainty = ["Extraction is heuristic. Review all fields before sharing."]
    if not qualifications:
        uncertainty.append("No recognized section headings. Add section corrections to enable matching.")
    if not experience:
        uncertainty.append("Employment date ranges not documented or not recognized.")
    if any(e["approximate"] for e in experience):
        uncertainty.append("Year-only dates use January; durations are approximate.")
    return {
        "contact": contact,
        "skills": skills,
        "sections": sections,
        "entities": entities,
        "experience": experience,
        "total_experience_months": union_months([(e["start_month"], e["end_month"]) for e in experience]),
        "education": sections.get("education", ""),
        "projects": sections.get("projects", ""),
        "certifications": sections.get("certifications", ""),
        "uncertainties": uncertainty,
        "as_of_date": today.isoformat(),
        "parser_version": "rules-spacy-1.0",
    }


def qualification_texts(parsed: dict):
    """Exclude contact, unrecognized sections and known PII from model inputs."""
    output = {}
    for key, value in parsed["sections"].items():
        if key not in HEADINGS:
            continue
        value = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|https?://\S+", " ", value)
        value = "\n".join(
            line
            for line in value.splitlines()
            if not re.search(
                r"\b(gender|date of birth|marital|nationality|religion|born|age)\s*:", line, re.I
            )
        )
        for entity in parsed.get("entities", []):
            if entity["label"] in {"PERSON", "GPE"}:
                value = re.sub(re.escape(entity["text"]), " ", value, flags=re.I)
        if value.strip():
            output[key] = value.strip()
    if parsed.get("skills"):
        output["skills"] = ", ".join(s["name"] for s in parsed["skills"])
    return output

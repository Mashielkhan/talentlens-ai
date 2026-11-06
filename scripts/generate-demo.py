"""Generate original, explicitly synthetic documents and independent relevance labels."""

import json
from pathlib import Path

import pymupdf
from docx import Document

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "datasets" / "generated"
DOMAINS = [
    (
        "Python Backend Engineer",
        ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "Build Python backend REST APIs using FastAPI and PostgreSQL. Package services with Docker and write tests.",
    ),
    (
        "React Frontend Engineer",
        ["React", "TypeScript", "CSS", "Playwright"],
        "Develop accessible React interfaces using TypeScript and CSS. Test responsive browser experiences with Playwright.",
    ),
    (
        "Machine Learning Engineer",
        ["Python", "PyTorch", "Machine Learning", "scikit-learn"],
        "Train and evaluate machine learning models with Python, PyTorch and scikit-learn. Build reproducible experiments.",
    ),
    (
        "Data Analyst",
        ["SQL", "pandas", "Tableau", "Excel"],
        "Analyze business data with SQL and pandas. Communicate findings in Tableau dashboards and Excel reports.",
    ),
    (
        "DevOps Engineer",
        ["Docker", "Kubernetes", "AWS", "Terraform"],
        "Operate container services with Docker and Kubernetes. Manage AWS infrastructure using Terraform.",
    ),
]


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs, documents = [], []
    for role, skills, description in DOMAINS:
        jobs.append(
            {
                "title": role + " — synthetic demo",
                "company": "Synthetic Example Labs",
                "description": description,
                "required_skills": [
                    {"name": s, "weight": 5 - i} for i, s in enumerate(skills[:3])
                ],
                "preferred_skills": [{"name": skills[3], "weight": 1}],
                "min_experience_months": 24,
                "education_requirement": "Computer Science",
                "status": "PUBLISHED",
                "requirements_confirmed": True,
            }
        )
    index = 0
    for domain, (role, skills, description) in enumerate(DOMAINS):
        for tier in range(4):
            index += 1
            subset = skills[: max(1, 4 - tier)]
            # Independent labels include skills explicitly present outside the
            # Skills section; never derive ground truth from parser predictions.
            gold_skills = set(subset)
            if domain == 0 and tier == 0:
                gold_skills.add("REST APIs")
            if domain == 2:
                gold_skills.add("Machine Learning")
            years = [4, 2, 1, 0][tier]
            work = (
                f"{role}\nJan {2024 - years} - Jan 2024\nUsed {', '.join(subset)} to deliver documented project work."
                if years
                else "Internship project; dates not documented."
            )
            text = f"Synthetic Candidate {index:02d}\nsynthetic{index:02d}@example.org\nSummary\n{role} building maintainable systems.\nSkills\n{', '.join(subset)}\nExperience\n{work}\nEducation\nBS Computer Science, Fictional Example University\nProjects\n{description if tier == 0 else 'A portfolio project using ' + ', '.join(subset)}\nCertifications\nNo certifications documented."
            stem = f"synthetic-{index:02d}"
            with pymupdf.open() as pdf:
                page = pdf.new_page()
                page.insert_textbox(pymupdf.Rect(45, 45, 550, 790), text, fontsize=10)
                pdf.save(OUT / f"{stem}.pdf")
            doc = Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(OUT / f"{stem}.docx")
            documents.append(
                {
                    "id": stem,
                    "text": text,
                    "domain": domain,
                    "tier": tier,
                    "gold_skills": sorted(gold_skills),
                    "gold_email": f"synthetic{index:02d}@example.org",
                    "relevance": [
                        max(0, 3 - tier)
                        if j == domain
                        else (1 if "Python" in subset and j in {0, 2} else 0)
                        for j in range(5)
                    ],
                }
            )
    (OUT / "jobs.json").write_text(json.dumps(jobs, indent=2), encoding="utf-8")
    (OUT / "annotations.json").write_text(
        json.dumps(documents, indent=2), encoding="utf-8"
    )
    print(
        f"Generated {len(documents)} synthetic PDF/DOCX pairs and {len(jobs)} jobs in {OUT}"
    )


if __name__ == "__main__":
    generate()

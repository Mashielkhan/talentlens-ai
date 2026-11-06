import pymupdf

from app.services.reports import render_report


def test_report_is_real_paginated_pdf_and_escapes_input():
    result = {
        "job_title": "Python <Engineer>",
        "resume_filename": "synthetic.pdf",
        "compatibility_index": 72.5,
        "score_breakdown": {"semantic_relevance": 75, "required_skills": 70, "experience": None},
        "effective_weights": {"semantic_relevance": 0.6, "required_skills": 0.4, "experience": 0},
        "matched_skills": ["Python"],
        "not_documented_required_skills": ["Docker"],
        "not_documented_preferred_skills": [],
        "uncertainties": ["Unknown experience"],
        "evidence": [{"name": "Python", "source_section": "skills", "evidence": "Built <API> & services"}],
        "recommendations": [{"action": "Demonstrate Docker in a project", "url": "https://docs.docker.com/"}],
        "disclaimer": "Not a hiring probability.",
        "model_version": "test-model",
        "scoring_version": "test",
        "as_of_date": "2026-01-01",
    }
    data = render_report([result] * 4)
    assert data.startswith(b"%PDF-")
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        assert len(pdf) >= 2
        text = " ".join(p.get_text() for p in pdf)
        assert "72.5" in text and "Not a hiring probability" in text and "<Engineer>" in text

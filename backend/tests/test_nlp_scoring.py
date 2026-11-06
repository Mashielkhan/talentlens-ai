from datetime import date
from types import SimpleNamespace

import pytest
import spacy

from app.ml.embeddings import semantic_score
from app.ml.scoring import score_match
from app.nlp.parser import experience_entries, parse_resume, qualification_texts, split_sections, union_months
from app.nlp.taxonomy import extract_skills


def test_aliases_and_symbol_languages():
    skills = extract_skills({"skills": "ReactJS React.js React JS Postgres Postgre SQL C++ C# .NET"})
    names = [s["name"] for s in skills]
    assert set(names) == {"React", "PostgreSQL", "C++", "C#", ".NET"}
    assert names.count("React") == 1


def test_go_to_market_not_programming():
    assert "Go" not in [s["name"] for s in extract_skills({"summary": "We go to market together."})]
    assert "Go" in [s["name"] for s in extract_skills({"skills": "Go, Python"})]


def test_phrase_boundaries():
    assert not extract_skills({"skills": "Pythonic reactive unrelated"})


def test_heading_variants_and_contacts():
    text = "Synthetic Person\na@example.org\nTechnical Expertise\nPython C++\nAcademic Background\nBS Computer Science"
    parsed = parse_resume(text, today=date(2026, 1, 1), nlp=spacy.blank("en"))
    assert parsed["contact"]["email"] == "a@example.org"
    assert "education" in split_sections(text)
    assert "a@example.org" not in " ".join(qualification_texts(parsed).values())
    assert parsed["contact"]["name"] == ""  # No fabricated PERSON from a blank test model.


def test_overlapping_employment_and_current_role():
    entries = experience_entries(
        "Jan 2020 - Jan 2023\nPython APIs\nJan 2022 - Present\nPython services", date(2024, 1, 1)
    )
    assert union_months([(e["start_month"], e["end_month"]) for e in entries]) == 48
    assert union_months([(1, 5), (3, 7), (10, 12)]) == 8


def test_missing_end_date_and_ambiguous_years():
    assert not experience_entries("Engineer since Jan 2020", date(2024, 1, 1))
    entries = experience_entries("2020 - 2022 Python", date(2024, 1, 1))
    assert entries[0]["approximate"]


def job(**overrides):
    values = dict(
        required_skills=[{"name": "Python", "weight": 5}, {"name": "Docker", "weight": 3}],
        preferred_skills=[{"name": "AWS", "weight": 1}],
        min_experience_months=24,
        education_requirement="Computer Science",
    )
    return SimpleNamespace(**(values | overrides))


def parsed():
    return {
        "skills": [{"name": "Python", "evidence": "Python API", "source_section": "skills"}],
        "experience": [],
        "education": "",
        "uncertainties": [],
    }


def test_weighted_gap_and_unknown_components():
    result = score_match(parsed(), job(), 80)
    assert result["score_breakdown"]["required_skills"] == 62.5
    assert result["score_breakdown"]["experience"] is None
    assert result["score_breakdown"]["education"] is None
    assert result["not_documented_required_skills"] == ["Docker"]
    assert result["not_documented_preferred_skills"] == ["AWS"]
    assert sum(result["effective_weights"].values()) == pytest.approx(1)
    assert result["compatibility_index"] == 73


def test_preferred_skill_never_changes_required_coverage():
    a = score_match(parsed(), job(), 80)
    b = score_match(parsed(), job(preferred_skills=[]), 80)
    assert a["score_breakdown"]["required_skills"] == b["score_breakdown"]["required_skills"]


def test_relevance_requires_job_skill_evidence():
    p = parsed()
    p["experience"] = [
        {"start_month": 24000, "end_month": 24024, "skills": ["React"], "evidence": "Frontend"}
    ]
    assert score_match(p, job(), 50)["relevant_experience_months"] is None
    p["experience"][0]["skills"] = ["Python"]
    assert score_match(p, job(), 50)["score_breakdown"]["experience"] == 100


def test_reproducibility_and_changed_requirements():
    assert score_match(parsed(), job(), 71.123) == score_match(parsed(), job(), 71.123)
    assert (
        score_match(parsed(), job(required_skills=[{"name": "Python", "weight": 1}]), 71)["score_breakdown"][
            "required_skills"
        ]
        == 100
    )


def test_semantic_component_uses_vectors_not_keywords():
    assert semantic_score([[1, 0], [0, 1]], [[1, 0]]) == 100
    assert semantic_score([[1, 0]], [[0, 1]]) == 0
    with pytest.raises(ValueError):
        semantic_score([], [[1, 0]])


def test_contact_and_explicit_demographics_excluded_from_embedding_input():
    p = {
        "sections": {
            "contact": "Jane a@example.org",
            "experience": "Python services\nGender: female\nAge: 28\nLondon",
        },
        "entities": [{"text": "London", "label": "GPE"}],
        "skills": [],
    }
    value = " ".join(qualification_texts(p).values())
    assert all(term not in value for term in ["Jane", "female", "28", "London", "example.org"])

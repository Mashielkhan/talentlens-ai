import hashlib
import json
import re

from app.core.config import settings
from app.nlp.parser import union_months
from app.nlp.taxonomy import RESOURCES, canonical_name

DISCLAIMER = "Heuristic relevance estimate based on documented qualifications, not a hiring probability. Human review is required. Undocumented does not mean absent."


def score_match(parsed, job, semantic):
    skills = {canonical_name(s["name"]).casefold(): s for s in parsed["skills"]}
    required, preferred = job.required_skills, job.preferred_skills
    matched = [s["name"] for s in required if s["name"].casefold() in skills]
    missing = [s["name"] for s in required if s["name"].casefold() not in skills]
    preferred_missing = [s["name"] for s in preferred if s["name"].casefold() not in skills]
    coverage = (
        (
            100
            * sum(s["weight"] for s in required if s["name"] in matched)
            / sum(s["weight"] for s in required)
        )
        if required
        else None
    )
    required_names = {s["name"].casefold() for s in required}
    relevant = [
        e for e in parsed.get("experience", []) if required_names & {s.casefold() for s in e["skills"]}
    ]
    months = union_months([(e["start_month"], e["end_month"]) for e in relevant]) if relevant else None
    experience = (
        min(100, months / job.min_experience_months * 100)
        if months is not None and job.min_experience_months
        else None
    )
    education_text = parsed.get("education", "").casefold()
    education = None
    if job.education_requirement and education_text:
        # Deliberately conservative, no inferred equivalence between credentials.
        terms = re.findall(r"\w+", job.education_requirement.casefold())
        education = 100.0 if all(re.search(rf"\b{re.escape(t)}\b", education_text) for t in terms) else None
    components = {
        "semantic_relevance": round(semantic, 2),
        "required_skills": coverage,
        "experience": experience,
        "education": education,
    }
    conf = settings()
    weights = dict(
        zip(
            components,
            [conf.semantic_weight, conf.skills_weight, conf.experience_weight, conf.education_weight],
            strict=True,
        )
    )
    active = sum(weights[key] for key, value in components.items() if value is not None)
    if active <= 0:
        raise ValueError("NO_ACTIVE_SCORING_COMPONENTS")
    effective = {
        key: weight / active if components[key] is not None else 0 for key, weight in weights.items()
    }
    score = sum((value or 0) * effective[key] for key, value in components.items())
    uncertainty = list(parsed.get("uncertainties", []))
    if job.min_experience_months and months is None:
        uncertainty.append("Relevant dated experience could not be established; experience score omitted.")
    if job.education_requirement and education is None:
        uncertainty.append(
            "Education requirement not established; credential equivalence requires human review."
        )
    return {
        "compatibility_index": round(score, 2),
        "score_type": "heuristic_relevance_index",
        "score_breakdown": {k: round(v, 2) if v is not None else None for k, v in components.items()},
        "configured_weights": weights,
        "effective_weights": effective,
        "matched_skills": matched,
        "not_documented_required_skills": missing,
        "not_documented_preferred_skills": preferred_missing,
        "evidence": [skills[s.casefold()] for s in matched],
        "relevant_experience_months": months,
        "experience_evidence": relevant,
        "education_evidence": parsed.get("education", ""),
        "uncertainties": uncertainty,
        "recommendations": [
            {
                "skill": skill,
                "action": f"If you have used {skill}, add a concrete project or work example. Otherwise, learn the fundamentals and build a small demonstrable project.",
                "url": RESOURCES.get(skill),
            }
            for skill in missing + preferred_missing
        ],
        "scoring_version": "hybrid-1.0-"
        + hashlib.sha256(json.dumps(weights, sort_keys=True).encode()).hexdigest()[:10],
        "disclaimer": DISCLAIMER,
    }

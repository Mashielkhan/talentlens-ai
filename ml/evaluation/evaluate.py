"""Measured synthetic sanity evaluation. Not a hiring validity or fairness study."""

import argparse
import json
import platform
import time
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from app.ml.embeddings import embed_sections, model_version, semantic_score
from app.ml.scoring import score_match
from app.nlp.parser import parse_resume, qualification_texts
from sklearn.metrics import ndcg_score

ROOT = Path(__file__).resolve().parents[2]


def retrieval_metrics(grades, scores, k=3):
    order = np.argsort(-np.asarray(scores), kind="stable")
    relevant = np.asarray(grades) >= 2
    hits = relevant[order[:k]].sum()
    first = np.flatnonzero(relevant[order])
    return {
        "precision_at_3": float(hits / k),
        "recall_at_3": float(hits / max(1, relevant.sum())),
        "mrr": float(1 / (first[0] + 1)) if first.size else 0.0,
        "ndcg_at_3": float(ndcg_score([grades], [scores], k=k)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cross-encoder",
        default=None,
        help="Optional model ID; downloads and measures actual inference",
    )
    parser.add_argument(
        "--cross-revision",
        default=None,
        help="Required immutable commit SHA for optional cross-encoder",
    )
    args = parser.parse_args()
    data = json.loads((ROOT / "ml/datasets/generated/annotations.json").read_text())
    jobs = json.loads((ROOT / "ml/datasets/generated/jobs.json").read_text())
    started = time.perf_counter()
    profiles = [parse_resume(d["text"], today=date(2026, 1, 1)) for d in data]
    parse_seconds = time.perf_counter() - started
    tp = fp = fn = 0
    for profile, annotation in zip(profiles, data, strict=True):
        predicted = {s["name"] for s in profile["skills"]}
        gold = set(annotation["gold_skills"])
        tp += len(predicted & gold)
        fp += len(predicted - gold)
        fn += len(gold - predicted)
    started = time.perf_counter()
    vectors = [
        [v for _, _, v in embed_sections(qualification_texts(p))] for p in profiles
    ]
    embedding_seconds = time.perf_counter() - started
    rows, per_job = [], []
    cross = None
    if args.cross_encoder:
        if not args.cross_revision:
            raise SystemExit("Supply --cross-revision with an immutable model commit")
        from sentence_transformers import CrossEncoder

        cross = CrossEncoder(
            args.cross_encoder,
            revision=args.cross_revision,
            device="cpu",
            trust_remote_code=False,
        )
    for j, job in enumerate(jobs):
        start = time.perf_counter()
        jvectors = [
            v
            for _, _, v in embed_sections(
                {
                    "description": job["description"],
                    "required": ", ".join(s["name"] for s in job["required_skills"]),
                    "preferred": ", ".join(s["name"] for s in job["preferred_skills"]),
                }
            )
        ]
        scores = {
            "keyword": [],
            "semantic": [],
            "hybrid": [],
            "semantic_skills": [],
            "semantic_skills_experience": [],
        }
        for i, (profile, vector) in enumerate(zip(profiles, vectors, strict=True)):
            semantic = semantic_score(vector, jvectors)
            hybrid = score_match(profile, SimpleNamespace(**job), semantic)
            skills = hybrid["score_breakdown"]["required_skills"] or 0
            experience = hybrid["score_breakdown"]["experience"]
            scores["keyword"].append(skills)
            scores["semantic"].append(semantic)
            scores["hybrid"].append(hybrid["compatibility_index"])
            scores["semantic_skills"].append(0.6 * semantic + 0.4 * skills)
            scores["semantic_skills_experience"].append(
                (
                    0.45 * semantic
                    + 0.3 * skills
                    + (0.15 * experience if experience is not None else 0)
                )
                / (0.9 if experience is not None else 0.75)
            )
            rows.append(
                {
                    "job": j,
                    "resume": data[i]["id"],
                    "grade": data[i]["relevance"][j],
                    "semantic": semantic,
                    "hybrid": hybrid["compatibility_index"],
                    "keyword": skills,
                }
            )
        latency = time.perf_counter() - start
        if cross:
            start = time.perf_counter()
            # Top-10 experimental rerank only; unselected documents retain their order.
            shortlist = np.argsort(-np.asarray(scores["hybrid"]))[:10]
            pairs = [
                (
                    job["description"],
                    "\n".join(qualification_texts(profiles[i]).values()),
                )
                for i in shortlist
            ]
            logits = cross.predict(pairs).tolist()
            ordered = sorted(
                zip(shortlist.tolist(), logits, strict=True),
                key=lambda x: x[1],
                reverse=True,
            )
            cross_scores = np.asarray(scores["hybrid"]) / 1000
            for position, (i, _) in enumerate(ordered):
                cross_scores[i] = 100 - position
            scores["cross_encoder_top10"] = cross_scores.tolist()
            cross_latency = time.perf_counter() - start
        else:
            cross_latency = None
        grades = [d["relevance"][j] for d in data]
        per_job.append(
            {
                "job": job["title"],
                "hybrid_seconds": latency,
                "cross_encoder_seconds": cross_latency,
                "metrics": {
                    name: retrieval_metrics(grades, value)
                    for name, value in scores.items()
                },
            }
        )
    precision, recall = tp / max(1, tp + fp), tp / max(1, tp + fn)
    report = {
        "scope": "20 original synthetic documents / 5 synthetic roles; developer-authored labels; smoke evaluation, not external validation",
        "model": model_version(),
        "platform": platform.platform(),
        "as_of_date": "2026-01-01",
        "skills": {
            "precision": precision,
            "recall": recall,
            "f1": 2 * precision * recall / max(1e-12, precision + recall),
        },
        "email_exact_accuracy": sum(
            p["contact"]["email"] == d["gold_email"]
            for p, d in zip(profiles, data, strict=True)
        )
        / len(data),
        "parsing_seconds": parse_seconds,
        "embedding_seconds": embedding_seconds,
        "jobs": per_job,
        "cross_encoder": args.cross_encoder,
        "cross_revision": args.cross_revision,
    }
    output = ROOT / "ml/results"
    output.mkdir(exist_ok=True)
    (output / "synthetic-evaluation.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    pd.DataFrame(rows).to_csv(output / "synthetic-rankings.csv", index=False)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

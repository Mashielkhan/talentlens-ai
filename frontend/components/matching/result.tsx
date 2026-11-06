"use client";
import { Download, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Match } from "@/types/api";
export function MatchView({ match }: { match: Match }) {
  return (
    <div className="stack">
      <section className="panel">
        <div className="row between">
          <div className="row">
            <span className="score">{Math.round(match.compatibility_index)}</span>
            <div>
              <h2 className="mb-1">Compatibility Index</h2>
              <p className="muted text-xs mb-0">
                {match.resume_filename} · {match.job_title}
              </p>
            </div>
          </div>
          <Button asChild variant="outline">
            <a href={`/api/v1/reports/${match.id}/export`}>
              <Download size={15} />
              Download PDF
            </a>
          </Button>
        </div>
        <div className="notice mt-5">{match.disclaimer}</div>
      </section>
      <div className="grid-2">
        <section className="panel">
          <h2>What goes into this score</h2>
          <div className="breakdown">
            {Object.entries(match.score_breakdown).map(([key, value]) => (
              <div key={key}>
                <div className="metric-label">
                  <span className="capitalize">{key.replaceAll("_", " ")}</span>
                  <strong>{value === null ? "Unknown / not applicable" : `${value.toFixed(1)} / 100`}</strong>
                </div>
                <div className="bar">
                  <span style={{ width: `${value || 0}%` }} />
                </div>
                <p className="muted text-[10px] mt-1 mb-0">
                  Effective weight: {(match.effective_weights[key] * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
          <p className="muted text-xs mt-5 mb-0">
            Unknown components are omitted and remaining weights are normalized. Compare the evidence
            alongside the index.
          </p>
        </section>
        <section className="panel">
          <h2>Qualification evidence</h2>
          <h3 className="muted text-xs">Documented required skills</h3>
          <div className="row">
            {match.matched_skills.map((s) => (
              <span className="pill green" key={s}>
                {s}
              </span>
            ))}
            {!match.matched_skills.length && (
              <span className="muted text-xs">No required skill matches documented.</span>
            )}
          </div>
          <h3 className="muted text-xs mt-6">Required skills not documented</h3>
          <div className="row">
            {match.not_documented_required_skills.map((s) => (
              <span className="pill amber" key={s}>
                {s}
              </span>
            ))}
            {!match.not_documented_required_skills.length && (
              <span className="muted text-xs">No undocumented required skills.</span>
            )}
          </div>
          <h3 className="muted text-xs mt-6">Preferred skills not documented</h3>
          <div className="row">
            {match.not_documented_preferred_skills.map((s) => (
              <span className="pill" key={s}>
                {s}
              </span>
            ))}
          </div>
          <p className="muted text-xs mt-6 mb-0">
            Relevant dated experience:{" "}
            {match.relevant_experience_months === null
              ? "Not established"
              : `${match.relevant_experience_months} months`}
          </p>
        </section>
      </div>
      <section className="panel">
        <h2>The evidence behind the match</h2>
        {match.evidence.map((s) => (
          <div className="evidence" key={s.name}>
            <strong>
              {s.name} · {s.source_section}
            </strong>
            <p>{s.evidence}</p>
          </div>
        ))}
        {match.education_evidence && (
          <div className="evidence">
            <strong>Education as documented</strong>
            <p>{match.education_evidence}</p>
          </div>
        )}
      </section>
      <section className="panel">
        <h2>What to demonstrate or develop next</h2>
        {match.recommendations.length ? (
          match.recommendations.map((r, i) => (
            <div className="step" key={r.skill}>
              <span className="step-index">{i + 1}</span>
              <div>
                <strong>{r.skill}</strong>
                <p>{r.action}</p>
                {r.url && (
                  <a className="text-link" href={r.url} target="_blank" rel="noreferrer">
                    Official learning resource <ExternalLink size={11} className="inline" />
                  </a>
                )}
              </div>
            </div>
          ))
        ) : (
          <p className="muted text-xs">
            All listed skills have supporting mentions. Review depth, recency, and project evidence with a
            human reviewer.
          </p>
        )}
      </section>
      <section className="panel">
        <h2>Uncertainty & reproducibility</h2>
        {match.uncertainties.map((u) => (
          <p key={u} className="text-xs muted">
            {u}
          </p>
        ))}
        <p className="text-[10px] muted break-all mb-0">
          Model: {match.model_version}
          <br />
          Scoring: {match.scoring_version}
          <br />
          Experience calculated as of {match.as_of_date} · Analysis{" "}
          {new Date(match.created_at).toLocaleString()}
        </p>
      </section>
    </div>
  );
}

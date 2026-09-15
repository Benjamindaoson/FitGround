"use client";

import { useEffect, useMemo, useState } from "react";

type Candidate = {
  action_id: string;
  family?: string;
  intended_delta_cm?: number | null;
  realized_delta_cm?: number | null;
  target_error_cm?: number | null;
  utility?: number | null;
  recommended?: boolean;
  simulation_status?: string;
  note?: string;
  side_effects?: Record<string, number>;
};

type PhysicsRow = {
  tag: string;
  label: string;
  clearance_p10_cm: number;
  contact_ratio: number;
  chest_clearance_p10_cm: number;
  wrinkle_proxy_cm: number;
  render: string;
};

type Overlay = {
  recommendation?: {
    action_id: string;
    summary: string;
    confidence: number;
    abstain: boolean;
    alternatives: string[];
    why_not_plus2: string;
  };
};

type Workspace = {
  tagline: string;
  current_sample: Record<string, unknown>;
  physics_outcomes: PhysicsRow[];
  hypotheses: { id: string; text: string; support: string; confidence: number }[];
  candidates: Candidate[];
  recommendation: {
    action_id: string;
    summary: string;
    confidence: number;
    abstain: boolean;
    alternatives: string[];
    why_not_plus2: string;
  };
  hero_cases: { id: string; title: string; problem: string; best: string; evidence: string; abstain?: boolean }[];
  metrics: Record<string, number | string>;
  audit: Record<string, unknown>;
  case_overlays?: Record<string, Overlay>;
  visual_disambiguation?: { verdict?: string; n_pairs?: number; n_vision_needed?: number };
};

function fmt(value: unknown, digits = 2) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toFixed(digits);
  return String(value);
}

export default function WorkspacePage() {
  const [data, setData] = useState<Workspace | null>(null);
  const [caseId, setCaseId] = useState("case-1-chest-tight");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/data/workspace.json")
      .then((r) => {
        if (!r.ok) throw new Error(`workspace.json ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const selectedCase = useMemo(
    () => data?.hero_cases.find((c) => c.id === caseId) ?? data?.hero_cases[0],
    [data, caseId]
  );

  if (error) {
    return (
      <main className="p-8">
        <h1 className="text-2xl">FitGround workspace failed to load</h1>
        <p className="mono mt-2 text-sm">{error}</p>
      </main>
    );
  }
  if (!data) {
    return (
      <main className="p-8">
        <p className="mono text-sm tracking-widest">LOADING EVIDENCE…</p>
      </main>
    );
  }

  const sample = data.current_sample;
  const overlay = data.case_overlays?.[caseId];
  const recommendation = overlay?.recommendation ?? data.recommendation;
  const rec = data.candidates.find((c) => c.recommended) ?? data.candidates[0];
  const abstain = Boolean(recommendation.abstain || selectedCase?.abstain);

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d8d0c4] px-6 py-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mono text-[11px] tracking-[0.25em] text-[#b4472a]">FITGROUND · TECHNICAL DESIGNER</p>
          <h1 className="text-3xl md:text-4xl leading-tight mt-1">What should change in the next sample?</h1>
          <p className="mt-1 text-sm opacity-70">{data.tagline} Counterfactual correction, not virtual try-on.</p>
        </div>
        <div className="mono text-xs text-right">
          <div>body collision: SYNTHETIC OBJ</div>
          <div>SMPL-X weights: ABSENT</div>
          <div>realized Δ: measured panels</div>
        </div>
      </header>

      <section className="px-6 py-4 border-b border-[#d8d0c4] flex gap-2 overflow-x-auto">
        {data.hero_cases.map((c) => (
          <button
            key={c.id}
            onClick={() => setCaseId(c.id)}
            className={`mono text-[11px] px-3 py-2 border whitespace-nowrap ${
              selectedCase?.id === c.id ? "bg-[#1c1915] text-[#f4efe6] border-[#1c1915]" : "border-[#d8d0c4]"
            }`}
          >
            {c.title}
          </button>
        ))}
      </section>

      <div className="grid lg:grid-cols-12 gap-0">
        <section className="lg:col-span-5 border-r border-[#d8d0c4] p-6">
          <h2 className="mono text-[11px] tracking-[0.2em]">01 · CURRENT SAMPLE</h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {data.physics_outcomes.slice(0, 2).map((row) => (
              <figure key={row.tag} className="border border-[#d8d0c4] bg-white">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={row.render} alt={row.label} className="w-full aspect-[3/4] object-cover" />
                <figcaption className="mono text-[10px] p-2">
                  {row.label} · contact {fmt(row.contact_ratio, 3)} · chest p10 {fmt(row.chest_clearance_p10_cm, 3)} cm
                </figcaption>
              </figure>
            ))}
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="opacity-60">Body bust</dt>
            <dd className="mono">{fmt(sample.body_bust_cm)} cm</dd>
            <dt className="opacity-60">Garment bust</dt>
            <dd className="mono">{fmt(sample.baseline_garment_bust_cm)} cm</dd>
            <dt className="opacity-60">Target bust</dt>
            <dd className="mono">{fmt(sample.target_garment_bust_cm)} cm</dd>
            <dt className="opacity-60">Fit intent</dt>
            <dd>{String(sample.fit_intent)}</dd>
            <dt className="opacity-60">Material</dt>
            <dd className="text-xs">{String(sample.material)}</dd>
          </dl>
          <div className="mt-4">
            <h3 className="mono text-[11px] tracking-[0.2em]">REGIONAL FIT</h3>
            <ul className="mt-2 text-sm space-y-1">
              {Object.entries((sample.region_fit_state as Record<string, string>) || {}).map(([k, v]) => (
                <li key={k}>
                  <span className="mono text-[11px] uppercase">{k}</span> — {v}
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="lg:col-span-4 border-r border-[#d8d0c4] p-6">
          <h2 className="mono text-[11px] tracking-[0.2em]">02 · CAUSE & CANDIDATES</h2>
          <ol className="mt-3 space-y-3">
            {data.hypotheses.map((h) => (
              <li key={h.id} className="border border-[#d8d0c4] p-3 bg-white/50">
                <div className="flex justify-between mono text-[11px]">
                  <span>{h.id}</span>
                  <span>conf {fmt(h.confidence)}</span>
                </div>
                <p className="mt-1 text-sm">{h.text}</p>
                <p className="mt-1 text-xs opacity-70">{h.support}</p>
              </li>
            ))}
          </ol>
          <table className="mt-5 w-full text-left text-sm">
            <thead className="mono text-[10px] tracking-widest opacity-60">
              <tr>
                <th className="py-1">Action</th>
                <th>Intended</th>
                <th>Realized</th>
                <th>Utility</th>
              </tr>
            </thead>
            <tbody>
              {data.candidates.map((c) => (
                <tr key={c.action_id} className={c.recommended ? "bg-[#e7efe8]" : ""}>
                  <td className="py-1.5 pr-2 mono text-[11px]">{c.action_id}</td>
                  <td>{fmt(c.intended_delta_cm)}</td>
                  <td>{fmt(c.realized_delta_cm)}</td>
                  <td>{fmt(c.utility, 3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="lg:col-span-3 p-6">
          <h2 className="mono text-[11px] tracking-[0.2em]">03 · RECOMMENDATION</h2>
          <div className={`mt-3 border p-4 ${abstain ? "border-[#b4472a] bg-[#f8e6e0]" : "border-[#2f6b4f] bg-[#e7efe8]"}`}>
            <p className={`mono text-[11px] ${abstain ? "text-[#b4472a]" : "text-[#2f6b4f]"}`}>
              {abstain ? "NO RECOMMENDATION — ESCALATE" : "NEXT SAMPLE"}
            </p>
            <p className="text-2xl mt-1">{recommendation.action_id}</p>
            <p className="text-sm mt-2">{recommendation.summary}</p>
            <p className="mono text-xs mt-3">
              confidence {fmt(recommendation.confidence)} · abstain {String(recommendation.abstain)}
            </p>
          </div>
          <p className="text-xs mt-3 opacity-70">{recommendation.why_not_plus2}</p>
          <h3 className="mono text-[11px] tracking-[0.2em] mt-6">COUNTERFACTUAL PREVIEW</h3>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {data.physics_outcomes
              .filter((p) => p.tag === "baseline" || p.tag === rec?.action_id)
              .map((row) => (
                <figure key={row.tag} className="border border-[#d8d0c4] bg-white">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={row.render} alt={row.label} className="w-full aspect-[3/4] object-cover" />
                  <figcaption className="mono text-[10px] p-1">{row.label}</figcaption>
                </figure>
              ))}
          </div>
          <h3 className="mono text-[11px] tracking-[0.2em] mt-6">AUDIT / PROVENANCE</h3>
          <ul className="mt-2 mono text-[11px] space-y-1">
            <li>realized source: {String(data.audit.realized_source)}</li>
            <li>geometry: {String(data.audit.parametric_garment_geometry ?? "PASS")}</li>
            <li>synthetic physics: {String(data.audit.synthetic_body_physics ?? "PASS")}</li>
            <li>SMPL-X: {String(data.audit.smpl_x_weights)}</li>
            <li>real-human: {String(data.audit.real_human_validation ?? "HARD_BLOCKED_LICENSE")}</li>
            <li>collision: {String(data.audit.body_collision)}</li>
            <li>vision: {String(data.visual_disambiguation?.verdict ?? "—")}</li>
          </ul>
        </section>
      </div>

      <section className="border-t border-[#d8d0c4] p-6 grid md:grid-cols-2 gap-6">
        <div>
          <h2 className="mono text-[11px] tracking-[0.2em]">04 · ACTIVE HERO CASE</h2>
          {selectedCase && (
            <div className="mt-3">
              <h3 className="text-xl">{selectedCase.title}</h3>
              <p className="mt-2 text-sm">{selectedCase.problem}</p>
              <p className="mt-2 text-sm">
                <span className="mono text-[11px]">BEST</span> {selectedCase.best}
              </p>
              <p className="mt-2 text-xs opacity-70">{selectedCase.evidence}</p>
            </div>
          )}
        </div>
        <div>
          <h2 className="mono text-[11px] tracking-[0.2em]">05 · EXPERIMENT PANEL</h2>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            {Object.entries(data.metrics).map(([k, v]) => (
              <div key={k} className="border border-[#d8d0c4] p-2">
                <dt className="mono text-[10px] opacity-60">{k}</dt>
                <dd>{String(v)}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-xs opacity-70">
            Observational B0/B1 are not intervention GT. Pattern Ridge beats the CNN on 192 drawings. Decision SFT
            1.0 is n=3. RLVR added no holdout gain.
          </p>
        </div>
      </section>
    </main>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";

type Lang = "zh" | "en";

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

type HeroCase = {
  id: string;
  title: string;
  problem: string;
  best: string;
  evidence: string;
  abstain?: boolean;
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
  hero_cases: HeroCase[];
  metrics: Record<string, number | string>;
  audit: Record<string, unknown>;
  case_overlays?: Record<string, Overlay>;
  visual_disambiguation?: { verdict?: string; n_pairs?: number; n_vision_needed?: number };
};

const COPY = {
  zh: {
    kicker: "FITGROUND · 技术设计师",
    title: "下一版样衣该改什么？",
    subtitle: "反事实修正，不是虚拟试穿。",
    collision: "碰撞体：合成 OBJ 人台",
    smpl: "SMPL-X 权重：缺失",
    realized: "realized Δ：实测面板",
    loading: "正在载入证据…",
    loadFail: "FitGround 工作台载入失败",
    current: "01 · 当前样衣",
    contact: "接触",
    chestP10: "胸围 p10",
    bodyBust: "人体胸围",
    garmentBust: "衣服胸围",
    targetBust: "目标胸围",
    fitIntent: "合体意图",
    material: "面料",
    regional: "分区合体",
    cause: "02 · 原因与候选",
    conf: "置信",
    action: "动作",
    intended: "intended",
    realizedCol: "realized",
    utility: "效用",
    rec: "03 · 建议",
    noRec: "不给建议 — 升级人工",
    nextSample: "下一版样衣",
    confidence: "置信度",
    abstain: "拒答",
    preview: "反事实预览",
    audit: "审计 / 出处",
    realizedSource: "realized 来源",
    geometry: "几何",
    synthPhys: "合成物理",
    realHuman: "真人",
    collisionShort: "碰撞",
    vision: "视觉",
    hero: "04 · 当前 Hero Case",
    best: "最优",
    panel: "05 · 实验面板",
    footnote:
      "观测 B0/B1 不是干预真值。192 张纸样图上 Ridge 打过 CNN。Decision SFT 的 1.0 是 n=3。RLVR 没有 holdout 增益。",
    cases: {
      "case-1-chest-tight": {
        title: "胸口过紧 → 胸围 +3 cm",
        problem: "当前样衣胸口过紧。在 ±3 cm 格子上，实测胸围 +3 cm 与 intended 一致，效用最高。",
      },
      "case-2-same-meas-material": {
        title: "同尺寸、不同面料弯曲",
        problem: "二维规格相同，弯曲刚度不同。default 不必改；stiff 更倾向 bust+2cm。视觉必要性仍未统计成立。",
      },
      "case-3-waist-side-effect": {
        title: "副作用定价：更小的胸围修改可以赢",
        problem: "flare=1 的 Shirt 上，改胸围会 100% 带动腰围。效用函数给副作用定价后，更大的刀不一定更好。",
      },
      "case-4-ood-body": {
        title: "OOD 人台 → 拒答",
        problem: "合成人体 OOD。几何映射仍准，但策略拒答。这不是真人泛化。",
      },
      "case-5-shoulder-vs-bust": {
        title: "肩 vs 胸：肩宽没有独立自由度",
        problem: "当前 Shirt 家族没有独立肩宽参数。connecting_width 会带动袖长。正式 NO-GO。",
      },
    } as Record<string, { title: string; problem: string }>,
  },
  en: {
    kicker: "FITGROUND · TECHNICAL DESIGNER",
    title: "What should change in the next sample?",
    subtitle: "Counterfactual correction, not virtual try-on.",
    collision: "body collision: SYNTHETIC OBJ",
    smpl: "SMPL-X weights: ABSENT",
    realized: "realized Δ: measured panels",
    loading: "LOADING EVIDENCE…",
    loadFail: "FitGround workspace failed to load",
    current: "01 · CURRENT SAMPLE",
    contact: "contact",
    chestP10: "chest p10",
    bodyBust: "Body bust",
    garmentBust: "Garment bust",
    targetBust: "Target bust",
    fitIntent: "Fit intent",
    material: "Material",
    regional: "REGIONAL FIT",
    cause: "02 · CAUSE & CANDIDATES",
    conf: "conf",
    action: "Action",
    intended: "Intended",
    realizedCol: "Realized",
    utility: "Utility",
    rec: "03 · RECOMMENDATION",
    noRec: "NO RECOMMENDATION — ESCALATE",
    nextSample: "NEXT SAMPLE",
    confidence: "confidence",
    abstain: "abstain",
    preview: "COUNTERFACTUAL PREVIEW",
    audit: "AUDIT / PROVENANCE",
    realizedSource: "realized source",
    geometry: "geometry",
    synthPhys: "synthetic physics",
    realHuman: "real-human",
    collisionShort: "collision",
    vision: "vision",
    hero: "04 · ACTIVE HERO CASE",
    best: "BEST",
    panel: "05 · EXPERIMENT PANEL",
    footnote:
      "Observational B0/B1 are not intervention GT. Pattern Ridge beats the CNN on 192 drawings. Decision SFT 1.0 is n=3. RLVR added no holdout gain.",
    cases: {
      "case-1-chest-tight": {
        title: "Chest too tight → Bust +3 cm",
        problem: "Chest too tight. On the ±3 cm lattice, measured bust +3 cm matches intended and ranks highest.",
      },
      "case-2-same-meas-material": {
        title: "Same measurements, different cloth bending",
        problem: "Same 2D spec, different bending stiffness. Default needs no edit; stiff leans bust+2cm. Vision necessity is still not statistically established.",
      },
      "case-3-waist-side-effect": {
        title: "Side-effect priced in: smaller bust edit can win",
        problem: "On a flare=1 Shirt, a bust edit always moves the waist. Once side effects are priced, the largest cut is not automatically best.",
      },
      "case-4-ood-body": {
        title: "OOD body → abstain",
        problem: "SYNTHETIC_BODY_OOD. The geometry map is still exact, but the policy refuses. Not real-human generalization.",
      },
      "case-5-shoulder-vs-bust": {
        title: "Bust vs shoulder: shoulder has no independent DoF",
        problem: "This Shirt family has no independent shoulder parameter. connecting_width moves sleeve length. Official NO-GO.",
      },
    } as Record<string, { title: string; problem: string }>,
  },
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
  const [lang, setLang] = useState<Lang>("zh");

  useEffect(() => {
    const stored = window.localStorage.getItem("fitground-lang");
    if (stored === "en" || stored === "zh") setLang(stored);
  }, []);

  useEffect(() => {
    document.documentElement.lang = lang;
    window.localStorage.setItem("fitground-lang", lang);
  }, [lang]);

  useEffect(() => {
    fetch("/data/workspace.json")
      .then((r) => {
        if (!r.ok) throw new Error(`workspace.json ${r.status}`);
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(String(e)));
  }, []);

  const t = COPY[lang];
  const selectedCase = useMemo(
    () => data?.hero_cases.find((c) => c.id === caseId) ?? data?.hero_cases[0],
    [data, caseId]
  );

  if (error) {
    return (
      <main className="p-8">
        <h1 className="text-2xl">{t.loadFail}</h1>
        <p className="mono mt-2 text-sm">{error}</p>
      </main>
    );
  }
  if (!data) {
    return (
      <main className="p-8">
        <p className="mono text-sm tracking-widest">{t.loading}</p>
      </main>
    );
  }

  const sample = data.current_sample;
  const overlay = data.case_overlays?.[caseId];
  const recommendation = overlay?.recommendation ?? data.recommendation;
  const rec = data.candidates.find((c) => c.recommended) ?? data.candidates[0];
  const abstain = Boolean(recommendation.abstain || selectedCase?.abstain);
  const caseCopy = selectedCase ? t.cases[selectedCase.id] : undefined;

  return (
    <main className="min-h-screen">
      <header className="border-b border-[#d8d0c4] px-6 py-4 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="mono text-[11px] tracking-[0.25em] text-[#b4472a]">{t.kicker}</p>
          <h1 className="text-3xl md:text-4xl leading-tight mt-1">{t.title}</h1>
          <p className="mt-1 text-sm opacity-70">{t.subtitle}</p>
        </div>
        <div className="flex flex-col items-end gap-3">
          <div className="inline-flex border border-[#d8d0c4] overflow-hidden" role="group" aria-label="Language">
            <button
              type="button"
              onClick={() => setLang("zh")}
              className={`mono text-[11px] px-3 py-1 ${lang === "zh" ? "bg-[#1c1915] text-[#f4efe6]" : "bg-transparent"}`}
            >
              中文
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              className={`mono text-[11px] px-3 py-1 ${lang === "en" ? "bg-[#1c1915] text-[#f4efe6]" : "bg-transparent"}`}
            >
              English
            </button>
          </div>
          <div className="mono text-xs text-right">
            <div>{t.collision}</div>
            <div>{t.smpl}</div>
            <div>{t.realized}</div>
          </div>
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
            {t.cases[c.id]?.title ?? c.title}
          </button>
        ))}
      </section>

      <div className="grid lg:grid-cols-12 gap-0">
        <section className="lg:col-span-5 border-r border-[#d8d0c4] p-6">
          <h2 className="mono text-[11px] tracking-[0.2em]">{t.current}</h2>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {data.physics_outcomes.slice(0, 2).map((row) => (
              <figure key={row.tag} className="border border-[#d8d0c4] bg-white">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={row.render} alt={row.label} className="w-full aspect-[3/4] object-cover" />
                <figcaption className="mono text-[10px] p-2">
                  {row.label} · {t.contact} {fmt(row.contact_ratio, 3)} · {t.chestP10} {fmt(row.chest_clearance_p10_cm, 3)} cm
                </figcaption>
              </figure>
            ))}
          </div>
          <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <dt className="opacity-60">{t.bodyBust}</dt>
            <dd className="mono">{fmt(sample.body_bust_cm)} cm</dd>
            <dt className="opacity-60">{t.garmentBust}</dt>
            <dd className="mono">{fmt(sample.baseline_garment_bust_cm)} cm</dd>
            <dt className="opacity-60">{t.targetBust}</dt>
            <dd className="mono">{fmt(sample.target_garment_bust_cm)} cm</dd>
            <dt className="opacity-60">{t.fitIntent}</dt>
            <dd>{String(sample.fit_intent)}</dd>
            <dt className="opacity-60">{t.material}</dt>
            <dd className="text-xs">{String(sample.material)}</dd>
          </dl>
          <div className="mt-4">
            <h3 className="mono text-[11px] tracking-[0.2em]">{t.regional}</h3>
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
          <h2 className="mono text-[11px] tracking-[0.2em]">{t.cause}</h2>
          <ol className="mt-3 space-y-3">
            {data.hypotheses.map((h) => (
              <li key={h.id} className="border border-[#d8d0c4] p-3 bg-white/50">
                <div className="flex justify-between mono text-[11px]">
                  <span>{h.id}</span>
                  <span>
                    {t.conf} {fmt(h.confidence)}
                  </span>
                </div>
                <p className="mt-1 text-sm">{h.text}</p>
                <p className="mt-1 text-xs opacity-70">{h.support}</p>
              </li>
            ))}
          </ol>
          <table className="mt-5 w-full text-left text-sm">
            <thead className="mono text-[10px] tracking-widest opacity-60">
              <tr>
                <th className="py-1">{t.action}</th>
                <th>{t.intended}</th>
                <th>{t.realizedCol}</th>
                <th>{t.utility}</th>
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
          <h2 className="mono text-[11px] tracking-[0.2em]">{t.rec}</h2>
          <div className={`mt-3 border p-4 ${abstain ? "border-[#b4472a] bg-[#f8e6e0]" : "border-[#2f6b4f] bg-[#e7efe8]"}`}>
            <p className={`mono text-[11px] ${abstain ? "text-[#b4472a]" : "text-[#2f6b4f]"}`}>
              {abstain ? t.noRec : t.nextSample}
            </p>
            <p className="text-2xl mt-1">{recommendation.action_id}</p>
            <p className="text-sm mt-2">{recommendation.summary}</p>
            <p className="mono text-xs mt-3">
              {t.confidence} {fmt(recommendation.confidence)} · {t.abstain} {String(recommendation.abstain)}
            </p>
          </div>
          <p className="text-xs mt-3 opacity-70">{recommendation.why_not_plus2}</p>
          <h3 className="mono text-[11px] tracking-[0.2em] mt-6">{t.preview}</h3>
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
          <h3 className="mono text-[11px] tracking-[0.2em] mt-6">{t.audit}</h3>
          <ul className="mt-2 mono text-[11px] space-y-1">
            <li>
              {t.realizedSource}: {String(data.audit.realized_source)}
            </li>
            <li>
              {t.geometry}: {String(data.audit.parametric_garment_geometry ?? "PASS")}
            </li>
            <li>
              {t.synthPhys}: {String(data.audit.synthetic_body_physics ?? "PASS")}
            </li>
            <li>
              SMPL-X: {String(data.audit.smpl_x_weights)}
            </li>
            <li>
              {t.realHuman}: {String(data.audit.real_human_validation ?? "HARD_BLOCKED_LICENSE")}
            </li>
            <li>
              {t.collisionShort}: {String(data.audit.body_collision)}
            </li>
            <li>
              {t.vision}: {String(data.visual_disambiguation?.verdict ?? "—")}
            </li>
          </ul>
        </section>
      </div>

      <section className="border-t border-[#d8d0c4] p-6 grid md:grid-cols-2 gap-6">
        <div>
          <h2 className="mono text-[11px] tracking-[0.2em]">{t.hero}</h2>
          {selectedCase && (
            <div className="mt-3">
              <h3 className="text-xl">{caseCopy?.title ?? selectedCase.title}</h3>
              <p className="mt-2 text-sm">{caseCopy?.problem ?? selectedCase.problem}</p>
              <p className="mt-2 text-sm">
                <span className="mono text-[11px]">{t.best}</span> {selectedCase.best}
              </p>
              <p className="mt-2 text-xs opacity-70">{selectedCase.evidence}</p>
            </div>
          )}
        </div>
        <div>
          <h2 className="mono text-[11px] tracking-[0.2em]">{t.panel}</h2>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            {Object.entries(data.metrics).map(([k, v]) => (
              <div key={k} className="border border-[#d8d0c4] p-2">
                <dt className="mono text-[10px] opacity-60">{k}</dt>
                <dd>{String(v)}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-3 text-xs opacity-70">{t.footnote}</p>
        </div>
      </section>
    </main>
  );
}

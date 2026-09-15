#!/usr/bin/env python3
"""Story diagrams for the FitGround README. No GPU required."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIGURES = ROOT / "reports" / "figures"
FIG_FINAL = FIGURES / "final"

INK = "#1c1915"
PAPER = "#f4efe6"
PANEL = "#fbf7f0"
GREEN = "#e7efe8"
GREEN_LINE = "#2f6b4f"
RED = "#f8e6e0"
RED_LINE = "#b4472a"
AMBER = "#f4ead4"
AMBER_LINE = "#9a6b12"
BLUE = "#e8eef4"
BLUE_LINE = "#3d5a73"
RULE = "#d8d0c4"


def _font():
    plt.rcParams.update(
        {
            "font.sans-serif": ["WenQuanYi Micro Hei", "Droid Sans Fallback", "DejaVu Sans"],
            "font.family": "sans-serif",
            "axes.unicode_minus": False,
            "figure.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "figure.dpi": 160,
        }
    )


def _box(ax, x, y, w, h, fc, ec, lw=1.35, r=0.08):
    p = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle=f"round,pad=0.012,rounding_size={r}",
        facecolor=fc,
        edgecolor=ec,
        linewidth=lw,
        mutation_aspect=None,
        zorder=2,
    )
    ax.add_patch(p)
    return p


def _text(ax, x, y, s, size=9, weight="normal", color=INK, ha="center", va="center", **kw):
    ax.text(x, y, s, fontsize=size, fontweight=weight, color=color, ha=ha, va=va, zorder=3, **kw)


def _arrow(ax, x1, y1, x2, y2, color=INK, rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=12,
            lw=1.25,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            zorder=4,
        )
    )


def _save(fig, name: str):
    FIGURES.mkdir(parents=True, exist_ok=True)
    FIG_FINAL.mkdir(parents=True, exist_ok=True)
    for folder in (FIGURES, FIG_FINAL):
        fig.savefig(folder / name, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)


def draw_architecture(lang: str = "zh") -> None:
    zh = lang == "zh"
    fig, ax = plt.subplots(figsize=(15.2, 9.4))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 9.4)
    ax.axis("off")

    # Banner: business problem
    _box(ax, 0.25, 8.15, 14.7, 1.05, RED, RED_LINE, lw=1.8, r=0.06)
    if zh:
        _text(ax, 7.6, 8.82, "业务问题：打样循环太贵。发现「胸口紧」不值钱，下一刀往哪改才值钱。", size=13.5, weight="bold")
        _text(
            ax,
            7.6,
            8.42,
            "技术设计师要的不是好看，而是：改哪个具名纸样参数 · 改几厘米 · 腰/袖会不会坏 · 证据不够能不能拒答",
            size=9.5,
            color="#5a4038",
        )
    else:
        _text(ax, 7.6, 8.82, "Business problem: sample iteration is expensive. Seeing “tight” is cheap; the next cut is not.", size=13, weight="bold")
        _text(
            ax,
            7.6,
            8.42,
            "A technical designer needs: which named pattern parameter · how many cm · what else moves · permission to abstain",
            size=9.5,
            color="#5a4038",
        )

    # Left: wrong answers vs our question
    _box(ax, 0.25, 4.55, 3.55, 3.4, PANEL, RULE, r=0.06)
    _text(ax, 2.02, 7.68, "答错题的现有方案" if zh else "Products that answer the wrong question", size=10, weight="bold")
    wrong = (
        [
            ("虚拟试穿 / VTO", "回答：穿上好不好看"),
            ("VLM / Agent 评语", "回答：看起来有点紧"),
            ("历史样本回归", "回答：过去差多少 cm"),
            ("一上来就 MLLM+RL", "回答：模型很新"),
        ]
        if zh
        else [
            ("Virtual try-on", "Answers: does it look good?"),
            ("VLM / agent copy", "Answers: looks a bit tight"),
            ("Observational fit", "Answers: historically X cm"),
            ("MLLM + RL first", "Answers: the model is new"),
        ]
    )
    for i, (a, b) in enumerate(wrong):
        y = 7.22 - i * 0.62
        _box(ax, 0.42, y - 0.22, 3.2, 0.52, RED, RED_LINE, lw=1.0, r=0.05)
        _text(ax, 2.02, y + 0.05, a, size=8.4, weight="bold")
        _text(ax, 2.02, y - 0.14, b, size=7.4, color="#6a3a32")

    _box(ax, 0.25, 2.55, 3.55, 1.85, GREEN, GREEN_LINE, r=0.06)
    _text(ax, 2.02, 4.1, "FitGround 只回答一句" if zh else "FitGround answers one sentence", size=10, weight="bold", color=GREEN_LINE)
    _text(
        ax,
        2.02,
        3.35,
        "下一版样衣该改什么？\n改几厘米？别的地方\n会不会坏？"
        if zh
        else "What should change in\nthe next sample, by how\nmany centimetres?",
        size=11,
        weight="bold",
    )

    # Product layer
    _box(ax, 4.05, 7.35, 10.9, 0.68, INK, INK, r=0.05)
    _text(
        ax,
        9.5,
        7.69,
        "产品层   技术设计师工作台  Next.js :43187    推荐 / 拒答 / 出处审计"
        if zh
        else "Product    Technical-designer workspace  Next.js :43187    recommend / abstain / provenance",
        size=10.5,
        color=PAPER,
        weight="bold",
    )

    # Decision layer
    _box(ax, 4.05, 5.85, 10.9, 1.35, GREEN, GREEN_LINE, r=0.06)
    _text(ax, 9.5, 6.92, "决策层   显式效用，而不是让大模型直接出厘米" if zh else "Decision    explicit utility — the VLM does not emit centimetres", size=11, weight="bold", color=GREEN_LINE)
    _text(
        ax,
        9.5,
        6.42,
        "U = −25·contact  −20·胸围过紧  −0.15·|改动量|  −0.25·副作用  −0.4·不确定度"
        if zh
        else "U = −25·contact  −20·chest tightness  −0.15·|edit|  −0.25·side-effect  −0.4·uncertainty",
        size=8.6,
    )
    _text(
        ax,
        9.5,
        6.08,
        "拒答：OOD 人体 / OOD 面料 / 动作超出 ±3 cm / 仿真不稳 / 候选分不开    失败感知 AUROC 0.90，拒答精确率 1.0"
        if zh
        else "Abstain: OOD body / OOD material / |Δ|>3 cm / unstable sim / tied candidates    AUROC 0.90, abstention precision 1.0",
        size=8.2,
        color="#3d4f44",
    )

    # Lattice
    _box(ax, 4.05, 5.05, 10.9, 0.68, AMBER, AMBER_LINE, r=0.05)
    _text(
        ax,
        9.5,
        5.39,
        "反事实格子   636 条转移 · 0 重复 state-action · 0 条把 intended 抄进 realized · 测试强制测量"
        if zh
        else "Counterfactual lattice   636 transitions · 0 duplicate (s,a) · 0 intended→realized copies · tests enforce measurement",
        size=9.2,
        weight="bold",
    )

    # Geometry vs physics
    _box(ax, 4.05, 2.55, 5.25, 2.35, BLUE, BLUE_LINE, r=0.06)
    _text(ax, 6.67, 4.62, "几何层  PASS" if zh else "Geometry  PASS", size=11, weight="bold", color=BLUE_LINE)
    geo = (
        [
            "GarmentCodeV2 Shirt / t-shirt.yaml",
            "具名参数  shirt.width.v = 目标胸围cm / 人体胸围",
            "序列化面板 → after − before 实测厘米",
            "袖长沿面板 X 构造（不是 Y）",
            "肩宽：无独立自由度 → 正式 NO-GO",
        ]
        if zh
        else [
            "GarmentCodeV2 Shirt / t-shirt.yaml",
            "Named param  shirt.width.v = desired_cm / body_bust",
            "Serialize panels → after − before centimetres",
            "Sleeve length is panel X, not Y",
            "Shoulder: no independent DoF → official NO-GO",
        ]
    )
    for i, line in enumerate(geo):
        _text(ax, 6.67, 4.22 - i * 0.32, line, size=8.2)

    _box(ax, 9.55, 2.55, 5.4, 2.35, GREEN, GREEN_LINE, r=0.06)
    _text(ax, 12.25, 4.62, "物理层  SYNTHETIC_BODY_PHYSICS" if zh else "Physics  SYNTHETIC_BODY_PHYSICS", size=11, weight="bold", color=GREEN_LINE)
    phy = (
        [
            "Warp XPBD 1.0.0-beta.6 · RTX 4090 · CUDA",
            "碰撞体：仓库内静态 OBJ（非 SMPL-X）",
            "人体顶点 ×100：米 → 厘米对齐",
            "指标：chest clearance p10 / contact ratio",
            "+3 cm：p10 0.47→0.50 cm，接触 0.027→0.022",
        ]
        if zh
        else [
            "Warp XPBD 1.0.0-beta.6 · RTX 4090 · CUDA",
            "Collider: in-repo static OBJ (not SMPL-X)",
            "Body verts ×100: metres → centimetres",
            "Metrics: chest clearance p10 / contact ratio",
            "+3 cm: p10 0.47→0.50 cm, contact 0.027→0.022",
        ]
    )
    for i, line in enumerate(phy):
        _text(ax, 12.25, 4.22 - i * 0.32, line, size=8.2)

    # Learning + license footer
    _box(ax, 0.25, 0.25, 7.55, 2.12, PANEL, RULE, r=0.06)
    _text(ax, 4.02, 2.08, "学习层：先证明有必要，再训练" if zh else "Learning: prove necessity, then train", size=10.5, weight="bold")
    learn = (
        [
            "平凡几何：解析逆映射 MAE ~0  >  Transition SFT 0.47 cm",
            "观测 FIT-Clean：B0 8.11 / XGB 7.88 —— 相关不是因果",
            "192 张纸样图：Ridge 3.45 打过 CNN 6.23；不做 FIT-100K 197GB",
            "RLVR 300 step、决策 holdout n=3、后悔已是 0 → NOT_JUSTIFIED",
            "Qwen2-VL 零样本 n=12，parse 100%，匹配率≈多数类，不做 LoRA",
        ]
        if zh
        else [
            "Trivial geometry: analytic MAE ~0  beats  Transition SFT 0.47 cm",
            "FIT-Clean observational: B0 8.11 / XGB 7.88 — correlation ≠ causal",
            "192 drawings: Ridge 3.45 beats CNN 6.23; no 197GB FIT-100K",
            "RLVR 300 steps, decision holdout n=3, regret already 0 → NOT_JUSTIFIED",
            "Qwen2-VL zero-shot n=12, parse 100%, match ≈ majority class; no LoRA",
        ]
    )
    for i, line in enumerate(learn):
        _text(ax, 4.02, 1.72 - i * 0.28, line, size=7.8)

    _box(ax, 8.0, 0.25, 6.95, 2.12, RED, RED_LINE, r=0.06)
    _text(ax, 11.47, 2.08, "硬限制（不停工，打标签）" if zh else "Hard limits (do not halt; label them)", size=10.5, weight="bold", color=RED_LINE)
    lim = (
        [
            "SMPL / SMPL-X 权重：HARD_BLOCKED_LICENSE",
            "真人 fit session：HARD_BLOCKED_LICENSE",
            "流水线改用静态 OBJ，禁止写成真人泛化",
            "目前只有 Shirt / tee 家族",
            "允许词汇：PASS · NO_GO_WITH_EVIDENCE · NOT_JUSTIFIED · HARD_BLOCKED_LICENSE",
        ]
        if zh
        else [
            "SMPL / SMPL-X weights: HARD_BLOCKED_LICENSE",
            "Real-human fit session: HARD_BLOCKED_LICENSE",
            "Continue on static OBJ; never call it real-human gen.",
            "Shirt / tee family only",
            "Allowed words: PASS · NO_GO_WITH_EVIDENCE · NOT_JUSTIFIED · HARD_BLOCKED_LICENSE",
        ]
    )
    for i, line in enumerate(lim):
        _text(ax, 11.47, 1.72 - i * 0.28, line, size=7.8)

    # arrows down the stack
    _arrow(ax, 9.5, 7.35, 9.5, 7.20)
    _arrow(ax, 9.5, 5.85, 9.5, 5.73)
    _arrow(ax, 9.5, 5.05, 9.5, 4.90)
    _arrow(ax, 6.67, 2.55, 6.67, 2.40)
    _arrow(ax, 12.25, 2.55, 12.25, 2.40)

    name = "01_system_architecture.png" if zh else "01_system_architecture_en.png"
    _save(fig, name)


def draw_pipeline(lang: str = "zh") -> None:
    zh = lang == "zh"
    fig, ax = plt.subplots(figsize=(15.2, 7.6))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 7.6)
    ax.axis("off")

    _text(
        ax,
        7.6,
        7.22,
        "干预流水线：intended Δ 永远不能抄进 realized Δ" if zh else "Intervention pipeline: intended Δ is never copied into realized Δ",
        size=14,
        weight="bold",
    )
    _text(
        ax,
        7.6,
        6.86,
        "这是防造假闸门，不是口号。抄一次，平凡几何上会出现假的 0 误差。"
        if zh
        else "This is an anti-fraud gate, not a slogan. One copy fakes a 0 error on trivial geometry.",
        size=9.5,
        color="#5a4038",
    )

    steps = (
        [
            ("1  意图", "设计师要\n胸围 +3 cm", GREEN, GREEN_LINE),
            ("2  参数", "Δwidth.v =\n3 / body_bust", BLUE, BLUE_LINE),
            ("3  纸样", "GarmentCode\n序列化面板", BLUE, BLUE_LINE),
            ("4  测量门", "after − before\n实测厘米", AMBER, AMBER_LINE),
            ("5  物理", "OBJ×100\nWarp XPBD", GREEN, GREEN_LINE),
            ("6  指标", "clearance p10\ncontact / 腰围Δ", GREEN, GREEN_LINE),
            ("7  排序", "效用最高者\n或 拒答", INK, INK),
        ]
        if zh
        else [
            ("1  Intent", "Designer wants\nbust +3 cm", GREEN, GREEN_LINE),
            ("2  Parameter", "Δwidth.v =\n3 / body_bust", BLUE, BLUE_LINE),
            ("3  Pattern", "GarmentCode\nserialize panels", BLUE, BLUE_LINE),
            ("4  Measure gate", "after − before\nmeasured cm", AMBER, AMBER_LINE),
            ("5  Physics", "OBJ ×100\nWarp XPBD", GREEN, GREEN_LINE),
            ("6  Metrics", "clearance p10\ncontact / waist Δ", GREEN, GREEN_LINE),
            ("7  Rank", "best utility\nor abstain", INK, INK),
        ]
    )
    xs = [0.35 + i * 2.1 for i in range(7)]
    for x, (title, body, fc, ec) in zip(xs, steps):
        fc_use, tc = (INK, PAPER) if title.startswith("7") else (fc, INK)
        _box(ax, x, 4.55, 1.95, 1.95, fc_use, ec, lw=1.6, r=0.08)
        _text(ax, x + 0.97, 6.18, title, size=9.5, weight="bold", color=PAPER if title.startswith("7") else ec)
        _text(ax, x + 0.97, 5.35, body, size=9, color=tc)
    for i in range(6):
        _arrow(ax, xs[i] + 1.95, 5.52, xs[i + 1], 5.52)

    # Forbidden vs required under the gate
    _box(ax, 0.35, 0.35, 7.15, 3.85, RED, RED_LINE, r=0.06)
    _text(ax, 3.92, 3.85, "禁止（测试会拒）" if zh else "Forbidden (tests reject)", size=12, weight="bold", color=RED_LINE)
    bad = (
        [
            "realized_delta_cm = intended_delta_cm",
            "用渲染图「看起来松了」代替厘米",
            "肩宽没有独立自由度却报 PASS",
            "把合成 OBJ 人台写成真人 / SMPL-X",
            "为了 MLLM 故事去改 split 让视觉「赢」",
        ]
        if zh
        else [
            "realized_delta_cm = intended_delta_cm",
            "Replace centimetres with “looks looser”",
            "Report shoulder PASS with no independent DoF",
            "Call a static OBJ a real human / SMPL-X",
            "Retune the split until vision “wins”",
        ]
    )
    for i, line in enumerate(bad):
        _text(ax, 3.92, 3.35 - i * 0.52, "✕   " + line, size=9.3, ha="center")

    _box(ax, 7.7, 0.35, 7.15, 3.85, GREEN, GREEN_LINE, r=0.06)
    _text(ax, 11.27, 3.85, "必须（本仓库的做法）" if zh else "Required (what this repo does)", size=12, weight="bold", color=GREEN_LINE)
    good = (
        [
            "厘米来自面板几何 after − before",
            "Warp 给出 clearance / contact 再排序",
            "肩宽扫描 Δ=0、袖长被带动 → NO-GO",
            "标签写 SYNTHETIC_BODY_PHYSICS",
            "7/33 翻转是真的；CI 重叠则必要性未成立",
        ]
        if zh
        else [
            "Centimetres from panel after − before",
            "Rank after Warp clearance / contact",
            "Shoulder scan Δ=0, sleeve moves → NO-GO",
            "Label the run SYNTHETIC_BODY_PHYSICS",
            "7/33 flips are real; overlapping CIs ≠ necessity",
        ]
    )
    for i, line in enumerate(good):
        _text(ax, 11.27, 3.35 - i * 0.52, "✓   " + line, size=9.3, ha="center")

    name = "02_intervention_pipeline.png" if zh else "02_intervention_pipeline_en.png"
    _save(fig, name)


def draw_hero_cases(lang: str = "zh") -> None:
    zh = lang == "zh"
    fig, ax = plt.subplots(figsize=(15.2, 6.8))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 6.8)
    ax.axis("off")
    _text(ax, 7.6, 6.42, "五个 Hero Case：同一句业务问题，五种技术裁决" if zh else "Five hero cases: one business question, five technical verdicts", size=14, weight="bold")
    _text(
        ax,
        7.6,
        6.05,
        "工作台问的是「下一版改什么」，不是「这件好不好看」。" if zh else "The workspace asks what should change next — not whether the drape looks nice.",
        size=10,
        color="#5a4038",
    )

    cards = (
        [
            ("01  胸口过紧", "问题：胸围余量不够", "证据：intended=+3\nrealized=+3.0000\nchest p10 0.47→0.50", "裁决：改 bust +3 cm", GREEN, GREEN_LINE, "GO"),
            ("02  同尺寸不同布", "问题：规格一样、刚度不同", "证据：33 对里 7 对翻转\n21%  [9%, 36%]\n分组 CI 重叠", "裁决：视觉必要性\n未统计成立", AMBER, AMBER_LINE, "HOLD"),
            ("03  腰围副作用", "问题：flare=1 改胸必改腰", "证据：±3 cm 胸围\n腰围跟随 100%\nn=162", "裁决：副作用进效用\n更大的刀不必赢", GREEN, GREEN_LINE, "GO"),
            ("04  OOD 人台", "问题：mean_female 出支持集", "证据：几何仍 ~0\n策略拒答精确率 1.0\n禁止叫真人泛化", "裁决：ABSTAIN\n升级人工", RED, RED_LINE, "STOP"),
            ("05  肩 vs 胸", "问题：要不要改肩宽", "证据：connecting_width\n肩 Δ=0，袖长被带动\n无独立自由度", "裁决：肩宽 NO-GO\n只考虑胸围家族", RED, RED_LINE, "STOP"),
        ]
        if zh
        else [
            ("01  Chest tight", "Problem: not enough ease", "Evidence: intended=+3\nrealized=+3.0000\nchest p10 0.47→0.50", "Verdict: bust +3 cm", GREEN, GREEN_LINE, "GO"),
            ("02  Same spec, stiff cloth", "Problem: matched measurements", "Evidence: 7/33 pairs flip\n21%  [9%, 36%]\ngrouped CIs overlap", "Verdict: vision necessity\nnot established", AMBER, AMBER_LINE, "HOLD"),
            ("03  Waist side-effect", "Problem: flare=1 couples waist", "Evidence: ±3 cm bust\nwaist follows 100%\nn=162", "Verdict: price side-effects\nlargest cut need not win", GREEN, GREEN_LINE, "GO"),
            ("04  OOD body", "Problem: mean_female OOD", "Evidence: geometry still ~0\nabstention precision 1.0\nnot real-human gen.", "Verdict: ABSTAIN\nescalate", RED, RED_LINE, "STOP"),
            ("05  Shoulder vs bust", "Problem: edit the shoulder?", "Evidence: connecting_width\nshoulder Δ=0, sleeve moves\nno independent DoF", "Verdict: shoulder NO-GO\nbust family only", RED, RED_LINE, "STOP"),
        ]
    )
    for i, (title, problem, evidence, verdict, fc, ec, badge) in enumerate(cards):
        x = 0.28 + i * 3.0
        _box(ax, x, 0.35, 2.85, 5.45, PANEL, ec, lw=1.7, r=0.08)
        _box(ax, x, 5.18, 2.85, 0.62, ec, ec, r=0.04)
        _text(ax, x + 1.42, 5.49, title, size=10, weight="bold", color=PAPER)
        _text(ax, x + 1.42, 4.85, problem, size=8.6, color="#4a4038")
        _box(ax, x + 0.12, 2.55, 2.61, 1.95, fc, ec, lw=1.0, r=0.05)
        _text(ax, x + 1.42, 3.52, evidence, size=8.0)
        _box(ax, x + 0.12, 0.5, 2.61, 1.85, fc, ec, lw=1.2, r=0.05)
        _text(ax, x + 1.42, 1.72, badge, size=9, weight="bold", color=ec)
        _text(ax, x + 1.42, 1.12, verdict, size=8.4, weight="bold")

    name = "13_hero_cases.png" if zh else "13_hero_cases_en.png"
    _save(fig, name)


def draw_problems(lang: str = "zh") -> None:
    zh = lang == "zh"
    fig, ax = plt.subplots(figsize=(15.2, 9.6))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 9.6)
    ax.axis("off")
    _text(ax, 7.6, 9.22, "实验过程里真正遇到的问题，和我们怎么收口" if zh else "Problems we actually hit, and how we closed them", size=14.5, weight="bold")
    _text(
        ax,
        7.6,
        8.82,
        "这些不是事后包装。每一行都有 artifact：探针 JSON、物理仿真、训练曲线或评测文件。"
        if zh
        else "Not post-hoc packaging. Every row has an artifact: probe JSON, physics, a training curve, or an eval file.",
        size=9.5,
        color="#5a4038",
    )

    rows = (
        [
            ("袖长探针 Δ = 0", "沿面板 Y 量，GarmentCode 沿 X 构造袖长", "改测量定义：袖片面平均 dx", "±2 cm MAE = 0，不把旧 bug 写成袖长 NO-GO", GREEN),
            ("clearance 单位错乱", "人体 OBJ 是米，布料网格是厘米", "碰撞体顶点 ×100 再算距离", "+3 cm 后 chest p10 0.47→0.50 cm，可解释", GREEN),
            ("肩宽扫不出来", "connecting_width：肩 Δ=0，袖长被带动", "官方 SHOULDER_ACTION = NO-GO", "假 PASS 比负结果更糟，选择发表 NO-GO", AMBER),
            ("视觉「必要性成立」是假的", "用 contact>0.08 阈值硬判 vision_needed", "改用下一态效用 + 分组切分 CI 是否分离", "7/33 翻转是真的；CI 重叠 → 必要性未成立", AMBER),
            ("intended 抄进 realized", "格子上会出现假的 0 误差", "测试拒收；realized 必须 after−before", "解析逆映射才是真的 ~0，SFT 0.47 是残差", GREEN),
            ("SMPL-X 权重不在", "许可资产，不能盗版，GPU 上也没有", "静态 OBJ 继续跑，打上 SYNTHETIC_BODY_PHYSICS", "禁止把合成人台写成真人泛化", AMBER),
            ("Torch / Warp 装不上", "2.11+cu126 卡 NVIDIA CDN；packman 挂死", "回退 Torch 2.5.1+cu124；物理不依赖 Torch", "Warp CUDA smoke PASS，仿真 127 条成功", GREEN),
            ("Qwen 图像 token = 0", "没走 chat template，模型看不见图", "AutoModelForImageTextToText + 模板", "parse 100%；match 83% n=12≈多数类，不做 LoRA", AMBER),
            ("RLVR / 大 CNN 更好看", "决策 holdout n=3 后悔已 0；FIT-100K 197GB 未下", "Ridge 3.45 > CNN 6.23；RLVR NOT_JUSTIFIED", "不为简历强行训练不该训的模型", GREEN),
        ]
        if zh
        else [
            ("Sleeve probe Δ = 0", "Measured panel Y; GarmentCode builds sleeve on X", "Remeasure mean sleeve-panel dx", "±2 cm MAE = 0; do not NO-GO the sleeve", GREEN),
            ("Clearance units broken", "Body OBJ in metres, cloth in centimetres", "Scale collider verts ×100 before distances", "+3 cm chest p10 0.47→0.50 cm, interpretable", GREEN),
            ("Shoulder will not move", "connecting_width: shoulder Δ=0, sleeve moves", "Official SHOULDER_ACTION = NO-GO", "A fake PASS is worse than a negative", AMBER),
            ("Vision “necessity” was a hack", "contact>0.08 threshold forced vision_needed", "Next-state utility + grouped-split CI overlap", "7/33 flips real; overlapping CIs → not established", AMBER),
            ("Copy intended into realized", "Would fake a 0 error on the lattice", "Tests reject; realized must be after−before", "Analytic inverse is the real ~0; SFT 0.47 is residual", GREEN),
            ("No SMPL-X weights", "Licensed assets; not pirated; absent on GPU", "Keep static OBJ, label SYNTHETIC_BODY_PHYSICS", "Never call a dummy real-human generalization", AMBER),
            ("Torch / Warp install", "2.11+cu126 NVIDIA CDN; packman hung", "Torch 2.5.1+cu124; physics does not need Torch", "Warp CUDA smoke PASS; 127 sims ok", GREEN),
            ("Qwen image tokens = 0", "No chat template, the model never saw the image", "AutoModelForImageTextToText + template", "parse 100%; match 83% n=12 ≈ majority; no LoRA", AMBER),
            ("RLVR / big CNN photograph better", "Decision n=3 regret already 0; no 197GB FIT-100K", "Ridge 3.45 > CNN 6.23; RLVR NOT_JUSTIFIED", "Do not train a model just because a résumé wants it", GREEN),
        ]
    )

    headers = ("碰到的问题", "现场现象", "技术处理", "收口") if zh else ("Problem", "What we saw", "What we did", "Close-out")
    col_x = [0.22, 3.55, 7.55, 11.45]
    col_w = [3.2, 3.85, 3.75, 3.5]
    _box(ax, 0.18, 8.22, 14.84, 0.42, INK, INK, r=0.03)
    for x, w, h in zip(col_x, col_w, headers):
        _text(ax, x + w / 2, 8.43, h, size=9.5, weight="bold", color=PAPER)

    for i, (a, b, c, d, fc) in enumerate(rows):
        y = 7.38 - i * 0.80
        _box(ax, 0.18, y, 14.84, 0.74, fc, RULE, lw=0.9, r=0.03)
        texts = (a, b, c, d)
        for x, w, t in zip(col_x, col_w, texts):
            _text(ax, x + w / 2, y + 0.37, t, size=7.7)

    name = "15_experiment_problems.png" if zh else "15_experiment_problems_en.png"
    _save(fig, name)


def draw_all() -> list[str]:
    _font()
    draw_architecture("zh")
    draw_architecture("en")
    draw_pipeline("zh")
    draw_pipeline("en")
    draw_hero_cases("zh")
    draw_hero_cases("en")
    draw_problems("zh")
    draw_problems("en")
    return [
        "01_system_architecture.png",
        "02_intervention_pipeline.png",
        "13_hero_cases.png",
        "15_experiment_problems.png",
        "01_system_architecture_en.png",
        "02_intervention_pipeline_en.png",
        "13_hero_cases_en.png",
        "15_experiment_problems_en.png",
    ]


if __name__ == "__main__":
    names = draw_all()
    print("wrote", ", ".join(names))

"""Exploratory data analysis on FIT-Clean manifest."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from fitground.config import FIGURES_DIR, MANIFEST_PATH, REPORTS_DIR
from fitground.data.schema import (
    CANONICAL_BODY_FIELDS,
    CANONICAL_GARMENT_FIELDS,
    CANONICAL_RELATIONAL_FIELDS,
)

MEASUREMENT_COLS = list(CANONICAL_BODY_FIELDS) + list(CANONICAL_GARMENT_FIELDS)
RELATIONAL_COLS = list(CANONICAL_RELATIONAL_FIELDS)


def distribution_stats(series: pd.Series) -> dict:
    s = series.dropna()
    if len(s) == 0:
        return {"count": 0, "missing": int(series.isna().sum())}
    return {
        "count": int(len(s)),
        "missing": int(series.isna().sum()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "p1": float(s.quantile(0.01)),
        "p5": float(s.quantile(0.05)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "p99": float(s.quantile(0.99)),
        "max": float(s.max()),
    }


def run_eda(manifest_path: Path = MANIFEST_PATH) -> dict:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(manifest_path)

    report: dict = {
        "total_samples": len(df),
        "train": int((df["source_split"] == "train").sum()),
        "eval": int((df["source_split"] == "eval").sum()),
        "valid": int((df["quality_status"] == "VALID").sum()),
        "suspicious": int((df["quality_status"] == "SUSPICIOUS").sum()),
        "invalid": int((df["quality_status"] == "INVALID").sum()),
        "usable_for_fitground": int(df["usable_for_fitground"].sum()),
        "measurements": {},
        "relational": {},
        "findings": [],
    }

    for col in MEASUREMENT_COLS + RELATIONAL_COLS:
        key = "measurements" if col in MEASUREMENT_COLS else "relational"
        report[key][col] = distribution_stats(df[col])

    # Missing rates
    report["measurement_missing_rates"] = {
        col: float(df[col].isna().mean()) for col in MEASUREMENT_COLS
    }

    # Image issues
    corrupt = df[
        df["quality_flags"].apply(
            lambda f: any("corrupt" in x or "missing" in x for x in (f or []))
        )
    ]
    report["image_issues"] = len(corrupt)

    # Distribution plots
    sns.set_theme(style="whitegrid")
    for col in MEASUREMENT_COLS:
        _plot_histogram(df, col, FIGURES_DIR / f"hist_{col}.png")
        _plot_boxplot_by_split(df, col, FIGURES_DIR / f"box_{col}_by_split.png")

    for col in RELATIONAL_COLS:
        _plot_histogram(df[df["usable_for_fitground"]], col, FIGURES_DIR / f"hist_{col}.png")

    _plot_quality_pie(df, FIGURES_DIR / "quality_status_distribution.png")
    _plot_bust_ease_scatter(df, FIGURES_DIR / "bust_ease_scatter.png")

    # Findings
    report["findings"] = _detect_findings(df, report)

    out_path = REPORTS_DIR / "fit_eda_report.json"
    out_path.write_text(json.dumps(report, indent=2))
    _write_eda_markdown(report)
    return report


def _plot_histogram(df: pd.DataFrame, col: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    data = df[col].dropna()
    if len(data) == 0:
        plt.close(fig)
        return
    ax.hist(data, bins=50, edgecolor="black", alpha=0.7)
    ax.set_title(f"Distribution: {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_boxplot_by_split(df: pd.DataFrame, col: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    df_plot = df[[col, "source_split"]].dropna()
    if len(df_plot) == 0:
        plt.close(fig)
        return
    sns.boxplot(data=df_plot, x="source_split", y=col, ax=ax)
    ax.set_title(f"{col} by Split")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_quality_pie(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 6))
    counts = df["quality_status"].value_counts()
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Quality Status Distribution")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _plot_bust_ease_scatter(df: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    sub = df[df["usable_for_fitground"]].dropna(subset=["bust_ease_cm", "body_bust_cm"])
    if len(sub) == 0:
        plt.close(fig)
        return
    ax.scatter(sub["body_bust_cm"], sub["bust_ease_cm"], alpha=0.15, s=5)
    ax.set_xlabel("Body Bust (cm)")
    ax.set_ylabel("Bust Ease (cm)")
    ax.set_title("Body Bust vs Bust Ease")
    ax.axhline(0, color="red", linestyle="--", alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def _detect_findings(df: pd.DataFrame, report: dict) -> list[str]:
    findings = []
    # Check sleeve zeros
    sleeve_zero = (df["garment_sleeve_cm"] == 0).sum()
    if sleeve_zero > 0:
        findings.append(
            f"garment_sleeve_cm has {sleeve_zero} zero values — likely sleeveless garments, not missing data"
        )

    # Check measurement missing
    for col, rate in report["measurement_missing_rates"].items():
        if rate > 0:
            findings.append(f"{col} missing rate: {rate:.4%}")

    # Split distribution shift
    for col in ["body_height_cm", "bust_ease_cm"]:
        train_med = df[df["source_split"] == "train"][col].median()
        eval_med = df[df["source_split"] == "eval"][col].median()
        if train_med and eval_med and abs(train_med - eval_med) / train_med > 0.05:
            findings.append(
                f"Possible split shift in {col}: train median={train_med:.2f}, eval median={eval_med:.2f}"
            )

    invalid_rate = report["invalid"] / report["total_samples"] if report["total_samples"] else 0
    if invalid_rate > 0.01:
        findings.append(f"INVALID rate {invalid_rate:.2%} exceeds 1% threshold")

    return findings


def _write_eda_markdown(report: dict) -> None:
    lines = [
        "# FIT EDA Report",
        "",
        f"Total samples: {report['total_samples']}",
        f"- Train: {report['train']}",
        f"- Eval: {report['eval']}",
        "",
        "## Quality",
        "",
        f"- VALID: {report['valid']}",
        f"- SUSPICIOUS: {report['suspicious']}",
        f"- INVALID: {report['invalid']}",
        f"- Usable for FitGround: {report['usable_for_fitground']}",
        "",
        "## Key Findings",
        "",
    ]
    for f in report.get("findings", []):
        lines.append(f"- {f}")

    lines.extend(["", "## Measurement Distributions", "", "| Field | Mean | Std | Median | P5 | P95 |", "|-------|------|-----|--------|----|-----|"])
    for col, stats in report.get("measurements", {}).items():
        if stats.get("count", 0) > 0:
            lines.append(
                f"| {col} | {stats['mean']:.2f} | {stats['std']:.2f} | {stats['median']:.2f} | {stats['p5']:.2f} | {stats['p95']:.2f} |"
            )

    (REPORTS_DIR / "fit_eda_report.md").write_text("\n".join(lines))

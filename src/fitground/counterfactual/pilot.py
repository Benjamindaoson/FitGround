"""Shard-aware stratified sampling for visual sanity checks."""

from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd

from fitground.config import COUNTERFACTUAL_RANDOM_SEED
from fitground.counterfactual.validation import ease_bin


def pair_shard_set(row: pd.Series) -> set[str]:
    return {str(row["anchor_shard_id"]), str(row["counterfactual_shard_id"])}


def select_pilot_pairs(
    pairs: pd.DataFrame,
    *,
    n_pairs: int = 120,
    max_shards: int = 64,
    seed: int = COUNTERFACTUAL_RANDOM_SEED,
    include_suspicious: bool = True,
) -> pd.DataFrame:
    """Select a visual-check set packed onto as few shards as possible.

    Person-reuse pairs almost always span two train shards, so a naive cap of
    16 shards yields too few pairs. Greedy 0-then-1-then-2 new-shard insertion
    is required to reach 100+ pairs under a 60GB download budget.
    """
    del include_suspicious
    if pairs.empty:
        return pairs.copy()
    work = pairs.copy()
    work["_ease_bin"] = work["anchor_bust_ease_cm"].map(lambda x: ease_bin(float(x)))
    work["_abs_delta"] = work["delta_bust_ease_cm"].abs()
    rng = work.sample(frac=1.0, random_state=seed)

    forced = []
    if (rng["pair_tier"] == "B").any():
        forced.extend(rng.index[rng["pair_tier"] == "B"].tolist())
    eval_eval = rng.index[rng["pair_split"] == "eval_eval"].tolist()
    forced.extend(eval_eval)
    same_shard = rng.index[rng["anchor_shard_id"] == rng["counterfactual_shard_id"]].tolist()
    forced.extend(same_shard)

    selected: list[Any] = []
    shards: set[str] = set()
    stratum_counts: Counter[str] = Counter()

    def _try_add(idx: Any) -> bool:
        if idx in selected:
            return False
        row = work.loc[idx]
        needed = pair_shard_set(row)
        new = needed - shards
        if shards and len(shards) + len(new) > max_shards and new:
            return False
        if not shards and len(new) > max_shards:
            return False
        selected.append(idx)
        shards.update(needed)
        stratum_counts[str(row["_ease_bin"])] += 1
        return True

    for idx in dict.fromkeys(forced):
        _try_add(idx)

    remaining = [i for i in rng.index.tolist() if i not in selected]
    while len(selected) < n_pairs and remaining:
        best = None
        best_key = None
        for idx in remaining:
            row = work.loc[idx]
            needed = pair_shard_set(row)
            new = needed - shards
            n_new = len(new)
            if shards and len(shards) + n_new > max_shards and n_new:
                continue
            underrep = -stratum_counts[str(row["_ease_bin"])]
            key = (n_new, underrep, -float(row["_abs_delta"]))
            if best_key is None or key < best_key:
                best_key = key
                best = idx
        if best is None:
            break
        if not _try_add(best):
            remaining = [i for i in remaining if i != best]
            continue
        remaining = [i for i in remaining if i not in selected]

    out = work.loc[selected].drop(columns=["_ease_bin", "_abs_delta"], errors="ignore")
    out.attrs["pilot_shards"] = sorted(shards)
    out.attrs["n_shards"] = len(shards)
    return out.reset_index(drop=True)

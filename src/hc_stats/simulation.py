"""Monte Carlo simulation engine.

Runs large numbers of hands and aggregates results by configurable keys,
making it easy to slice results by starting-hand bucket, flop texture, etc.

The key function receives a GameResult (which includes .hole and .flop) so the
key is always derived from the same cards that were actually played.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np
from tqdm import tqdm  # type: ignore[import-untyped]

from hc_stats.deck import Deck
from hc_stats.game import GameResult, Strategy, play_hand


@dataclass
class BucketStats:
    count: int = 0
    net_sum: float = 0.0
    net_sq_sum: float = 0.0  # for variance calculation

    def update(self, result: GameResult) -> None:
        self.count += 1
        self.net_sum += result.net
        self.net_sq_sum += result.net ** 2

    @property
    def ev(self) -> float:
        return self.net_sum / self.count if self.count else 0.0

    @property
    def std(self) -> float:
        if self.count < 2:
            return 0.0
        mean = self.net_sum / self.count
        variance = (self.net_sq_sum / self.count) - mean ** 2
        return float(np.sqrt(max(0.0, variance)))

    @property
    def sem(self) -> float:
        return self.std / np.sqrt(self.count) if self.count else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "ev": self.ev,
            "std": self.std,
            "sem": self.sem,
        }


# Key function: receives a GameResult and returns a bucket key (or None to skip).
KeyFn = Callable[[GameResult], str | None]


def run_simulation(
    strategy: Strategy,
    key_fn: KeyFn,
    n_simulations: int,
    *,
    seed: int | None = None,
    show_progress: bool = True,
) -> dict[str, BucketStats]:
    """Run *n_simulations* hands; group results by key_fn.

    Returns a dict mapping bucket key → BucketStats.
    The key function receives the full GameResult (including .hole and .flop),
    so the key is always derived from the exact cards that were played.
    """
    if seed is not None:
        import random
        random.seed(seed)

    deck = Deck()
    stats: dict[str, BucketStats] = defaultdict(BucketStats)

    iterator = range(n_simulations)
    if show_progress:
        iterator = tqdm(iterator, desc="Simulating", unit=" hands")

    for _ in iterator:
        result = play_hand(deck, strategy)
        key = key_fn(result)
        if key is not None:
            stats[key].update(result)

    return dict(stats)

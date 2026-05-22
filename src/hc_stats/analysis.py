"""Analysis helpers: hand bucketing, strategy definitions, result formatting."""

from __future__ import annotations

from hc_stats.deck import FACE_RANKS, RANKS, Card
from hc_stats.evaluator import flop_has_pair
from hc_stats.game import BettingStage, GameResult, GameState

# ---------------------------------------------------------------------------
# Starting-hand canonical key  (same as poker hand notation)
# ---------------------------------------------------------------------------

def hole_key(c1: Card, c2: Card) -> str:
    """Return canonical 2-card hand notation, e.g. 'AKs', 'TT', '72o'."""
    hi, lo = (c1, c2) if c1.rank >= c2.rank else (c2, c1)
    r1, r2 = RANKS[hi.rank], RANKS[lo.rank]
    if hi.rank == lo.rank:
        return f"{r1}{r2}"  # pocket pair
    suited = "s" if hi.suit == lo.suit else "o"
    return f"{r1}{r2}{suited}"


# ---------------------------------------------------------------------------
# Key functions for simulation bucketing
# ---------------------------------------------------------------------------

def key_by_hole(result: GameResult) -> str:
    """Bucket by canonical hole-card notation."""
    return hole_key(result.hole[0], result.hole[1])


def key_flop_pair_facecard(result: GameResult) -> str | None:
    """Bucket flop-analysis hands.

    Only counts hands where:
    - The flop has a pair (two or more cards of the same rank).
    - The player's highest hole card is a face card (J/Q/K/A).

    Returns a bucket like 'AKs_flop-pair' or None to skip.
    """
    if not flop_has_pair(result.flop):
        return None
    hi = result.hole[0] if result.hole[0].rank >= result.hole[1].rank else result.hole[1]
    if hi.rank not in FACE_RANKS:
        return None
    return hole_key(result.hole[0], result.hole[1])


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

def strategy_always_4x(state: GameState) -> int:
    """Raise 4× every hand pre-flop (upper bound on aggression)."""
    if state.stage == BettingStage.PREFLOP:
        return 4
    if state.stage == BettingStage.FLOP:
        return 2
    return 1


def strategy_always_check_preflop(state: GameState) -> int:
    """Never raise pre-flop; always bet 2× on flop, 1× on river."""
    if state.stage == BettingStage.PREFLOP:
        return 0
    if state.stage == BettingStage.FLOP:
        return 2
    return 1


def strategy_preflop_4x_only(state: GameState) -> int:
    """Only take the 4× line; check flop, bet 1× river (for EV comparison)."""
    if state.stage == BettingStage.PREFLOP:
        return 4
    if state.stage == BettingStage.FLOP:
        return 0  # check
    return 1  # bet 1× river (must)


def strategy_check_preflop_bet_flop(state: GameState) -> int:
    """Check pre-flop, bet 2× flop regardless, 1× river."""
    if state.stage == BettingStage.PREFLOP:
        return 0
    if state.stage == BettingStage.FLOP:
        return 2
    return 1


def strategy_check_preflop_check_flop(state: GameState) -> int:
    """Check pre-flop, check flop, bet 1× river."""
    if state.stage == BettingStage.PREFLOP:
        return 0
    if state.stage == BettingStage.FLOP:
        return 0
    return 1

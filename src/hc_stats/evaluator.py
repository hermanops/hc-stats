"""Hand evaluator for Ultimate Texas Hold'em.

Uses the `treys` library for fast hand ranking, and adds UTH-specific
payout logic for the Blind and Trips bets.

Hand ranks (treys, lower = better):
    Royal Flush   ≤ 10
    Str. Flush    ≤ 166
    Four of a Kind ≤ 322
    Full House    ≤ 1599
    Flush         ≤ 1599  (use treys rank class for distinction)
    Straight      ≤ ...
    Three of a Kind, Two Pair, Pair, High Card
"""

from __future__ import annotations

from enum import IntEnum

from treys import Card as TCard  # type: ignore[import-untyped]
from treys import Evaluator as TreyEvaluator

from hc_stats.deck import Card

_evaluator = TreyEvaluator()


class HandClass(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


# Map from treys' get_rank_class() return value → our HandClass.
# Verified against the installed treys version: 0=Royal Flush, 9=High Card.
_TREYS_CLASS_MAP: dict[int, HandClass] = {
    0: HandClass.ROYAL_FLUSH,
    1: HandClass.STRAIGHT_FLUSH,
    2: HandClass.FOUR_OF_A_KIND,
    3: HandClass.FULL_HOUSE,
    4: HandClass.FLUSH,
    5: HandClass.STRAIGHT,
    6: HandClass.THREE_OF_A_KIND,
    7: HandClass.TWO_PAIR,
    8: HandClass.PAIR,
    9: HandClass.HIGH_CARD,
}


def _to_treys(card: Card) -> int:
    """Convert our Card to a treys integer card."""
    rank_chars = "23456789TJQKA"
    suit_chars = "cdhs"
    return int(TCard.new(rank_chars[card.rank] + suit_chars[card.suit]))


def evaluate(hole: list[Card], community: list[Card]) -> tuple[int, HandClass]:
    """Return (treys_rank, HandClass). Lower treys_rank = stronger hand."""
    t_hole = [_to_treys(c) for c in hole]
    t_board = [_to_treys(c) for c in community]
    rank: int = int(_evaluator.evaluate(t_board, t_hole))
    hand_class = _TREYS_CLASS_MAP[int(_evaluator.get_rank_class(rank))]
    return rank, hand_class


# ---------------------------------------------------------------------------
# Blind bet payout multipliers (player must win with straight or better)
# Push (0) if player wins with less than straight.
# ---------------------------------------------------------------------------
BLIND_PAYOUT: dict[HandClass, float] = {
    HandClass.STRAIGHT: 1.0,
    HandClass.FLUSH: 1.5,
    HandClass.FULL_HOUSE: 3.0,
    HandClass.FOUR_OF_A_KIND: 10.0,
    HandClass.STRAIGHT_FLUSH: 50.0,
    HandClass.ROYAL_FLUSH: 500.0,
}

# ---------------------------------------------------------------------------
# Trips bet payout multipliers (independent of dealer hand)
# ---------------------------------------------------------------------------
TRIPS_PAYOUT: dict[HandClass, float] = {
    HandClass.THREE_OF_A_KIND: 3.0,
    HandClass.STRAIGHT: 4.0,
    HandClass.FLUSH: 7.0,
    HandClass.FULL_HOUSE: 8.0,
    HandClass.FOUR_OF_A_KIND: 30.0,
    HandClass.STRAIGHT_FLUSH: 40.0,
    HandClass.ROYAL_FLUSH: 50.0,
}


def blind_payout(hand_class: HandClass) -> float:
    """Return Blind bet payout multiplier (0 = push, negative not possible)."""
    return BLIND_PAYOUT.get(hand_class, 0.0)


def trips_payout(hand_class: HandClass) -> float:
    """Return Trips payout multiplier (-1 = lose)."""
    return TRIPS_PAYOUT.get(hand_class, -1.0)


def dealer_qualifies(dealer_rank: int, dealer_class: HandClass) -> bool:
    """Dealer qualifies with at least a pair."""
    return dealer_class >= HandClass.PAIR


def flop_has_pair(flop: list[Card]) -> bool:
    """Return True if at least two flop cards share a rank."""
    ranks = [c.rank for c in flop]
    return len(ranks) != len(set(ranks))

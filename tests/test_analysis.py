"""Tests for analysis helpers (hand bucketing, key functions)."""

import pytest
from hc_stats.deck import Card
from hc_stats.analysis import hole_key, key_flop_pair_facecard
from hc_stats.game import GameResult
from hc_stats.evaluator import HandClass


def _make_result(hole_strs: list[str], flop_strs: list[str]) -> GameResult:
    return GameResult(
        net=0.0,
        trips_net=0.0,
        player_class=HandClass.HIGH_CARD,
        dealer_class=HandClass.HIGH_CARD,
        dealer_qualified=False,
        bet_stage=None,
        bet_multiplier=0,
        hole=[Card.from_str(s) for s in hole_strs],
        flop=[Card.from_str(s) for s in flop_strs],
    )


@pytest.mark.parametrize("c1,c2,expected", [
    ("Ah", "Kh", "AKs"),   # suited
    ("Ah", "Kd", "AKo"),   # off-suit
    ("Ah", "Ad", "AA"),    # pocket pair
    ("2h", "7d", "72o"),   # low off-suit (higher rank first)
    ("7h", "2d", "72o"),   # same hand, different order
])
def test_hole_key(c1: str, c2: str, expected: str) -> None:
    assert hole_key(Card.from_str(c1), Card.from_str(c2)) == expected


def test_key_flop_pair_facecard_match():
    # Flop has pair (7-7-K) and player has Ace high
    result = _make_result(["Ah", "2d"], ["7c", "7h", "Ks"])
    key = key_flop_pair_facecard(result)
    assert key == "A2o"


def test_key_flop_pair_facecard_no_flop_pair():
    # Flop has no pair
    result = _make_result(["Ah", "2d"], ["7c", "8h", "Ks"])
    assert key_flop_pair_facecard(result) is None


def test_key_flop_pair_facecard_no_facecard():
    # Flop has pair but player's highest card is a Ten (not a face card)
    result = _make_result(["Tc", "2d"], ["7c", "7h", "Ks"])
    assert key_flop_pair_facecard(result) is None

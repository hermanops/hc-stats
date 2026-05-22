"""Tests for the hand evaluator."""

import pytest
from hc_stats.deck import Card
from hc_stats.evaluator import (
    HandClass,
    evaluate,
    blind_payout,
    trips_payout,
    dealer_qualifies,
    flop_has_pair,
)


def _cards(*strs: str) -> list[Card]:
    return [Card.from_str(s) for s in strs]


def test_royal_flush():
    hole = _cards("Ah", "Kh")
    community = _cards("Qh", "Jh", "Th", "2c", "3d")
    _, hc = evaluate(hole, community)
    assert hc == HandClass.ROYAL_FLUSH


def test_pair():
    hole = _cards("Ah", "Ad")
    community = _cards("2c", "7h", "9s", "Kd", "3h")
    _, hc = evaluate(hole, community)
    assert hc == HandClass.PAIR


def test_high_card():
    hole = _cards("2h", "7d")
    community = _cards("9c", "Jh", "Ks", "3d", "5h")
    _, hc = evaluate(hole, community)
    assert hc == HandClass.HIGH_CARD


def test_dealer_qualifies_with_pair():
    hole = _cards("Ah", "Ad")
    community = _cards("2c", "7h", "9s", "Kd", "3h")
    rank, hc = evaluate(hole, community)
    assert dealer_qualifies(rank, hc)


def test_dealer_does_not_qualify_with_high_card():
    hole = _cards("2h", "7d")
    community = _cards("9c", "Jh", "Ks", "3d", "5h")
    rank, hc = evaluate(hole, community)
    assert not dealer_qualifies(rank, hc)


def test_blind_payout_royal():
    assert blind_payout(HandClass.ROYAL_FLUSH) == 500.0


def test_blind_payout_straight():
    assert blind_payout(HandClass.STRAIGHT) == 1.0


def test_blind_payout_pair():
    assert blind_payout(HandClass.PAIR) == 0.0  # push


def test_trips_payout_three_of_a_kind():
    assert trips_payout(HandClass.THREE_OF_A_KIND) == 3.0


def test_trips_payout_high_card_loses():
    assert trips_payout(HandClass.HIGH_CARD) == -1.0


def test_flop_has_pair_true():
    flop = _cards("7c", "7h", "Ks")
    assert flop_has_pair(flop)


def test_flop_has_pair_false():
    flop = _cards("2c", "7h", "Ks")
    assert not flop_has_pair(flop)


def test_flop_trips_counts_as_pair():
    flop = _cards("7c", "7h", "7s")
    assert flop_has_pair(flop)

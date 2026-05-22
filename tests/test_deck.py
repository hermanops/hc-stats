"""Tests for deck and card primitives."""

from hc_stats.deck import Card, Deck


def test_card_from_str():
    c = Card.from_str("Ah")
    assert c.rank == 12  # Ace
    assert c.suit == 2   # hearts
    assert str(c) == "Ah"


def test_card_face():
    assert Card.from_str("Jc").is_face
    assert Card.from_str("Qd").is_face
    assert Card.from_str("Kh").is_face
    assert Card.from_str("As").is_face
    assert not Card.from_str("Tc").is_face
    assert not Card.from_str("9h").is_face


def test_deck_all_unique():
    deck = Deck()
    deck.shuffle()
    cards = deck.deal_n(52)
    assert len(set(c.code for c in cards)) == 52


def test_deck_deal_n():
    deck = Deck()
    deck.shuffle()
    hand = deck.deal_n(5)
    assert len(hand) == 5
    assert all(isinstance(c, Card) for c in hand)

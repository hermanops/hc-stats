"""Tests for the game engine — focus on payout correctness."""

from hc_stats.analysis import strategy_always_4x
from hc_stats.deck import Deck
from hc_stats.game import BettingStage, GameResult, GameState, play_hand


def _always_bet(state: GameState) -> int:
    if state.stage == BettingStage.PREFLOP:
        return 4
    if state.stage == BettingStage.FLOP:
        return 2
    return 1


def _always_check_fold(state: GameState) -> int:
    """Check everywhere, then fold at river."""
    if state.stage == BettingStage.RIVER:
        return 0  # fold
    return 0


def test_play_hand_returns_game_result():
    deck = Deck()
    result = play_hand(deck, _always_bet)
    assert isinstance(result, GameResult)


def test_play_hand_hole_and_flop_populated():
    """GameResult must always carry the actual hole cards and flop dealt."""
    deck = Deck()
    result = play_hand(deck, _always_bet)
    assert len(result.hole) == 2
    assert len(result.flop) == 3


def test_fold_at_river_loses_two_units():
    """Folding at the river costs -1 Ante -1 Blind = -2."""
    deck = Deck()
    result = play_hand(deck, _always_check_fold)
    assert result.net == -2.0
    assert result.bet_multiplier == 0
    assert result.bet_stage is None


def test_preflop_4x_bet_stage():
    deck = Deck()
    result = play_hand(deck, strategy_always_4x)
    assert result.bet_stage == BettingStage.PREFLOP
    assert result.bet_multiplier == 4


def test_net_is_finite():
    """Run 200 hands and confirm every net result is a finite number."""
    import math
    deck = Deck()
    for _ in range(200):
        result = play_hand(deck, _always_bet)
        assert math.isfinite(result.net), f"Non-finite net: {result.net}"


def test_play_bet_compared_even_when_dealer_unqualified():
    """
    Regression: when dealer doesn't qualify but has the better hand, the player
    loses ALL bets (Ante + Play + Blind).  This verifies:
      - Play bet is compared regardless of qualifying.
      - Ante is NOT protected when dealer wins without qualifying.

    We run many hands and confirm that some unqualified-dealer wins result in
    a large negative net (e.g. −6 for a 4× bet: −1 Ante −4 Play −1 Blind).
    """
    deck = Deck()
    unqualified_dealer_wins = []
    for _ in range(10_000):
        result = play_hand(deck, _always_bet)
        if not result.dealer_qualified:
            # Determine whether dealer won by inspecting net:
            # If player won, Play (+4) and Ante (push, 0) and Blind (0 or +) → net >= 0
            # If dealer won, Play (−4) and Ante (−1) and Blind (−1) → net = −6
            unqualified_dealer_wins.append(result.net)

    assert len(unqualified_dealer_wins) > 0, "Expected some unqualified dealer hands"
    # With the corrected rule, dealer wins without qualifying → net ≤ −6 for 4× bet.
    min_net = min(unqualified_dealer_wins)
    assert min_net <= -6.0, (
        f"Expected full loss when unqualified dealer wins (net ≤ −6); got min={min_net}"
    )

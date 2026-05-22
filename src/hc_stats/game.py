"""Ultimate Texas Hold'em game engine.

Simulates a single hand with a configurable betting strategy function so
callers can test different strategies and measure their EV.

Bet sizes are expressed as multiples of the Ante.

Payouts summary (Holland Casino rules)
---------------------------------------
The best 5-of-7 hand comparison is ALWAYS performed regardless of dealer qualifying.

* Ante:
  - Dealer wins hand comparison              : −1  (whether or not dealer qualifies)
  - Dealer qualifies, player wins            : +1
  - Dealer qualifies, tie                    : push
  - Dealer does NOT qualify, player wins     : push  (assumption — see README)
  - Dealer does NOT qualify, tie             : push

* Play (pre-flop 4×, flop 2×, or river 1×) — ALWAYS compared:
  - Player wins hand comparison  : +bet_multiplier
  - Tie                          : push
  - Dealer wins hand comparison  : −bet_multiplier

* Blind: resolved on player's best 5-card hand when player wins comparison.
  Push if player wins with less than a straight; −1 if player loses or ties.
  See BLIND_PAYOUT for straight-or-better payouts.

* Trips: always resolved on player's best 5-card hand (see TRIPS_PAYOUT).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol

from hc_stats.deck import Card, Deck
from hc_stats.evaluator import (
    HandClass,
    blind_payout,
    dealer_qualifies,
    evaluate,
    trips_payout,
)


class BettingStage(Enum):
    PREFLOP = "preflop"
    FLOP = "flop"
    RIVER = "river"


@dataclass(frozen=True)
class GameState:
    """Snapshot passed to the strategy function at each decision point."""

    stage: BettingStage
    hole: list[Card]
    community: list[Card]  # 0, 3, or 5 cards depending on stage
    already_bet: int  # 0 = no play bet placed yet


class Strategy(Protocol):
    """Callable: receives GameState, returns bet multiplier (0=check/fold, 1/2/4)."""

    def __call__(self, state: GameState) -> int: ...


@dataclass
class GameResult:
    """Net profit/loss in units of 1× Ante (excluding Trips side bet)."""

    net: float  # total P&L including Ante, Play, Blind
    trips_net: float  # P&L of the Trips side bet
    player_class: HandClass
    dealer_class: HandClass
    dealer_qualified: bool
    bet_stage: BettingStage | None  # when/where the play bet was placed
    bet_multiplier: int  # 0 if folded
    hole: list[Card] = field(default_factory=list)
    flop: list[Card] = field(default_factory=list)


def play_hand(
    deck: Deck,
    strategy: Strategy,
    *,
    trips: bool = False,
) -> GameResult:
    """Deal and play one complete hand of Ultimate Texas Hold'em.

    Returns a GameResult with net P&L expressed in Ante units.
    Set `trips=True` to also resolve the Trips side bet.
    """
    deck.shuffle()

    # Deal hole and full board
    hole = deck.deal_n(2)
    flop = deck.deal_n(3)
    turn_river = deck.deal_n(2)
    dealer_hole = deck.deal_n(2)

    community_full = flop + turn_river
    community_dealer = dealer_hole + community_full  # dealer uses all 7

    # Evaluate hands
    player_rank, player_class = evaluate(hole, community_full)
    dealer_rank, dealer_class = evaluate(dealer_hole, community_full)
    qual = dealer_qualifies(dealer_rank, dealer_class)

    # --- Betting decisions ---
    bet_multiplier = 0
    bet_stage: BettingStage | None = None

    # Pre-flop decision
    pf_bet = strategy(GameState(BettingStage.PREFLOP, hole, [], 0))
    if pf_bet == 4:
        bet_multiplier = 4
        bet_stage = BettingStage.PREFLOP

    # Flop decision (only if no pre-flop bet)
    if bet_multiplier == 0:
        fl_bet = strategy(GameState(BettingStage.FLOP, hole, flop, 0))
        if fl_bet == 2:
            bet_multiplier = 2
            bet_stage = BettingStage.FLOP

    # River decision (only if still no bet; must bet 1× or fold)
    if bet_multiplier == 0:
        rv_bet = strategy(GameState(BettingStage.RIVER, hole, community_full, 0))
        if rv_bet == 1:
            bet_multiplier = 1
            bet_stage = BettingStage.RIVER
        else:
            # Player folds: loses Ante + Blind
            net = -2.0  # -1 Ante, -1 Blind
            trips_net = trips_payout(player_class) if trips else 0.0
            return GameResult(
                net=net,
                trips_net=trips_net,
                player_class=player_class,
                dealer_class=dealer_class,
                dealer_qualified=qual,
                bet_stage=None,
                bet_multiplier=0,
                hole=hole,
                flop=flop,
            )

    # --- Resolve bets ---
    # Compare hands (lower treys rank = stronger)
    if player_rank < dealer_rank:
        winner = "player"
    elif player_rank > dealer_rank:
        winner = "dealer"
    else:
        winner = "tie"

    # Ante result.
    # When dealer doesn't qualify the hand comparison still matters:
    #   - Dealer wins  → Ante loses (you lose all your money).
    #   - Player wins  → Ante pushes (standard UTH non-qualifying protection).
    #   - Tie          → Ante pushes.
    # When dealer qualifies, Ante is resolved normally by hand comparison.
    # NOTE: the Ante push on a player win vs. a non-qualifying dealer is an
    # assumption; verify against Holland Casino house rules if in doubt.
    if winner == "dealer":
        ante_result = -1.0
    elif winner == "player" and qual:
        ante_result = 1.0
    else:
        ante_result = 0.0  # push (tie, or player wins vs non-qualifying dealer)

    # Play bet result — always resolved by hand comparison, regardless of qualifying.
    if winner == "player":
        play_result = float(bet_multiplier)
    elif winner == "tie":
        play_result = 0.0
    else:
        play_result = -float(bet_multiplier)

    # Blind result (only player wins count)
    if winner == "player":
        blind_mult = blind_payout(player_class)
        blind_result = blind_mult if blind_mult > 0 else 0.0  # push if < straight
    elif winner == "tie":
        blind_result = 0.0
    else:
        blind_result = -1.0

    # Total: we stake 1 Ante + 1 Blind + bet_multiplier Ante
    net = ante_result + play_result + blind_result
    trips_net = trips_payout(player_class) if trips else 0.0

    return GameResult(
        net=net,
        trips_net=trips_net,
        player_class=player_class,
        dealer_class=dealer_class,
        dealer_qualified=qual,
        bet_stage=bet_stage,
        bet_multiplier=bet_multiplier,
        hole=hole,
        flop=flop,
    )

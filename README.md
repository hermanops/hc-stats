# hc-stats: Ultimate Texas Hold'em Strategy Analyser

Monte Carlo simulation engine for analysing optimal strategy in **Ultimate Texas Hold'em** as played at Holland Casino.

## What it analyses

| Question | Script |
|---|---|
| Which starting hands should you raise **4× pre-flop**? | `hc-preflop` |
| Should you bet **2× on the flop** when you have a face-card high and the flop pairs? | `hc-flop` |

## Quick start

```bash
pip install -e ".[dev]"

# Run pre-flop analysis (1 million hands per starting-hand bucket)
hc-preflop --simulations 1_000_000

# Run flop analysis
hc-flop --simulations 1_000_000
```

Results (CSV + charts) are written to `results/`.

## Game rules (Holland Casino variant)

* Player posts **Ante** + **Blind** (equal size).
* Optional **Trips** side bet.
* Pre-flop: raise **4× Ante** *or* check.
* Flop (3 community cards): raise **2× Ante** *or* check.
* River (turn + river together): raise **1× Ante** *or* fold.
* The **best 5-card hand** (out of 7) is always compared, regardless of whether the dealer qualifies.
* Dealer **qualifies** with **pair or better**.

### Payout table

| Situation | Ante | Play | Blind |
|---|---|---|---|
| Dealer qualifies, player wins | +1 | +multiplier | see below |
| Dealer qualifies, tie | push | push | push |
| Dealer qualifies, dealer wins | −1 | −multiplier | −1 |
| Dealer **does not** qualify, player wins | **push** ¹ | +multiplier | see below |
| Dealer **does not** qualify, tie | push | push | push |
| Dealer **does not** qualify, dealer wins | **−1** | −multiplier | **−1** |
| Player folds (river) | −1 | — | −1 |

> ¹ **Assumption:** when the dealer does not qualify *and* the player has the better hand, the Ante pushes.
> If Holland Casino pays the Ante 1:1 in this situation, please open an issue to correct this.
>
> **Key rule confirmed by the user:** if the dealer does not qualify but holds the stronger 5-card hand, the player **loses all bets** (Ante + Play + Blind).

### Blind bonus payouts (player must win the hand comparison)

| Player hand | Blind pays |
|---|---|
| Straight | 1:1 |
| Flush | 3:2 |
| Full house | 3:1 |
| Four of a kind | 10:1 |
| Straight flush | 50:1 |
| Royal flush | 500:1 |
| Less than straight | push |

### Trips side bet

| Player hand | Pays |
|---|---|
| Three of a kind | 3:1 |
| Straight | 4:1 |
| Flush | 7:1 |
| Full house | 8:1 |
| Four of a kind | 30:1 |
| Straight flush | 40:1 |
| Royal flush | 50:1 |
| Less than three of a kind | −1 |

## Development

```bash
# Lint
ruff check src tests

# Type-check
mypy

# Test
pytest
```

## CI / GitHub Actions

* **CI** (`ci.yml`): runs on every push and pull request — lint, type-check, tests.
* **Simulate** (`simulate.yml`): manually triggered workflow; configurable number of simulations; uploads result artifacts.

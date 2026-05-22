# hc-stats: Ultimate Texas Hold'em Strategy Analyser

Monte Carlo simulation engine for analysing optimal strategy in **Ultimate Texas Hold'em** as played at **Holland Casino**.

Runs millions of simulated hands to answer two practical questions:

1. **Which starting hands should you raise 4× before the flop?**
2. **When you hold a face-card and the flop pairs — should you bet 2×?**

---

## How to run the analyses (no install needed)

The easiest way is to run the analyses directly on GitHub using the built-in workflow.

### Step 1 — Go to the Actions tab

Open [Actions → Run Simulations](https://github.com/hermanops/hc-stats/actions/workflows/simulate.yml) in your browser.

### Step 2 — Trigger the workflow

Click **"Run workflow"** (top-right of the runs list), fill in the inputs, then click the green button.

| Input | Description | Default |
|---|---|---|
| `simulations` | Hands simulated per starting-hand bucket | `500000` |
| `seed` | Random seed for reproducibility | `42` |
| `analysis` | `preflop`, `flop`, or `both` | `both` |

> For reliable results use at least **500 000**. For publication-quality results use **1 000 000** (takes ~10 min).

### Step 3 — Download the results

Once the run finishes (green checkmark), click into the run and scroll to **Artifacts** at the bottom. Download `simulation-results-<N>`.

The ZIP contains:

```
results/
  preflop_ev.csv          – EV per starting hand (4× raise vs fold)
  preflop_ev.png          – heatmap of EV delta by hand bucket
  flop_facecard_pair.csv  – EV per scenario (bet 2× vs check)
  flop_facecard_pair.png  – bar chart of EV by flop scenario
```

---

## Run locally

```bash
# Install
pip install -e ".[dev]"

# Pre-flop: which hands to raise 4×?
hc-preflop --simulations 1_000_000 --output-dir results

# Flop: bet 2× with face-card high when flop pairs?
hc-flop --simulations 1_000_000 --output-dir results
```

All options:

```
hc-preflop --help
hc-flop    --help
```

---

## How the simulation works

Each simulated hand:

1. Deals 2 hole cards and 5 community cards from a shuffled 52-card deck.
2. Plays the hand under the **strategy under test** (e.g. always raise 4× pre-flop).
3. Compares hands using best-5-of-7 evaluation (via the [treys](https://github.com/ihendley/treys) library).
4. Resolves all bets (Ante, Play, Blind, Trips) according to Holland Casino rules.
5. Records the net result in units of the Ante bet.

Results are grouped into **buckets** (e.g. `AKs`, `TT`, `72o`) and the **expected value (EV)** is computed per bucket, comparing the strategy under test against the fold/check baseline.

---

## Game rules (Holland Casino variant)

* Player posts **Ante** + **Blind** (equal size). Optional **Trips** side bet.
* **Pre-flop:** raise **4× Ante** *or* check.
* **Flop** (3 community cards): raise **2× Ante** *or* check (only if checked pre-flop).
* **River** (turn + river together): raise **1× Ante** *or* fold (only if checked both earlier streets).
* The **best 5-card hand** out of 7 is always compared — even if the dealer does not qualify.
* Dealer **qualifies** with a **pair or better**.

### Payout table

| Situation | Ante | Play | Blind |
|---|---|---|---|
| Dealer qualifies, player wins | +1 | +bet | Blind bonus (see below) |
| Dealer qualifies, tie | push | push | push |
| Dealer qualifies, dealer wins | −1 | −bet | −1 |
| Dealer **does not qualify**, player wins | push ¹ | +bet | Blind bonus |
| Dealer **does not qualify**, tie | push | push | push |
| Dealer **does not qualify**, dealer wins | **−1** | **−bet** | **−1** |
| Player folds (river) | −1 | — | −1 |

> ¹ **Open question (see [Issue #1](https://github.com/hermanops/hc-stats/issues/1)):** when the dealer does not qualify *and* the player wins, the Ante is currently assumed to **push**. If Holland Casino pays 1:1 here, please confirm and close the issue.
>
> **Confirmed rule:** if the dealer does not qualify but holds the stronger hand, the player **loses all bets** (Ante + Play + Blind).

### Blind bonus (only paid when player wins the hand)

| Hand | Blind pays |
|---|---|
| Royal flush | 500:1 |
| Straight flush | 50:1 |
| Four of a kind | 10:1 |
| Full house | 3:1 |
| Flush | 3:2 |
| Straight | 1:1 |
| Less than straight | push |

### Trips side bet (always paid on player's hand, win or lose)

| Hand | Trips pays |
|---|---|
| Royal flush | 50:1 |
| Straight flush | 40:1 |
| Four of a kind | 30:1 |
| Full house | 8:1 |
| Flush | 7:1 |
| Straight | 4:1 |
| Three of a kind | 3:1 |
| Less | −1 |

---

## Project structure

```
src/hc_stats/
  deck.py          – Card and Deck (integer-encoded)
  evaluator.py     – Hand ranking (wraps treys), payout tables
  game.py          – Single-hand engine, bet resolution
  simulation.py    – Monte Carlo runner, per-bucket statistics
  analysis.py      – Hand buckets (hole_key), filters, strategy functions
  scripts/
    run_preflop.py – hc-preflop entry point
    run_flop.py    – hc-flop entry point
tests/             – 31 unit & integration tests
.github/workflows/
  ci.yml           – Lint + type-check + tests on every push / PR
  simulate.yml     – Manual simulation workflow with artifact upload
```

---

## Development

```bash
pip install -e ".[dev]"

ruff check src tests   # lint
mypy                   # type-check
pytest                 # run all 31 tests
```

CI runs automatically on every push via GitHub Actions.

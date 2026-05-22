"""Pre-flop 4× raise analysis.

For each of the 169 canonical starting hands, compares the EV of:
  - always raising 4× pre-flop (then 2× flop, 1× river)
  - never raising pre-flop      (then 2× flop, 1× river)

Hands where EV(4×) > EV(check) should be raised 4× pre-flop.

Results are written to results/preflop_ev.csv and results/preflop_ev.png.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd  # type: ignore[import-untyped]
import seaborn as sns  # type: ignore[import-untyped]
from rich.console import Console
from rich.table import Table

from hc_stats.analysis import (
    key_by_hole,
    strategy_check_preflop_bet_flop,
    strategy_preflop_4x_only,
)
from hc_stats.simulation import run_simulation

RESULTS_DIR = Path("results")
console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-flop 4× EV analysis")
    parser.add_argument("--simulations", type=int, default=500_000,
                        help="Number of hands per strategy (default: 500,000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    console.rule("[bold blue]Pre-flop 4× Raise Analysis")

    console.print("\n[cyan]Running strategy: always 4× pre-flop…")
    stats_4x = run_simulation(
        strategy_preflop_4x_only,
        key_by_hole,
        args.simulations,
        seed=args.seed,
    )

    console.print("\n[cyan]Running strategy: check pre-flop (bet 2× flop)…")
    stats_check = run_simulation(
        strategy_check_preflop_bet_flop,
        key_by_hole,
        args.simulations,
        seed=args.seed + 1,
    )

    # Build comparison dataframe
    all_hands = sorted(set(stats_4x) | set(stats_check))
    rows = []
    for hand in all_hands:
        s4 = stats_4x.get(hand)
        sc = stats_check.get(hand)
        if s4 and sc:
            rows.append({
                "hand": hand,
                "ev_4x": s4.ev,
                "ev_check": sc.ev,
                "ev_diff": s4.ev - sc.ev,
                "count_4x": s4.count,
                "count_check": sc.count,
                "sem_4x": s4.sem,
                "sem_check": sc.sem,
                "raise_4x": (s4.ev - sc.ev) > 0,
            })

    df = pd.DataFrame(rows).sort_values("ev_diff", ascending=False)

    # Save CSV
    csv_path = args.output_dir / "preflop_ev.csv"
    df.to_csv(csv_path, index=False)
    console.print(f"\n[green]CSV saved → {csv_path}")

    # Print top / bottom hands
    _print_table(df, "hands where 4× is better (raise)", df[df["raise_4x"]].head(20))
    _print_table(df, "hands where CHECK is better (don't raise)", df[~df["raise_4x"]].head(20))

    # Plot EV comparison heatmap
    _plot_heatmap(df, args.output_dir / "preflop_ev.png")
    console.print(f"[green]Chart saved → {args.output_dir / 'preflop_ev.png'}")


def _print_table(df: pd.DataFrame, title: str, subset: pd.DataFrame) -> None:
    table = Table(title=title, show_header=True)
    table.add_column("Hand", style="bold")
    table.add_column("EV 4×", justify="right")
    table.add_column("EV check", justify="right")
    table.add_column("Diff", justify="right")
    for _, row in subset.iterrows():
        color = "green" if row["raise_4x"] else "red"
        table.add_row(
            f"[{color}]{row['hand']}",
            f"{row['ev_4x']:.4f}",
            f"{row['ev_check']:.4f}",
            f"{row['ev_diff']:+.4f}",
        )
    console.print(table)


def _plot_heatmap(df: pd.DataFrame, path: Path) -> None:
    """Plot a 13×13 heatmap of EV diff (4× minus check)."""
    ranks_order = list("AKQJT98765432")
    # Build pivot table
    import numpy as np

    matrix = pd.DataFrame(index=ranks_order, columns=ranks_order, dtype=float)
    matrix[:] = np.nan

    for _, row in df.iterrows():
        hand = row["hand"]
        if len(hand) == 2:
            r1, r2 = hand[0], hand[1]
            matrix.loc[r1, r2] = row["ev_diff"]
            matrix.loc[r2, r1] = row["ev_diff"]
        elif len(hand) == 3:
            r1, r2, suit = hand[0], hand[1], hand[2]
            if suit == "s":
                matrix.loc[r1, r2] = row["ev_diff"]
            else:
                matrix.loc[r2, r1] = row["ev_diff"]

    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        matrix.astype(float),
        center=0,
        cmap="RdYlGn",
        annot=True,
        fmt=".2f",
        linewidths=0.5,
        ax=ax,
    )
    ax.set_title("Pre-flop EV diff: 4× raise minus check\n(green = raise 4×, red = check)")
    ax.set_xlabel("Lower card rank  (off-suit = lower-left triangle)")
    ax.set_ylabel("Higher card rank  (suited = upper-right triangle)")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

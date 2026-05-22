"""Flop betting analysis: face-card high + paired flop.

Question: when the flop contains a pair AND your highest hole card is a face
card (J/Q/K/A), should you bet 2× on the flop?

Compares EV of:
  - bet 2× on flop (after checking pre-flop)
  - check flop     (then bet 1× river)

Results written to results/flop_facecard_pair.csv and .png.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from rich.console import Console
from rich.table import Table

from hc_stats.analysis import (
    key_flop_pair_facecard,
    strategy_check_preflop_bet_flop,
    strategy_check_preflop_check_flop,
)
from hc_stats.simulation import run_simulation

RESULTS_DIR = Path("results")
console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flop analysis: face-card high + paired flop"
    )
    parser.add_argument("--simulations", type=int, default=1_000_000,
                        help="Total hands to simulate (default: 1,000,000)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    console.rule("[bold blue]Flop Analysis: Face-Card High + Paired Flop")

    console.print(
        "\n[dim]Only counting hands where flop has a pair AND player's best "
        "hole card is J/Q/K/A[/dim]"
    )

    console.print("\n[cyan]Running strategy: check pre-flop → bet 2× flop…")
    stats_bet = run_simulation(
        strategy_check_preflop_bet_flop,
        key_flop_pair_facecard,
        args.simulations,
        seed=args.seed,
    )

    console.print("\n[cyan]Running strategy: check pre-flop → check flop → bet 1× river…")
    stats_check = run_simulation(
        strategy_check_preflop_check_flop,
        key_flop_pair_facecard,
        args.simulations,
        seed=args.seed + 1,
    )

    all_hands = sorted(set(stats_bet) | set(stats_check))
    rows = []
    for hand in all_hands:
        sb = stats_bet.get(hand)
        sc = stats_check.get(hand)
        if sb and sc:
            rows.append({
                "hand": hand,
                "ev_bet_flop": sb.ev,
                "ev_check_flop": sc.ev,
                "ev_diff": sb.ev - sc.ev,
                "count_bet": sb.count,
                "count_check": sc.count,
                "sem_bet": sb.sem,
                "sem_check": sc.sem,
                "bet_flop": (sb.ev - sc.ev) > 0,
            })

    df = pd.DataFrame(rows).sort_values("ev_diff", ascending=False)

    csv_path = args.output_dir / "flop_facecard_pair.csv"
    df.to_csv(csv_path, index=False)
    console.print(f"\n[green]CSV saved → {csv_path}")

    _print_table(df, "bet 2× on flop (better)", df[df["bet_flop"]])
    _print_table(df, "check flop (better)", df[~df["bet_flop"]])

    _plot_bar(df, args.output_dir / "flop_facecard_pair.png")
    console.print(f"[green]Chart saved → {args.output_dir / 'flop_facecard_pair.png'}")

    # Summary
    n_bet = df["bet_flop"].sum()
    n_check = (~df["bet_flop"]).sum()
    console.print(
        f"\n[bold]Summary:[/bold] {n_bet} hand types → bet flop | "
        f"{n_check} hand types → check flop"
    )


def _print_table(df: pd.DataFrame, title: str, subset: pd.DataFrame) -> None:
    table = Table(title=title, show_header=True)
    table.add_column("Hand", style="bold")
    table.add_column("EV bet flop", justify="right")
    table.add_column("EV check flop", justify="right")
    table.add_column("Diff", justify="right")
    for _, row in subset.iterrows():
        color = "green" if row["bet_flop"] else "red"
        table.add_row(
            f"[{color}]{row['hand']}",
            f"{row['ev_bet_flop']:.4f}",
            f"{row['ev_check_flop']:.4f}",
            f"{row['ev_diff']:+.4f}",
        )
    console.print(table)


def _plot_bar(df: pd.DataFrame, path: Path) -> None:
    df_sorted = df.sort_values("ev_diff", ascending=True)
    colors = ["green" if v > 0 else "red" for v in df_sorted["ev_diff"]]

    fig, ax = plt.subplots(figsize=(max(12, len(df_sorted) * 0.4), 6))
    ax.bar(df_sorted["hand"], df_sorted["ev_diff"], color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Starting hand")
    ax.set_ylabel("EV diff (bet flop − check flop)")
    ax.set_title(
        "Flop bet 2× vs check: EV difference\n"
        "Filter: flop has pair + player's best card is J/Q/K/A\n"
        "Green = bet flop is better | Red = check flop is better"
    )
    plt.xticks(rotation=90, fontsize=7)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from utils.benchmark import get_btc_returns
from utils.evaluation import sharpe_ratio, max_drawdown


INITIAL_CAPITAL = 1000
PERIODS_PER_YEAR = 365

RESULTS_DIR = Path("results")
OUTPUT_DIR = RESULTS_DIR / "combined_plus_btc"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    strategy_returns = pd.read_csv(
        RESULTS_DIR / "strategy_returns.csv",
        index_col=0,
        parse_dates=True,
    )

    best_combos = pd.read_csv(
        RESULTS_DIR / "combinations" / "best_combinations.csv"
    )

    best = best_combos.sort_values("sharpe", ascending=False).iloc[0]

    left = best["left_strategy"]
    right = best["right_strategy"]

    left_weight = best["left_weight"]
    right_weight = best["right_weight"]

    best_combined_returns = (
        strategy_returns[left] * left_weight
        + strategy_returns[right] * right_weight
    )

    btc_returns = get_btc_returns(
        start_ts=best_combined_returns.index.min(),
        end_ts=best_combined_returns.index.max(),
    )

    aligned = pd.concat(
        [best_combined_returns, btc_returns],
        axis=1,
    ).dropna()

    aligned.columns = ["combined_strategy", "btc"]

    weight_rows = []

    for w in np.arange(0, 1.05, 0.05):
        # w = weight in combined strategy
        # 1-w = weight in BTC
        portfolio_returns = (
            w * aligned["combined_strategy"]
            + (1 - w) * aligned["btc"]
        )

        wealth = (1 + portfolio_returns).cumprod() * INITIAL_CAPITAL

        row = {
            "combined_strategy_weight": w,
            "btc_weight": 1 - w,
            "final_value": wealth.iloc[-1],
            "profit": wealth.iloc[-1] - INITIAL_CAPITAL,
            "sharpe": sharpe_ratio(portfolio_returns, PERIODS_PER_YEAR),
            "max_drawdown": max_drawdown(wealth),
        }

        weight_rows.append(row)

    weight_df = pd.DataFrame(weight_rows)
    weight_df.to_csv(
        OUTPUT_DIR / "combined_strategy_btc_weight_scan.csv",
        index=False,
    )

    best_row = weight_df.sort_values("sharpe", ascending=False).iloc[0]
    best_row.to_frame().T.to_csv(
        OUTPUT_DIR / "best_combined_strategy_btc_mix.csv",
        index=False,
    )

    print("\nCombined Strategy + BTC weight scan:")
    print(weight_df)

    print("\nBest mix:")
    print(best_row)

    # Plot Sharpe by weight
    plt.figure(figsize=(10, 5))
    plt.plot(
        weight_df["combined_strategy_weight"],
        weight_df["sharpe"],
        marker="o",
    )
    plt.title("Combined Strategy + BTC Weight Scan")
    plt.xlabel("Combined Strategy Weight")
    plt.ylabel("Sharpe Ratio")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "combined_strategy_btc_weight_scan.png",
        dpi=200,
    )
    plt.close()

    # Plot best equity curve
    w = best_row["combined_strategy_weight"]

    best_returns = (
        w * aligned["combined_strategy"]
        + (1 - w) * aligned["btc"]
    )

    combined_wealth = (
        1 + aligned["combined_strategy"]
    ).cumprod() * INITIAL_CAPITAL

    btc_wealth = (
        1 + aligned["btc"]
    ).cumprod() * INITIAL_CAPITAL

    best_wealth = (
        1 + best_returns
    ).cumprod() * INITIAL_CAPITAL

    plt.figure(figsize=(12, 6))
    plt.plot(combined_wealth, label="Best Alpha Portfolio")
    plt.plot(btc_wealth, label="BTC Buy & Hold")
    plt.plot(best_wealth, label="Alpha Portfolio + BTC Mix", linewidth=2.5)

    plt.title("Alpha Portfolio + BTC Mix")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "alpha_portfolio_btc_mix_equity_curve.png",
        dpi=200,
    )
    plt.close()


if __name__ == "__main__":
    main()
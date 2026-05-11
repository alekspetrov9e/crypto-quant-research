import os
from pathlib import Path

from utils.benchmark import (
    get_strategy_returns_from_csv,
    get_btc_returns,
    run_ols_alpha_beta,
    benchmark_summary,
    save_alpha_report,
)


INITIAL_CAPITAL = 1000

STRATEGY_NAME = "Breadth_Weighted_Momentum_Final"

TWSQROOT = os.environ['TWSQROOT']

POS_PNL_PATH = (
    Path(TWSQROOT)
    / "alphas"
    / STRATEGY_NAME
    / "backtest"
    / "pos_pnl.csv"
)

if not POS_PNL_PATH.exists():
    raise FileNotFoundError(
        f"Could not find pos_pnl.csv at: {POS_PNL_PATH}"
    )

OUTPUT_DIR = Path("results") / "benchmark"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    strategy_returns = get_strategy_returns_from_csv(
        POS_PNL_PATH,
        initial_capital=INITIAL_CAPITAL,
    )

    start_ts = strategy_returns.index.min()
    end_ts = strategy_returns.index.max()

    btc_returns = get_btc_returns(start_ts=start_ts, end_ts=end_ts)

    alpha_results = run_ols_alpha_beta(
        strategy_returns,
        btc_returns,
        periods_per_year=365,
    )

    summary = benchmark_summary(
        strategy_returns,
        btc_returns,
        periods_per_year=365,
    )

    print("\nBenchmark summary:")
    print(summary)

    print("\nOLS alpha/beta results:")
    print("Daily alpha:", alpha_results["alpha_daily"])
    print("Annual alpha:", alpha_results["alpha_annual"])
    print("Beta vs BTC:", alpha_results["beta"])
    print("R-squared:", alpha_results["r_squared"])
    print("Information ratio:", alpha_results["information_ratio"])
    print("Alpha t-stat:", alpha_results["t_stat_alpha"])
    print("Alpha p-value:", alpha_results["p_value_alpha"])

    print("\nFull regression summary:")
    print(alpha_results["model"].summary())

    summary.to_csv(OUTPUT_DIR / f"{STRATEGY_NAME}_benchmark_summary.csv", index=False)

    save_alpha_report(
        alpha_results,
        OUTPUT_DIR / f"{STRATEGY_NAME}_alpha_report.csv",
    )


if __name__ == "__main__":
    main()
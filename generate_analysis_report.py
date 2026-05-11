from pathlib import Path
from utils.combined_analysis import analyze_combined_strategy
import numpy as np
import pandas as pd

from strategies.MovingAverageSignalProportionDynamicUniverse import (
    MovingAverageSignalProportionDynamicUniverse,
)
from strategies.BreadthWeightedMomentum import BreadthWeightedMomentum
from strategies.CapitulationBounceDaily import CapitulationBounceDaily
from strategies.CapitulationBounceSelective import CapitulationBounceSelective

from utils.evaluation import (
    make_summary_table,
    make_correlation_table,
    make_returns_table,
    evaluate_combination,
    combine_returns,
)

from utils.benchmark import (
    get_strategy_returns_from_result,
    get_btc_returns,
    run_ols_alpha_beta,
    benchmark_summary,
)

from utils.plotting import (
    save_equity_curves,
    save_drawdowns,
    save_correlation_heatmap,
    save_metric_bar_chart,
    save_weight_scan_plot,
)


INITIAL_CAPITAL = 1000
START_DATE = "2021-01-01"
FREQ = "1d"

TAKER_FEE = 0.0026
MAKER_FEE = 0.0016
SLIP = 0.001

RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
BENCHMARK_DIR = RESULTS_DIR / "benchmark"
COMBINATIONS_DIR = RESULTS_DIR / "combinations"

for directory in [RESULTS_DIR, FIGURES_DIR, BENCHMARK_DIR, COMBINATIONS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


def run_backtests():
    results = {}

    print("Running momentum...")
    results["momentum"] = MovingAverageSignalProportionDynamicUniverse.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Momentum_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running breadth...")
    results["breadth"] = BreadthWeightedMomentum.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Breadth_Weighted_Momentum_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running capitulation daily...")
    results["capitulation_daily"] = CapitulationBounceDaily.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Capitulation_Bounce_Daily_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running capitulation selective...")
    results["capitulation_selective"] = CapitulationBounceSelective.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Capitulation_Bounce_Selective_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    return results


def analyze_standalone_strategies(results):
    summary = make_summary_table(
        results,
        initial_capital=INITIAL_CAPITAL,
        periods_per_year=365,
    )

    correlations = make_correlation_table(
        results,
        initial_capital=INITIAL_CAPITAL,
    )

    returns = make_returns_table(
        results,
        initial_capital=INITIAL_CAPITAL,
    )

    summary.to_csv(RESULTS_DIR / "summary_metrics.csv", index=False)
    correlations.to_csv(RESULTS_DIR / "correlations.csv")

    save_equity_curves(
        results,
        FIGURES_DIR / "equity_curves.png",
        initial_capital=INITIAL_CAPITAL,
    )

    save_drawdowns(
        results,
        FIGURES_DIR / "drawdowns.png",
        initial_capital=INITIAL_CAPITAL,
    )

    save_correlation_heatmap(
        correlations,
        FIGURES_DIR / "correlation_heatmap.png",
    )

    save_metric_bar_chart(
        summary,
        metric="sharpe",
        output_path=FIGURES_DIR / "sharpe_bar_chart.png",
        title="Sharpe Ratio by Strategy",
    )

    save_metric_bar_chart(
        summary,
        metric="max_drawdown",
        output_path=FIGURES_DIR / "max_drawdown_bar_chart.png",
        title="Maximum Drawdown by Strategy",
    )

    save_metric_bar_chart(
        summary,
        metric="turnover_multiple",
        output_path=FIGURES_DIR / "turnover_bar_chart.png",
        title="Turnover Multiple by Strategy",
    )

    return summary, correlations, returns


def analyze_vs_btc(results):
    alpha_rows = []
    benchmark_rows = []

    for name, result in results.items():
        strategy_returns = get_strategy_returns_from_result(
            result,
            initial_capital=INITIAL_CAPITAL,
        )

        btc_returns = get_btc_returns(
            start_ts=strategy_returns.index.min(),
            end_ts=strategy_returns.index.max(),
        )

        alpha_result = run_ols_alpha_beta(
            strategy_returns,
            btc_returns,
            periods_per_year=365,
        )

        alpha_rows.append(
            {
                "strategy": name,
                "alpha_daily": alpha_result["alpha_daily"],
                "alpha_annual": alpha_result["alpha_annual"],
                "beta_vs_btc": alpha_result["beta"],
                "r_squared": alpha_result["r_squared"],
                "information_ratio": alpha_result["information_ratio"],
                "alpha_t_stat": alpha_result["t_stat_alpha"],
                "alpha_p_value": alpha_result["p_value_alpha"],
            }
        )

        bench = benchmark_summary(
            strategy_returns,
            btc_returns,
            periods_per_year=365,
        )

        bench["strategy_name"] = name
        benchmark_rows.append(bench)

    alpha_df = pd.DataFrame(alpha_rows)
    benchmark_df = pd.concat(benchmark_rows, ignore_index=True)

    alpha_df.to_csv(BENCHMARK_DIR / "alpha_beta_summary.csv", index=False)
    benchmark_df.to_csv(BENCHMARK_DIR / "benchmark_metrics.csv", index=False)

    save_metric_bar_chart(
        alpha_df.rename(columns={"strategy": "strategy"}),
        metric="alpha_annual",
        output_path=FIGURES_DIR / "annual_alpha_bar_chart.png",
        title="Annualized Alpha vs BTC",
    )

    save_metric_bar_chart(
        alpha_df.rename(columns={"strategy": "strategy"}),
        metric="beta_vs_btc",
        output_path=FIGURES_DIR / "beta_vs_btc_bar_chart.png",
        title="Beta vs BTC",
    )

    return alpha_df, benchmark_df


def analyze_combinations(returns):
    combo_rows = []

    candidate_pairs = [
        ("momentum", "capitulation_daily"),
        ("momentum", "capitulation_selective"),
        ("breadth", "capitulation_daily"),
        ("breadth", "capitulation_selective"),
    ]

    best_rows = []

    for left, right in candidate_pairs:
        pair_returns = returns[[left, right]].dropna()
        rows = []

        for w in np.arange(0, 1.05, 0.05):
            weights = {
                left: w,
                right: 1 - w,
            }

            result = evaluate_combination(
                pair_returns,
                weights,
                initial_capital=INITIAL_CAPITAL,
                periods_per_year=365,
            )

            row = {
                "left_strategy": left,
                "right_strategy": right,
                "left_weight": w,
                "right_weight": 1 - w,
                "final_value": result["final_value"],
                "profit": result["profit"],
                "sharpe": result["sharpe"],
                "max_drawdown": result["max_drawdown"],
            }

            rows.append(row)
            combo_rows.append(row)

        pair_df = pd.DataFrame(rows)
        pair_df.to_csv(
            COMBINATIONS_DIR / f"weight_scan_{left}_{right}.csv",
            index=False,
        )

        best = pair_df.sort_values("sharpe", ascending=False).iloc[0].to_dict()
        best_rows.append(best)

        if left == "momentum" and right == "capitulation_daily":
            save_weight_scan_plot(
                pair_df.rename(columns={"left_weight": "momentum_weight"}),
                FIGURES_DIR / "momentum_capitulation_weight_scan.png",
            )

    all_combos = pd.DataFrame(combo_rows)
    best_combos = pd.DataFrame(best_rows)

    all_combos.to_csv(COMBINATIONS_DIR / "all_combination_weight_scans.csv", index=False)
    best_combos.to_csv(COMBINATIONS_DIR / "best_combinations.csv", index=False)

    return all_combos, best_combos


def main():
    results = run_backtests()

    summary, correlations, returns = analyze_standalone_strategies(results)
    alpha_df, benchmark_df = analyze_vs_btc(results)
    all_combos, best_combos = analyze_combinations(returns)

    print("\nSummary metrics:")
    print(summary)

    print("\nCorrelations:")
    print(correlations)

    print("\nAlpha/Beta vs BTC:")
    print(alpha_df)

    print("\nBest combinations:")
    print(best_combos)

    # ==========================================
    # ANALYZE BEST COMBINED STRATEGY
    # ==========================================

    best_combo = best_combos.sort_values(
        "sharpe",
        ascending=False
    ).iloc[0]

    left = best_combo["left_strategy"]
    right = best_combo["right_strategy"]

    weights = {
        left: best_combo["left_weight"],
        right: best_combo["right_weight"],
    }

    pair_returns = returns[[left, right]].dropna()

    combined_returns = (
            pair_returns[left] * weights[left]
            + pair_returns[right] * weights[right]
    )

    from utils.benchmark import get_btc_returns

    btc_returns = get_btc_returns(
        start_ts=combined_returns.index.min(),
        end_ts=combined_returns.index.max(),
    )

    analyze_combined_strategy(
        combined_returns=combined_returns,
        btc_returns=btc_returns,
        weights=weights,
        output_dir="results/combined",
        initial_capital=INITIAL_CAPITAL,
        periods_per_year=365,
    )

    print("\nBest combined strategy analyzed successfully.")


if __name__ == "__main__":
    main()
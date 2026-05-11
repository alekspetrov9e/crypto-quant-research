import numpy as np
import pandas as pd

from strategies.MovingAverageSignalProportionDynamicUniverse import MovingAverageSignalProportionDynamicUniverse
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

from utils.data_helpers import (
    save_summary_metrics,
    save_correlations,
)

from utils.plotting import (
    plot_equity_curves,
    plot_drawdowns,
    plot_correlation_heatmap,
    plot_combined_vs_components,
    plot_weight_scan,
)


INITIAL_CAPITAL = 1000
START_DATE = "2021-01-01"
FREQ = "1d"

# DEFAULT FEES
TAKER_FEE = 0.0026
MAKER_FEE = 0.0016
SLIP = 0.001


def run_all_backtests():
    print("Running momentum strategy...")
    result_momentum = MovingAverageSignalProportionDynamicUniverse.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Momentum_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running breadth-weighted momentum strategy...")
    result_breadth = BreadthWeightedMomentum.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Breadth_Weighted_Momentum_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running daily capitulation bounce strategy...")
    result_capitulation_daily = CapitulationBounceDaily.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Capitulation_Bounce_Daily_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    print("Running selective capitulation bounce strategy...")
    result_capitulation_selective = CapitulationBounceSelective.run_backtest(
        start_ts=START_DATE,
        freq=FREQ,
        name="Capitulation_Bounce_Selective_Final",
        taker_fee=TAKER_FEE,
        maker_fee=MAKER_FEE,
        slip=SLIP,
    )

    return {
        "momentum": result_momentum,
        "breadth": result_breadth,
        "capitulation daily": result_capitulation_daily,
        "capitulation selective": result_capitulation_selective
    }


def analyze_results(results):
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

    print("\nSummary metrics:")
    print(summary)

    print("\nCorrelations:")
    print(correlations)

    save_summary_metrics(summary, "results/summary_metrics.csv")
    save_correlations(correlations, "results/correlations.csv")

    plot_equity_curves(results, initial_capital=INITIAL_CAPITAL)
    plot_drawdowns(results, initial_capital=INITIAL_CAPITAL)
    plot_correlation_heatmap(correlations)

    return summary, correlations, returns


def scan_momentum_capitulation_weights(returns):
    weight_results = []

    pair_returns = returns[["momentum", "capitulation daily"]].dropna()

    for w in np.arange(0, 1.05, 0.05):
        weights = {
            "momentum": w,
            "capitulation daily": 1 - w,
        }

        result = evaluate_combination(
            pair_returns,
            weights,
            initial_capital=INITIAL_CAPITAL,
            periods_per_year=365,
        )

        result["momentum_weight"] = w
        result["capitulation_weight"] = 1 - w

        weight_results.append(result)

    weight_df = pd.DataFrame(weight_results)
    weight_df.to_csv("results/weight_scan_momentum_capitulation.csv", index=False)

    print("\nMomentum/Capitulation weight scan:")
    print(weight_df)

    plot_weight_scan(weight_df)

    best_row = weight_df.sort_values("sharpe", ascending=False).iloc[0]

    print("\nBest combination:")
    print(best_row)

    best_weights = {
        "momentum": best_row["momentum_weight"],
        "capitulation daily": best_row["capitulation_weight"],
    }

    combined_returns = combine_returns(pair_returns, best_weights)

    plot_combined_vs_components(
        pair_returns,
        combined_returns,
        initial_capital=INITIAL_CAPITAL,
        title="Momentum + Daily  Capitulation Combined Portfolio",
    )

    return weight_df


if __name__ == "__main__":
    results = run_all_backtests()
    summary, correlations, returns = analyze_results(results)
    weight_scan = scan_momentum_capitulation_weights(returns)
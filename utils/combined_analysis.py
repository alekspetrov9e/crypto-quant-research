import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

from utils.evaluation import evaluate_combination
from utils.benchmark import (
    run_ols_alpha_beta,
    benchmark_summary,
)

def analyze_combined_strategy(
    combined_returns,
    btc_returns,
    weights,
    output_dir,
    initial_capital=1000,
    periods_per_year=365,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # PERFORMANCE METRICS
    # ==========================================

    metrics = evaluate_combination(
        combined_returns.to_frame("combined"),
        {"combined": 1.0},
        initial_capital=initial_capital,
        periods_per_year=periods_per_year,
    )

    metrics_df = pd.DataFrame([metrics])
    metrics_df["weights"] = str(weights)

    metrics_df.to_csv(
        output_dir / "best_combined_metrics.csv",
        index=False,
    )

    # ==========================================
    # BENCHMARK / ALPHA ANALYSIS
    # ==========================================

    alpha_report = run_ols_alpha_beta(
        combined_returns,
        btc_returns,
        periods_per_year=periods_per_year,
    )

    alpha_df = pd.DataFrame([alpha_report])

    alpha_df.to_csv(
        output_dir / "best_combined_alpha_report.csv",
        index=False,
    )

    benchmark_df = benchmark_summary(
        combined_returns,
        btc_returns,
        periods_per_year=periods_per_year,
    )

    benchmark_df.to_csv(
        output_dir / "best_combined_benchmark_summary.csv",
        index=False,
    )

    # ==========================================
    # EQUITY CURVE
    # ==========================================

    aligned = pd.concat(
        [combined_returns, btc_returns],
        axis=1
    ).dropna()

    aligned.columns = ["combined", "btc"]

    strategy_wealth = (1 + aligned["combined"]).cumprod() * initial_capital

    btc_wealth = (1 + aligned["btc"]).cumprod() * initial_capital

    plt.figure(figsize=(12, 6))

    plt.plot(strategy_wealth, label="Combined Portfolio")
    plt.plot(btc_wealth, label="BTC Buy & Hold")

    plt.title("Combined Strategy vs BTC")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        output_dir / "best_combined_vs_btc.png",
        dpi=200,
    )

    plt.close()

    # ==========================================
    # DRAWDOWN
    # ==========================================

    drawdown = strategy_wealth / strategy_wealth.cummax() - 1

    plt.figure(figsize=(12, 5))

    plt.plot(drawdown)

    plt.title("Combined Strategy Drawdown")
    plt.ylabel("Drawdown")
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        output_dir / "best_combined_drawdown.png",
        dpi=200,
    )

    plt.close()

    return {
        "metrics": metrics_df,
        "alpha": alpha_df,
        "benchmark": benchmark_df,
    }
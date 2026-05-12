from pathlib import Path
import numpy as np
import pandas as pd

from utils.benchmark import get_btc_returns
from utils.evaluation import sharpe_ratio, max_drawdown


INITIAL_CAPITAL = 1000
PERIODS_PER_YEAR = 365

RESULTS_DIR = Path("results")
OUTPUT_DIR = RESULTS_DIR / "regime_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_strategy_returns():
    return pd.read_csv(
        RESULTS_DIR / "strategy_returns.csv",
        index_col=0,
        parse_dates=True,
    )


def compute_regime_metrics(returns, regime_mask, regime_name):
    rows = []

    for col in returns.columns:
        r = returns.loc[regime_mask, col].dropna()

        if len(r) < 30:
            continue

        wealth = (1 + r).cumprod() * INITIAL_CAPITAL

        rows.append(
            {
                "strategy": col,
                "regime": regime_name,
                "num_days": len(r),
                "final_value": wealth.iloc[-1],
                "total_return": wealth.iloc[-1] / INITIAL_CAPITAL - 1,
                "annualized_return": (wealth.iloc[-1] / INITIAL_CAPITAL) ** (PERIODS_PER_YEAR / len(r)) - 1,
                "annualized_volatility": r.std() * np.sqrt(PERIODS_PER_YEAR),
                "sharpe": sharpe_ratio(r, PERIODS_PER_YEAR),
                "max_drawdown": max_drawdown(wealth),
            }
        )

    return rows


def main():
    strategy_returns = load_strategy_returns()

    start_ts = strategy_returns.index.min()
    end_ts = strategy_returns.index.max()

    btc_returns = get_btc_returns(start_ts=start_ts, end_ts=end_ts)

    data = pd.concat(
        [strategy_returns, btc_returns.rename("btc")],
        axis=1,
    ).dropna()

    btc_30d_return = (
        (1 + data["btc"])
        .rolling(30)
        .apply(lambda x: x.prod(), raw=False)
        - 1
    )

    data["btc_30d_return"] = btc_30d_return

    bull_mask = data["btc_30d_return"] > 0
    bear_mask = data["btc_30d_return"] <= 0

    returns_only = data.drop(columns=["btc_30d_return"])

    rows = []
    rows.extend(compute_regime_metrics(returns_only, bull_mask, "BTC bull regime"))
    rows.extend(compute_regime_metrics(returns_only, bear_mask, "BTC bear regime"))

    regime_df = pd.DataFrame(rows)
    regime_df.to_csv(OUTPUT_DIR / "btc_regime_performance.csv", index=False)

    print("\nBTC regime performance:")
    print(regime_df)

    # Also save regime counts
    regime_counts = pd.DataFrame(
        [
            {
                "regime": "BTC bull regime",
                "num_days": int(bull_mask.sum()),
            },
            {
                "regime": "BTC bear regime",
                "num_days": int(bear_mask.sum()),
            },
        ]
    )

    regime_counts.to_csv(OUTPUT_DIR / "btc_regime_counts.csv", index=False)

    print("\nRegime counts:")
    print(regime_counts)


if __name__ == "__main__":
    main()
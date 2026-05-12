from pathlib import Path
import itertools
import pandas as pd

from strategies.MovingAverageSignalProportionDynamicUniverse import (
    MovingAverageSignalProportionDynamicUniverse,
)
from strategies.CapitulationBounceDaily import CapitulationBounceDaily

from utils.evaluation import evaluate_result


INITIAL_CAPITAL = 1000
START_DATE = "2021-01-01"
FREQ = "1d"

TAKER_FEE = 0.0026
MAKER_FEE = 0.0016
SLIP = 0.001

OUTPUT_DIR = Path("results") / "robustness"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class MomentumRobustness(MovingAverageSignalProportionDynamicUniverse):
    def prepare(
        self,
        fast_window=10,
        slow_window=30,
        vol_window=20,
        n_winners=3,
        n_liquid=20,
    ):
        super().prepare()

        self.fast_window = fast_window
        self.slow_window = slow_window
        self.vol_window = vol_window
        self.n_winners = n_winners
        self.n_liquid = n_liquid

        self.lookback = max(
            self.slow_window,
            self.vol_window,
            self.liquidity_window,
        ) + 5


class CapitulationRobustness(CapitulationBounceDaily):
    def prepare(
        self,
        max_return=-0.05,
        min_volume_shock=2.0,
        n_winners=3,
        capital=1000,
    ):
        super().prepare()

        self.max_return = max_return
        self.min_volume_shock = min_volume_shock
        self.n_winners = n_winners
        self.capital = capital


def run_momentum_parameter_sweep():
    rows = []

    fast_windows = [5, 10, 15]
    slow_windows = [20, 30, 50]
    n_winners_values = [2, 3, 5]

    for fast, slow, n_winners in itertools.product(
        fast_windows,
        slow_windows,
        n_winners_values,
    ):
        if fast >= slow:
            continue

        name = f"Momentum_Robust_fast{fast}_slow{slow}_n{n_winners}"

        print(f"Running {name}...")

        result = MomentumRobustness.run_backtest(
            start_ts=START_DATE,
            freq=FREQ,
            name=name,
            taker_fee=TAKER_FEE,
            maker_fee=MAKER_FEE,
            slip=SLIP,
            fast_window=fast,
            slow_window=slow,
            n_winners=n_winners,
        )

        metrics = evaluate_result(
            result=result,
            name=name,
            initial_capital=INITIAL_CAPITAL,
            periods_per_year=365,
        )

        metrics["fast_window"] = fast
        metrics["slow_window"] = slow
        metrics["n_winners"] = n_winners

        rows.append(metrics)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "momentum_parameter_robustness.csv", index=False)

    return df


def run_capitulation_parameter_sweep():
    rows = []

    max_returns = [-0.03, -0.05, -0.07]
    volume_shocks = [1.5, 2.0, 2.5, 3.0]
    n_winners_values = [1, 2, 3]

    for max_return, volume_shock, n_winners in itertools.product(
        max_returns,
        volume_shocks,
        n_winners_values,
    ):
        name = (
            f"Capitulation_Robust_ret{abs(max_return):.2f}"
            f"_vol{volume_shock}_n{n_winners}"
        )

        print(f"Running {name}...")

        result = CapitulationRobustness.run_backtest(
            start_ts=START_DATE,
            freq=FREQ,
            name=name,
            taker_fee=TAKER_FEE,
            maker_fee=MAKER_FEE,
            slip=SLIP,
            max_return=max_return,
            min_volume_shock=volume_shock,
            n_winners=n_winners,
        )

        metrics = evaluate_result(
            result=result,
            name=name,
            initial_capital=INITIAL_CAPITAL,
            periods_per_year=365,
        )

        metrics["max_return"] = max_return
        metrics["min_volume_shock"] = volume_shock
        metrics["n_winners"] = n_winners

        rows.append(metrics)

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DIR / "capitulation_parameter_robustness.csv", index=False)

    return df


def main():
    momentum_df = run_momentum_parameter_sweep()
    capitulation_df = run_capitulation_parameter_sweep()

    print("\nMomentum robustness:")
    print(momentum_df.sort_values("sharpe", ascending=False).head(10))

    print("\nCapitulation robustness:")
    print(capitulation_df.sort_values("sharpe", ascending=False).head(10))


if __name__ == "__main__":
    main()
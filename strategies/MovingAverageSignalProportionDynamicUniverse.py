import pandas as pd
import numpy as np

from strategies.BaseCryptoStrategy import BaseCryptoStrategy


class MovingAverageSignalProportionDynamicUniverse(BaseCryptoStrategy):

    def prepare(self):
        self.prepare_base_universe()

        self.fast_window = 10
        self.slow_window = 30
        self.vol_window = 20

        self.liquidity_window = 20
        self.n_liquid = 20
        self.n_winners = 3

        self.capital = 1000

        self.lookback = max(
            self.slow_window,
            self.vol_window,
            self.liquidity_window
        ) + 5

    def rebalance(self):
        liquid_symbols, data_by_symbol = self.get_liquid_universe(
            lookback=self.lookback,
            freq="1d",
            liquidity_window=self.liquidity_window,
            n_liquid=self.n_liquid,
        )

        if len(liquid_symbols) == 0:
            return

        scores = {}

        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]

            fast_ma = bars["close"].rolling(self.fast_window).mean().iloc[-1]
            slow_ma = bars["close"].rolling(self.slow_window).mean().iloc[-1]

            trend = fast_ma / slow_ma - 1

            returns = np.log(bars["close"]).diff()
            vol = returns.rolling(self.vol_window).std().iloc[-1]

            if pd.isna(trend) or pd.isna(vol) or vol == 0:
                continue

            score = trend / vol

            if score > 0:
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        target = self.empty_target()

        if len(scores_series) > 0:
            n_selected = min(self.n_winners, len(scores_series))

            winners = (
                scores_series
                .sort_values(ascending=False)
                .head(n_selected)
            )

            weights = winners / winners.sum()

            for symbol, weight in weights.items():
                price = self.get_current_price(symbol)
                base = symbol.split("/")[0]

                dollar_allocation = self.capital * weight
                target[base] = dollar_allocation / price

        self.rebalance_to_target(target)
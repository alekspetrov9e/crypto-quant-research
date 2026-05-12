import pandas as pd
import numpy as np

from strategies.BaseCryptoStrategy import BaseCryptoStrategy


class CapitulationBounceDaily(BaseCryptoStrategy):

    def prepare(self):
        self.prepare_base_universe()

        self.liquidity_window = 20
        self.n_liquid = 20

        self.volume_window = 20
        self.vol_window = 20

        self.min_volume_shock = 2.0
        self.max_return = -0.05

        self.n_winners = 3
        self.capital = 1000

        self.lookback = max(
            self.liquidity_window,
            self.volume_window,
            self.vol_window
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

            close = bars["close"]
            volume = bars["volume"]

            one_day_return = close.iloc[-1] / close.iloc[-2] - 1

            avg_volume = volume.iloc[:-1].tail(self.volume_window).mean()
            current_volume = volume.iloc[-1]

            if pd.isna(avg_volume) or avg_volume <= 0:
                continue

            volume_shock = current_volume / avg_volume

            returns = np.log(close).diff()
            vol = returns.rolling(self.vol_window).std().iloc[-1]

            if pd.isna(vol) or vol <= 0:
                continue

            if one_day_return > self.max_return:
                continue

            if volume_shock < self.min_volume_shock:
                continue

            score = (-one_day_return * volume_shock) / vol

            if score > 0:
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        target = self.empty_target()

        if len(scores_series) > 0:
            winners = scores_series.sort_values(ascending=False).head(
                min(self.n_winners, len(scores_series))
            )

            weights = winners / winners.sum()

            for symbol, weight in weights.items():
                price = self.get_current_price(symbol)
                base = symbol.split("/")[0]
                target[base] = (self.capital * weight) / price

        self.rebalance_to_target(target)
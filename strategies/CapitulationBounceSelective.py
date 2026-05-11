from twsq.alpha import Alpha
import pandas as pd
import numpy as np


class CapitulationBounceSelective(Alpha):

    def prepare(self):
        self.candidate_symbols = [
            "BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD", "XRP/USD",
            "AVAX/USD", "LINK/USD", "ADA/USD", "DOGE/USD", "LTC/USD",
            "DOT/USD", "TRX/USD", "ETC/USD", "ATOM/USD", "FIL/USD",
            "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD", "SUI/USD",
            "INJ/USD", "UNI/USD", "AAVE/USD", "XLM/USD", "RUNE/USD",
            "SEI/USD", "TIA/USD", "PEPE/USD", "SHIB/USD", "FET/USD",
        ]

        self.liquidity_window = 20
        self.n_liquid = 20

        self.volume_window = 20
        self.vol_window = 20

        # stricter than before
        self.min_volume_shock = 2.5
        self.max_return = -0.06

        self.n_winners = 2

        # lower exposure because capitulation is risky
        self.capital = 600

        self.lookback = max(
            self.liquidity_window,
            self.volume_window,
            self.vol_window
        ) + 5

    def rebalance(self):
        data_by_symbol = {}
        liquidity_scores = {}

        for symbol in self.candidate_symbols:
            try:
                bars = self.get_lastn_bars(symbol, self.lookback, "1d").copy()
            except Exception:
                continue

            if bars is None or len(bars) < self.lookback:
                continue

            dollar_volume = (
                bars["close"] * bars["volume"]
            ).tail(self.liquidity_window).mean()

            if pd.notna(dollar_volume):
                data_by_symbol[symbol] = bars
                liquidity_scores[symbol] = dollar_volume

        if len(liquidity_scores) == 0:
            return

        liquid_symbols = (
            pd.Series(liquidity_scores)
            .sort_values(ascending=False)
            .head(self.n_liquid)
            .index
            .tolist()
        )

        scores = {}
        market_down_count = 0

        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]
            close = bars["close"]

            one_day_return = close.iloc[-1] / close.iloc[-2] - 1

            if one_day_return < 0:
                market_down_count += 1

        # only trade when broad market stress exists
        stress_ratio = market_down_count / len(liquid_symbols)

        if stress_ratio < 0.50:
            target = {
                symbol.split("/")[0]: 0
                for symbol in self.candidate_symbols
            }
            self._rebalance_to_target(target)
            return

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

        target = {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

        if len(scores_series) > 0:
            winners = scores_series.sort_values(ascending=False).head(
                min(self.n_winners, len(scores_series))
            )

            weights = winners / winners.sum()

            for symbol, weight in weights.items():
                price = self.get_current_price(symbol)
                base = symbol.split("/")[0]

                target[base] = (self.capital * weight) / price

        self._rebalance_to_target(target)

    def _rebalance_to_target(self, target):
        current_positions = self.get_pos()

        # Sell first
        for symbol in self.candidate_symbols:
            base = symbol.split("/")[0]
            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if current_qty > target_qty:
                self.create_order(
                    symbol,
                    current_qty - target_qty,
                    "sell",
                    route=True
                )

        current_positions = self.get_pos()

        # Buy second
        for symbol in self.candidate_symbols:
            base = symbol.split("/")[0]
            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if target_qty > current_qty:
                self.create_order(
                    symbol,
                    target_qty - current_qty,
                    "buy",
                    route=True
                )
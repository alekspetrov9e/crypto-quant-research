from twsq.alpha import Alpha
import pandas as pd
import numpy as np


class BreadthWeightedMomentum(Alpha):

    def prepare(self):
        self.candidate_symbols = [
            "BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD", "XRP/USD",
            "AVAX/USD", "LINK/USD", "ADA/USD", "DOGE/USD", "LTC/USD",
            "DOT/USD", "TRX/USD", "ETC/USD", "ATOM/USD", "FIL/USD",
            "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD", "SUI/USD",
            "INJ/USD", "UNI/USD", "AAVE/USD", "XLM/USD", "RUNE/USD",
            "SEI/USD", "TIA/USD", "PEPE/USD", "SHIB/USD", "FET/USD",
        ]

        self.fast_window = 10
        self.slow_window = 30
        self.vol_window = 20

        self.liquidity_window = 20
        self.n_liquid = 20
        self.n_winners = 3

        self.max_capital = 1000

        self.lookback = max(
            self.slow_window,
            self.vol_window,
            self.liquidity_window
        ) + 5

    def rebalance(self):
        data_by_symbol = {}
        dollar_volume_scores = {}

        # 1. Dynamic liquid universe
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
                dollar_volume_scores[symbol] = dollar_volume

        if len(dollar_volume_scores) == 0:
            return

        liquid_symbols = (
            pd.Series(dollar_volume_scores)
            .sort_values(ascending=False)
            .head(self.n_liquid)
            .index
            .tolist()
        )

        scores = {}
        positive_trend_count = 0

        # 2. Compute momentum signal and breadth
        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]
            close = bars["close"]

            fast_ma = close.rolling(self.fast_window).mean().iloc[-1]
            slow_ma = close.rolling(self.slow_window).mean().iloc[-1]

            trend = fast_ma / slow_ma - 1

            returns = np.log(close).diff()
            vol = returns.rolling(self.vol_window).std().iloc[-1]

            if pd.isna(trend) or pd.isna(vol) or vol <= 0:
                continue

            if trend > 0:
                positive_trend_count += 1

                # same good signal as your working strategy
                score = trend / vol
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        # 3. Breadth controls total capital exposure
        # If 20/20 coins trend up -> invest 100%
        # If 10/20 trend up -> invest 50%
        # If 0/20 trend up -> invest 0%
        breadth = positive_trend_count / len(liquid_symbols)
        active_capital = self.max_capital * breadth

        target = {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

        # 4. Select top positive-trend coins
        if len(scores_series) > 0 and active_capital > 0:
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

                dollar_allocation = active_capital * weight
                target_qty = dollar_allocation / price

                target[base] = target_qty

        current_positions = self.get_pos()

        # 5. Sell first
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

        # 6. Buy second
        current_positions = self.get_pos()

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
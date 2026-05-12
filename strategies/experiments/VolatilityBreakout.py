from twsq.alpha import Alpha
import pandas as pd
import numpy as np


class VolatilityBreakout(Alpha):

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

        self.breakout_window = 20
        self.vol_window = 20
        self.exit_ma_window = 10

        self.n_winners = 3
        self.capital = 1000

        self.lookback = max(
            self.liquidity_window,
            self.breakout_window,
            self.vol_window,
            self.exit_ma_window
        ) + 5

    def rebalance(self):
        data_by_symbol = {}
        liquidity_scores = {}

        # 1. Dynamic liquidity universe
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

        # 2. Breakout signal
        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]

            close = bars["close"]
            returns = np.log(close).diff()

            current_close = close.iloc[-1]

            # previous high, excluding current bar
            previous_high = close.iloc[:-1].tail(self.breakout_window).max()

            recent_vol = returns.rolling(self.vol_window).std().iloc[-1]

            if pd.isna(previous_high) or pd.isna(recent_vol) or recent_vol <= 0:
                continue

            # breakout strength: how far above previous high, risk-adjusted
            breakout_strength = current_close / previous_high - 1

            if breakout_strength > 0:
                score = breakout_strength / recent_vol
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        # target everything to zero first
        target = {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

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
                target_qty = dollar_allocation / price

                target[base] = target_qty

        # 3. Exit rule:
        # If held asset is below its exit MA, force target to zero.
        current_positions = self.get_pos()

        for symbol in self.candidate_symbols:
            base = symbol.split("/")[0]
            held_qty = current_positions.get(base, 0)

            if held_qty <= 0:
                continue

            try:
                bars = data_by_symbol.get(symbol)
                if bars is None:
                    bars = self.get_lastn_bars(symbol, self.lookback, "1d").copy()
            except Exception:
                continue

            exit_ma = bars["close"].rolling(self.exit_ma_window).mean().iloc[-1]
            current_close = bars["close"].iloc[-1]

            if pd.notna(exit_ma) and current_close < exit_ma:
                target[base] = 0

        # 4. Sell first
        current_positions = self.get_pos()

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

        # 5. Buy second
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
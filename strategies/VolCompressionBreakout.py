from twsq.alpha import Alpha
import pandas as pd
import numpy as np


class VolCompressionBreakout(Alpha):

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

        self.short_vol_window = 10
        self.long_vol_window = 60
        self.momentum_window = 5

        self.n_winners = 3
        self.capital = 1000

        self.lookback = max(
            self.liquidity_window,
            self.short_vol_window,
            self.long_vol_window,
            self.momentum_window + 1
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

            dollar_volume = (bars["close"] * bars["volume"]).tail(self.liquidity_window).mean()

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

        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]
            close = bars["close"]

            ret = np.log(close).diff()

            short_vol = ret.rolling(self.short_vol_window).std().iloc[-1]
            long_vol = ret.rolling(self.long_vol_window).std().iloc[-1]

            if pd.isna(short_vol) or pd.isna(long_vol) or long_vol <= 0:
                continue

            compression = short_vol / long_vol

            recent_return = close.iloc[-1] / close.iloc[-(self.momentum_window + 1)] - 1

            # We want low volatility compression and positive price confirmation
            if compression >= 0.7:
                continue

            if recent_return <= 0:
                continue

            score = recent_return / compression

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

        current_positions = self.get_pos()

        for symbol in self.candidate_symbols:
            base = symbol.split("/")[0]
            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if current_qty > target_qty:
                self.create_order(symbol, current_qty - target_qty, "sell", route=True)

        current_positions = self.get_pos()

        for symbol in self.candidate_symbols:
            base = symbol.split("/")[0]
            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if target_qty > current_qty:
                self.create_order(symbol, target_qty - current_qty, "buy", route=True)
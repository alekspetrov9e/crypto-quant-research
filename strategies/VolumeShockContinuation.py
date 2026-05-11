from twsq.alpha import Alpha
import pandas as pd
import numpy as np


class VolumeShockContinuation(Alpha):

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

        self.n_winners = 3
        self.capital = 1000

        # require unusual volume
        self.min_volume_shock = 1.5

        self.lookback = max(
            self.liquidity_window,
            self.volume_window,
            self.vol_window
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

        # 2. Volume shock continuation signal
        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]

            close = bars["close"]
            volume = bars["volume"]

            one_day_return = close.iloc[-1] / close.iloc[-2] - 1

            avg_volume = volume.iloc[:-1].tail(self.volume_window).mean()
            current_volume = volume.iloc[-1]

            if avg_volume <= 0 or pd.isna(avg_volume):
                continue

            volume_shock = current_volume / avg_volume

            returns = np.log(close).diff()
            vol = returns.rolling(self.vol_window).std().iloc[-1]

            if pd.isna(one_day_return) or pd.isna(volume_shock) or pd.isna(vol) or vol <= 0:
                continue

            # Require positive price move and abnormal volume
            if one_day_return <= 0:
                continue

            if volume_shock < self.min_volume_shock:
                continue

            # Score = positive move confirmed by volume, penalized by volatility
            score = (one_day_return * volume_shock) / vol

            if score > 0:
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        # 3. Target all assets to zero first
        target = {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

        # 4. Select top min(3, available signals)
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
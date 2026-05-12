from twsq.alpha import Alpha
import pandas as pd


class CrossSectionalMeanReversionSafe(Alpha):

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

        self.return_window = 6
        self.n_longs = 3
        self.n_shorts = 3

        # smaller gross exposure because shorts can lose more than 100%
        self.gross_capital = 300
        self.long_capital = self.gross_capital / 2
        self.short_capital = self.gross_capital / 2

        self.lookback = max(
            self.liquidity_window,
            self.return_window + 1
        ) + 5

    def rebalance(self):
        data_by_symbol = {}
        liquidity_scores = {}

        for symbol in self.candidate_symbols:
            try:
                # lag=1 avoids using the freshest/current bar too aggressively
                bars = self.get_lastn_bars(symbol, self.lookback, "4h", lag=1).copy()
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

        recent_returns = {}

        for symbol in liquid_symbols:
            bars = data_by_symbol[symbol]

            recent_return = (
                bars["close"].iloc[-1] /
                bars["close"].iloc[-(self.return_window + 1)]
                - 1
            )

            if pd.notna(recent_return):
                recent_returns[symbol] = recent_return

        returns_series = pd.Series(recent_returns).dropna()

        if len(returns_series) < self.n_longs + self.n_shorts:
            return

        # Mean reversion:
        # long recent losers, short recent winners
        longs = (
            returns_series
            .sort_values(ascending=True)
            .head(self.n_longs)
        )

        shorts = (
            returns_series
            .sort_values(ascending=False)
            .head(self.n_shorts)
        )

        target = {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

        # Equal-weight version first. Safer than giving largest shorts to extreme pumps.
        dollars_per_long = self.long_capital / len(longs)
        dollars_per_short = self.short_capital / len(shorts)

        for symbol in longs.index:
            price = self.get_current_price(symbol)
            base = symbol.split("/")[0]
            target[base] = dollars_per_long / price

        for symbol in shorts.index:
            price = self.get_current_price(symbol)
            base = symbol.split("/")[0]
            target[base] = -dollars_per_short / price

        current_positions = self.get_pos()

        # Sell/decrease first
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

        # Buy/increase second
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
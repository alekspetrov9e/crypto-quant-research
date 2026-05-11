from twsq.alpha import Alpha
import pandas as pd


class MovingAverageSignalProportion(Alpha):

    def prepare(self):
        self.symbols = [
            "BTC/USD",
            "ETH/USD",
            "SOL/USD",
            "BNB/USD",
            "XRP/USD",
            "AVAX/USD",
            "LINK/USD",
            "ADA/USD",
            "DOGE/USD",
        ]

        self.fast_window = 10
        self.slow_window = 30
        self.lookback = self.slow_window + 5

        self.capital = 1000
        self.n_winners = 3

    def rebalance(self):
        scores = {}

        for symbol in self.symbols:
            bars = self.get_lastn_bars(symbol, self.lookback, "1d")

            fast_ma = bars["close"].rolling(self.fast_window).mean().iloc[-1]
            slow_ma = bars["close"].rolling(self.slow_window).mean().iloc[-1]

            score = fast_ma / slow_ma - 1

            if score > 0:
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        # Target all universe assets to zero first
        target = {
            symbol.split("/")[0]: 0
            for symbol in self.symbols
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

        current_positions = self.get_pos()

        # 1. Sell first
        for symbol in self.symbols:
            base = symbol.split("/")[0]

            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if current_qty > target_qty:
                sell_qty = current_qty - target_qty

                self.create_order(
                    symbol,
                    sell_qty,
                    "sell",
                    route=True
                )

        # 2. Then buy
        current_positions = self.get_pos()

        for symbol in self.symbols:
            base = symbol.split("/")[0]

            current_qty = current_positions.get(base, 0)
            target_qty = target.get(base, 0)

            if target_qty > current_qty:
                buy_qty = target_qty - current_qty

                self.create_order(
                    symbol,
                    buy_qty,
                    "buy",
                    route=True
                )
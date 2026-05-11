from twsq.alpha import Alpha
import pandas as pd


class MovingAverageCrossoverTop3PositiveOnly(Alpha):

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

        self.dollars_per_trade = 20
        self.n_winners = 3
        self.capital_limit = 1000

    def rebalance(self):
        scores = {}

        for symbol in self.symbols:
            bars = self.get_lastn_bars(symbol, self.lookback, "1d")

            fast_ma = bars["close"].rolling(self.fast_window).mean().iloc[-1]
            slow_ma = bars["close"].rolling(self.slow_window).mean().iloc[-1]

            score = fast_ma / slow_ma - 1

            # only consider positive trend assets
            if score > 0:
                scores[symbol] = score

        scores_series = pd.Series(scores).dropna()

        winners = (
            scores_series
            .sort_values(ascending=False)
            .head(self.n_winners)
            .index
            .tolist()
        )

        current_positions = self.get_pos()

        invested_value = 0

        for symbol in self.symbols:
            base = symbol.split("/")[0]
            qty = current_positions.get(base, 0)

            if qty > 0:
                price = self.get_current_price(symbol)
                invested_value += qty * price

        remaining_cash = self.capital_limit - invested_value

        # Buy $5 more of each positive top-3 winner, if capital is available
        for symbol in winners:
            if remaining_cash <= 0:
                break

            price = self.get_current_price(symbol)

            trade_value = min(self.dollars_per_trade, remaining_cash)
            buy_qty = trade_value / price

            if buy_qty > 0:
                self.create_order(
                    symbol,
                    buy_qty,
                    "buy",
                    route=True
                )

                remaining_cash -= trade_value

        # Sell $5 worth of any held coin that is not currently a winner
        for symbol in self.symbols:
            if symbol in winners:
                continue

            base = symbol.split("/")[0]
            held_qty = current_positions.get(base, 0)

            if held_qty > 0:
                price = self.get_current_price(symbol)

                sell_qty = min(
                    held_qty,
                    self.dollars_per_trade / price
                )

                if sell_qty > 0:
                    self.create_order(
                        symbol,
                        sell_qty,
                        "sell",
                        route=True
                    )
from twsq.alpha import Alpha
import pandas as pd


class BaseCryptoStrategy(Alpha):
    """
    Shared base class for crypto strategies.

    Provides:
    - common candidate universe
    - dynamic liquidity filtering
    - empty target construction
    - sell-first / buy-second target rebalancing
    """

    def prepare_base_universe(self):
        self.candidate_symbols = [
            "BTC/USD", "ETH/USD", "SOL/USD", "BNB/USD", "XRP/USD",
            "AVAX/USD", "LINK/USD", "ADA/USD", "DOGE/USD", "LTC/USD",
            "DOT/USD", "TRX/USD", "ETC/USD", "ATOM/USD", "FIL/USD",
            "NEAR/USD", "APT/USD", "ARB/USD", "OP/USD", "SUI/USD",
            "INJ/USD", "UNI/USD", "AAVE/USD", "XLM/USD", "RUNE/USD",
            "SEI/USD", "TIA/USD", "PEPE/USD", "SHIB/USD", "FET/USD",
        ]

    def get_liquid_universe(
        self,
        lookback,
        freq="1d",
        liquidity_window=20,
        n_liquid=20,
    ):
        data_by_symbol = {}
        dollar_volume_scores = {}

        for symbol in self.candidate_symbols:
            try:
                bars = self.get_lastn_bars(symbol, lookback, freq).copy()
            except Exception:
                continue

            if bars is None or len(bars) < lookback:
                continue

            dollar_volume = (
                bars["close"] * bars["volume"]
            ).tail(liquidity_window).mean()

            if pd.notna(dollar_volume):
                data_by_symbol[symbol] = bars
                dollar_volume_scores[symbol] = dollar_volume

        if len(dollar_volume_scores) == 0:
            return [], {}

        liquid_symbols = (
            pd.Series(dollar_volume_scores)
            .sort_values(ascending=False)
            .head(n_liquid)
            .index
            .tolist()
        )

        return liquid_symbols, data_by_symbol

    def empty_target(self):
        return {
            symbol.split("/")[0]: 0
            for symbol in self.candidate_symbols
        }

    def rebalance_to_target(self, target):
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
                    route=True,
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
                    route=True,
                )
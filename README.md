# crypto-quant-research
## TWSQ Trading Library Usage

This project uses the TWSQ Trading Library as the backtesting engine.

Each strategy inherits from `twsq.alpha.Alpha` and implements:

- `prepare()` — defines parameters and the tradable security universe
- `rebalance()` — computes signals and creates trades at each rebalance step for the specified frequency

Historical OHLCV data is accessed with:

```python
self.get_lastn_bars(symbol, n, freq)
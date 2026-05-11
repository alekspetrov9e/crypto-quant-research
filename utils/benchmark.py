import numpy as np
import pandas as pd
import statsmodels.api as sm


def get_strategy_returns_from_result(result, initial_capital=1000):
    portfolio_value = initial_capital + result.pos_pnl["port_val"]
    return portfolio_value.pct_change().dropna()


def get_strategy_returns_from_csv(pos_pnl_path, initial_capital=1000):
    df = pd.read_csv(pos_pnl_path, index_col="Date", parse_dates=True)
    portfolio_value = initial_capital + df["port_val"]
    return portfolio_value.pct_change().dropna()


def get_btc_returns(start_ts=None, end_ts=None):
    from twsq.data import BinancePrices

    px = BinancePrices()
    btc = px.get_bars("BTC/USD", "1d", start_ts=start_ts, end_ts=end_ts).copy()
    return btc["close"].pct_change().dropna()


def align_returns(strategy_returns, benchmark_returns):
    combined = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()
    combined.columns = ["strategy", "benchmark"]
    return combined


def run_ols_alpha_beta(strategy_returns, benchmark_returns, periods_per_year=365):
    combined = align_returns(strategy_returns, benchmark_returns)

    X = sm.add_constant(combined["benchmark"])
    y = combined["strategy"]

    model = sm.OLS(y, X).fit()

    alpha_daily = model.params["const"]
    beta = model.params["benchmark"]

    residuals = model.resid

    alpha_annual = alpha_daily * periods_per_year
    residual_vol_annual = residuals.std() * np.sqrt(periods_per_year)

    information_ratio = (
        alpha_annual / residual_vol_annual
        if residual_vol_annual != 0
        else np.nan
    )

    return {
        "alpha_daily": alpha_daily,
        "alpha_annual": alpha_annual,
        "beta": beta,
        "r_squared": model.rsquared,
        "information_ratio": information_ratio,
        "t_stat_alpha": model.tvalues["const"],
        "p_value_alpha": model.pvalues["const"],
        "model": model,
        "combined_returns": combined,
    }


def benchmark_summary(strategy_returns, benchmark_returns, periods_per_year=365):
    combined = align_returns(strategy_returns, benchmark_returns)

    rows = []

    for col in ["strategy", "benchmark"]:
        r = combined[col]
        wealth = (1 + r).cumprod()

        sharpe = (
            np.sqrt(periods_per_year) * r.mean() / r.std()
            if r.std() != 0
            else np.nan
        )

        max_drawdown = (wealth / wealth.cummax() - 1).min()
        total_return = wealth.iloc[-1] - 1
        annual_return = (1 + total_return) ** (periods_per_year / len(r)) - 1
        annual_vol = r.std() * np.sqrt(periods_per_year)

        rows.append(
            {
                "asset": col,
                "total_return": total_return,
                "annual_return": annual_return,
                "annual_volatility": annual_vol,
                "sharpe": sharpe,
                "max_drawdown": max_drawdown,
            }
        )

    return pd.DataFrame(rows)


def save_alpha_report(alpha_results, output_path):
    report = {
        "alpha_daily": alpha_results["alpha_daily"],
        "alpha_annual": alpha_results["alpha_annual"],
        "beta": alpha_results["beta"],
        "r_squared": alpha_results["r_squared"],
        "information_ratio": alpha_results["information_ratio"],
        "t_stat_alpha": alpha_results["t_stat_alpha"],
        "p_value_alpha": alpha_results["p_value_alpha"],
    }

    pd.DataFrame([report]).to_csv(output_path, index=False)
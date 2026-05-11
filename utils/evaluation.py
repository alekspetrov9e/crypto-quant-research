import numpy as np
import pandas as pd


def get_portfolio_value(result, initial_capital=1000):
    return initial_capital + result.pos_pnl["port_val"]


def get_returns(result, initial_capital=1000):
    value = get_portfolio_value(result, initial_capital)
    return value.pct_change().dropna()


def sharpe_ratio(returns, periods_per_year=365):
    if returns.std() == 0:
        return np.nan
    return np.sqrt(periods_per_year) * returns.mean() / returns.std()


def max_drawdown(portfolio_value):
    drawdown = portfolio_value / portfolio_value.cummax() - 1
    return drawdown.min()


def total_return(portfolio_value):
    return portfolio_value.iloc[-1] / portfolio_value.iloc[0] - 1


def turnover(result, initial_capital=1000):
    orders = result.orders.copy()

    if len(orders) == 0:
        return 0

    if "ntn_filled" in orders.columns:
        traded_notional = orders["ntn_filled"].abs().sum()
    else:
        traded_notional = (orders["qty"] * orders["avg_px"]).abs().sum()

    return traded_notional / initial_capital


def evaluate_result(
    result,
    name,
    initial_capital=1000,
    periods_per_year=365,
):
    portfolio_value = get_portfolio_value(result, initial_capital)
    returns = portfolio_value.pct_change().dropna()

    return {
        "strategy": name,
        "final_value": portfolio_value.iloc[-1],
        "profit": portfolio_value.iloc[-1] - initial_capital,
        "total_return": total_return(portfolio_value),
        "sharpe": sharpe_ratio(returns, periods_per_year),
        "max_drawdown": max_drawdown(portfolio_value),
        "turnover_multiple": turnover(result, initial_capital),
        "num_orders": len(result.orders),
    }


def make_summary_table(results_dict, initial_capital=1000, periods_per_year=365):
    rows = []

    for name, result in results_dict.items():
        rows.append(
            evaluate_result(
                result=result,
                name=name,
                initial_capital=initial_capital,
                periods_per_year=periods_per_year,
            )
        )

    return pd.DataFrame(rows).sort_values("sharpe", ascending=False)


def make_returns_table(results_dict, initial_capital=1000):
    returns = {}

    for name, result in results_dict.items():
        returns[name] = get_returns(result, initial_capital)

    return pd.DataFrame(returns).dropna()


def make_correlation_table(results_dict, initial_capital=1000):
    returns = make_returns_table(results_dict, initial_capital)
    return returns.corr()


def combine_returns(returns_df, weights):
    weights = pd.Series(weights)
    missing = set(weights.index) - set(returns_df.columns)
    if missing:
        raise ValueError(f"Weight keys not found in returns_df columns: {missing}")

    weights = weights / weights.sum()

    return returns_df[weights.index].mul(weights, axis=1).sum(axis=1)


def evaluate_combination(
    returns_df,
    weights,
    initial_capital=1000,
    periods_per_year=365,
):
    combined_returns = combine_returns(returns_df, weights)
    wealth = (1 + combined_returns).cumprod() * initial_capital

    return {
        "weights": weights,
        "final_value": wealth.iloc[-1],
        "profit": wealth.iloc[-1] - initial_capital,
        "sharpe": sharpe_ratio(combined_returns, periods_per_year),
        "max_drawdown": max_drawdown(wealth),
    }
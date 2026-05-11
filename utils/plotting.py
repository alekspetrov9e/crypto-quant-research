import matplotlib.pyplot as plt
import pandas as pd


def plot_equity_curves(results_dict, initial_capital=1000, title="Equity Curves"):
    plt.figure(figsize=(12, 6))

    for name, result in results_dict.items():
        value = initial_capital + result.pos_pnl["port_val"]
        plt.plot(value.index, value, label=name)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_drawdowns(results_dict, initial_capital=1000, title="Drawdowns"):
    plt.figure(figsize=(12, 6))

    for name, result in results_dict.items():
        value = initial_capital + result.pos_pnl["port_val"]
        drawdown = value / value.cummax() - 1
        plt.plot(drawdown.index, drawdown, label=name)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Drawdown")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_correlation_heatmap(corr, title="Strategy Correlations"):
    plt.figure(figsize=(8, 6))

    plt.imshow(corr, aspect="auto")
    plt.colorbar(label="Correlation")

    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.index)), corr.index)

    plt.title(title)
    plt.tight_layout()
    plt.show()


def plot_weight_scan(weight_results, title="Portfolio Weight Scan"):
    df = pd.DataFrame(weight_results)

    plt.figure(figsize=(10, 5))
    plt.plot(df["momentum_weight"], df["sharpe"], marker="o")

    plt.title(title)
    plt.xlabel("Momentum Weight")
    plt.ylabel("Sharpe")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_combined_vs_components(
    returns_df,
    combined_returns,
    initial_capital=1000,
    title="Combined Portfolio vs Components",
):
    plt.figure(figsize=(12, 6))

    for col in returns_df.columns:
        wealth = (1 + returns_df[col]).cumprod() * initial_capital
        plt.plot(wealth.index, wealth, label=col)

    combined_wealth = (1 + combined_returns).cumprod() * initial_capital
    plt.plot(combined_wealth.index, combined_wealth, label="combined", linewidth=3)

    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
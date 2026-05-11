from pathlib import Path
import pandas as pd


def load_pos_pnl(path):
    path = Path(path)
    return pd.read_csv(path, index_col="Date", parse_dates=True)


def load_orders(path):
    path = Path(path)
    return pd.read_csv(path, parse_dates=["start_ts", "end_ts"], low_memory=False)


def save_summary_metrics(summary_df, output_path="results/summary_metrics.csv"):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)


def save_correlations(corr_df, output_path="results/correlations.csv"):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    corr_df.to_csv(output_path)


def load_backtest_from_folder(folder):
    folder = Path(folder)

    pos_pnl_path = folder / "pos_pnl.csv"
    orders_path = folder / "orders.csv"

    pos_pnl = load_pos_pnl(pos_pnl_path)
    orders = load_orders(orders_path)

    return pos_pnl, orders
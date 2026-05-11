from pathlib import Path
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle,
    PageBreak,
)


RESULTS_DIR = Path("results")
FIGURES_DIR = RESULTS_DIR / "figures"
COMBINED_DIR = RESULTS_DIR / "combined"
BENCHMARK_DIR = RESULTS_DIR / "benchmark"
COMBINATIONS_DIR = RESULTS_DIR / "combinations"
REPORTS_DIR = Path("reports")

REPORTS_DIR.mkdir(exist_ok=True)

OUTPUT_PATH = REPORTS_DIR / "crypto_quant_research_report.pdf"


def format_df(df, max_rows=None, drop_columns=None):
    df = df.copy()

    if drop_columns is not None:
        df = df.drop(columns=[c for c in drop_columns if c in df.columns])

    if max_rows is not None:
        df = df.head(max_rows)

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].map(lambda x: f"{x:.4f}")

    return df

def add_page_number(canvas, doc):
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(7.8 * inch, 0.3 * inch, text)

def df_to_table(df):
    data = [df.columns.tolist()] + df.astype(str).values.tolist()

    table = Table(data, repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ]
        )
    )

    return table


def add_image(story, path, width=6.4 * inch):
    path = Path(path)

    if not path.exists():
        story.append(Paragraph(f"Missing figure: {path}", styles["BodyText"]))
        story.append(Spacer(1, 0.15 * inch))
        return

    img = Image(str(path))
    img._restrictSize(width, 4.5 * inch)
    story.append(img)
    story.append(Spacer(1, 0.25 * inch))


def add_csv_table(story, title, path, max_rows=None, drop_columns=None):
    path = Path(path)

    story.append(Paragraph(title, styles["Heading2"]))

    if not path.exists():
        story.append(Paragraph(f"Missing table: {path}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))
        return

    df = pd.read_csv(path)
    df = format_df(df, max_rows=max_rows, drop_columns=drop_columns)

    story.append(df_to_table(df))
    story.append(Spacer(1, 0.3 * inch))


def build_report():
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=0.45 * inch,
        leftMargin=0.45 * inch,
        topMargin=0.45 * inch,
        bottomMargin=0.45 * inch,
    )

    story = []

    story.append(Paragraph("Crypto Quant Research Report", styles["Title"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(
        Paragraph(
            "This report summarizes a systematic crypto trading research project using the "
            "TWSQ Trading Library. The project evaluates momentum, breadth-weighted momentum, "
            "capitulation-reversal strategies, and combined portfolios under realistic transaction costs.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Research Questions", styles["Heading2"]))
    story.append(
        Paragraph(
            "1. Can cross-sectional crypto momentum outperform BTC buy-and-hold? ",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "2. Can a low-correlation capitulation strategy improve portfolio Sharpe? ",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "3. Are strategy returns explained by BTC beta or by independent alpha?",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Strategies Evaluated", styles["Heading2"]))

    story.append(Paragraph(
        "<b>1. Momentum Strategy:</b> Selects the most liquid cryptocurrencies and ranks them using a "
        "volatility-adjusted moving average signal. The strategy buys assets with positive trend scores.",
        styles["BodyText"],
    ))

    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph(
        "<b>2. Breadth-Weighted Momentum:</b> Extends the momentum strategy by scaling exposure according "
        "to market breadth. If many coins are in positive trends, the strategy invests more capital; "
        "if market breadth is weak, it reduces exposure.",
        styles["BodyText"],
    ))

    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph(
        "<b>3. Capitulation Bounce Daily:</b> A reversal strategy that buys liquid assets after large "
        "negative daily returns combined with abnormal volume spikes, expecting short-term panic reversals.",
        styles["BodyText"],
    ))

    story.append(Spacer(1, 0.12 * inch))

    story.append(Paragraph(
        "<b>4. Capitulation Bounce Selective:</b> A more conservative version of the capitulation strategy "
        "with stricter entry filters and lower exposure. It trades less frequently and aims to reduce drawdowns.",
        styles["BodyText"],
    ))

    story.append(PageBreak())

    add_csv_table(
        story,
        "Standalone Strategy Summary",
        RESULTS_DIR / "summary_metrics.csv",
    )

    story.append(Paragraph("Equity Curves", styles["Heading2"]))
    add_image(story, FIGURES_DIR / "equity_curves.png")

    story.append(Paragraph("Drawdowns", styles["Heading2"]))
    add_image(story, FIGURES_DIR / "drawdowns.png")

    story.append(PageBreak())

    story.append(Paragraph("Strategy Correlations", styles["Heading2"]))
    story.append(
        Paragraph(
            "Low correlation between momentum and capitulation strategies suggests that "
            "capitulation can act as a diversifying alpha source.",
            styles["BodyText"],
        )
    )
    add_csv_table(story, "Correlation Matrix", RESULTS_DIR / "correlations.csv")
    add_image(story, FIGURES_DIR / "correlation_heatmap.png")

    story.append(PageBreak())

    story.append(Paragraph("Performance Metrics", styles["Heading2"]))
    add_image(story, FIGURES_DIR / "sharpe_bar_chart.png")
    add_image(story, FIGURES_DIR / "max_drawdown_bar_chart.png")
    add_image(story, FIGURES_DIR / "turnover_bar_chart.png")

    add_csv_table(
        story,
        "Alpha/Beta Regression vs BTC",
        BENCHMARK_DIR / "alpha_beta_summary.csv",
    )

    story.append(
        Paragraph(
            "The alpha/beta regression estimates whether the strategy returns are explained "
            "by BTC buy-and-hold exposure. Low beta and low R-squared indicate that strategy "
            "returns are not simply crypto market beta.",
            styles["BodyText"],
        )
    )

    add_image(story, FIGURES_DIR / "annual_alpha_bar_chart.png")
    add_image(story, FIGURES_DIR / "beta_vs_btc_bar_chart.png")

    story.append(PageBreak())

    add_csv_table(
        story,
        "Best Strategy Combinations",
        COMBINATIONS_DIR / "best_combinations.csv",
    )

    story.append(Paragraph("Momentum + Capitulation Weight Scan", styles["Heading2"]))
    add_image(story, FIGURES_DIR / "momentum_capitulation_weight_scan.png")

    story.append(PageBreak())

    story.append(Paragraph("Best Combined Portfolio", styles["Heading2"]))

    story.append(Paragraph(
        "The final portfolio combines the strongest standalone alpha, momentum, with the lower-correlation "
        "capitulation strategy. The optimal weight was selected by scanning portfolio weights from 0% to 100% "
        "in 5% increments and choosing the allocation with the highest Sharpe ratio. The best result was an "
        "80% allocation to momentum and a 20% allocation to daily capitulation.",
        styles["BodyText"],
    ))

    story.append(Spacer(1, 0.2 * inch))

    add_csv_table(
        story,
        "Best Combined Portfolio Metrics",
        COMBINED_DIR / "best_combined_metrics.csv",
    )

    add_csv_table(
        story,
        "Best Combined Portfolio Alpha Report",
        COMBINED_DIR / "best_combined_alpha_report.csv",
        drop_columns=["model", "combined_returns"],
    )

    add_csv_table(
        story,
        "Best Combined Portfolio Benchmark Summary",
        COMBINED_DIR / "best_combined_benchmark_summary.csv",
    )

    story.append(Paragraph("Best Combined Portfolio vs BTC", styles["Heading2"]))
    add_image(story, COMBINED_DIR / "best_combined_vs_btc.png")

    story.append(Paragraph("Best Combined Portfolio Drawdown", styles["Heading2"]))
    add_image(story, COMBINED_DIR / "best_combined_drawdown.png")

    story.append(PageBreak())

    story.append(Paragraph("Key Findings", styles["Heading2"]))
    story.append(
        Paragraph(
            "The momentum strategy delivered the strongest standalone performance, while "
            "the capitulation strategy showed materially lower correlation to momentum. "
            "Combining the two improved the portfolio Sharpe ratio and reduced drawdown "
            "relative to the standalone momentum strategy.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Limitations", styles["Heading2"]))
    story.append(
        Paragraph(
            "This is a research backtest, not a production trading system. Limitations include "
            "possible survivorship bias in the candidate universe, simplified execution assumptions, "
            "absence of order book data, no funding-rate data, and limited out-of-sample validation.",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Future Work", styles["Heading2"]))
    story.append(
        Paragraph(
            "Future improvements include walk-forward validation, parameter sensitivity analysis, "
            "transaction-cost stress tests, volatility targeting, funding-rate integration, and live paper trading.",
            styles["BodyText"],
        )
    )

    doc.build(story,
              onFirstPage=add_page_number,
              onLaterPages=add_page_number,
              )


if __name__ == "__main__":
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="SmallText",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
        )
    )

    build_report()
    print(f"PDF report generated at: {OUTPUT_PATH}")
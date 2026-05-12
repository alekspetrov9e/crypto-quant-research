# Crypto Quant Research

A research-focused crypto systematic trading project exploring momentum, breadth, and capitulation-based alpha strategies using the `twsq` quantitative trading framework.

The project includes:

- Cross-sectional crypto momentum strategies
- Breadth-weighted trend allocation
- Capitulation reversal strategies
- Portfolio combination and optimization
- Alpha/Beta benchmarking vs BTC
- Parameter robustness analysis
- BTC regime analysis
- Automated visualization and PDF report generation

The goal of the project is not only to build profitable strategies, but also to evaluate them professionally through robustness tests, benchmarking, diversification analysis, and portfolio construction.

---

# Project Goals

This repository explores several research questions:

1. Can cross-sectional momentum generate alpha in crypto markets?
2. Can breadth information improve trend-following allocation?
3. Can capitulation/reversal effects diversify momentum crashes?
4. How robust are the strategies across parameter choices?
5. How do the strategies behave in BTC bull and bear regimes?
6. Can combining multiple low-correlation strategies improve Sharpe ratio?
7. Does adding BTC exposure improve the final portfolio?

---

# Implemented Strategies

## 1. Dynamic Cross-Sectional Momentum

File:

```text
strategies/MovingAverageSignalProportionDynamicUniverse.py
```

Core idea:

- Dynamically select the most liquid crypto assets
- Rank assets by moving-average trend strength
- Long strongest trending assets
- Position sizing proportional to signal strength

Features:

- Dynamic liquid universe selection
- Volatility-adjusted trend scoring
- Cross-sectional ranking
- Fully systematic rebalancing

---

## 2. Breadth-Weighted Momentum

File:

```text
strategies/BreadthWeightedMomentum.py
```

Core idea:

- Measure how many assets participate in the trend
- Reduce portfolio exposure during weak market breadth
- Increase exposure when broad participation exists

Key innovation:

```text
Exposure ∝ percentage of coins with positive trend
```

This creates adaptive market participation.

---

## 3. Daily Capitulation Bounce

File:

```text
strategies/CapitulationBounceDaily.py
```

Core idea:

- Detect large daily selloffs with abnormal volume
- Buy short-term panic events
- Capture mean reversion after liquidation events

Signals include:

- Large negative return threshold
- Volume shock filter
- Cross-sectional selection

---

## 4. Selective Capitulation Bounce

File:

```text
strategies/CapitulationBounceSelective.py
```

A more defensive and selective version of the capitulation strategy.

Designed to:

- Trade less frequently
- Avoid weaker reversals
- Improve behavior during BTC bear regimes

# Additional Experimental Strategies

The `strategies/` folder also contains several additional experimental strategy implementations that were explored during the research process.

These strategies included variations of:

- alternative momentum constructions
- different reversal specifications
- broader allocation schemes
- experimental filters and ranking systems

While some of these approaches occasionally produced profitable backtests, they generally suffered from one or more of the following issues:

- unstable performance across parameter choices
- poor Sharpe ratios
- excessive drawdowns
- weak robustness
- inconsistent behavior across BTC market regimes
- over-sensitivity to market conditions

As a result, they were not included in the final portfolio construction pipeline and were not further developed.

This research process was intentionally iterative:

```text
implement → evaluate → benchmark → test → keep or discard
```

Only strategies that demonstrated:

- consistent profitability
- robustness across nearby parameters
- reasonable drawdown behavior
- diversification value
- statistically meaningful alpha characteristics

were retained for the final analysis and portfolio construction.
---

# Portfolio Construction

The project explores multiple portfolio combinations.

## Alpha Portfolio

Best alpha-only portfolio:

```text
80% Momentum
20% Daily Capitulation
```

This improved:

- Sharpe ratio
- Diversification
- Drawdown behavior

compared with standalone momentum.

---

## Final Portfolio

The final portfolio additionally combines the alpha portfolio with BTC exposure.

Best allocation:

```text
85% Alpha Portfolio
15% BTC Buy & Hold
```

Since the alpha portfolio itself is:

```text
80% Momentum
20% Capitulation
```

the effective final allocation becomes:

```text
68% Momentum Alpha
17% Capitulation Alpha
15% BTC Buy & Hold
```

This final allocation achieved the strongest overall risk-adjusted performance in the project.

---

# Final Results

## Standalone Strategies

| Strategy | Sharpe | Max Drawdown | Total Return |
|---|---|---|---|
| Momentum | ~1.28 | ~-25.6% | ~434% |
| Breadth Momentum | ~1.26 | ~-18.2% | ~326% |
| Capitulation Daily | ~0.67 | ~-39.0% | ~141% |
| Capitulation Selective | ~0.46 | ~-26.6% | ~44% |

---

## Best Alpha Portfolio

```text
80% Momentum
20% Capitulation Daily
```

Results:

- Sharpe ≈ 1.33
- Reduced drawdown relative to pure momentum
- Improved diversification

---

## Final Portfolio (Alpha + BTC)

```text
68% Momentum
17% Capitulation
15% BTC
```

Results:

- Sharpe ≈ 1.47
- Better risk-adjusted returns than standalone BTC or standalone alpha
- Diversified return streams
- Low BTC beta
- Improved stability during large BTC market swings

---

# Benchmarking & Statistical Analysis

The project includes professional quantitative evaluation tools.

Implemented analyses include:

## Performance Metrics

- Total return
- Annualized return
- Annualized volatility
- Sharpe ratio
- Maximum drawdown
- Turnover
- Number of trades

---

## Alpha/Beta Regression vs BTC

Using OLS regression:

```text
strategy_return = alpha + beta * btc_return + error
```

Metrics computed:

- Daily alpha
- Annualized alpha
- Beta vs BTC
- R²
- Information ratio
- t-statistics
- p-values

Results showed:

- Near-zero BTC beta
- Positive alpha
- Strong diversification properties

---

## Correlation Analysis

The project computes:

- Strategy return correlations
- Correlation heatmaps
- Combination diversification analysis

Key finding:

Momentum and capitulation signals have relatively low correlation, which helps improve portfolio diversification when combined.

---

# Parameter Robustness Analysis

The project includes extensive parameter sweeps to reduce overfitting concerns.

## Momentum Robustness

Parameters tested:

- Fast moving average windows
- Slow moving average windows
- Number of winners

Result:

The momentum effect remained profitable across many nearby parameter choices.

This suggests the strategy is not dependent on a single optimized parameter set.

Strong parameter regions consistently produced Sharpe ratios around:

```text
1.2 - 1.4
```

which indicates structural robustness rather than isolated overfitting.

---

## Capitulation Robustness

Parameters tested:

- Return shock thresholds
- Volume shock thresholds
- Number of reversal positions

Result:

Stronger volume confirmation significantly improved reversal quality and drawdown behavior.

The strongest configurations produced Sharpe ratios above:

```text
1.2
```

while maintaining relatively controlled drawdowns.

---

# BTC Regime Analysis

The project evaluates all strategies separately in:

- BTC Bull Regimes
- BTC Bear Regimes

Key findings:

## Bull Regimes

Momentum performs exceptionally well during trending BTC environments.

Example:

- Momentum Sharpe during bull regimes ≈ 2.96

---

## Bear Regimes

Capitulation strategies become more defensive.

The selective capitulation strategy was the only tested strategy with positive Sharpe during BTC bear regimes.

This supports combining:

```text
Trend-following + Reversal signals
```

because they behave differently across market environments.

---

# Combination Analysis

The repository performs exhaustive weight scans between strategies.

Examples include:

- Momentum + Capitulation
- Breadth + Capitulation
- Alpha Portfolio + BTC

The project evaluates:

- Sharpe ratio
- Drawdown
- Final value
- Profit
- Diversification effects

for all tested combinations.

---

# Generated Visualizations

The repository automatically generates:

- Equity curves
- Drawdown charts
- Correlation heatmaps
- Sharpe comparison charts
- Turnover charts
- Weight-scan charts
- BTC comparison charts
- Combined portfolio analysis
- Parameter robustness charts
- Regime analysis charts

---

# Automated Research Report Generation

A major component of this project is the fully automated research report generation pipeline.

The repository can automatically generate a professional multi-page PDF research report containing:

- strategy descriptions
- performance summaries
- benchmarking statistics
- alpha/beta analysis
- correlation analysis
- parameter robustness studies
- BTC regime analysis
- portfolio combination analysis
- allocation breakdowns
- visualizations and charts

The report is generated directly from the backtest outputs, CSV summaries, and generated figures.

---

## Generating the Report

Run:

```bash
python generate_analysis_report.py
python generate_pdf_report.py
```

This automatically creates:

- summary CSV files
- benchmark tables
- robustness analysis outputs
- regime analysis outputs
- portfolio combination analysis
- visualizations
- final PDF report

---

## Report Location

The final report is generated in:

```text
results/reports/
```

Example:

```text
results/reports/crypto_quant_research_report.pdf
```

---

# Included Report Sections

The generated report includes:

## Strategy Overview

- explanation of all implemented strategies
- portfolio construction rationale
- combination methodology

---

## Performance Metrics

For all strategies and portfolio combinations:

- final portfolio value
- total return
- annualized return
- annualized volatility
- Sharpe ratio
- maximum drawdown
- turnover
- number of trades

---

## Benchmarking vs BTC

OLS regression analysis against BTC buy-and-hold:

```text
strategy_return = alpha + beta * btc_return + error
```

Included statistics:

- daily alpha
- annualized alpha
- beta vs BTC
- R²
- information ratio
- alpha t-statistics
- alpha p-values

---

## Correlation Analysis

- strategy correlation matrices
- diversification analysis
- correlation heatmaps

---

## Portfolio Combination Analysis

Weight scans between:

- momentum + capitulation
- breadth + capitulation
- alpha portfolio + BTC

including:

- Sharpe optimization
- drawdown comparison
- allocation analysis

---

## Parameter Robustness Analysis

Extensive parameter sweeps for:

### Momentum Strategies

- fast MA windows
- slow MA windows
- number of winners

### Capitulation Strategies

- return shock thresholds
- volume shock thresholds
- position counts

This section evaluates whether the strategies remain profitable across nearby parameter choices and helps reduce overfitting concerns.

---

## BTC Regime Analysis

Performance is evaluated separately during:

- BTC bull regimes
- BTC bear regimes

The report compares how each strategy behaves under different market environments.

---

# Generated Visualizations

The report automatically includes:

- equity curves
- BTC comparison charts
- drawdown charts
- correlation heatmaps
- weight optimization plots
- robustness heatmaps
- regime comparison charts
- portfolio allocation charts

---

# Research Workflow

The reporting system is designed to support a complete quantitative research workflow:

```text
strategy development
    ↓
backtesting
    ↓
evaluation
    ↓
benchmarking
    ↓
robustness testing
    ↓
portfolio construction
    ↓
automated research reporting
```

This makes the repository function not only as a collection of strategies, but as a reusable quantitative research framework.

# Project Structure

```text
crypto-quant-research/
│
├── strategies/
│   ├── MovingAverageSignalProportionDynamicUniverse.py
│   ├── BreadthWeightedMomentum.py
│   ├── CapitulationBounceDaily.py
│   └── CapitulationBounceSelective.py
│
├── utils/
│   ├── benchmark.py
│   ├── combined_analysis.py
│   ├── data_helpers.py
│   ├── evaluation.py
│   └── plotting.py
│
├── results/
│   ├── benchmark/
│   ├── combinations/
│   ├── combined/
│   ├── combined_plus_btc/
│   ├── robustness/
│   ├── regime_analysis/
│   └── figures/
│
├── run_backtests.py
├── generate_analysis_report.py
├── generate_pdf_report.py
├── analyze_alpha_vs_btc.py
├── README.md
└── requirements.txt
```

---

# Running the Project

## 1. Create Virtual Environment

```bash
python -m venv myenv
source myenv/bin/activate
```

---

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 3. Run Backtests

```bash
python run_backtests.py
```

This generates:

- Summary metrics
- Correlations
- Strategy return tables
- Visualizations

---

## 4. Generate Full Analysis

```bash
python generate_analysis_report.py
```

This generates:

- Alpha/Beta reports
- Combination analysis
- BTC comparison analysis
- Regime analysis
- Parameter robustness analysis

---

## 5. Generate Final PDF Report

```bash
python generate_pdf_report.py
```

This produces a complete research-style PDF report with:

- Tables
- Charts
- Benchmarking
- Statistical analysis
- Portfolio construction
- Robustness analysis
- Regime analysis

---

# Technologies Used

- Python
- pandas
- numpy
- matplotlib
- statsmodels
- scipy
- twsq
- reportlab

---

# Research Conclusions

The project produced several important findings:

1. Cross-sectional momentum is highly effective in crypto markets.
2. Breadth information helps reduce drawdowns.
3. Capitulation reversal strategies diversify momentum crashes.
4. Strategy combinations improve Sharpe ratios significantly.
5. BTC exposure can improve portfolio efficiency when mixed correctly.
6. The strategies appear robust across nearby parameter choices.
7. Momentum and reversal signals behave differently across BTC market regimes.

The final portfolio achieved approximately:

```text
Sharpe Ratio ≈ 1.47
```

while maintaining relatively controlled drawdowns for a crypto-focused systematic portfolio.

---

# Notes

This project is research-focused and educational.

It is designed to demonstrate:

- systematic strategy development
- portfolio construction
- quantitative evaluation
- robustness testing
- benchmarking
- research-style reporting

rather than production-ready live trading infrastructure.

---

# Future Improvements

Possible future extensions:

- Transaction-cost modeling improvements
- Funding-rate integration
- Perpetual futures strategies
- Market-neutral portfolios
- Walk-forward optimization
- Bayesian parameter selection
- Multi-factor crypto portfolios
- Volatility targeting
- Regime-adaptive allocation
- Live deployment integration

---

# Author

Aleks Petrov

Technical University of Munich (TUM)


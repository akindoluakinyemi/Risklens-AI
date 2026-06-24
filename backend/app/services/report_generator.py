def interpret_volatility(volatility):
    if volatility < 0.20:
        return "low"
    elif volatility < 0.30:
        return "moderate"
    return "high"


def interpret_sharpe(sharpe_ratio):
    if sharpe_ratio < 0.5:
        return "weak"
    elif sharpe_ratio < 1:
        return "reasonable"
    return "strong"


def generate_portfolio_report(
    portfolio_risk,
    stress_result,
    optimization_result
):
    volatility_level = interpret_volatility(portfolio_risk["volatility"])
    sharpe_level = interpret_sharpe(portfolio_risk["sharpe_ratio"])

    max_sharpe = optimization_result["optimized_portfolios"]["max_sharpe_portfolio"]
    min_vol = optimization_result["optimized_portfolios"]["minimum_volatility_portfolio"]

    report = f"""
Portfolio Risk Report

The selected portfolio has {volatility_level} risk, with annualised volatility of {portfolio_risk["volatility"]:.2%}. 
Its Sharpe ratio is {portfolio_risk["sharpe_ratio"]:.2f}, indicating {sharpe_level} risk-adjusted performance.

The portfolio's 95% Value at Risk is {portfolio_risk["var_95"]:.2%}, meaning that on a typical trading day, losses worse than this level are expected only about 5% of the time. 
The Conditional Value at Risk is {portfolio_risk["cvar_95"]:.2%}, showing the average loss during the worst 5% of trading days.

The maximum historical drawdown is {portfolio_risk["max_drawdown"]:.2%}, which represents the largest peak-to-trough decline observed in the selected period.

Under the selected stress scenario, the portfolio would fall by {stress_result["portfolio_loss"]:.2%}. 
For an initial portfolio value of €{stress_result["initial_value"]:,.2f}, this implies an estimated loss of €{stress_result["estimated_loss_value"]:,.2f}, leaving a stressed portfolio value of €{stress_result["stressed_portfolio_value"]:,.2f}.

The maximum Sharpe portfolio from the optimisation process has an expected return of {max_sharpe["return"]:.2%}, volatility of {max_sharpe["volatility"]:.2%}, and Sharpe ratio of {max_sharpe["sharpe_ratio"]:.2f}. 
The minimum volatility portfolio has expected return of {min_vol["return"]:.2%}, volatility of {min_vol["volatility"]:.2%}, and Sharpe ratio of {min_vol["sharpe_ratio"]:.2f}.

Overall, this analysis combines historical risk, downside risk, scenario stress testing, and portfolio optimisation to provide a clearer view of portfolio exposure.
"""

    return report.strip()
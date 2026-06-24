import pandas as pd
import numpy as np


def calculate_daily_returns(prices):
    return prices.pct_change().dropna()


def calculate_volatility(returns):
    return returns.std() * np.sqrt(252)


def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * np.sqrt(252)

    return (annual_return - risk_free_rate) / annual_volatility


def calculate_var(returns, confidence=0.95):
    return np.percentile(returns, (1 - confidence) * 100)


def calculate_cvar(returns, confidence=0.95):
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def calculate_max_drawdown(prices):
    running_max = prices.cummax()
    drawdown = (prices - running_max) / running_max

    return drawdown.min()
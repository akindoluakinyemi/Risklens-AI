import numpy as np
import pandas as pd

def simulate_portfolios(
        returns_df: pd.DataFrame,
        simulations: int = 10000,
        risk_free_rate: float = 0.02
):
    mean_returns = returns_df.mean() * 252
    cov_matrix = returns_df.cov() * 252
    assets = returns_df.columns.to_list()

    results = []

    for _ in range(simulations):
        weights = np.random.random(len(assets))
        weights = weights / np.sum(weights)

        portfolio_return = np.dot(weights, mean_returns)
        portfolio_volatility = np.sqrt(
            np.dot(weights.T, np.dot(cov_matrix, weights))
        )

        sharpe_ratio = (
            portfolio_return - risk_free_rate
        ) / portfolio_volatility

        results.append({
            "return": round(float(portfolio_return), 4),
            "volatility": round(float(portfolio_volatility), 4),
            "sharpe_ratio": round(float(sharpe_ratio), 4),
            "weights": {
                assets[i]: round(float(weights[i]), 4)
                for i in range(len(assets))
            }
        })

    return results


def get_optimized_portfolios(results):
    max_sharpe = max(results, key=lambda x: x["sharpe_ratio"])
    min_volatility = min(results, key=lambda x: x["volatility"])

    return {
        "max_sharpe_portfolio": max_sharpe,
        "minimum_volatility_portfolio": min_volatility,
    }

    

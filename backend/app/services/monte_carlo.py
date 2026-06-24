import numpy as np
import pandas as pd


def run_monte_carlo(
    returns: pd.Series,
    initial_value: float = 100000,
    days: int = 252,
    simulations: int = 5000
):
    mean_return = returns.mean()
    volatility = returns.std()

    simulated_paths = np.zeros((days, simulations))
    simulated_paths[0] = initial_value

    for t in range(1, days):
        random_returns = np.random.normal(mean_return, volatility, simulations)
        simulated_paths[t] = simulated_paths[t - 1] * (1 + random_returns)

    final_values = simulated_paths[-1]

    return {
        "initial_value": initial_value,
        "days": days,
        "simulations": simulations,
        "expected_final_value": round(float(np.mean(final_values)), 2),
        "median_final_value": round(float(np.median(final_values)), 2),
        "worst_5_percent_value": round(float(np.percentile(final_values, 5)), 2),
        "best_5_percent_value": round(float(np.percentile(final_values, 95)), 2),
        "probability_of_loss": round(float(np.mean(final_values < initial_value)), 4),
        "final_values_sample": [round(float(x), 2) for x in final_values[:1000]]
    }
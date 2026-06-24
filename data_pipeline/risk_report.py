import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from dotenv import load_dotenv
from backend.app.services.risk_metrics import (
    calculate_daily_returns,
    calculate_volatility,
    calculate_sharpe_ratio,
    calculate_var,
    calculate_cvar,
    calculate_max_drawdown,
)
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
def get_asset_prices(symbol):
    query = f"""
    SELECT date, close
    FROM asset_prices
    WHERE symbol = '{symbol}'
    ORDER BY date
    """
    return pd.read_sql(query, engine)

def analyze_asset(symbol):
    df = get_asset_prices(symbol)
    prices = df["close"]
    returns = calculate_daily_returns(prices)
    report = {
        "Asset": symbol,
        "Volatility": calculate_volatility(returns),
        "Sharpe Ratio": calculate_sharpe_ratio(returns),
        "VaR 95%": calculate_var(returns),
        "CVaR 95%": calculate_cvar(returns),
        "Max Drawdown": calculate_max_drawdown(prices),
    }

    return report

ASSETS = ["AAPL", "MSFT", "GOOGL", "JPM", "SPY"]

if __name__ == "__main__":
    report = []
    for symbols in ASSETS:
        report.append(analyze_asset(symbols))
    report_df = pd.DataFrame(report)
    print("\nRisk Report\n")
    print(report_df)


import yfinance as yf
import pandas as pd


ASSETS = ["AAPL", "MSFT", "GOOGL", "JPM", "SPY"]


def fetch_asset_data(symbol: str, start_date: str = "2020-01-01") -> pd.DataFrame:
    data = yf.download(symbol, start=start_date, progress=False, auto_adjust=True)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    data["symbol"] = symbol

    data = data.rename(columns={
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })

    data["adjusted_close"] = data["close"]

    return data[[
        "symbol", "date", "open", "high", "low",
        "close", "adjusted_close", "volume"
    ]]


def fetch_all_assets() -> pd.DataFrame:
    all_data = []

    for symbol in ASSETS:
        print(f"Fetching data for {symbol}...")
        df = fetch_asset_data(symbol)
        all_data.append(df)

    return pd.concat(all_data, ignore_index=True)


if __name__ == "__main__":
    market_data = fetch_all_assets()
    market_data.to_csv("market_data.csv", index=False)
    print("Market data saved to market_data.csv")
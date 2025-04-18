import yfinance as yf
from datetime import datetime
import pandas as pd


def download_ticker_data(ticker_symbol: str, start_date: str, end_date: str):
    """
    Download historical data for a given ticker and save to CSV

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL')
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        None
    """
    # Create a Ticker object
    ticker = yf.Ticker(ticker_symbol)

    # Download the data
    data = ticker.history(start=start_date, end=end_date)

    # Ensure dates are in ISO format and prices are rounded to 2 decimals
    data.index = data.index.strftime('%Y-%m-%d')  # Convert index to ISO format
    data = data.round(2)  # Round all numeric columns to 2 decimals

    # Save to CSV
    output_file = f"{ticker_symbol}.csv"
    data.to_csv(output_file)
    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    # Download data for AAPL, MSFT, and TSLA
    start = "2025-01-01"
    end = "2025-04-18"

    # Download tickers
    tickers = ["AAPL", "MSFT", "TSLA"]
    for ticker in tickers:
        download_ticker_data(ticker, start, end)

import yfinance as yf
from datetime import datetime


def download_ticker_data(ticker_symbol: str, start_date: str, end_date: str, output_file: str = None):
    """
    Download historical data for a given ticker and save to CSV

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL')
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        output_file (str, optional): Output CSV filename. If None, will use ticker_symbol_start_end.csv

    Returns:
        str: Path to the saved CSV file
    """
    # Create ticker object
    ticker = yf.Ticker(ticker_symbol)

    # Download the data
    df = ticker.history(start=start_date, end=end_date)

    # Format the index (dates) to YYYY-MM-DD
    df.index = df.index.strftime('%Y-%m-%d')

    # Round price columns to 2 decimal places
    price_columns = ['Open', 'High', 'Low', 'Close']
    df[price_columns] = df[price_columns].round(2)

    # Generate output filename if not provided
    if output_file is None:
        output_file = f"{ticker_symbol}_{start_date}_{end_date}.csv"

    # Save to CSV
    df.to_csv(output_file)
    print(f"Data saved to {output_file}")
    return output_file


if __name__ == "__main__":
    # Download data for both AAPL and MSFT
    start = "2025-01-01"
    end = "2025-04-18"

    # Download both tickers
    tickers = ["AAPL", "MSFT"]
    for ticker in tickers:
        download_ticker_data(ticker, start, end)

import csv
import json
from class_definition import Content
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List


def calculate_weekly_data(file_paths: Dict[str, str], descriptions: Dict[str, str]) -> tuple[Content, Content]:
    all_weekly_data: Dict[str, List[dict]] = {}
    common_dates = set()

    # Process each stock's data
    for ticker, file_path in file_paths.items():
        # Read CSV into pandas DataFrame and parse dates
        df = pd.read_csv(file_path, parse_dates=['Date'])
        df['Date'] = df['Date'].dt.tz_localize(None)  # Remove timezone info

        # Ensure weeks start on Monday by using pandas resample
        df.set_index('Date', inplace=True)
        # Resample to weekly frequency starting on Monday
        weekly_groups = df.resample('W-MON')

        # Calculate weekly data
        weekly_data = []
        previous_end_price = None

        for date, group in weekly_groups:
            if not group.empty:
                # Get Monday's date for the week
                start_date = (date - timedelta(days=date.weekday())).strftime('%m-%d')  # MM-DD format
                end_price = round(float(group['Close'].iloc[-1]), 2)  # 2 decimals

                if previous_end_price is not None:
                    pct_change = round(((end_price - previous_end_price) / previous_end_price) * 100, 2)
                else:
                    pct_change = 0  # No previous week available

                weekly_data.append({'date': start_date, 'change': pct_change, 'close': end_price})
                common_dates.add(start_date)

                previous_end_price = end_price  # Update for next iteration

        all_weekly_data[ticker] = weekly_data

    # Sort dates to ensure consistent order
    dates = sorted(list(common_dates))

    # Create content structures for both files
    content_changes: Content = {"metadata": {"name": "Stock Weekly Returns 2024", "datatype": "return", "time": dates}, "data": []}

    content_prices: Content = {"metadata": {"name": "Stock Weekly Prices 2024", "datatype": "price", "time": dates}, "data": []}

    # Add data for each ticker
    for ticker in file_paths.keys():
        # Create date-to-data mappings
        date_to_change = {d['date']: d['change'] for d in all_weekly_data[ticker]}
        date_to_price = {d['date']: d['close'] for d in all_weekly_data[ticker]}

        # Calculate cumulative return (total) for changes
        price_timeseries = [date_to_price[date] for date in dates]
        total_return = round(((price_timeseries[-1] - price_timeseries[0]) / price_timeseries[0]) * 100, 2)

        # Add to changes content
        content_changes["data"].append(
            {"id": ticker, "description": descriptions[ticker], "timeseries": [date_to_change[date] for date in dates], "total": total_return}
        )

        # Calculate price delta (total) for prices
        total_price_delta = round(price_timeseries[-1] - price_timeseries[0], 2)

        # Add to prices content
        content_prices["data"].append({"id": ticker, "description": descriptions[ticker], "timeseries": price_timeseries, "total": total_price_delta})

    return content_changes, content_prices


if __name__ == "__main__":
    # Define input files and descriptions
    tickers = {
        "AAPL": {"file": "AAPL.csv", "description": "Apple Inc."},
        "MSFT": {"file": "MSFT.csv", "description": "Microsoft Corporation"},
        "TSLA": {"file": "TSLA.csv", "description": "Tesla, Inc."},
        "NVDA": {"file": "NVDA.csv", "description": "nVIDIA Corporation"},
        "META": {"file": "META.csv", "description": "Meta Platforms, Inc."},
        "GOOGL": {"file": "GOOGL.csv", "description": "Alphabet Inc."},
        "AMZN": {"file": "AMZN.csv", "description": "Amazon.com, Inc."},
        "SPY": {"file": "SPY.csv", "description": "SPDR S&P 500 ETF Trust"},
        "GLDM": {"file": "GLDM.csv", "description": "SPDR Gold ETF"},
        "VRT": {"file": "VRT.csv", "description": "Vertiv Holdings Co."},
        "VWETX": {"file": "VWETX.csv", "description": "Vanguard Long Term IG Fund"},
    }

    # Parse stock data and get both weekly changes and closing prices
    file_paths = {ticker: data["file"] for ticker, data in tickers.items()}
    descriptions = {ticker: data["description"] for ticker, data in tickers.items()}

    content_changes, content_prices = calculate_weekly_data(file_paths, descriptions)

    # Save weekly changes to testdata2.json
    with open("testdata2.json", "w") as f:
        json.dump(content_changes, f, indent=4)

    # Save weekly closing prices to testdata3.json
    with open("testdata3.json", "w") as f:
        json.dump(content_prices, f, indent=4)

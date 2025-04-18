import csv
import json
from class_definition import Content
from datetime import datetime
import pandas as pd
from typing import Dict, List


def calculate_weekly_data(file_paths: Dict[str, str], descriptions: Dict[str, str]) -> tuple[Content, Content]:
    all_weekly_data: Dict[str, List[dict]] = {}
    common_dates = set()

    # Process each stock's data
    for ticker, file_path in file_paths.items():
        # Read CSV into pandas DataFrame
        df = pd.read_csv(file_path)
        df['Date'] = pd.to_datetime(df['Date'])
        df['Week'] = (df['Date'] - df['Date'].min()).dt.days // 7 + 1

        # Group by week and calculate data
        weekly_data = []
        for week in df['Week'].unique():
            week_df = df[df['Week'] == week]
            if len(week_df) > 0:
                start_date = week_df.iloc[0]['Date'].strftime('%m-%d')
                start_price = week_df.iloc[0]['Close']
                end_price = week_df.iloc[-1]['Close']
                pct_change = ((end_price - start_price) / start_price) * 100
                weekly_data.append({'date': start_date, 'change': round(pct_change, 2), 'close': round(end_price, 2)})
                common_dates.add(start_date)

        all_weekly_data[ticker] = weekly_data

    # Sort dates to ensure consistent order
    dates = sorted(list(common_dates))

    # Create content structures for both files
    content_changes: Content = {"metadata": {"time": dates}, "data": []}

    content_prices: Content = {"metadata": {"time": dates}, "data": []}

    # Add data for each ticker
    for ticker in file_paths.keys():
        # Create date-to-data mappings
        date_to_change = {d['date']: d['change'] for d in all_weekly_data[ticker]}
        date_to_price = {d['date']: d['close'] for d in all_weekly_data[ticker]}

        # Add to changes content
        content_changes["data"].append({"id": ticker, "description": descriptions[ticker], "timeseries": [date_to_change[date] for date in dates]})

        # Add to prices content
        content_prices["data"].append({"id": ticker, "description": descriptions[ticker], "timeseries": [date_to_price[date] for date in dates]})

    return content_changes, content_prices


if __name__ == "__main__":
    # Define input files and descriptions
    tickers = {
        "AAPL": {"file": "AAPL_2025-01-01_2025-04-18.csv", "description": "Apple Inc."},
        "MSFT": {"file": "MSFT_2025-01-01_2025-04-18.csv", "description": "Microsoft Corporation"},
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

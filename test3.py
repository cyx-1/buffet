import csv
import json
from class_definition import Content


def parse_aapl_data(file_path: str) -> Content:
    # Initialize data structures
    dates = []
    closing_prices = []

    # Read CSV file
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dates.append(row['Date'])
            closing_prices.append(float(row['Close']))

    # Create the content structure with daily data
    content: Content = {"metadata": {"time": dates}, "data": [{"id": "AAPL", "description": "Apple Inc.", "timeseries": closing_prices}]}

    return content


if __name__ == "__main__":
    # Parse AAPL data
    content = parse_aapl_data("AAPL_2024-01-01_2024-04-18.csv")

    # Save to testdata2.json
    with open("testdata2.json", "w") as f:
        json.dump(content, f, indent=4)

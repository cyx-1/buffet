import csv
from datetime import datetime
from typing import TypedDict, List
import json


class AssetData(TypedDict):
    id: str
    description: str
    timeseries: List[float]


class ContentMetadata(TypedDict):
    time: List[str]


class Content(TypedDict):
    metadata: ContentMetadata
    data: List[AssetData]


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

    # Save to testdata2.py
    with open("testdata2.py", "w") as f:
        f.write("from typing import TypedDict, List\n\n\n")
        f.write("class AssetData(TypedDict):\n")
        f.write("    id: str\n")
        f.write("    description: str\n")
        f.write("    timeseries: List[float]\n\n\n")
        f.write("class ContentMetadata(TypedDict):\n")
        f.write("    time: List[str]\n\n\n")
        f.write("class Content(TypedDict):\n")
        f.write("    metadata: ContentMetadata\n")
        f.write("    data: List[AssetData]\n\n\n")
        f.write(f"content: Content = {json.dumps(content, indent=4)}\n")

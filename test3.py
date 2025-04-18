import csv
from datetime import datetime
from typing import TypedDict, List
import json


class AssetData(TypedDict):
    id: str
    description: str
    timeseries: List[float]


class ContentMetadata(TypedDict):
    years: List[str]


class Content(TypedDict):
    metadata: ContentMetadata
    data: List[AssetData]


def parse_aapl_data(file_path: str) -> Content:
    # Initialize data structures
    monthly_closes = {}

    # Read CSV file
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date = datetime.strptime(row['Date'], '%Y-%m-%d')
            year_month = date.strftime('%Y-%m')

            # Store the last (most recent) closing price for each month
            monthly_closes[year_month] = float(row['Close'])

    # Get sorted unique years
    years = sorted(list(set(ym.split('-')[0] for ym in monthly_closes.keys())))

    # Create the content structure
    content: Content = {
        "metadata": {"years": years},
        "data": [
            {
                "id": "AAPL",
                "description": "Apple Inc.",
                "timeseries": [
                    monthly_closes[f"{year}-12"] if f"{year}-12" in monthly_closes else list(v for k, v in monthly_closes.items() if k.startswith(year))[-1]
                    for year in years
                ],
            }
        ],
    }

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
        f.write("    years: List[str]\n\n\n")
        f.write("class Content(TypedDict):\n")
        f.write("    metadata: ContentMetadata\n")
        f.write("    data: List[AssetData]\n\n\n")
        f.write(f"content: Content = {json.dumps(content, indent=4)}\n")

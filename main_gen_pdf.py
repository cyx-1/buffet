import util_data
import json
import os
from util_ui import load_content, transform_data
from util_ui import PDF, create_table

if __name__ == "__main__":
    start = "2025-01-01"
    end = "2025-04-18"

    tickers_to_download = ["AAPL", "MSFT", "TSLA", "NVDA", "META", "GOOGL", "AMZN", "SPY", "GLDM", "VRT", "VWETX"]
    for ticker in tickers_to_download:
        util_data.download_ticker_data(ticker, start, end)

    # Define input files and descriptions
    finance_data_path = util_data.get_finance_data_path()
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
    file_paths = {ticker: os.path.join(finance_data_path, "asset_prices", data["file"]) for ticker, data in tickers.items()}
    descriptions = {ticker: data["description"] for ticker, data in tickers.items()}

    content_changes, content_prices = util_data.calculate_weekly_data(file_paths, descriptions)

    # Save weekly changes to testdata2.json
    with open("testdata2.json", "w") as f:
        json.dump(content_changes, f, indent=4)

    # Save weekly closing prices to testdata3.json
    with open("testdata3.json", "w") as f:
        json.dump(content_prices, f, indent=4)

    # Load data from JSON files dynamically
    json_files = sorted([f for f in os.listdir('.') if f.startswith('testdata') and f.endswith('.json')], key=lambda x: int(''.join(filter(str.isdigit, x))))
    contents = [load_content(json_file) for json_file in json_files]

    dfs = [transform_data(content) for content in contents]

    pdf = PDF(orientation="L")
    pdf.add_page()

    current_y = pdf.get_y()

    for i, (df, content) in enumerate(zip(dfs, contents)):
        current_y = create_table(pdf, df, content, current_y, content["metadata"].get("datatype") == "price")
        if i < len(dfs) - 1:
            pdf.ln(5)  # Add spacing between tables

    pdf.output("asset_returns.pdf")
    print("PDF has been generated as 'asset_returns.pdf'")

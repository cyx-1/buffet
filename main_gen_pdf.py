import util_data
import json
import os
from util_ui import load_content, transform_data
from util_ui import PDF, create_table

if __name__ == "__main__":
    start = "2025-01-01"
    end = "2025-04-18"

    tickers = {
        "AAPL": "Apple Inc.",
        "MSFT": "Microsoft Corporation",
        "TSLA": "Tesla, Inc.",
        "NVDA": "nVIDIA Corporation",
        "META": "Meta Platforms, Inc.",
        "GOOGL": "Alphabet Inc.",
        "AMZN": "Amazon.com, Inc.",
        "SPY": "SPDR S&P 500 ETF Trust",
        "GLDM": "SPDR Gold ETF",
        "VRT": "Vertiv Holdings Co.",
        "YPF": "YPF Sociedad Anonima",
        "WMT": "Walmart Inc.",
        "WAB": "Westinghouse Air Brake Technologies Corporation",
        "GE": "General Electric Aerospace",
        "GEHC": "GE HealthCare Technologies Inc.",
        "GEV": "GE Vernova",
        "INTC": "Intel Corporation",
        "MRK": "Merck & Co., Inc.",
        "WBD": "Warner Bros. Discovery, Inc.",
        "BYDDY": "BYD Company Limited",
        "VWETX": "Vanguard Long Term IG Fund",
        "VWENX": "Vanguard Wellington Admiral Fund",
        "VIIIX": "Vanguard Institutional Index Fund, SP500",
        "BTC": "Bitcoin",
    }

    for ticker in tickers:
        util_data.download_ticker_data(ticker, start, end)

    # Parse stock data and get both weekly changes and closing prices
    finance_data_path = util_data.get_finance_data_path()
    file_paths = {ticker: os.path.join(finance_data_path, "asset_prices", f"{ticker}.csv") for ticker in tickers}
    descriptions = tickers

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

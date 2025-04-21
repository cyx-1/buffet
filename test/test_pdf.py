import os
import pytest
from pypdf import PdfReader
import util_data
from util_ui import transform_data
from util_ui import PDF, create_table
import json


def setup_test_data(start_date, end_date, use_baseline=True):
    # Test with a smaller set of tickers
    test_tickers = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "SPY": "SPDR S&P 500 ETF Trust"}

    # Only download data if not using baseline
    if not use_baseline:
        for ticker in test_tickers:
            util_data.download_ticker_data(ticker, start_date, end_date)

    finance_data_path = util_data.get_finance_data_path()
    file_paths = {ticker: os.path.join(finance_data_path, "asset_prices", f"{ticker}.csv") for ticker in test_tickers}

    return file_paths, test_tickers


def load_baseline_data():
    """Load weekly data from baseline JSON files."""
    baseline_dir = os.path.join("test", "baseline")
    baseline_changes = os.path.join(baseline_dir, "baseline_changes.json")
    baseline_prices = os.path.join(baseline_dir, "baseline_prices.json")

    try:
        with open(baseline_changes, 'r') as f:
            content_changes = json.load(f)
        with open(baseline_prices, 'r') as f:
            content_prices = json.load(f)
        return content_changes, content_prices
    except Exception as e:
        raise ValueError(f"Failed to load baseline data: {str(e)}")


def generate_test_pdf(file_paths, descriptions, use_baseline=True, output_path="test_asset_returns.pdf"):
    if use_baseline:
        try:
            content_changes, content_prices = load_baseline_data()
        except Exception as e:
            print(f"Failed to load baseline data: {str(e)}, falling back to live data")
            content_changes, content_prices = util_data.calculate_weekly_data(file_paths, descriptions)
    else:
        content_changes, content_prices = util_data.calculate_weekly_data(file_paths, descriptions)

    # Generate PDF
    contents = [content_changes, content_prices]
    dfs = [transform_data(content) for content in contents]

    pdf = PDF(orientation="L")
    pdf.add_page()
    current_y = pdf.get_y()

    for i, (df, content) in enumerate(zip(dfs, contents)):
        current_y = create_table(pdf, df, content, current_y, content["metadata"].get("datatype") == "price")
        if i < len(dfs) - 1:
            pdf.ln(5)

    pdf.output(output_path)
    return output_path, content_changes, content_prices


def extract_pdf_text(pdf_path):
    """Extract text content from a PDF file"""
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        text += page.extract_text()
    return text


@pytest.fixture(scope="module")
def test_dates():
    return "2025-01-01", "2025-04-18"


def test_pdf_generation(test_dates):
    start_date, end_date = test_dates

    # Generate test PDF with reduced ticker set, using baseline data by default
    file_paths, descriptions = setup_test_data(start_date, end_date, use_baseline=True)
    test_pdf_path, _, _ = generate_test_pdf(file_paths, descriptions, use_baseline=True)

    # Extract text from generated PDF
    test_text = extract_pdf_text(test_pdf_path)

    # Save or compare with baseline
    baseline_dir = os.path.join("test", "baseline")
    os.makedirs(baseline_dir, exist_ok=True)
    baseline_text_path = os.path.join(baseline_dir, "baseline.txt")

    if not os.path.exists(baseline_text_path):
        # Save extracted text as baseline
        with open(baseline_text_path, 'w', encoding='utf-8') as f:
            f.write(test_text)
        pytest.skip("Baseline text file created. Run the test again to compare.")

    # Compare with baseline
    with open(baseline_text_path, 'r', encoding='utf-8') as f:
        baseline_text = f.read()

    assert test_text == baseline_text, "Generated PDF text differs from baseline"

    # Basic content verification
    assert "Apple Inc." in test_text, "PDF should contain Apple Inc."
    assert "Microsoft Corporation" in test_text, "PDF should contain Microsoft Corporation"
    assert "SPDR S&P 500 ETF Trust" in test_text, "PDF should contain SPDR S&P 500 ETF Trust"
    assert "Prior Week Asset Returns" in test_text, "PDF should contain Prior Week Asset Returns table"
    assert "Weekly Asset Prices" in test_text, "PDF should contain Weekly Asset Prices table"

    # Cleanup
    os.remove(test_pdf_path)

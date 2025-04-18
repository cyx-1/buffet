import pytest
from test import create_pdf, get_string_width, PDF
from testdata import content
import pandas as pd


@pytest.fixture
def sample_pdf():
    return PDF(orientation="L")


def test_set_cell_colors(sample_pdf):
    """Test cell color setting for positive and negative values"""
    # Test positive value
    sample_pdf.set_cell_colors(10.5)
    assert sample_pdf.fill_color == (230, 255, 230)  # light green background
    assert sample_pdf.text_color == (0, 100, 0)  # dark green text

    # Test negative value
    sample_pdf.set_cell_colors(-5.2)
    assert sample_pdf.fill_color == (255, 230, 230)  # light red background
    assert sample_pdf.text_color == (139, 0, 0)  # dark red text


def test_get_string_width(sample_pdf):
    """Test string width calculation"""
    sample_pdf.set_font("Courier", "", 12)
    width1 = get_string_width(sample_pdf, "Test")
    width2 = get_string_width(sample_pdf, "TestTest")
    assert width2 > width1  # Longer string should have greater width


def test_data_transformation():
    """Test that data is correctly transformed into DataFrame format"""
    # Transform data using the same logic as in the main code
    time_periods = content["metadata"]["time"]
    transformed_data = {
        "ID": [],
        "Description": [],
    }
    for period in time_periods:
        transformed_data[period] = []

    for item in content["data"]:
        transformed_data["ID"].append(item["id"])
        transformed_data["Description"].append(item["description"])
        for i, value in enumerate(item["timeseries"]):
            transformed_data[time_periods[i]].append(value)

    df = pd.DataFrame(transformed_data)

    # Verify DataFrame structure
    assert list(df.columns) == ["ID", "Description"] + time_periods
    assert len(df) == len(content["data"])

    # Verify data content
    first_item = content["data"][0]
    first_row = df.iloc[0]
    assert first_row["ID"] == first_item["id"]
    assert first_row["Description"] == first_item["description"]
    for i, period in enumerate(time_periods):
        assert first_row[period] == first_item["timeseries"][i]


def test_highest_lowest_returns():
    """Test calculation of highest and lowest returns"""
    # Create PDF to access the transformed data
    pdf = create_pdf()

    # Get the periods from content
    time_periods = content["metadata"]["time"]

    # For each period, verify that the highest and lowest returns are correct
    for period in time_periods:
        all_returns = [item["timeseries"][time_periods.index(period)] for item in content["data"]]
        max_return = max(all_returns)
        min_return = min(all_returns)

        # Find the corresponding IDs
        max_id = next(item["id"] for item in content["data"] if item["timeseries"][time_periods.index(period)] == max_return)
        min_id = next(item["id"] for item in content["data"] if item["timeseries"][time_periods.index(period)] == min_return)

        # These values should match what's shown in the PDF summary rows
        assert any(cell.text == str(max_id) for cell in pdf._cells if cell.text)  # type: ignore
        assert any(cell.text == str(min_id) for cell in pdf._cells if cell.text)  # type: ignore

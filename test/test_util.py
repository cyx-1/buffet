from util_data import download_file_and_compare, process_data_from_fred, Status, create_dual_axis_plot, calculate_weekly_data
import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')  # Use non-interactive backend for testing


def test_download_success(mocker):
    with open('./test/unemployment.csv', mode='rb') as file:
        csv_content = file.read()
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=200, content=csv_content))
    status = download_file_and_compare('', './temp', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'New file downloaded'

    status = download_file_and_compare('', './temp', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'No Change, skipping file update'

    with open('./test/unemployment2.csv', mode='rb') as file:
        csv_content = file.read()
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=200, content=csv_content))
    status = download_file_and_compare('', './temp', 'temp-unemployment.csv')
    assert status.success
    assert status.result == 'Change detected, file updated'
    os.remove('./temp/temp-unemployment.csv')


def test_download_failure(mocker):
    mocker.patch('requests.get', return_value=mocker.Mock(status_code=503, content=None))
    status = download_file_and_compare('', './temp', 'unemployment-monthly.csv')

    assert not status.success
    assert status.result == 'Failed with status code 503'


def test_process_data_from_fred_success(mocker):
    """Test the happy path for process_data_from_fred function."""
    # Mock the download_file_and_compare function
    mocker.patch('util_data.download_file_and_compare', return_value=Status(success=True, result='New file downloaded'))

    # Create a mock DataFrame that would be returned by pd.read_csv
    with open('./test/unemployment.csv', mode='rb') as file:
        csv_content = file.read()

    # Ensure the temp directory exists
    if not os.path.exists('./temp'):
        os.makedirs('./temp')

    # Write the mock data to a temporary file
    with open('./temp/test_unemployment.csv', 'wb') as file:
        file.write(csv_content)

    # Mock os.path.exists to return True for our test file
    original_exists = os.path.exists
    mocker.patch('os.path.exists', side_effect=lambda path: path == './temp/test_unemployment.csv' or original_exists(path))

    # Mock pd.read_csv to return our DataFrame
    mock_df = pd.read_csv('./temp/test_unemployment.csv')
    mocker.patch('pandas.read_csv', return_value=mock_df)

    # Call the function with test parameters
    status = process_data_from_fred('https://test.url', 'test_unemployment.csv', ['observation_date', 'UNRATE'], './temp')

    # Assert the results
    assert status.success
    assert isinstance(status.result, dict)
    assert status.result['download_status'] == 'New file downloaded'
    assert status.result['record_count'] == len(mock_df)
    assert 'date_range' in status.result
    assert 'latest_values' in status.result
    np.testing.assert_allclose(status.result['latest_values']['UNRATE'], 4.1, rtol=1e-10)  # Using approximate comparison for floating point

    # Clean up
    os.remove('./temp/test_unemployment.csv')


def test_process_data_from_fred_error_cases(mocker):
    """Test error handling in process_data_from_fred function."""
    # Create test data
    with open('./test/unemployment.csv', mode='rb') as file:
        csv_content = file.read()

    # Ensure the temp directory exists
    if not os.path.exists('./temp'):
        os.makedirs('./temp')

    # Test with invalid columns
    # First, create the test file
    with open('./temp/test_unemployment.csv', 'wb') as file:
        file.write(csv_content)

    # Mock necessary functions
    mocker.patch('util_data.download_file_and_compare', return_value=Status(success=True, result='New file downloaded'))

    # Mock os.path.exists to return True for our test file
    original_exists = os.path.exists
    mocker.patch('os.path.exists', side_effect=lambda path: path == './temp/test_unemployment.csv' or original_exists(path))

    # Mock pd.read_csv to return our DataFrame
    mock_df = pd.read_csv('./temp/test_unemployment.csv')
    mocker.patch('pandas.read_csv', return_value=mock_df)

    # Test with invalid columns
    status = process_data_from_fred('https://test.url', 'test_unemployment.csv', ['observation_date', 'INVALID_COLUMN'], './temp')

    # Should fail because the column doesn't exist
    assert not status.success
    assert "Required columns not found" in status.result

    # Clean up
    os.remove('./temp/test_unemployment.csv')

    # Test with download failure
    mocker.patch('util_data.download_file_and_compare', return_value=Status(success=False, result='Failed with status code 404'))

    status = process_data_from_fred('https://test.url', 'test_unemployment.csv', ['observation_date', 'UNRATE'], './temp')

    # Should fail because the download failed
    assert not status.success
    assert "Download failed" in status.result


def test_create_dual_axis_plot():
    """Test the dual axis plot creation function."""
    # Create sample data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='ME')  # Using ME instead of deprecated M
    rng = np.random.default_rng(seed=42)  # Create a seeded Generator instance for reproducible results
    df1 = pd.DataFrame({'observation_date': dates, 'value1': rng.uniform(3, 6, len(dates))})  # Simulated unemployment data
    df2 = pd.DataFrame({'observation_date': dates, 'value2': rng.uniform(20000, 25000, len(dates))})  # Simulated GDP data

    # Create the plot
    fig, ax1, ax2 = create_dual_axis_plot(
        df1=df1, df2=df2, date_column='observation_date', y1_column='value1', y2_column='value2', title='Test Dual Axis Plot', y1_label='Value 1', y2_label='Value 2'
    )

    # Test that the plot components were created correctly
    assert isinstance(fig, matplotlib.figure.Figure)
    assert isinstance(ax1, matplotlib.axes.Axes)
    assert isinstance(ax2, matplotlib.axes.Axes)

    # Test that the axes have the correct labels
    assert ax1.get_ylabel() == 'Value 1'
    assert ax2.get_ylabel() == 'Value 2'
    assert ax1.get_xlabel() == 'Date'

    # Test that the title was set correctly
    assert ax1.get_title() == 'Test Dual Axis Plot'

    # Test that both lines were plotted
    assert len(ax1.lines) == 1  # One line on primary axis
    assert len(ax2.lines) == 1  # One line on secondary axis

    # Clean up
    plt.close(fig)


def test_calculate_weekly_data(tmp_path):
    """Test the calculate_weekly_data function with sample stock data."""
    # Create sample data
    dates = pd.date_range(start='2023-01-02', end='2023-01-30', freq='B')  # Business days for 4+ weeks
    sample_data = pd.DataFrame(
        {
            'Date': dates,
            'Open': np.linspace(100, 110, len(dates)),
            'High': np.linspace(101, 111, len(dates)),
            'Low': np.linspace(99, 109, len(dates)),
            'Close': np.linspace(100.5, 110.5, len(dates)),
            'Volume': np.ones(len(dates)) * 1000000,
        }
    )

    # Create two sample CSV files
    file_path1 = tmp_path / "AAPL.csv"
    file_path2 = tmp_path / "MSFT.csv"
    sample_data.to_csv(file_path1, index=False)
    sample_data.to_csv(file_path2, index=False)

    # Setup input data
    file_paths = {"AAPL": str(file_path1), "MSFT": str(file_path2)}
    descriptions = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation"}

    # Call the function
    content_changes, content_prices = calculate_weekly_data(file_paths, descriptions)

    # Test metadata structure
    assert "metadata" in content_changes
    assert "metadata" in content_prices
    assert "name" in content_changes["metadata"]
    assert "name" in content_prices["metadata"]
    assert content_changes["metadata"]["name"] == "Prior Week Asset Returns"
    assert content_prices["metadata"]["name"] == "Weekly Asset Prices"

    # Test data structure
    assert "data" in content_changes
    assert "data" in content_prices
    assert len(content_changes["data"]) == 2  # Two stocks
    assert len(content_prices["data"]) == 2  # Two stocks

    # Test specific stock data
    for stock_data in content_changes["data"]:
        assert stock_data["id"] in ["AAPL", "MSFT"]
        assert stock_data["description"] in ["Apple Inc.", "Microsoft Corporation"]
        assert isinstance(stock_data["timeseries"], list)
        assert isinstance(stock_data["total"], float)

    for stock_data in content_prices["data"]:
        assert stock_data["id"] in ["AAPL", "MSFT"]
        assert stock_data["description"] in ["Apple Inc.", "Microsoft Corporation"]
        assert isinstance(stock_data["timeseries"], list)
        assert isinstance(stock_data["total"], float)


def test_calculate_weekly_data_empty_data(tmp_path):
    """Test calculate_weekly_data function with empty data."""
    # Create empty DataFrame
    empty_df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Save empty DataFrame
    file_path = tmp_path / "EMPTY.csv"
    empty_df.to_csv(file_path, index=False)

    file_paths = {"EMPTY": str(file_path)}
    descriptions = {"EMPTY": "Empty Stock"}

    # Call the function
    content_changes, content_prices = calculate_weekly_data(file_paths, descriptions)

    # Verify basic structure is maintained
    assert "metadata" in content_changes
    assert "metadata" in content_prices
    assert "data" in content_changes
    assert "data" in content_prices

    # Verify empty data is handled gracefully
    assert len(content_changes["data"]) == 1
    assert len(content_prices["data"]) == 1
    assert len(content_changes["data"][0]["timeseries"]) == 0
    assert len(content_prices["data"][0]["timeseries"]) == 0
    assert content_changes["data"][0]["total"] == 0
    assert content_prices["data"][0]["total"] == 0


def calculate_weekly_data_single_week(tmp_path):
    """Test calculate_weekly_data function with single week of data."""
    # Create sample data for a single week
    dates = pd.date_range(start='2023-01-02', end='2023-01-06', freq='B')  # One business week
    sample_data = pd.DataFrame(
        {
            'Date': dates,
            'Open': [100] * len(dates),
            'High': [101] * len(dates),
            'Low': [99] * len(dates),
            'Close': [100.5] * len(dates),
            'Volume': [1000000] * len(dates),
        }
    )

    file_path = tmp_path / "SINGLE.csv"
    sample_data.to_csv(file_path, index=False)

    file_paths = {"SINGLE": str(file_path)}
    descriptions = {"SINGLE": "Single Week Stock"}

    # Call the function
    content_changes, content_prices = calculate_weekly_data(file_paths, descriptions)

    # Verify single week data
    assert len(content_changes["data"]) == 1
    assert len(content_prices["data"]) == 1
    assert len(content_changes["data"][0]["timeseries"]) == 1
    assert len(content_prices["data"][0]["timeseries"]) == 1
    assert content_changes["data"][0]["total"] == 0  # No change in price
    assert content_prices["data"][0]["total"] == 0  # No change in price

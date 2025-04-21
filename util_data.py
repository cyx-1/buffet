import requests
import os
import pandas as pd
from collections import namedtuple
import matplotlib.pyplot as plt
import yaml
import yfinance as yf
from typing import Dict, List
from class_definition import Content

Status = namedtuple('Status', ['success', 'result'])


def download_file_and_compare(url, folder_path, file_name):
    """
    Downloads a file from a URL and compares it with an existing local file if present.

    This function attempts to download a file from the specified URL and handles
    several scenarios:
    1. If the local folder doesn't exist, it creates it
    2. If the file doesn't exist locally, it downloads and saves it
    3. If the file exists locally, it compares the content with the downloaded version:
       - If identical, it skips the update
       - If different, it updates the local file with the new content

    Parameters:
    -----------
    url : str
        The URL from which to download the file
    folder_path : str
        The local directory path where the file should be saved
    file_name : str
        The name to give the downloaded file

    Returns:
    --------
    Status : namedtuple
        A namedtuple with fields:
        - success (bool): True if the operation was successful, False otherwise
        - result (str): A message describing the outcome of the operation

    Possible Status Results:
    -----------------------
    - Success=True, result='New file downloaded': File didn't exist and was downloaded
    - Success=True, result='No Change, skipping file update': File exists and content is identical
    - Success=True, result='Change detected, file updated': File exists but content changed, so it was updated
    - Success=False, result='Failed with status code {code}': Download failed with the specified HTTP status code
    """

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)  # pragma: no cover

    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder_path, file_name)
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return Status(success=True, result='New file downloaded')
        else:
            with open(file_path, 'rb') as file:
                file_content = file.read()
                if file_content == response.content:
                    return Status(success=True, result='No Change, skipping file update')
                else:
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                    return Status(success=True, result='Change detected, file updated')
    else:
        return Status(success=False, result=f'Failed with status code {response.status_code}')


def process_data_from_fred(url: str, file_name: str, columns: list[str], folder_path: str) -> Status:
    """
    Download and process time series data from a given URL.

    Args:
        url (str): The URL to download the time series data from
        file_name (str): The name of the file to save the data as
        columns (list[str]): List of columns where first is date column and rest are data columns
        folder_path (str): Path to the folder where data should be saved

    Returns:
        Status: A Status object with success flag and result message or data summary
    """
    try:
        # Download and get the file path
        download_status = download_file_and_compare(url, folder_path, file_name)

        if not download_status.success:
            return Status(success=False, result=f"Download failed: {download_status.result}")

        # Read and process the data
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)

            # Validate data
            if not all(col in df.columns for col in columns):
                return Status(success=False, result=f"Required columns not found in the data. Need {columns}")

            date_column = columns[0]
            data_columns = columns[1:]

            # Prepare data summary
            date_range = f"{df[date_column].min()} to {df[date_column].max()}"
            record_count = len(df)
            latest_values = {col: df[col].iloc[-1] for col in data_columns}

            # Create a detailed result dictionary
            result = {'download_status': download_status.result, 'date_range': date_range, 'record_count': record_count, 'latest_values': latest_values}

            return Status(success=True, result=result)
        else:
            return Status(success=False, result=f"File not found at {file_path}")

    except Exception as e:
        return Status(success=False, result=f"An error occurred: {str(e)}")


def _add_recession_shading(ax, recession_df, date_range):
    """Add recession shading to the plot if recession data is available."""
    if recession_df is None or recession_df.empty:
        return

    min_date, max_date = date_range
    try:
        recession_df.columns = recession_df.columns.str.strip()

        if 'Type' in recession_df.columns:
            recession_df = recession_df[recession_df['Type'].isna() | (recession_df['Type'].str.strip() == 'Recession')]

        for col in ['Start', 'End']:
            if col not in recession_df.columns:
                raise ValueError(f"Required column '{col}' not found in recession data")
            recession_df[col] = pd.to_datetime(recession_df[col].str.strip())

        mask = (recession_df['Start'] <= max_date) & (recession_df['End'] >= min_date)
        recession_df = recession_df[mask]

        for idx, row in recession_df.iterrows():
            ax.axvspan(row['Start'], row['End'], color='gray', alpha=0.2, label='Recession' if idx == 0 else "")
    except Exception as e:
        print(f"Warning: Could not process recession data: {str(e)}")


def create_dual_axis_plot(
    df1: pd.DataFrame,
    df2: pd.DataFrame,
    date_column: str,
    y1_column: str,
    y2_column: str,
    title: str,
    y1_label: str,
    y2_label: str,
    recession_df: pd.DataFrame | None = None,
    figsize: tuple = (12, 6),
) -> tuple[plt.Figure, plt.Axes, plt.Axes]:
    """
    Create a dual-axis plot comparing two time series.

    Args:
        df1 (pd.DataFrame): First dataframe containing the first time series
        df2 (pd.DataFrame): Second dataframe containing the second time series
        date_column (str): Name of the date column in both dataframes
        y1_column (str): Name of the column to plot on primary y-axis
        y2_column (str): Name of the column to plot on secondary y-axis
        title (str): Title of the plot
        y1_label (str): Label for primary y-axis
        y2_label (str): Label for secondary y-axis
        recession_df (pd.DataFrame | None): DataFrame with recession periods (Start and End columns)
        figsize (tuple): Figure size in inches (width, height)

    Returns:
        tuple[plt.Figure, plt.Axes, plt.Axes]: Figure and both axes objects
    """
    df1[date_column] = pd.to_datetime(df1[date_column])
    df2[date_column] = pd.to_datetime(df2[date_column])

    fig, ax1 = plt.subplots(figsize=figsize)

    date_range = (min(df1[date_column].min(), df2[date_column].min()), max(df1[date_column].max(), df2[date_column].max()))
    _add_recession_shading(ax1, recession_df, date_range)

    # Plot first series
    color1 = '#1f77b4'
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel(y1_label, color=color1, fontsize=12)
    line1 = ax1.plot(df1[date_column], df1[y1_column], color=color1, label=y1_label)
    ax1.tick_params(axis='y', labelcolor=color1)

    # Plot second series
    ax2 = ax1.twinx()
    color2 = '#ff7f0e'
    ax2.set_ylabel(y2_label, color=color2, fontsize=12)
    line2 = ax2.plot(df2[date_column], df2[y2_column], color=color2, label=y2_label, linestyle='--')
    ax2.tick_params(axis='y', labelcolor=color2)

    ax1.grid(True, alpha=0.3)

    # Handle legend
    lines = line1 + line2
    labels = [line.get_label() for line in lines]
    if recession_df is not None and not recession_df.empty:
        from matplotlib.patches import Patch

        recession_patch = Patch(facecolor='gray', alpha=0.2, label='Recession')
        ax1.legend(handles=lines + [recession_patch], labels=labels + ['Recession'], loc='upper left')

    ax1.legend(lines, [str(label) for label in labels], loc='upper left')
    ax1.set_title(title, fontsize=14, pad=15)
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig, ax1, ax2


def get_finance_data_path():
    """
    Reads the .buffet file in the home directory to get the finance_data path.

    Returns:
        str: The full path to the finance_data directory.
    """
    home_dir = os.path.expanduser("~")
    buffet_file = os.path.join(home_dir, ".buffet")

    with open(buffet_file, "r") as file:
        config = yaml.safe_load(file)

    return config["finance_data"]


def download_ticker_data(ticker_symbol: str, start_date: str, end_date: str):
    """
    Download historical data for a given ticker and save to CSV only if the file doesn't exist

    Args:
        ticker_symbol (str): The stock ticker symbol (e.g., 'AAPL')
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format

    Returns:
        None
    """
    finance_data_path = get_finance_data_path()
    output_dir = os.path.join(finance_data_path, "asset_prices")
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"{ticker_symbol}.csv")

    # Check if file already exists
    if os.path.exists(output_file):
        print(f"File {output_file} already exists. Skipping download.")
        return

    # Create a Ticker object
    ticker = yf.Ticker(ticker_symbol)

    # Download the data
    data = ticker.history(start=start_date, end=end_date)

    # Ensure dates are in ISO format and prices are rounded to 2 decimals
    data.index = data.index.strftime('%Y-%m-%d')  # Convert index to ISO format
    data = data.round(2)  # Round all numeric columns to 2 decimals

    # Save to CSV
    data.to_csv(output_file)
    print(f"Data saved to {output_file}")


def calculate_weekly_data(file_paths: Dict[str, str], descriptions: Dict[str, str]) -> tuple[Content, Content]:
    """
    Calculate weekly data for given file paths and descriptions.

    Args:
        file_paths (Dict[str, str]): A dictionary mapping tickers to file paths.
        descriptions (Dict[str, str]): A dictionary mapping tickers to descriptions.

    Returns:
        tuple[Content, Content]: Weekly changes and weekly prices content.
    """
    # Original calculation logic
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
                date = pd.to_datetime(str(date))  # convert hashable to timestamp
                start_date = date.strftime('%m-%d')  # MM-DD format
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
    content_changes: Content = {"metadata": {"name": "Prior Week Asset Returns", "datatype": "return", "time": dates}, "data": []}

    content_prices: Content = {"metadata": {"name": "Weekly Asset Prices", "datatype": "price", "time": dates}, "data": []}

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

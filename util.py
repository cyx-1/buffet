import requests
import os
import sys
import pandas as pd
from collections import namedtuple
from pathlib import Path
import matplotlib.pyplot as plt

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
            result = {
                'download_status': download_status.result,
                'date_range': date_range,
                'record_count': record_count,
                'latest_values': latest_values
            }
                
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
            ax.axvspan(row['Start'], row['End'], color='gray', alpha=0.2, 
                      label='Recession' if idx == 0 else "")
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
    figsize: tuple = (12, 6)
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
    
    date_range = (
        min(df1[date_column].min(), df2[date_column].min()),
        max(df1[date_column].max(), df2[date_column].max())
    )
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
    labels = [l.get_label() for l in lines]
    if recession_df is not None and not recession_df.empty:
        from matplotlib.patches import Patch
        lines.append(Patch(facecolor='gray', alpha=0.2))
        labels.append('Recession')
    
    ax1.legend(lines, labels, loc='upper left')
    ax1.set_title(title, fontsize=14, pad=15)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig, ax1, ax2

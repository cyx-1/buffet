import util
import sys
import os
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


def create_economic_indicators_plot(folder_path: str) -> tuple[plt.Figure, plt.Axes, plt.Axes]:
    """
    Download economic indicators from FRED and create a dual-axis plot.
    
    Args:
        folder_path (str): Path where the data files will be stored
        
    Returns:
        tuple[plt.Figure, plt.Axes, plt.Axes]: The figure and both axes objects
    """
    # Download unemployment data
    unemployment_url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=UNRATE&cosd=1948-01-01&fq=Monthly'
    unemployment_file = 'unemployment-monthly.csv'
    unemployment_status = util.process_data_from_fred(
        unemployment_url, 
        unemployment_file, 
        ['observation_date', 'UNRATE'], 
        folder_path
    )
    
    # Download GDP data
    gdp_url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=GDP&cosd=1947-01-01&fq=Quarterly'
    gdp_file = 'gdp-quarterly.csv'
    gdp_status = util.process_data_from_fred(
        gdp_url, 
        gdp_file, 
        ['observation_date', 'GDP'], 
        folder_path
    )
    
    # Check if both downloads were successful
    if not (unemployment_status.success and gdp_status.success):
        raise RuntimeError("Failed to download economic data")
    
    # Read the data files
    unemployment_df = pd.read_csv(os.path.join(folder_path, unemployment_file))
    gdp_df = pd.read_csv(os.path.join(folder_path, gdp_file))
    
    # Read recession data
    recession_file = os.path.join(folder_path, 'recessions.csv')
    recession_df = None
    if os.path.exists(recession_file):
        try:
            # Read CSV with proper handling of whitespace in column names
            recession_df = pd.read_csv(recession_file, delimiter='\t')
        except Exception as e:
            print(f"Warning: Could not read recession data: {str(e)}")
    
    # Create the plot
    return util.create_dual_axis_plot(
        df1=unemployment_df,
        df2=gdp_df,
        date_column='observation_date',
        y1_column='UNRATE',
        y2_column='GDP',
        title='US Unemployment Rate and GDP Over Time',
        y1_label='Unemployment Rate (%)',
        y2_label='GDP (Billions of Dollars)',
        recession_df=recession_df
    )


if __name__ == '__main__':
    # Use a portable path structure
    home_dir = str(Path.home())
    folder_path = os.path.join(home_dir, 'OneDrive', 'PDAJ', 'Yexin', 'Finance', 'Data')
    
    # Create the plot
    fig, ax1, ax2 = create_economic_indicators_plot(folder_path)
    
    # Save the plot
    plt.savefig(os.path.join(folder_path, 'economic_indicators.png'))
    plt.close(fig)


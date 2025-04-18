import pandas as pd
from fpdf import FPDF
from typing import Dict, List, Union
import json
import os
from class_definition import Content


def load_content(json_file: str) -> Content:
    """Load content from a JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)


def transform_data(content: Dict) -> pd.DataFrame:
    """Transform content dictionary into a DataFrame"""
    time_periods: List[str] = content["metadata"]["time"]
    transformed_data: Dict[str, List[Union[str, float]]] = {"ID": [], "Description": []}
    for period in time_periods:
        transformed_data[period] = []

    has_total = "total" in content["data"][0]  # Check if 'total' exists in the JSON
    if has_total:
        transformed_data["Total"] = []  # Include Total column if it exists

    for item in content["data"]:
        transformed_data["ID"].append(item["id"])
        transformed_data["Description"].append(item["description"])
        for i, value in enumerate(item["timeseries"]):
            transformed_data[time_periods[i]].append(value)
        if has_total:
            transformed_data["Total"].append(item["total"])  # Use Total from JSON if it exists

    return pd.DataFrame(transformed_data)


class PDF(FPDF):
    def set_cell_colors(self, value: float) -> None:
        if value > 0:
            self.set_fill_color(230, 255, 230)  # light green background
            self.set_text_color(0, 100, 0)  # dark green text
        else:
            self.set_fill_color(255, 230, 230)  # light red background
            self.set_text_color(139, 0, 0)  # dark red text


def get_string_width(pdf: FPDF, text: str) -> float:
    return pdf.get_string_width(str(text))


def create_table(pdf: FPDF, df: pd.DataFrame, content: Dict, start_y: float, is_price_table: bool = False) -> float:
    """Create a table in the PDF and return the ending Y position"""
    time_periods = list(df.columns)[2:]  # Skip ID and Description columns

    # Calculate highest and lowest returns for each period
    highest_returns: Dict[str, float] = {}
    lowest_returns: Dict[str, float] = {}
    highest_ids: Dict[str, str] = {}
    lowest_ids: Dict[str, str] = {}
    for period in time_periods:
        highest_idx = df[period].idxmax()
        lowest_idx = df[period].idxmin()
        highest_returns[period] = float(pd.to_numeric(df.loc[highest_idx, period], errors='coerce'))
        lowest_returns[period] = float(pd.to_numeric(df.loc[lowest_idx, period], errors='coerce'))
        highest_ids[period] = str(df.loc[highest_idx, "ID"])
        lowest_ids[period] = str(df.loc[lowest_idx, "ID"])

    # Calculate optimal column widths
    pdf.set_font("Courier", "", 5)  # Base font for content
    pdf.set_font("Courier", "B", 6)  # Header font

    # Calculate ID width with extra padding considering both content and header
    all_ids = list(df["ID"]) + [highest_ids[period] for period in time_periods] + [lowest_ids[period] for period in time_periods]
    id_width = max(get_string_width(pdf, "ID"), max(get_string_width(pdf, str(id_val)) for id_val in all_ids)) * 1.2

    # Calculate description width with extra padding considering both content and header
    pdf.set_font("Courier", "B", 6)  # Header font for "Description"
    header_desc_width = get_string_width(pdf, "Description")
    pdf.set_font("Courier", "", 5)  # Content font
    content_desc_width = max(get_string_width(pdf, str(desc)) for desc in df["Description"])
    description_width = max(header_desc_width, content_desc_width) * 1.15

    # Calculate maximum width needed for any return column
    pdf.set_font("Courier", "B", 6)  # Header font for period headers
    max_return_width = 0
    for period in time_periods:
        # Get header width
        header_width = get_string_width(pdf, period)

        # Get maximum content width using content font
        pdf.set_font("Courier", "", 5)
        if is_price_table:
            content_widths = [get_string_width(pdf, f"{value:.2f}") for value in df[period]]
        else:
            content_widths = [get_string_width(pdf, f"{value:.1f}%") for value in df[period]]
        content_width = max(content_widths)

        # Use the larger of header or content width
        period_width = max(header_width, content_width)
        max_return_width = max(max_return_width, period_width)

    standard_return_width = max_return_width * 1.25  # Reduced padding for better compactness
    row_height = pdf.font_size * 1.8  # Slightly reduced row height

    # Set position for the table
    pdf.set_xy(pdf.l_margin, start_y)

    # Add title from metadata
    pdf.set_font("Courier", "B", 7.5)
    pdf.cell(0, 6, content["metadata"]["name"], ln=True, align="L")
    pdf.ln(2)

    # Table headers - set explicit colors
    pdf.set_font("Courier", "B", 6)
    pdf.set_text_color(0, 0, 0)  # Black text
    pdf.set_fill_color(240, 240, 240)  # Light gray background for headers

    pdf.cell(id_width, row_height, "ID", 1, fill=True, align="L")
    pdf.cell(description_width, row_height, "Description", 1, fill=True, align="L")
    for period in time_periods:
        pdf.cell(standard_return_width, row_height, period, 1, align="L", fill=True)
    pdf.ln()

    # Table data
    pdf.set_font("Courier", "", 5)
    for index, row in df.iterrows():
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)

        pdf.cell(id_width, row_height, str(row["ID"]), 1, fill=True, align="L")
        pdf.cell(description_width, row_height, str(row["Description"]), 1, fill=True, align="L")

        for period in time_periods:
            value = float(row[period])
            if not is_price_table:
                pdf.set_cell_colors(value)
            pdf.set_font("Courier", "B", 5)
            if is_price_table:
                pdf.cell(standard_return_width, row_height, f"{value:.2f}", 1, align="L", fill=True)
            else:
                pdf.cell(standard_return_width, row_height, f"{value:.1f}%", 1, align="L", fill=True)
            pdf.set_font("Courier", "", 5)
        pdf.ln()

    # Summary rows
    if not is_price_table:
        combined_width = id_width + description_width

        # Highest Returns row
        pdf.set_font("Courier", "B", 5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)
        pdf.cell(combined_width, row_height, "Highest Return", 1, fill=True, align="L")
        for period in time_periods:
            pdf.cell(standard_return_width, row_height, str(highest_ids[period]), 1, align="L", fill=True)
        pdf.ln()

        # Lowest Returns row
        pdf.cell(combined_width, row_height, "Lowest Return", 1, fill=True, align="L")
        for period in time_periods:
            pdf.cell(standard_return_width, row_height, str(lowest_ids[period]), 1, align="L", fill=True)
        pdf.ln()

    return pdf.get_y()


if __name__ == "__main__":
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

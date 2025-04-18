import pandas as pd
from fpdf import FPDF
from typing import Dict, List, Union
import json


def load_content(json_file: str) -> Dict:
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

    highest_ids, lowest_ids = calculate_extremes(df, time_periods)
    id_width, description_width, standard_return_width, row_height = calculate_column_widths(pdf, df, time_periods, is_price_table)

    pdf.set_xy(pdf.l_margin, start_y)
    add_table_title(pdf, content)
    add_table_headers(pdf, time_periods, id_width, description_width, standard_return_width, row_height)
    add_table_data(pdf, df, time_periods, id_width, description_width, standard_return_width, row_height, is_price_table)
    if not is_price_table:
        add_summary_rows(pdf, time_periods, id_width, description_width, standard_return_width, row_height, highest_ids, lowest_ids)

    return pdf.get_y()


def calculate_extremes(df: pd.DataFrame, time_periods: List[str]):
    highest_ids, lowest_ids = {}, {}
    for period in time_periods:
        highest_idx = df[period].idxmax()
        lowest_idx = df[period].idxmin()
        highest_ids[period] = str(df.loc[highest_idx, "ID"])
        lowest_ids[period] = str(df.loc[lowest_idx, "ID"])
    return highest_ids, lowest_ids


def calculate_column_widths(pdf: FPDF, df: pd.DataFrame, time_periods: List[str], is_price_table: bool):
    pdf.set_font("Courier", "", 5)
    pdf.set_font("Courier", "B", 6)

    all_ids = (
        list(df["ID"]) + [str(df.loc[df[period].idxmax(), "ID"]) for period in time_periods] + [str(df.loc[df[period].idxmin(), "ID"]) for period in time_periods]
    )
    id_width = max(get_string_width(pdf, "ID"), max(get_string_width(pdf, str(id_val)) for id_val in all_ids)) * 1.2

    header_desc_width = get_string_width(pdf, "Description")
    content_desc_width = max(get_string_width(pdf, str(desc)) for desc in df["Description"])
    description_width = max(header_desc_width, content_desc_width) * 1.15

    max_return_width = 0.0
    for period in time_periods:
        header_width = get_string_width(pdf, period)
        content_widths = [get_string_width(pdf, f"{value:.2f}" if is_price_table else f"{value:.1f}%") for value in df[period]]
        content_width = max(content_widths)
        max_return_width = max(max_return_width, max(header_width, content_width))

    standard_return_width = max_return_width * 1.25
    row_height = pdf.font_size * 1.8
    return id_width, description_width, standard_return_width, row_height


def add_table_title(pdf: FPDF, content: Dict):
    pdf.set_font("Courier", "B", 7)
    pdf.cell(0, 6, content["metadata"]["name"], ln=True, align="L")
    pdf.ln(0.5)


def add_table_headers(pdf: FPDF, time_periods: List[str], id_width: float, description_width: float, standard_return_width: float, row_height: float):
    pdf.set_font("Courier", "B", 6)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(240, 240, 240)

    pdf.cell(id_width, row_height, "ID", 1, fill=True, align="L")
    pdf.cell(description_width, row_height, "Description", 1, fill=True, align="L")
    for period in time_periods:
        pdf.cell(standard_return_width, row_height, period, 1, align="L", fill=True)
    pdf.ln()


def add_table_data(
    pdf: FPDF,
    df: pd.DataFrame,
    time_periods: List[str],
    id_width: float,
    description_width: float,
    standard_return_width: float,
    row_height: float,
    is_price_table: bool,
):
    pdf.set_font("Courier", "", 5)
    for _, row in df.iterrows():
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)

        pdf.cell(id_width, row_height, str(row["ID"]), 1, fill=True, align="L")
        pdf.cell(description_width, row_height, str(row["Description"]), 1, fill=True, align="L")

        for period in time_periods:
            value = float(row[period])
            if not is_price_table and isinstance(pdf, PDF):
                pdf.set_cell_colors(value)
            pdf.set_font("Courier", "B", 5)
            pdf.cell(standard_return_width, row_height, f"{value:.2f}" if is_price_table else f"{value:.1f}%", 1, align="L", fill=True)
            pdf.set_font("Courier", "", 5)
        pdf.ln()


def add_summary_rows(
    pdf: FPDF,
    time_periods: List[str],
    id_width: float,
    description_width: float,
    standard_return_width: float,
    row_height: float,
    highest_ids: Dict[str, str],
    lowest_ids: Dict[str, str],
):
    combined_width = id_width + description_width

    pdf.set_font("Courier", "B", 5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

    pdf.cell(combined_width, row_height, "Highest Return", 1, fill=True, align="L")
    for period in time_periods:
        pdf.cell(standard_return_width, row_height, str(highest_ids[period]), 1, align="L", fill=True)
    pdf.ln()

    pdf.cell(combined_width, row_height, "Lowest Return", 1, fill=True, align="L")
    for period in time_periods:
        pdf.cell(standard_return_width, row_height, str(lowest_ids[period]), 1, align="L", fill=True)
    pdf.ln()

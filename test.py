import pandas as pd
from fpdf import FPDF
from testdata import content
from typing import Dict, List, Union


# Transform data into DataFrame format
time_periods: List[str] = content["metadata"]["time"]
transformed_data: Dict[str, List[Union[str, float]]] = {
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

# Create DataFrame
df = pd.DataFrame(transformed_data)


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


def create_pdf() -> FPDF:
    # Create a PDF
    pdf = PDF(orientation="L")
    pdf.add_page()

    # Change default font to Courier
    pdf.set_font("Courier", "B", 8)

    # Calculate the exact width needed for the title
    title_width = get_string_width(pdf, "Asset Class Total Returns 2020-2024")
    pdf.cell(title_width, 6, "Asset Class Total Returns 2020-2024", ln=True, align="L")
    pdf.ln(2)

    # Calculate highest and lowest returns and corresponding IDs for each period
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

    # Calculate optimal column widths based on exact content width with safety margin
    pdf.set_font("Courier", "", 5)

    # Calculate ID width with extra padding and include highest/lowest IDs in calculation
    all_ids = list(df["ID"]) + [highest_ids[period] for period in time_periods] + [lowest_ids[period] for period in time_periods]
    id_width = max(get_string_width(pdf, "ID"), max(get_string_width(pdf, str(id_val)) for id_val in all_ids)) * 1.5  # Increased padding to 50% for ID column

    description_width = (
        max(get_string_width(pdf, "Description"), max(get_string_width(pdf, str(desc)) for desc in df["Description"])) * 1.2
    )  # Increased padding to 20%

    # Calculate maximum width needed for any return column
    max_return_width = 0.0
    for period in time_periods:
        period_width = max(
            get_string_width(pdf, period),
            max(get_string_width(pdf, f"{value:.1f}%") for value in df[period]),  # Format to 1 decimal place
            get_string_width(pdf, f"{highest_returns[period]:.1f}%"),
            get_string_width(pdf, f"{lowest_returns[period]:.1f}%"),
        )
        max_return_width = max(max_return_width, period_width)

    # Add 20% padding to the return column width and use it for all period columns
    standard_return_width = max_return_width * 1.2

    # Calculate row height based on font size with more space
    row_height = pdf.font_size * 1.8  # Increased from 1.5 to 1.8 for better visibility

    # Reset colors for headers
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

    # Table headers with adjusted height
    pdf.set_font("Courier", "B", 6)
    pdf.cell(id_width, row_height, "ID", 1, fill=True, align="L")
    pdf.cell(description_width, row_height, "Description", 1, fill=True, align="L")
    for period in time_periods:
        pdf.cell(standard_return_width, row_height, period, 1, align="L", fill=True)
    pdf.ln()

    # Table data with adjusted height
    pdf.set_font("Courier", "", 5)
    for index, row in df.iterrows():
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)

        pdf.cell(id_width, row_height, str(row["ID"]), 1, fill=True, align="L")
        pdf.cell(description_width, row_height, str(row["Description"]), 1, fill=True, align="L")

        for period in time_periods:
            value = float(row[period])
            pdf.set_cell_colors(value)
            pdf.set_font("Courier", "B", 5)
            pdf.cell(standard_return_width, row_height, f"{value:.1f}%", 1, align="L", fill=True)  # Format to 1 decimal place
            pdf.set_font("Courier", "", 5)
        pdf.ln()

    # Add summary rows
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

    return pdf


if __name__ == "__main__":
    pdf = create_pdf()
    pdf.output("asset_returns.pdf")
    print("PDF has been generated as 'asset_returns.pdf'")

import pandas as pd
from fpdf import FPDF
from testdata import content
from typing import Dict, List, Union


# Transform data into DataFrame format
years: List[str] = content["metadata"]["years"]
transformed_data: Dict[str, List[Union[str, float]]] = {
    "ID": [],
    "Description": [],
}
for year in years:
    transformed_data[year] = []

for item in content["data"]:
    transformed_data["ID"].append(item["id"])
    transformed_data["Description"].append(item["description"])
    for i, value in enumerate(item["timeseries"]):
        transformed_data[years[i]].append(value)

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
    pdf.set_font("Courier", "B", 12)

    # Add title
    pdf.cell(0, 10, "Asset Class Total Returns 2020-2024", ln=True, align="C")
    pdf.ln(5)

    # Calculate highest and lowest returns and corresponding IDs for each year
    highest_returns: Dict[str, float] = {}
    lowest_returns: Dict[str, float] = {}
    highest_ids: Dict[str, str] = {}
    lowest_ids: Dict[str, str] = {}
    for year in years:
        highest_idx = df[year].idxmax()
        lowest_idx = df[year].idxmin()
        highest_returns[year] = float(pd.to_numeric(df.loc[highest_idx, year], errors='coerce'))
        lowest_returns[year] = float(pd.to_numeric(df.loc[lowest_idx, year], errors='coerce'))
        highest_ids[year] = str(df.loc[highest_idx, "ID"])
        lowest_ids[year] = str(df.loc[lowest_idx, "ID"])

    # Calculate optimal column widths based on content
    pdf.set_font("Courier", "", 8)
    id_width = max(get_string_width(pdf, "ID"), max(get_string_width(pdf, str(id_val)) for id_val in df["ID"])) + 4

    description_width = max(get_string_width(pdf, "Description"), max(get_string_width(pdf, str(desc)) for desc in df["Description"])) + 2

    # Calculate year column widths
    year_widths: Dict[str, float] = {}
    for year in years:
        year_widths[year] = (
            max(
                get_string_width(pdf, year),
                max(get_string_width(pdf, f"{value}%") for value in df[year]),
                get_string_width(pdf, f"{highest_returns[year]}%"),
                get_string_width(pdf, f"{lowest_returns[year]}%"),
            )
            + 4
        )

    # Reset colors for headers
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

    # Table headers
    pdf.set_font("Courier", "B", 9)
    pdf.cell(id_width, 10, "ID", 1, fill=True, align="C")
    pdf.cell(description_width, 10, "Description", 1, fill=True)
    for year in years:
        pdf.cell(year_widths[year], 10, year, 1, align="C", fill=True)
    pdf.ln()

    # Table data
    pdf.set_font("Courier", "", 8)
    for index, row in df.iterrows():
        pdf.set_text_color(0, 0, 0)
        pdf.set_fill_color(255, 255, 255)

        pdf.cell(id_width, 10, str(row["ID"]), 1, fill=True, align="C")
        pdf.cell(description_width, 10, str(row["Description"]), 1, fill=True)

        for year in years:
            value = float(row[year])
            pdf.set_cell_colors(value)
            pdf.set_font("Courier", "B", 8)
            pdf.cell(year_widths[year], 10, f"{value}%", 1, align="C", fill=True)
            pdf.set_font("Courier", "", 8)
        pdf.ln()

    # Add summary rows for highest and lowest returns
    combined_width = id_width + description_width

    # Highest Returns row
    pdf.set_font("Courier", "B", 8)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(combined_width, 10, "Highest Return", 1, fill=True, align="C")
    for year in years:
        pdf.cell(year_widths[year], 10, str(highest_ids[year]), 1, align="C", fill=True)
    pdf.ln()

    # Lowest Returns row
    pdf.cell(combined_width, 10, "Lowest Return", 1, fill=True, align="C")
    for year in years:
        pdf.cell(year_widths[year], 10, str(lowest_ids[year]), 1, align="C", fill=True)
    pdf.ln()

    return pdf


if __name__ == "__main__":
    pdf = create_pdf()
    pdf.output("asset_returns.pdf")
    print("PDF has been generated as 'asset_returns.pdf'")

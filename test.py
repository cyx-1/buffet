import pandas as pd
from fpdf import FPDF
from testdata import data

# Create DataFrame
df = pd.DataFrame(data)


class PDF(FPDF):
    def set_cell_colors(self, value):
        if value > 0:
            self.set_fill_color(230, 255, 230)  # light green background
            self.set_text_color(0, 100, 0)  # dark green text
        else:
            self.set_fill_color(255, 230, 230)  # light red background
            self.set_text_color(139, 0, 0)  # dark red text


# Create a PDF
pdf = PDF(orientation='L')  # Landscape orientation for better fit
pdf.add_page()

# Change default font to Courier
pdf.set_font('Courier', 'B', 12)

# Add title
pdf.cell(0, 10, 'Asset Class Total Returns 2020-2024', ln=True, align='C')
pdf.ln(5)


# Function to calculate text width
def get_string_width(pdf, text):
    return pdf.get_string_width(str(text))


# Calculate highest and lowest returns and corresponding IDs for each year
highest_returns = {}
lowest_returns = {}
highest_ids = {}
lowest_ids = {}
years = ['2020', '2021', '2022', '2023', '2024']
for year in years:
    highest_idx = df[year].idxmax()
    lowest_idx = df[year].idxmin()
    highest_returns[year] = df.loc[highest_idx, year]
    lowest_returns[year] = df.loc[lowest_idx, year]
    highest_ids[year] = df.loc[highest_idx, 'ID']
    lowest_ids[year] = df.loc[lowest_idx, 'ID']

# Calculate optimal column widths based on content
pdf.set_font('Courier', '', 8)  # Set font for content measurement
id_width = max(get_string_width(pdf, 'ID'), max(get_string_width(pdf, str(id_val)) for id_val in df['ID'])) + 4

description_width = max(get_string_width(pdf, 'Description'), max(get_string_width(pdf, str(desc)) for desc in df['Description'])) + 2

# Calculate year column widths
year_widths = {}
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
pdf.set_text_color(0, 0, 0)  # Black text for headers
pdf.set_fill_color(255, 255, 255)  # White background for headers

# Table headers
pdf.set_font('Courier', 'B', 9)
pdf.cell(id_width, 10, 'ID', 1, fill=True, align='C')  # Center-aligned header
pdf.cell(description_width, 10, 'Description', 1, fill=True)
for year in years:
    pdf.cell(year_widths[year], 10, year, 1, align='C', fill=True)
pdf.ln()

# Table data
pdf.set_font('Courier', '', 8)
for index, row in df.iterrows():
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

    pdf.cell(id_width, 10, str(row['ID']), 1, fill=True, align='C')  # Center-aligned ID
    pdf.cell(description_width, 10, str(row['Description']), 1, fill=True)

    for year in years:
        value = float(row[year])
        pdf.set_cell_colors(value)
        pdf.set_font('Courier', 'B', 8)  # Set bold font for return value
        pdf.cell(year_widths[year], 10, f"{value}%", 1, align='C', fill=True)
        pdf.set_font('Courier', '', 8)  # Reset to normal font
    pdf.ln()

# Add summary rows for highest and lowest returns
# Highest Returns row
pdf.set_font('Courier', 'B', 8)
pdf.set_text_color(0, 0, 0)  # Black text
pdf.set_fill_color(255, 255, 255)  # White background
# Combine width of first two columns for the label
combined_width = id_width + description_width
pdf.cell(combined_width, 10, 'Highest Return', 1, fill=True, align='C')
for year in years:
    pdf.set_font('Courier', 'B', 8)  # Set bold font for IDs in summary rows
    pdf.cell(year_widths[year], 10, highest_ids[year], 1, align='C', fill=True)
pdf.ln()

# Lowest Returns row
pdf.set_font('Courier', 'B', 8)
pdf.cell(combined_width, 10, 'Lowest Return', 1, fill=True, align='C')
for year in years:
    pdf.cell(year_widths[year], 10, lowest_ids[year], 1, align='C', fill=True)
pdf.ln()

# Save the PDF
pdf.output('asset_returns.pdf')

print("PDF has been generated as 'asset_returns.pdf'")

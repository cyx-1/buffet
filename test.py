import polars as pl
import datetime
from dateutil.relativedelta import relativedelta  # type: ignore


def parse_investment_ledger():
    """Parse the investment ledger Excel file and print the first 10 rows."""
    # Path to the Excel file
    file_path = r"C:\Users\yexin\OneDrive\investment ledger.xlsx"

    try:
        # Read the specific sheet "Transactions-Schwab" into a Polars DataFrame
        df = pl.read_excel(file_path, sheet_name="Transactions-Schwab")

        # Select only the first 9 columns
        df_first9 = df.select(df.columns[:9])

        print("Successfully loaded data from 'Transactions-Schwab' sheet")
        print(f"DataFrame shape (first 9 columns): {df_first9.shape}")
        print("\nFirst 10 rows (first 9 columns):")

        # Columns to format as numeric with 2 decimals
        num_cols = ["Qty", "Cost per share", "Txn MV"]
        # Replace nulls with blanks, cast to float, and format to 2 decimals for these columns
        df_display = df_first9.head(10).with_columns(
            [pl.col(col).cast(pl.Float64).round(2).fill_null("") if col in num_cols else pl.col(col).fill_null("") for col in df_first9.columns]
        )

        # Print all columns and all values in full (no abbreviation)
        with pl.Config(
            tbl_cols=-1,  # show all columns
            tbl_rows=10,  # show all rows (up to 10)
            tbl_width_chars=2000,  # very wide to avoid truncation
            tbl_hide_column_data_types=True,  # optional: hide types for clarity
        ):
            print(df_display)

        return df_first9

    except FileNotFoundError:
        print(f"Error: Could not find the file at {file_path}")
        print("Please check if the file exists and the path is correct.")
        return None
    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return None


def compute_eom_position(transactions_df: pl.DataFrame, account_name: str, start_month: str = "2023-08-01", end_month: str = None) -> pl.DataFrame:
    """
    Compute end-of-month position for each holding in the account.
    Args:
        transactions_df: DataFrame containing transaction data (must include columns: 'Account Name', 'Security', 'Entry Date', 'Qty')
        account_name: The account name to filter on
        start_month: The starting month in YYYY-MM-DD format (default: '2023-08-01')
    Returns:
        DataFrame with columns: ['Account Name', 'Security', 'Month', 'End of Month Qty']
    """
    # Ensure correct dtypes
    df = transactions_df.with_columns([pl.col("Entry Date").cast(pl.Utf8).str.strptime(pl.Date, "%Y-%m-%d", strict=False), pl.col("Qty").cast(pl.Float64)])

    # Filter by account name
    df = df.filter(pl.col("Account Name") == account_name)

    # Filter out rows without Entry Date or Qty
    df = df.filter(pl.col("Entry Date").is_not_null() & pl.col("Qty").is_not_null())

    # Add a 'Month' column (Mon-YY, e.g., Aug-23)
    df = df.with_columns([pl.col("Entry Date").dt.strftime("%b-%y").alias("Month"), pl.col("Entry Date").dt.strftime("%Y-%m").alias("_MonthSort")])

    # Group by Account, Security, Month, _MonthSort, sum Qty (include all months)
    monthly = (
        df.group_by(["Account Name", "Security", "Month", "_MonthSort"])
        .agg([pl.col("Qty").sum().alias("Monthly Qty")])
        .sort(["Account Name", "Security", "_MonthSort"])
    )

    # Compute cumulative sum for each Account/Security
    result = monthly.with_columns([pl.col("Monthly Qty").cum_sum().over(["Account Name", "Security"]).alias("End of Month Qty")])

    # Get all months from the earliest transaction to the latest, but only show months >= start_month
    min_month_sort = result["_MonthSort"].min()
    max_month_sort = result["_MonthSort"].max()

    def month_range(start, end):
        months = []
        current = datetime.datetime.strptime(start, "%Y-%m")
        end_dt = datetime.datetime.strptime(end, "%Y-%m")
        while current <= end_dt:
            months.append((current.strftime("%b-%y"), current.strftime("%Y-%m")))
            current += relativedelta(months=1)
        return months

    # Always start from the earliest transaction month to ensure correct cumulative sum
    # If end_month is specified, extend the month range to include it
    if end_month is not None:
        try:
            # start_month may be in YYYY-MM-DD or YYYY-MM format
            try:
                start_month_dt = datetime.datetime.strptime(start_month, "%Y-%m-%d")
            except Exception:
                start_month_dt = datetime.datetime.strptime(start_month, "%Y-%m")
            end_month_dt = datetime.datetime.strptime(end_month, "%b-%y")
            # If end_month is before min_month_sort, use min_month_sort as start
            min_dt = min(start_month_dt, datetime.datetime.strptime(min_month_sort, "%Y-%m"))
            max_dt = max(end_month_dt, datetime.datetime.strptime(max_month_sort, "%Y-%m"))
            months = []
            current = min_dt
            while current <= max_dt:
                months.append((current.strftime("%b-%y"), current.strftime("%Y-%m")))
                next_month = current.replace(day=28) + datetime.timedelta(days=4)
                current = next_month - datetime.timedelta(days=next_month.day - 1)
            all_months_tuples = months
        except Exception:
            all_months_tuples = month_range(min_month_sort, max_month_sort)
    else:
        all_months_tuples = month_range(min_month_sort, max_month_sort)
    all_months = [m[0] for m in all_months_tuples]
    all_months_sort = [m[1] for m in all_months_tuples]

    # Get all securities for this account
    all_securities = result["Security"].unique().to_list()

    # Create a DataFrame with all combinations of Security and Month (Mon-YY) and _MonthSort
    combos = pl.DataFrame(
        {
            "Security": [sec for sec in all_securities for _ in all_months],
            "Month": all_months * len(all_securities),
            "_MonthSort": all_months_sort * len(all_securities),
        }
    )
    combos = combos.with_columns([pl.lit(account_name).alias("Account Name")])

    # Join with result and fill forward End of Month Qty
    merged = combos.join(result, on=["Account Name", "Security", "Month", "_MonthSort"], how="left")
    merged = merged.sort(["Security", "_MonthSort"])
    merged = merged.with_columns([pl.col("End of Month Qty").forward_fill().over(["Security"])])
    # If a security never had a position, fill with 0
    merged = merged.with_columns([pl.col("End of Month Qty").fill_null(0)])
    # Only keep relevant columns and sort by _MonthSort ascending
    merged = merged.select(["Account Name", "Security", "Month", "End of Month Qty", "_MonthSort"]).sort(["_MonthSort", "Security"])

    # Always generate the full range from start_month to end_month (inclusive), even if there are no transactions for the end month
    def parse_month_str(month_str):
        for fmt in ("%b-%y", "%Y-%m-%d", "%Y-%m"):
            try:
                return datetime.datetime.strptime(month_str, fmt)
            except Exception:
                continue
        raise ValueError(f"Invalid month format: {month_str}")

    # Determine the full month range to use for the output
    start_dt = parse_month_str(start_month)
    if end_month:
        end_dt = parse_month_str(end_month)
    else:
        # If not specified, use the max month in the data
        end_dt = datetime.datetime.strptime(max_month_sort, "%Y-%m")
    months = []
    current = start_dt
    while current <= end_dt:
        months.append((current.strftime("%b-%y"), current.strftime("%Y-%m")))
        next_month = current.replace(day=28) + datetime.timedelta(days=4)
        current = next_month - datetime.timedelta(days=next_month.day - 1)
    all_months = [m[0] for m in months]
    all_months_sort = [m[1] for m in months]

    # Only keep EOM positions for the full requested range
    merged = merged.filter(pl.col("_MonthSort").is_in(all_months_sort))
    # Pivot so each month (Mon-YY) is a row, each security is a column, values are End of Month Qty
    qty_pivot = merged.pivot(index=["Month"], on="Security", values="End of Month Qty")
    # Ensure all months in the requested range are present, even if there are no transactions
    month_sort_map = pl.DataFrame({"Month": all_months, "_MonthSort": all_months_sort})
    qty_pivot = qty_pivot.join(month_sort_map, on="Month", how="right")
    qty_pivot = qty_pivot.sort("_MonthSort")
    qty_pivot = qty_pivot.drop("_MonthSort")

    # Load price data for each security (except Cash)
    import os

    price_dir = r"C:\Users\yexin\OneDrive\PDAJ\Yexin\Finance\Data\asset_prices"
    price_dfs = {}
    for sec in qty_pivot.columns:
        if sec in ("Month", "Cash"):
            continue
        price_path = os.path.join(price_dir, f"{sec}.csv")
        if os.path.exists(price_path):
            price_df = pl.read_csv(price_path)
            # Try to find a date column and a price column
            date_col = None
            for c in price_df.columns:
                if c.lower() in ("date", "asofdate", "as_of_date"):
                    date_col = c
                    break
            price_col = None
            for c in price_df.columns:
                if c.lower() in ("close", "adj close", "price"):
                    price_col = c
                    break
            if date_col and price_col:
                # Convert date to datetime
                price_df = price_df.with_columns(
                    [pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d", strict=False).alias("_Date"), pl.col(price_col).cast(pl.Float64).alias("_Price")]
                )
                # For each month in qty_pivot, find the price with the closest date <= last day of month
                month_price_rows = []
                for month in qty_pivot["Month"].to_list():
                    # Get last day of month
                    dt = datetime.datetime.strptime(month, "%b-%y")
                    next_month = dt.replace(day=28) + datetime.timedelta(days=4)
                    last_day = next_month - datetime.timedelta(days=next_month.day)
                    # Find all price rows with _Date <= last_day
                    candidates = price_df.filter(pl.col("_Date") <= last_day)
                    if candidates.height > 0:
                        # Take the row with the max _Date
                        row = candidates.sort("_Date", descending=True).row(0)
                        price_idx = candidates.columns.index("_Price")
                        month_price_rows.append({"Month": month, "_Price": row[price_idx]})
                    else:
                        # No price before or on last day, try to take the earliest after
                        candidates = price_df.filter(pl.col("_Date") > last_day)
                        if candidates.height > 0:
                            row = candidates.sort("_Date").row(0)
                            price_idx = candidates.columns.index("_Price")
                            month_price_rows.append({"Month": month, "_Price": row[price_idx]})
                        else:
                            month_price_rows.append({"Month": month, "_Price": None})
                price_dfs[sec] = pl.DataFrame(month_price_rows)
    # For each security, add price and MV columns
    out_df = qty_pivot
    new_cols = ["Month"]
    if "Cash" in out_df.columns:
        new_cols.append("Cash")
    for sec in out_df.columns:
        if sec in ("Month", "Cash"):
            continue
        # Add price column
        if sec in price_dfs:
            price_map = price_dfs[sec]
            out_df = out_df.join(price_map, on="Month", how="left")
            out_df = out_df.rename({"_Price": f"{sec}_Price"})
        else:
            out_df = out_df.with_columns([pl.lit(None).alias(f"{sec}_Price")])
        # Add MV column
        out_df = out_df.with_columns([(pl.col(sec) * pl.col(f"{sec}_Price")).alias(f"{sec}_MV")])
        new_cols.extend([sec, f"{sec}_Price", f"{sec}_MV"])
    # Reorder columns: Month, Cash, then for each sec: sec, sec_Price, sec_MV
    out_df = out_df.select([col for col in new_cols if col in out_df.columns])

    # Add a column at the end to compute the total of cash plus all the MV for each security
    mv_cols = [col for col in out_df.columns if col.endswith('_MV')]
    if 'Cash' in out_df.columns:
        out_df = out_df.with_columns([(pl.col('Cash') + sum([pl.col(c).fill_null(0) for c in mv_cols])).alias('Total')])
    else:
        out_df = out_df.with_columns([(sum([pl.col(c).fill_null(0) for c in mv_cols])).alias('Total')])
    return out_df


if __name__ == "__main__":
    df = parse_investment_ledger()
    if df is not None:
        print("\nEnd-of-month positions for account 'Hong Bo IRA':")
        eom_df_hongbo = compute_eom_position(df, account_name="Hong Bo IRA", start_month="2023-08-01", end_month="Jul-25")
        with pl.Config(tbl_rows=-1, tbl_cols=-1, tbl_width_chars=2000, tbl_hide_column_data_types=True):
            print(eom_df_hongbo)
        # Write the output to an Excel file
        output_path = "eom_positions_hongboira.xlsx"
        eom_df_hongbo.write_excel(output_path)
        print(f"\nExcel file written to: {output_path}")

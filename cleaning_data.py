import pandas as pd
import numpy as np

def main():
    csv_file = "seilas.csv"

    df = pd.read_csv(
        csv_file,
        sep=";",
        decimal=",",
        encoding="latin1",
        na_values=["", " "],
        keep_default_na=False
    )

    # convert date/time columns
    date_cols = [
        "etd_estimert_avgangstidspunkt",
        "ankomsttidspunkt"
    ]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # numeric columns
    numeric_cols = [
        "byggeaar",
        "bruttotonnasje_bt",
        "doedvekttonn_dwt",
        "lengde",
        "bredde",
        "dypgaaende",
        "dypgaaende_aktuell"
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # handle encoding issues in text columns
    if "avgangshavn_navn" in df.columns:
        df["avgangshavn_navn"] = (
            df["avgangshavn_navn"]
            .str.replace("�", "ø", regex=False)
            .str.replace("B�tsfjord", "Båtsfjord", regex=False)
        )

    if "ankomsthavn_navn" in df.columns:
        df["ankomsthavn_navn"] = (
            df["ankomsthavn_navn"]
            .str.replace("�", "ø", regex=False)
            .str.replace("Mj�lstadneset", "Mjølstadneset", regex=False)
        )

    # create a coloumn named 'travel_duration_hours' and calculated the travel duration in hours
    if "etd_estimert_avgangstidspunkt" in df.columns and "ankomsttidspunkt" in df.columns:
        df["travel_duration_hours"] = (
            df["ankomsttidspunkt"] - df["etd_estimert_avgangstidspunkt"]
        ).dt.total_seconds() / 3600

    # quick checks
    print("===== HEAD OF DATA =====")
    print(df.head())

    print("\n===== DATA INFO =====")
    print(df.info())

    print("\n===== MISSING VALUES =====")
    print(df.isnull().sum())


    df.to_csv("seilas_cleaned.csv", index=False, sep=";")

if __name__ == "__main__":
    main()

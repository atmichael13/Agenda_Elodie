import json
import datetime
import pandas as pd
from babel.dates import format_date

def build_shabbat_excel_french(start_date_str, end_date_str, shabbat_data, output_path="shabbat_planning_fr.xlsx"):
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
    date_range = pd.date_range(start=start_date, end=end_date)

    df = pd.DataFrame({
        "date": [format_date(d, format="d MMMM y", locale="fr_FR") for d in date_range],
        "jour": [format_date(d, format="EEEE", locale="fr_FR").capitalize() for d in date_range],
        "parasha": ["" for _ in date_range],
        "allumage des bougies": ["" for _ in date_range],
        "avdallah": ["" for _ in date_range],
    })

    shabbat_by_date = {entry["date"]: entry for entry in shabbat_data}

    for i, raw_date in enumerate(date_range):
        date_str = raw_date.strftime("%Y-%m-%d")
        tomorrow_str = (raw_date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        if date_str in shabbat_by_date:
            df.at[i, "allumage des bougies"] = shabbat_by_date[date_str].get("allumage", "")

        if tomorrow_str in shabbat_by_date:
            df.at[i, "parasha"] = shabbat_by_date[tomorrow_str].get("parasha", "")
            df.at[i, "avdallah"] = shabbat_by_date[tomorrow_str].get("havdalah", "")

    df.to_excel(output_path, index=False)
    print(f">> Fichier Excel généré : {output_path}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python generate_excel_fr.py START_DATE END_DATE")
        print("Exemple: python generate_excel_fr.py 2025-04-10 2025-04-30")
        sys.exit(1)

    start_date = sys.argv[1]
    end_date = sys.argv[2]

    with open("shabbat_data.json", "r", encoding="utf-8") as f:
        shabbat_data = json.load(f)

    build_shabbat_excel_french(start_date, end_date, shabbat_data)

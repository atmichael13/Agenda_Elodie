from flask import Flask, request
import requests
import datetime
import json
import pandas as pd
from collections import OrderedDict
from babel.dates import format_date

from fete_en_fr import fete_en_fr

app = Flask(__name__)

ville_to_geonameid = {
    "paris": 2988507,
    "marseille": 2995469,
    "lyon": 2996944,
    "strasbourg": 2973783,
    "jerusalem": 281184
}


def get_shabbat_times(start_date: str, end_date: str, geonameid: int):
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    fridays = []
    current = start_dt
    while current <= end_dt:
        if current.weekday() == 4:
            fridays.append(current)
        current += datetime.timedelta(days=1)

    shabbat_list = []

    for friday in fridays:
        friday_str = friday.strftime("%Y-%m-%d")
        saturday = friday + datetime.timedelta(days=1)
        saturday_str = saturday.strftime("%Y-%m-%d")

        url = "https://www.hebcal.com/shabbat"
        params = {
            "cfg": "json",
            "geonameid": geonameid,
            "M": "on",
            "gy": friday.year,
            "gm": friday.month,
            "gd": friday.day,
            "_ts": datetime.datetime.now().timestamp()
        }

        try:
            response = requests.get(url, params=params)
            data = response.json()
        except Exception as e:
            print(f"Erreur Hebcal pour {friday_str}: {e}")
            continue

        parasha = allumage = havdalah = None
        items = data.get("items", [])

        for item in items:
            cat = item.get("category")
            title = item.get("title")
            item_date = item.get("date")[:10]

            if cat == "candles" and item_date == friday_str:
                allumage = title.split(": ")[-1]
            elif cat == "havdalah" and item_date == saturday_str:
                havdalah = title.split(": ")[-1]
            elif cat == "parashat" and item_date == saturday_str:
                parasha = title.replace("Parashat ", "")

        if parasha is None:
            for item in items:
                if item.get("category") == "holiday" and item.get("date")[:10] == saturday_str:
                    holiday_title = item.get("title")
                    parasha = fete_en_fr.get(holiday_title, holiday_title)
                    break

        if allumage and havdalah:
            entry = OrderedDict()
            entry["date"] = friday_str
            entry["parasha"] = parasha
            entry["allumage"] = allumage
            entry["havdalah"] = havdalah
            shabbat_list.append(entry)

    return shabbat_list

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

    # Nouvelle logique : on place allumage sur la date exacte et parasha/havdalah le jour suivant
    allumage_by_date = {}
    parasha_by_next_day = {}
    havdalah_by_next_day = {}

    for entry in shabbat_data:
        date_obj = datetime.datetime.strptime(entry["date"], "%Y-%m-%d").date()
        allumage_by_date[date_obj] = entry.get("allumage", "")
        next_day = date_obj + datetime.timedelta(days=1)
        parasha_by_next_day[next_day] = entry.get("parasha", "")
        havdalah_by_next_day[next_day] = entry.get("havdalah", "")

    for i, raw_date in enumerate(date_range):
        date_only = raw_date.date()
        df.at[i, "allumage des bougies"] = allumage_by_date.get(date_only, "")
        df.at[i, "parasha"] = parasha_by_next_day.get(date_only, "")
        df.at[i, "avdallah"] = havdalah_by_next_day.get(date_only, "")

    df.to_excel(output_path, index=False)
    print(f">> Fichier Excel généré localement : {output_path}")

@app.route('/shabbat-excel')
def shabbat_excel():
    start = request.args.get('start')
    end = request.args.get('end')
    ville = request.args.get('ville')
    geonameid = request.args.get('geonameid', type=int)

    if ville:
        ville = ville.lower()
        if ville not in ville_to_geonameid:
            return {
                "error": f"Ville '{ville}' inconnue. Villes disponibles : {list(ville_to_geonameid.keys())}"
            }, 400
        geonameid = ville_to_geonameid[ville]

    if not geonameid:
        geonameid = 2988507  # Paris par défaut

    if not start or not end:
        return {"error": "Please provide 'start' and 'end' in YYYY-MM-DD format."}, 400

    try:
        results = get_shabbat_times(start, end, geonameid)
        build_shabbat_excel_french(start, end, results)
        return {"message": "Fichier Excel généré avec succès."}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    print(">> Flask va démarrer sur le port 3000")
    app.run(port=3000, debug=True)

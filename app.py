from flask import Flask, request
import requests
import datetime
import json
from collections import OrderedDict
import logging

from fete_en_fr import fete_en_fr
from parasha_corrigee import parasha_corrigee  # Import externe ajouté

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ville_to_geonameid = {
    "paris": 2988507,
    "marseille": 2995469,
    "lyon": 2996944,
    "strasbourg": 2973783,
    "jerusalem": 281184
}

def corriger_parasha(nom):
    return parasha_corrigee.get(nom, nom)

def get_shabbat_times(start_date: str, end_date: str, geonameid: int):
    logger.info(f"get_shabbat_times appelé avec start={start_date}, end={end_date}, geonameid={geonameid}")
    
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")

    fridays = []
    current = start_dt
    while current <= end_dt:
        if current.weekday() == 4:
            fridays.append(current)
        current += datetime.timedelta(days=1)

    logger.info(f"{len(fridays)} vendredis trouvés entre {start_date} et {end_date}")

    shabbat_list = []

    for friday in fridays:
        friday_str = friday.strftime("%Y-%m-%d")
        saturday = friday + datetime.timedelta(days=1)
        saturday_str = saturday.strftime("%Y-%m-%d")
        logger.info(f"Traitement du Chabbat de {friday_str}")

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
            logger.error(f"Erreur de requête à Hebcal pour {friday_str} : {e}")
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

        if parasha:
            parasha = corriger_parasha(parasha)

        if allumage and havdalah:
            entry = OrderedDict()
            entry["date"] = friday_str
            entry["parasha"] = parasha
            entry["allumage"] = allumage
            entry["havdalah"] = havdalah
            shabbat_list.append(entry)
            logger.info(f"Ajouté : {entry}")
        else:
            logger.warning(f"Incomplet pour {friday_str} : allumage={allumage}, havdalah={havdalah}, parasha={parasha}")

    return shabbat_list

@app.route('/shabbat')
def shabbat():
    logger.info("Requête reçue sur /shabbat")
    start = request.args.get('start')
    end = request.args.get('end')
    ville = request.args.get('ville')
    geonameid = request.args.get('geonameid', type=int)

    if ville:
        ville = ville.lower()
        if ville not in ville_to_geonameid:
            logger.warning(f"Ville inconnue : {ville}")
            return {
                "error": f"Ville '{ville}' inconnue. Villes disponibles : {list(ville_to_geonameid.keys())}"
            }, 400
        geonameid = ville_to_geonameid[ville]

    if not geonameid:
        geonameid = 2988507  # Paris par défaut

    if not start or not end:
        logger.error("Paramètres 'start' et 'end' manquants")
        return {"error": "Please provide 'start' and 'end' in YYYY-MM-DD format."}, 400

    try:
        results = get_shabbat_times(start, end, geonameid)
        with open("shabbat_data.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Fichier shabbat_data.json sauvegardé avec {len(results)} entrées")

        return app.response_class(
            response=json.dumps(results, ensure_ascii=False),
            mimetype='application/json'
        )
    except Exception as e:
        logger.error(f"Erreur dans la route /shabbat : {e}")
        return {"error": str(e)}, 500

@app.route('/fetes')
def fetes():
    logger.info("▶ Requête reçue sur /fetes")

    start = request.args.get('start')
    end = request.args.get('end')
    ville = request.args.get('ville')
    geonameid = request.args.get('geonameid', type=int)

    if ville:
        ville = ville.lower()
        if ville not in ville_to_geonameid:
            logger.warning(f"⚠ Ville inconnue : {ville}")
            return {
                "error": f"Ville '{ville}' inconnue. Villes disponibles : {list(ville_to_geonameid.keys())}"
            }, 400
        geonameid = ville_to_geonameid[ville]

    if not geonameid:
        geonameid = 2988507  # Paris par défaut

    if not start or not end:
        logger.error("❌ Paramètres 'start' et 'end' manquants")
        return {"error": "Please provide 'start' and 'end' in YYYY-MM-DD format."}, 400

    try:
        logger.info(f"📅 Période demandée : {start} ➡ {end} | geonameid={geonameid}")
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d")

        url = "https://www.hebcal.com/hebcal"
        params = {
            "maj": "on",        # Include major Jewish holidays (Yom Kippour, Souccot, Pessah, etc.)
            "min": "on",        # Include minor Jewish holidays (Tou Bichevat, Lag BaOmer, etc.)
            "mf": "on",         # Include minor fasts (jeûnes : Guédalia, 10 Tevet, 17 Tamouz, etc.)
            "mod": "off",       # Exclude modern Israeli holidays (Yom Haatsmaout, Yom Hazikaron, etc.)
            "ss": "off",         # Include weekly Shabbat (used here mainly to enrich calendar, though tu les filtres ensuite)
            "c": "off",          # Include Torah readings (lecture de la Parasha)
            "v": "1",           # Version de l'API Hebcal
            "cfg": "json",      # Format de réponse : JSON (peut être aussi XML ou d'autres formats si besoin)
            # "geo": "geoname",   # Méthode de géolocalisation utilisée (ici par ID GeoNames)
            "geonameid": geonameid,  # ID GeoNames de la ville (Paris = 2988507)
            "start": start_dt.strftime("%Y-%m-%d"),  # Date de début de la période demandée (format ISO)
            "end": end_dt.strftime("%Y-%m-%d"),      # Date de fin de la période demandée
            "M": "on"         # Inclure les horaires d’allumage et de havdalah
            # "m": 250            # Nombre maximal d’événements à retourner (peut être augmenté si période longue)
        }


        logger.info("🌐 Requête vers Hebcal API...")
        response = requests.get(url, params=params)
        data = response.json()
        items = data.get("items", [])
        logger.info(f"✅ {len(items)} événements récupérés depuis Hebcal")

        # DEBUG TEMP : Sauvegarde brute (optionnel)
        # with open("hebcal_raw.json", "w", encoding="utf-8") as f:
        #     json.dump(items, f, ensure_ascii=False, indent=2)

        results = []
        for item in items:
            cat = item.get("category")
            title = item.get("title")
            date = item.get("date")[:10]

            if cat in {"holiday", "roshchodesh", "minor", "fast"} and "Shabbat" not in title:
                logger.info(f"🎉 Fête trouvée : {title} ({date})")
                results.append({
                    "date": date,
                    "fete": fete_en_fr.get(title, title)
                })

        # Ajouter horaires d’allumage / havdalah / jeûne
        for item in items:
            date = item.get("date")[:10]
            title = item.get("title")
            cat = item.get("category")
            heure = title.split(": ")[-1]

            existing = next((r for r in results if r["date"] == date), None)
            if not existing:
                continue

            titre_lower = title.lower()
            if cat == "candles" or "zmanim":
                if cat == "zmanim" or "alot hashachar" in titre_lower:
                    heure = item["date"][11:16]  # extrait "HH:MM" de la date complète
                if titre_lower.startswith("fast begins"):
                    existing["debut_jeune"] = heure
                    logger.info(f"🕘 Début du jeûne ajouté pour {date}: {heure}")
                else:
                    existing["allumage"] = heure
                    logger.info(f"🕯 Allumage ajouté pour {date}: {heure}")
            elif cat == "havdalah":
                if "fast ends" in titre_lower or titre_lower.startswith("fast ends"):
                    existing["fin_jeune"] = heure
                    logger.info(f"🕘 Fin du jeûne ajouté pour {date}: {heure}")
                else:
                    existing["havdalah"] = heure
                    logger.info(f"🔥 Havdalah ajouté pour {date}: {heure}")

        logger.info(f"📦 Total des fêtes renvoyées : {len(results)}")
        return app.response_class(
            response=json.dumps(results, ensure_ascii=False, indent=2),
            mimetype='application/json'
        )

    except Exception as e:
        logger.exception(f"💥 Erreur dans la route /fetes : {e}")
        return {"error": str(e)}, 500

if __name__ == '__main__':
    logger.info("Flask va démarrer sur le port 3000")
    app.run(port=3000, debug=True)

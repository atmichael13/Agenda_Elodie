from flask import Flask, request, jsonify
import requests
from datetime import datetime
from fonctions_agenda import *

app = Flask(__name__)

# https://www.hebcal.com/home/197/shabbat-times-rest-api
# Coordonnées des principales villes françaises
villes_coords = {
    "paris": {"lat": 48.8566, "lon": 2.3522},
    "marseille": {"lat": 43.2965, "lon": 5.3698},
    "lyon": {"lat": 45.7640, "lon": 4.8357},
    "strasbourg": {"lat": 48.5734, "lon": 7.7521},
    "nice": {"lat": 43.7102, "lon": 7.2620}
}

@app.route('/shabbat')
def horaires_shabbat():
    type_requete = request.args.get('type', 'tout').lower()

    ville = request.args.get('ville', '').lower()
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if ville not in villes_coords:
        return jsonify({"error": f"Ville '{ville}' non reconnue."}), 400
    if not start_date or not end_date:
        return jsonify({"error": "start et end requis"}), 400

    coords = villes_coords[ville]
    try:
        vendredis = get_vendredis(start_date, end_date)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    results = []
    fetes = []
    for date in vendredis:
        gy, gm, gd = map(int, date.split("-"))
        parasha = ""
        fete = ""

        params = {
            "cfg": "json",
            "latitude": coords["lat"],
            "longitude": coords["lon"],
            "tzid": "Europe/Paris",
            # "start": date,
            "gy": gy,
            "gm": gm,
            "gd": gd,
            # "end": date,
            # "b": 18,
            "m": 50,
            "maj": "on"
        }
        try:
            response = requests.get("https://www.hebcal.com/shabbat/", params=params)
            data = response.json()

            entree, sortie = None, None
            for item in data.get("items", []):
                if item["category"] == "candles":
                    entree = item["title"]
                    entree = heure_to_24h(entree)
                    if "memo" in item and "Parashat" in item["memo"]:
                        parasha = item["memo"].replace("Parashat ", "")
                elif item["category"] == "havdalah":
                    sortie = item["title"]
                    sortie = heure_to_24h(sortie)
                # elif item["category"] == "holiday" and item.get("yomtov") == True:
                #TODO SHABATOT SPECIALS
                if item["category"] == "holiday" and (item.get("subcat") != 'minor' and item.get("subcat") != 'shabbat'):
                    fete_date = item["date"][:10]  # format YYYY-MM-DD
                    gy, gm, gd = map(int, fete_date.split("-"))
                    params_fete = {
                        "cfg": "json",
                        "geo": "pos",
                        "latitude": coords["lat"],
                        "longitude": coords["lon"],
                        "tzid": "Europe/Paris",
                        "gy": gy,
                        "gm": gm,
                        "gd": gd,
                        "m": 50,
                        "maj": "on"
                    }
                    try:
                        response_fete = requests.get("https://www.hebcal.com/shabbat/", params=params_fete)
                        data_fete = response_fete.json()
                        # item = data_fete['items'][1]
                        for item in data_fete.get("items", []):
                            if item['category'] == "candles" and item['date'].startswith(fete_date):
                                entree_fete = item['date']
                                dt = datetime.fromisoformat(entree_fete)
                                entree_fete = dt.strftime("%H:%M")
                                fetes.append({
                                    "nom": item["memo"],
                                    "date": fete_date,
                                    "entree_fete": entree_fete
                                })
                            elif item['category'] == "havdalah" and item['date'].startswith(fete_date):
                                sortie_fete = item['date']
                                dt = datetime.fromisoformat(sortie_fete)
                                sortie_fete = dt.strftime("%H:%M")
                                fetes.append({
                                    "nom": item["memo"],
                                    "date": fete_date,
                                    "sortie_fete": sortie_fete
                                })
                            
                            # fetes.append({
                            #     "nom": item["title"],
                            #     "date": fete_date,
                            #     "entree_fete": entree_fete,
                            #     "sortie_fete": sortie_fete
                            #     # "details": data_fete.get("items", [])
                            # })
                    except Exception as e:
                        fetes.append({
                            "date": fete_date,
                            "nom": item["title"],
                            "error": str(e)
                        })

            if entree:
                results.append({
                    "date": date,
                    "ville": ville.capitalize(),
                    "entree_shabbat": entree,
                    "sortie_shabbat": sortie,
                    "Parasha": parasha
                })

        except Exception as e:
            results.append({
                "date": date,
                "error": str(e)
            })

    # return jsonify(results, fetes)
    if type_requete == "chabbat":
        return jsonify({"Chabbatot": results})
    elif type_requete == "fete":
        return jsonify({"Fetes": fetes})
    else:
        return jsonify({
            "Chabbatot": results,
            "Fetes": fetes
        })



if __name__ == '__main__':
    print(">> Flask va démarrer sur le port 3000")
    app.run(host='0.0.0.0', port=3000, debug=True)
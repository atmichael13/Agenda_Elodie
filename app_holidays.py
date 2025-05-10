from flask import Flask, request, jsonify
import requests
import datetime
import json

from fete_en_fr import fete_en_fr

app = Flask(__name__)

#TODO Tou Bichevat Pessah Cheni Lag Ba'omer

ville_to_geonameid = {
    "paris": 2988507,
    "marseille": 2995469,
    "lyon": 2996944,
    "strasbourg": 2973783,
    "jerusalem": 281184
}

@app.route('/holidays')
def holidays():
    start = request.args.get('start')
    end = request.args.get('end')
    ville = request.args.get('ville', 'paris').lower()

    if ville not in ville_to_geonameid:
        return {
            "error": f"Ville '{ville}' inconnue. Villes disponibles : {list(ville_to_geonameid.keys())}"
        }, 400

    try:
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d")
    except Exception as e:
        return {"error": "Please provide 'start' and 'end' in YYYY-MM-DD format."}, 400

    geonameid = ville_to_geonameid[ville]

    url = "https://www.hebcal.com/hebcal"
    params = {
        "v": "1",
        "cfg": "json",
        "start": start,
        "end": end,
        "geonameid": geonameid,
        "maj": "on",   # Fêtes majeures
        "mf": "on",    # Fêtes majeures (alternative ou complément)
        "mod": "on",   # Jeûnes, jours spéciaux
        "nx": "on",    # Rosh Hodesh
        "ss": "on",    # Shabbats spéciaux
        # "o": "on",     # Jours du Omer
        "c": "on",     # Jours civils israéliens
        "s": "on"      # Shabbat et fêtes
    }   
    

    try:
        response = requests.get(url, params=params)
        data = response.json()
    except Exception as e:
        return {"error": f"Erreur de récupération: {e}"}, 500

    holidays = []
    for item in data.get("items", []):
        if item.get("category") in ["holiday", "roshchodesh", "fast", "omer"]:
            title = item.get("title")
            translated = fete_en_fr.get(title, title)
            holidays.append({
                "date": item.get("date")[:10],
                "fete": translated
            })


    with open("holidays_data.json", "w", encoding="utf-8") as f:
        json.dump(holidays, f, ensure_ascii=False, indent=2)
    
    return jsonify(holidays)

if __name__ == '__main__':
    print(">> Flask va démarrer sur le port 3000")
    app.run(port=3000, debug=True)

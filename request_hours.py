import requests
print(requests.__version__)
import pandas as pd

# Coordonnées GPS de Paris
lat = 48.8566
lon = 2.3522
start_date = "2025-08-31"
end_date = "2026-07-04"

# Requête API
params = {
    "cfg": "json",
    "latitude": lat,
    "longitude": lon,
    "tzid": "Europe/Paris",
    "start": start_date,
    "end": end_date,
    "maj": "on",
    "m": 50
}

url = "https://www.hebcal.com/shabbat/"
response = requests.get(url, params=params)
data = response.json()
print(data)

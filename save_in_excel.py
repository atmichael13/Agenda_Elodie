from datetime import datetime

import pandas as pd

# Initialisation de la liste des résultats
horaires = []
date_entree = None

for item in data["items"]:
    if item["category"] == "candles":
        date_entree = datetime.fromisoformat(item["date"]).date()
        entree = item["title"]
    elif item["category"] == "havdalah" and date_entree:
        sortie = item["title"]
        horaires.append({
            "Date": date_entree,
            "Entrée Shabbat": entree,
            "Sortie Shabbat": sortie
        })
        date_entree = None

# Création d’un DataFrame et export vers Excel
df = pd.DataFrame(horaires)
df.to_excel("horaires_shabbat_paris_2025_2026.xlsx", index=False)

print("✅ Fichier Excel créé : horaires_shabbat_paris_2025_2026.xlsx")

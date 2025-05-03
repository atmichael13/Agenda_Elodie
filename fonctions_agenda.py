from datetime import datetime, timedelta

def get_vendredis(start_date: str, end_date: str):
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception as e:
        raise ValueError(f"Dates invalides : {e}")


    # Se placer au premier vendredi suivant ou égal à start
    while start.weekday() != 4:  # 4 = vendredi
        start += timedelta(days=1)

    vendredis = []
    while start <= end:
        vendredis.append(start.strftime("%Y-%m-%d"))
        start += timedelta(days=7)

    return vendredis

def heure_to_24h(text):
    try:
        heure_12h = text.split(": ", 1)[1]
        return datetime.strptime(heure_12h, "%I:%M%p").strftime("%H:%M")
    except:
        return text

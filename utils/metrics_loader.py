import json

def load_metrics():
    with open("data/politician_metrics.json", "r", encoding="utf-8") as file:
        return json.load(file)

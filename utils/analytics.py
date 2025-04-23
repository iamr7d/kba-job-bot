import json
import os
from datetime import datetime

ANALYTICS_FILE = os.environ.get("ANALYTICS_FILE", "analytics.json")

def increment_usage(feature, user_id=None):
    data = {}
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    if feature not in data:
        data[feature] = 0
    data[feature] += 1
    if user_id:
        user_key = f"user_{user_id}"
        if user_key not in data:
            data[user_key] = {"saved_jobs": 0}
        # Only increment saved_jobs for that feature
        if feature == "saved_jobs":
            data[user_key]["saved_jobs"] = data[user_key].get("saved_jobs", 0) + 1
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def export_analytics_csv(path="analytics_export.csv"):
    import csv
    if not os.path.exists(ANALYTICS_FILE):
        return None
    with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(path, "w", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Feature", "Count"])
        for k, v in data.items():
            if isinstance(v, dict):
                writer.writerow([k, json.dumps(v)])
            else:
                writer.writerow([k, v])
    return path

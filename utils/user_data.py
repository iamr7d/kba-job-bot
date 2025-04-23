import json
USERDATA_FILE = "user_data.json"

def load_user_data():
    try:
        with open(USERDATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_user_data(data):
    with open(USERDATA_FILE, "w") as f:
        json.dump(data, f)

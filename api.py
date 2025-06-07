import requests
from const import WAYBACK_API_ENDPOINT

def get_availability(url: str):
    params = {
        "url": url,
        "output": "json"
    }
    response = requests.get(WAYBACK_API_ENDPOINT, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
        except:
            return response.text
        entries = data[1:]
        headers = data[0]
        values: list[dict[str, str]] = []
        for entry in entries:
            entry_dict: dict[str, str] = {}
            for i, value in enumerate(entry):
                entry_dict[headers[i]] = value
            values.append(entry_dict)
        return values
    else:
        raise Exception(f"Error fetching availability: {response.status_code} - {response.text}")
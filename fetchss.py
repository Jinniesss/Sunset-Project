import requests
import json
from datetime import date
import os

today_date = date.today().isoformat() # 'YYYY-MM-DD'
# New Haven, CT
latitude = '41'
longitude = '-73'
key = '3e8d4655015973f5d25179d1369ea0bb'
filename = f'{today_date}.json'

url = f'https://api.sunsethue.com/forecast?latitude={latitude}&longitude={longitude}&key={key}'

# Fetch forecast data from the API
try:    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            print("Data loaded from local file.")
    else:
        # Delete previous json files
        for file in os.listdir('.'):
            if file.endswith('.json'):
                os.remove(file)

        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print("Data fetched from API and saved to local file.")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error occurred: {e}")
    if e.response is not None:
        print("Error response:", e.response.text)
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

# Process fetched data


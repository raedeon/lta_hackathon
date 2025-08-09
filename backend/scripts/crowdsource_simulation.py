import numpy as np
import pandas as pd
import random
import requests
import os
import time

addr = os.getenv("BASE_URL", "http://localhost:5000")
url = f"{addr}/events/crowdsource"

df = pd.read_csv("./data/csv/Waze_Alerts.csv")
df.columns = df.columns.str.lower()
df.drop(columns=["sn", "firstextracted"], inplace=True)

for _, row in df.iterrows():
    row = row.replace([np.nan, np.inf, -np.inf], None)
    data = row.to_dict()
    try:
        data['timestamp'] = time.time()
        response = requests.post(url, json=data)
        print(f"Sent: {data}, Reponse: {response.status_code}")
        time.sleep(random.randint(1,3))
    except requests.exceptions.RequestException as e:
        print(f"Failed to send data: {e}")

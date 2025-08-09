import time
import threading
import os
import requests
from sseclient import SSEClient

URL = os.getenv("BASE_URL", "http://localhost:5000")
CROWDSOURCE_URI = "store/crowdsource"
FILTERED_URI = "store/filtered"

def listen_to_sse(uri):
    try:
        response = requests.get(f'{URL}/{uri}', stream=True)
        response.raise_for_status()  
        client = SSEClient(response)
        for event in client.events():
            print(f"Received event id from {uri}: {event.data}")
    except requests.exceptions.ConnectionError:
        print("Error: Unable to connect to the backend. Please make sure the server is running.")
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")


def listen_to_crowdsource():
    listen_to_sse(CROWDSOURCE_URI)

def listen_to_filtered():
    listen_to_sse(FILTERED_URI)
    

if __name__ == "__main__":
    thread_crowdsource = threading.Thread(target=listen_to_crowdsource, daemon=True)
    thread_filtered = threading.Thread(target=listen_to_filtered, daemon=True)

    thread_crowdsource.start()
    time.sleep(2)
    thread_filtered.start()

    thread_crowdsource.join()
    thread_filtered.join()

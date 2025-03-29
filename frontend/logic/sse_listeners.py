import streamlit as st
import threading
import requests
from sseclient import SSEClient
from streamlit.runtime.scriptrunner import add_script_run_ctx


# URL/URIs for retrieving incoming & filtered data
URL = "http://localhost:5000"
CROWDSOURCE_URI = "store/crowdsource"
FILTERED_URI = "store/filtered"


##### API CALL TO BACKEND TO RETRIEVE INCOMING AND FILTERED DATA #####
# Functions for listening and handling server-sent events from backend
def listen_to_sse(uri):
    try:
        response = requests.get(f"{URL}/{uri}", stream=True) # Stream=True keeps the connection open indefinitely to receive live event updates
        response.raise_for_status() # Check if response is OK
        client = SSEClient(response) # SSEClient class processes incoming SSE messages

        storage_type = uri.split("/")[1] # Get type of storage
        for event in client.events(): # This is a permanent loop because of stream=True. Every time a new event arrives, the loop executes only for that event, then waits for the next one
            print(f"Received event id from {uri}: {event.data}")

            # Get exact event details
            try:
                response = requests.get(f"{URL}/events/{storage_type}/{event.data}")
                data = response.json()
            except requests.exceptions.RequestException as e: # For troubleshooting
                print(f"Request failed: {e}")

            if storage_type == "crowdsource": # Add to incoming storage session state
                st.session_state["incoming"].append(data)

            if storage_type == "filtered": # Add to filtered storage session state
                st.session_state["filtered"].append(data)       

    except requests.exceptions.ConnectionError: # Catches connection errors
        print("Error: Unable to connect to the backend. Please make sure the server is running.")
    except requests.exceptions.RequestException as e: # Catches other HTTP-related errors (e.g., timeout, bad request, unauthorised access)
        print(f"An error occurred: {e}")


# Listen to crowdsource store
def listen_to_crowdsource():
    listen_to_sse(CROWDSOURCE_URI)


# Listen to filtered store
def listen_to_filtered():
    listen_to_sse(FILTERED_URI)


# Start SSE Listener Threads (only once)
def start_threads():
    if not st.session_state["sse_thread_started"]:
        # Create threads
        thread_crowdsource = threading.Thread(target=listen_to_crowdsource, daemon=True) # This thread will run the listen_to_crowdsource() function. daemon: thread  will automatically stop when the main program exits, and 
        thread_filtered = threading.Thread(target=listen_to_filtered, daemon=True) # Runs the listen_to_filtered() function in a separate thread. daemon: ensures the thread does not block program termination.

        # Prevent missing ScriptRunContext
        add_script_run_ctx(thread_crowdsource)
        add_script_run_ctx(thread_filtered)

        # Start threads (only need .join() if you want to pause the main script and wait for the thread to complete before moving on)
        # Note: thread continues to run in the background even as main script continues executing, always listening to new events
        thread_crowdsource.start()
        thread_filtered.start()

        st.session_state["sse_thread_started"] = True
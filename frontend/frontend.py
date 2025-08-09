import base64
import logging
import os
import pandas as pd
import pydeck as pdk
import streamlit as st
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv
from sseclient import SSEClient
from streamlit.runtime.scriptrunner import add_script_run_ctx
from zoneinfo import ZoneInfo

# GLOBAL VARIABLES
# URL/URIs for retrieving incoming & filtered data
URL= os.getenv("BASE_URL", "http://localhost:5000")
CROWDSOURCE_URI = "store/crowdsource"
FILTERED_URI = "store/filtered"

# TELEGRAM BOT TOKEN
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def dispatch_to_tele():
    incident = st.session_state["incident_to_tele"]

    # Parse incident
    town = incident["crowdsource_event"]["town"]
    street = incident["crowdsource_event"]["street"]
    timestamp = convert_unix(incident["crowdsource_event"]["timestamp"])  # Assume you have this function
    alert_type = incident["crowdsource_event"]["alert_type"].replace("_", " ").capitalize()
    alert_subtype = (
        incident["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize()
        if incident["crowdsource_event"]["alert_subtype"] is not None
        else "Unknown"
    )
    image = incident["image_event"]["image_src"]    

    # Craft message depending on whether fields are relevant
    message = f"🚨 *New Traffic Incident!* 🚨\n\n"

    if town: # Handles expressway incidents
        message += f"🏙️ *Town:* {town}\n"

    message += (
        f"🛣️ *Street:* {street}\n"
        f"⏰ *Date & Time:* {timestamp}\n"
        f"⚠️ *Type:* {alert_type}\n"
    )
    
    if alert_subtype != "Unknown":
        message += f"📌 *Subtype:* {alert_subtype}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto" # Send photo with caption

    files = {"photo": open(f"../{image}", "rb")}

    # JSON payload
    payload = {
        "chat_id": "@optimove_ai",
        "caption": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, data=payload, files=files)
        response.raise_for_status()  # Handles HTTP error codes like 400, 401, 403, or 500 because requests.post only raises exceptions when something technical goes wrong e.g. no internet connection, timeout error, invalid URL,
                                     # But if the server simply returns an error status code (like 401 Unauthorized), the response is still technically successful in terms of communication, so no exception is raised unless you explicitly include this line
        st.session_state["incident_to_tele"] = None
    except requests.exceptions.RequestException as e: #	Catches all network errors (timeouts, bad responses, etc.)
        logging.error(f"Telegram request failed: {e}")
        st.session_state["incident_to_tele"] = None
        st.error("❌ Failed to send incident to Telegram.")
    except FileNotFoundError as e: # If the image file path is incorrect or missing
        logging.error(f"Image file not found: {e}")
        st.session_state["incident_to_tele"] = None
        st.error("❌ Image file for this incident could not be found.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        st.session_state["incident_to_tele"] = None
        st.error("❌ Something went wrong while dispatching to Telegram.")


# Load CSS
def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:  # Force UTF-8 encoding
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Convert time from UNIX timestamp to UTC time
def convert_unix(time):
    dt_local = datetime.fromtimestamp(time)  # Converts to local time
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")


# Initialise keys in session state
def initialise_session_states():
    if "incoming" not in st.session_state:
        st.session_state["incoming"] = []

    if "filtered" not in st.session_state:
        st.session_state["filtered"] = []

    if "validated" not in st.session_state:
        st.session_state["validated"] = []

    if "parsed_filtered" not in st.session_state:
        st.session_state["parsed_filtered"] = []

    if "parsed_validated" not in st.session_state:
        st.session_state["parsed_validated"] = []

    if "sse_thread_started" not in st.session_state:
        st.session_state["sse_thread_started"] = False

    # Incident to show details for upon checking of checkbox by user in Table 2
    if "selected_filtered" not in st.session_state:
        st.session_state["selected_filtered"] = None

    # Incident to show details for upon viewing details in Table 3
    if "selected_validated" not in st.session_state:
        st.session_state["selected_validated"] = None

    # Incident to dispatch information to Telegram etc. for
    if "incident_to_tele" not in st.session_state:
        st.session_state["incident_to_tele"] = None



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


# Converts an image to base64
def convert_img(dir, width=200):
    with open(dir, "rb") as f:
        img_bytes = f.read()
        img_base64 = base64.b64encode(img_bytes).decode()

    return f'<img src="data:image/png;base64,{img_base64}" width="{width}"/>'


# Different coloured cell in homescreen table depending on priority level
def highlight_priority(priority):
    if priority == "High":
        return "background-color: red; color: black;"
    elif priority == "Medium":
        return "background-color: orange; color: black;"
    else:
        return "background-color: yellow; color: black;"


# Get colour of cell in details table depending on priority
def get_colour(incident):
    if incident["priority"] == "High":
        return "#FF0000"  # red
    elif incident["priority"] == "Medium":
        return "#FFA500"  # orange
    else:
        return "#FFD700"  # yellow


# Bin priorities based on their score
def bin_priority(score):
    if score >= 0.7:
        return "High"
    elif 0.29 < score < 0.69:
        return "Medium"
    else:
        return "Low"
    
# Displays details of a filtered incident
def display_filtered_incident_details():
        incident = st.session_state["filtered"][st.session_state["selected_filtered"] - 1] # Retrieve specific incident checked. Minus one to account for overcounting due to the row of column headers being included

        # Parses full json into dict with keys: id, street, longitude, latitude, timestamp, alert_type, alert_subtype, camera_id, image_src, priority
        def parse_incident(incident):
            return {
                "id": incident["id"],
                "town": incident["crowdsource_event"]["town"],
                "street": incident["crowdsource_event"]["street"],
                "longitude": incident["crowdsource_event"]["x"],
                "latitude": incident["crowdsource_event"]["y"],
                "timestamp": convert_unix(incident["crowdsource_event"]["timestamp"]),
                "alert_type": incident["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                "alert_subtype": (incident["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                if incident["crowdsource_event"]["alert_subtype"] is not None
                                else "Unknown"
                ),
                "camera_id": incident["image_event"]["camera_id"],
                "image_src": convert_img(f"../{incident['image_event']['image_src']}", width=500), # Convert to base64
                "number_of_similar": len(incident["repeated_events_crowdsource_id"]), # Number of reports on this incident including itself
                "priority": bin_priority(incident["priority_score"]),
            }

        # Parses full json into dict with keys: id, street, timestamp, alert_type, alert_subtype, priority
        def parse_filtered(data):
            return {
                "id": data["id"],
                "street": data["crowdsource_event"]["street"],
                "timestamp": convert_unix(data["crowdsource_event"]["timestamp"]),
                "alert_type": data["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                "alert_subtype": (data["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                if data["crowdsource_event"]["alert_subtype"] is not None
                                else "Unknown"
                ),
                "priority": bin_priority(data["priority_score"])
            }

        parsed_incident = parse_incident(incident) # Used for displaying the incident in the table
        parsed_filtered = parse_filtered(incident) # Used for removing this incident from the "parsed_filtered" session state

        st.title(f"📌 ID {incident['id']}")

            
        priority_colour = get_colour(parsed_incident)


        # Display the table using HTML inside `st.markdown()`
        st.markdown(f"""
            <table class="incident-table">
                <tr>
                    <th>Field</th>
                    <th>Information</th>
                </tr>
                <tr>
                    <td>🏙️ Town</td>
                    <td>{parsed_incident["town"]}</td>
                </tr>
                <tr>
                    <td>🛣️ Street</td>
                    <td>{parsed_incident["street"]}</td>
                </tr>
                <tr>
                    <td>📍 Longitude</td>
                    <td>{parsed_incident["longitude"]}</td>
                </tr>
                <tr>
                    <td>📍 Latitude</td>
                    <td>{parsed_incident["latitude"]}</td>
                </tr>
                <tr>
                    <td>⏰ Date & Time</td>
                    <td>{parsed_incident["timestamp"]}</td>
                </tr>
                <tr>
                    <td>⚠️ Incident Type</td>
                    <td>{parsed_incident["alert_type"]}</td>
                </tr>
                <tr>
                    <td>📌 Incident Subtype</td>
                    <td>{parsed_incident["alert_subtype"]}</td>
                </tr>
                <tr>
                    <td>🖼️ Image</td>
                    <td>{parsed_incident["image_src"]}</td>
                </tr>
                <tr>
                    <td>🎥 Camera ID</td>
                    <td>{parsed_incident["camera_id"]}</td>
                </tr>
                <tr>
                    <td>📢 Number of Similar Reports</td>
                    <td>{parsed_incident["number_of_similar"]}</td>
                </tr>
                <tr>
                    <td>🔥 Priority</td>
                    <td style='color: white; background-color: {priority_colour}; font-weight: bold; padding: 6px 10px; border-radius: 6px; text-align: center;'>
                        {parsed_incident["priority"]}
                    </td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

        with st.container(): # Container with all three buttons
            approve, reject, back = st.columns([1.25,1,1]) # One column per button

            with approve: # Column with checkboxes and button
                with st.container(key="approve"): # Container with checkboxes and button
                    with st.container(key="checkboxes"): # Container with checkboxes only
                        tele, emerg = st.columns(2)
                        is_tele = tele.checkbox("📩 Dispatch to Telegram")
                        is_emerg = emerg.checkbox("🚑 Dispatch to Emergency Services")
                    if st.button("✅ Approve", key="approve_button"): # Container with button only
                        validated_incident = incident.copy()
                        validated_incident["status"] = "❌ Undispatched" # Add default undispatched status
                        validated_incident["is_emerg"] = False # Whether dispatched to emergency
                        if is_tele: #TODO
                            validated_incident["status"] = "📩 Dispatched to Telegram"
                            st.session_state["incident_to_tele"] = incident
                        if is_emerg: #TODO
                            validated_incident["status"] = "🚑 Dispatched to Emergency Services"
                            validated_incident["is_emerg"] = True
                        if is_tele and is_emerg:
                            st.session_state["incident_to_tele"] = incident
                            validated_incident["status"] = "✅ Dispatched to All"
                        st.session_state["validated"].append(validated_incident)
                        st.session_state["filtered"].remove(incident)
                        st.session_state["parsed_filtered"].remove(parsed_filtered)
                        st.session_state["selected_filtered"] = None
                        st.rerun()
            with reject:
                if st.button("❌ Reject", key="reject_button"): # If incident approved, then remove incident
                    st.session_state["filtered"].remove(incident)
                    st.session_state["parsed_filtered"].remove(parsed_filtered)
                    st.session_state["selected_filtered"] = None
                    st.rerun()

            with back:
                if st.button("⬅ Back", key="back_button"): # If no action taken and user presses back, go back to homepage
                    st.session_state["selected_filtered"] = None
                    st.rerun() 

        display_trademark()


def display_validated_incident_details():
        incident = st.session_state["validated"][st.session_state["selected_validated"] - 1] # Retrieve specific incident checked. Minus one to account for overcounting due to the row of column headers being included

        # Parses full json into dict with keys: id, street, longitude, latitude, timestamp, alert_type, alert_subtype, camera_id, image_src, priority
        def parse_incident(incident):
            return {
                "id": incident["id"],
                "town": incident["crowdsource_event"]["town"],
                "street": incident["crowdsource_event"]["street"],
                "longitude": incident["crowdsource_event"]["x"],
                "latitude": incident["crowdsource_event"]["y"],
                "timestamp": convert_unix(incident["crowdsource_event"]["timestamp"]),
                "alert_type": incident["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                "alert_subtype": (incident["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                if incident["crowdsource_event"]["alert_subtype"] is not None
                                else "Unknown"
                ),
                "camera_id": incident["image_event"]["camera_id"],
                "image_src": convert_img(f"../{incident['image_event']['image_src']}", width=500), # Convert to base64
                "number_of_similar": len(incident["repeated_events_crowdsource_id"]), # Number of reports similar to this incident
                "priority": bin_priority(incident["priority_score"]),
                "status": incident["status"]
            }

        parsed_incident = parse_incident(incident)
            
        priority_colour = get_colour(parsed_incident)

        st.title(f"📌 ID {incident['id']}")

        # Display the table using HTML inside `st.markdown()`
        st.markdown(f"""
            <table class="incident-table">
                <tr>
                    <th>Field</th>
                    <th>Information</th>
                </tr>
                <tr>
                    <td>🏙️ Town</td>
                    <td>{parsed_incident["town"]}</td>
                </tr>
                <tr>
                    <td>🛣️ Street</td>
                    <td>{parsed_incident["street"]}</td>
                </tr>
                <tr>
                    <td>📍 Longitude</td>
                    <td>{parsed_incident["longitude"]}</td>
                </tr>
                <tr>
                    <td>📍 Latitude</td>
                    <td>{parsed_incident["latitude"]}</td>
                </tr>
                <tr>
                    <td>⏰ Date & Time</td>
                    <td>{parsed_incident["timestamp"]}</td>
                </tr>
                <tr>
                    <td>⚠️ Incident Type</td>
                    <td>{parsed_incident["alert_type"]}</td>
                </tr>
                <tr>
                    <td>📌 Incident Subtype</td>
                    <td>{parsed_incident["alert_subtype"]}</td>
                </tr>
                <tr>
                    <td>🖼️ Image</td>
                    <td>{parsed_incident["image_src"]}</td>
                </tr>
                <tr>
                    <td>🎥 Camera ID</td>
                    <td>{parsed_incident["camera_id"]}</td>
                </tr>
                <tr>
                    <td>📢 Number of Similar Reports</td>
                    <td>{parsed_incident["number_of_similar"]}</td>
                </tr>
                <tr>
                    <td>🔥 Priority</td>
                    <td style='color: white; background-color: {priority_colour}; font-weight: bold; padding: 6px 10px; border-radius: 6px; text-align: center;'>
                        {parsed_incident["priority"]}
                    </td>
                </tr>
                <tr>
                    <td>📦 Status</td>
                    <td>{parsed_incident["status"]}</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

        with st.container(): # Container with all three buttons
            # If incident is undispatched  
            if incident["status"] == "❌ Undispatched":
                with st.container(): # Container with all three buttons
                    dispatch, back = st.columns([1.25,1]) # One column per button
                    with dispatch: # Column with checkboxes and button
                        with st.container(key="approve"): # Container with checkboxes and button
                            with st.container(key="checkboxes"): # Container with checkboxes only
                                tele, emerg = st.columns(2)
                                is_tele = tele.checkbox("📩 Dispatch to Telegram")
                                is_emerg = emerg.checkbox("🚑 Dispatch to Emergency Services")
                            if st.button("✅ Dispatch", key="approve_button"): # Container with button only
                                if is_tele: #TODO
                                    incident["status"] = "📩 Dispatched to Telegram"
                                    st.session_state["incident_to_tele"] = incident
                                if is_emerg: #TODO
                                    incident["status"] = "🚑 Dispatched to Emergency Services"
                                    incident["is_emerg"] = True
                                    pass
                                if is_tele and is_emerg:
                                    incident["status"] = "✅ Dispatched to All"
                                    st.session_state["incident_to_tele"] = incident
                                st.session_state["validated"][st.session_state["selected_validated"] - 1] = incident # Update validated ss
                                st.session_state["parsed_validated"] = [] # Reset parsed validated ss to retain the order of incidents in st.session_state["validated"]
                                st.session_state["selected_validated"] = None
                                st.rerun()

                    with back:
                        if st.button("⬅ Back", key="back_button"): # If no action taken and user presses back, go back to homepage
                            st.session_state["selected_validated"] = None
                            st.rerun() 

            # If incident only dispatched to telegram
            elif incident["status"] == "📩 Dispatched to Telegram":
                with st.container(): # Container with all three buttons
                    dispatch, back = st.columns([1.25,1]) # One column per button
                    with dispatch: # Column with checkboxes and button
                        if st.button("🚑 Dispatch to Emergency Services", key="dispatch_button"): # Container with button only
                            incident["status"] = "✅ Dispatched to All"
                            incident["is_emerg"] = True # Update to True
                            st.session_state["validated"][st.session_state["selected_validated"] - 1] = incident # Update validated ss
                            st.session_state["parsed_validated"] = [] # Reset parsed validated ss to retain the order of incidents in st.session_state["validated"]
                            st.session_state["selected_validated"] = None
                            st.rerun()

                    with back:
                        if st.button("⬅ Back", key="back_button"): # If no action taken and user presses back, go back to homepage
                            st.session_state["selected_validated"] = None
                            st.rerun() 

            elif incident["status"] == "🚑 Dispatched to Emergency Services":
                    dispatch, back = st.columns([1.25,1]) # One column per button
                    with dispatch: # Column with checkboxes and button
                        if st.button("📩 Dispatch to Telegram", key="dispatch_button"): # Container with button only
                            incident["status"] = "✅ Dispatched to All" # Update status
                            incident["is_emerg"] = True # Update to True
                            st.session_state["incident_to_tele"] = incident
                            st.session_state["validated"][st.session_state["selected_validated"] - 1] = incident # Update validated ss
                            st.session_state["parsed_validated"] = [] # Reset parsed validated ss to retain the order of incidents in st.session_state["validated"]
                            st.session_state["selected_validated"] = None
                            st.rerun()

                    with back:
                        if st.button("⬅ Back", key="back_button"): # If no action taken and user presses back, go back to homepage
                            st.session_state["selected_validated"] = None
                            st.rerun() 

            # If incident already dispatched to all, then remove dispatch button
            else:
                if st.button("⬅ Back"):
                    st.session_state["selected_validated"] = None
                    st.rerun()

        display_trademark()
        

# Display map and filtered incidents table
@st.fragment(run_every=3) # Fragment that reruns every 3 seconds to handle changes in session state i.e. new filtered incident
def display_map_and_filtered_incidents_table():
    with st.container(key="pydeck_map"):

        ##### Map #####
        #TODO: prevent map flickering by using run_only_if in @st.fragment
        # Display filtered and validated incidents data points

        def get_icon_data(incident):
            # CROSS: https://img.icons8.com/ios-filled/50/(colour)/cancel.png


            if incident["type"] == "Filtered":
                if incident["priority"] == "High": 
                    url = "https://img.icons8.com/ios-filled/50/FF0000/google-web-search.png" # red magnifying glass
                elif incident["priority"] == "Medium": 
                    url = "https://img.icons8.com/ios-filled/50/FFA500/google-web-search.png" # orange magnifying glass
                else:
                    url = "https://img.icons8.com/ios-filled/50/FFD700/google-web-search.png" # yellow magnifying glass

            elif incident["type"] == "Validated":
                if incident["priority"] == "High": 
                    url = "https://img.icons8.com/ios-filled/50/FF0000/checked--v1.png" # red tick
                elif incident["priority"] == "Medium":
                    url = "https://img.icons8.com/ios-filled/50/FFA500/checked--v1.png" # orange tick
                else:
                    url = "https://img.icons8.com/ios-filled/50/FFD700/checked--v1.png" # yellow tick

            return {
                "url": url,
                "width": 128,
                "height": 128,
                "anchorY": 128, # controls how the icon is anchored vertically relative to the map point. 128 anchorY and 128 height means the bottom of the icon touches the map point 
            }

                
        # Parse JSON to get longitude, latitude, priority, alert_subtype
        def parse_incident(incident):
            return {
                "id": incident["id"],
                "longitude": incident["crowdsource_event"]["x"],
                "latitude": incident["crowdsource_event"]["y"],
                "alert_subtype": (incident["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                if incident["crowdsource_event"]["alert_subtype"] is not None
                                else "Unknown"
                                ),
                "priority": bin_priority(incident["priority_score"]),
            }


        # For demo purposes
        def hardcode_demo():
            for incident in st.session_state["filtered"]:
                # Hardcode priorities and unknown subtype
                if incident["id"] == 1:
                    incident["priority_score"] = 0.9
                    incident["crowdsource_event"]["alert_subtype"] = "Accident major"
                    incident["repeated_events_crowdsource_id"] = [1]
                elif incident["id"] == 2:
                    incident["priority_score"] = 0.5
                else:
                    incident["priority_score"] = 0.1

        hardcode_demo()

        # Filtered incidents layer
        incidents = [parse_incident(incident) for incident in st.session_state["filtered"] if incident]
        data = pd.DataFrame(incidents)
        data["type"] = "Filtered" # Add a type column with "Filtered" as every value in that column

        data["icon"] = data.apply(get_icon_data, axis=1) # Add icon column based on the incident

        filtered_layer = pdk.Layer(
            "IconLayer",
            data=data, # Type of layer (iconlayer = icons)
            get_icon="icon", # Data source
            get_position=["longitude", "latitude"],
            size_scale=25, # Marker size to scale with zooming
            pickable=True, # Enable hovering to show tooltips
        )

        # Validated incidents layer
        # Create map markers with colour and radius
        incidents = [parse_incident(incident) for incident in st.session_state["validated"] if incident]
        data = pd.DataFrame(incidents)
        data["type"] = "Validated" # Add a type column with "Filtered" as every value in that column

        data["icon"] = data.apply(get_icon_data, axis=1) # Add colour columnn based on the incident
        
        validated_layer = pdk.Layer(
            "IconLayer", # Type of layer (iconlayer = icons)
            data=data, # Data source
            get_icon="icon",
            get_position=["longitude", "latitude"],
            size_scale=25, # Marker size to scale with zooming
            pickable=True, # Enable hovering to show tooltips
        )

        # Define tooltip
        tooltip = {
            "html": """
                <div style='text-align: center'>
                    <b>ID {id}</b><br>
                    <span style='font-size: 13px;'>Subtype: {alert_subtype}</span>
                </div>
            """,
            "style": {
                "color": "#004488",               # Deep blue text (matches headings)
                "backgroundColor": "#F0F2F6",     # Light grey background (matches rest of UI)
                "padding": "8px 12px",            # Slightly more padding for clarity
                "borderRadius": "8px",            # Rounded corners
                "border": "2px solid #0072ff",    # Accent blue border (matches tabs/map/etc.)
                "fontSize": "14px",               # Clean, readable
                "boxShadow": "0 2px 6px rgba(0, 0, 0, 0.15)"  # Subtle shadow for depth
            }
        }

        # Controls where the map is centered, i.e. centered around Singapore
        view_state = pdk.ViewState(
            latitude=1.3521,
            longitude=103.8198,
            zoom=11, # Zoom level
            min_zoom=10.5,
            pitch=0, # No tilt
        )

        # Renders map
        st.pydeck_chart(pdk.Deck(
            layers=[filtered_layer, validated_layer],
            initial_view_state=view_state,
            map_style=None, # Streetview selected TODO: choose a map style that makes it easier to see the coloured dots
            tooltip=tooltip,
        ), use_container_width=False) # Centralise map in the container because for some reason it is not done by default

    #######################################
    ##### Table 2: Filtered Incidents #####
    with st.container(key="filtered_cont"):
        st.header("🔍 Filtered Incidents")

        # Initialise column headers and empty row
        table_col = ["ID", "Street", "Date & Time", "Incident Type", "Incident Subtype", "Priority"] 
        table_col = ["📌 ID", "🛣️ Street", "⏰ Date & Time", "⚠️ Incident Type", "📌 Incident Subtype", "🔥 Priority"]
        empty = ["...", "...", "...", "...", "...", "..."]

        # If no filtered incidents, display empty table
        if not st.session_state["filtered"]:
            df = pd.DataFrame([empty],columns=table_col)
            df["S/N"] = ["🚨 No Records Found"] # Initialise serial number value as default value
            df = df[["S/N"] + table_col] # Reorder columns
            st.data_editor(df, use_container_width=True, key="filtered_incidents_editor", disabled=["S/N"] + table_col, hide_index=True)

        else:

            # Parses full json into dict with keys: id, street, timestamp, alert_type, alert_subtype, priority
            # So that can integrate with dataframe better
            def parse_filtered(data):
                return {
                    "id": data["id"],
                    "street": data["crowdsource_event"]["street"],
                    "timestamp": convert_unix(data["crowdsource_event"]["timestamp"]),
                    "alert_type": data["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                    "alert_subtype": (data["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                    if data["crowdsource_event"]["alert_subtype"] is not None
                                    else "Unknown"
                    ),
                    "priority": bin_priority(data["priority_score"])
                }
            
            # Clean up the data of st.session_state["filtered"]
            # This step is necessary because for every duplicate event in incoming incidents about the same incident,
            # each duplicate will generate a filtered event about that same incident with all the same key-values, 
            # with only a change in the value of key "repeated_events_crowdsource_id".
            def clean_filtered():
                cleaned_ids = []
                for incident in st.session_state["filtered"]:
                    if incident["id"] in cleaned_ids:
                        st.session_state["filtered"].remove(incident)
                    else:
                        cleaned_ids.append(incident["id"])

            clean_filtered()

            # Sort by higher to lower priority
            st.session_state["filtered"] = sorted(
                st.session_state["filtered"],
                key=lambda x: x["priority_score"],
                reverse=True,
            )

            all_ids = [incident["id"] for incident in st.session_state["parsed_filtered"]] # Get all IDs currently in table

            for incident in st.session_state["filtered"]:
                if incident["id"] not in all_ids: # If incident is not in table yet
                    st.session_state["parsed_filtered"].append(parse_filtered(incident))

            df = pd.DataFrame(st.session_state["parsed_filtered"])
            df.columns = table_col # Rename columns  
            df.index = range(1, len(df) + 1) # Initialise serial number column to be one-indexed
        
            df.index.name = "S/N" # Rename index column 

            # Create new column for checkbox to view details
            df["🧾 View Details"] = [False] * len(df)

            styled_df = df.style.map(highlight_priority, subset=["🔥 Priority"]) # Apply colour


            edited_df = st.data_editor(styled_df, use_container_width=True, key="filtered_incidents_editor", disabled=table_col) # Display table. Used over st.dataframe because this handles adjusting to the column width, 
                                                                                                                                                                # and also allows checkboxes in tables
                                                                                                                                                                # Disable all columns
                                                                                                                                                                # Height displays every row at once, instead of scrolling within the table
            # Detect checked rows
            checked_index = edited_df.index[edited_df["🧾 View Details"]].tolist() # edited_df.index[...] keeps only indices where "View Details" is True i.e. checkbox is ticked

            # If any checkbox is checked, update session state and rerun
            if checked_index:
                st.session_state["selected_filtered"] = checked_index[0]
                st.rerun()


########################################
##### Table 3: Validated Incidents #####
def display_validated_incidents_table():
    with st.container(key="validated_cont"):
        st.header("✅ Validated Incidents")

        ##### Table #####
        # Initialise column headers and empty row
        table_col = ["ID", "Street", "Date & Time", "Incident Type", "Incident Subtype", "Priority", "Status"]
        table_col = ["📌 ID", "🛣️ Street", "⏰ Date & Time", "⚠️ Incident Type", "📌 Incident Subtype", "🔥 Priority", "📦 Status"]
        empty = ["...", "...", "...", "...", "...", "...", "..."]

        # Initialise column headers and empty row
        if not st.session_state["validated"]:
            df = pd.DataFrame([empty],columns=table_col)
            df["S/N"] = ["🚨 No Records Found"] # Initialise serial number value as default value
            df = df[["S/N"] + table_col] # Reorder columns
            st.data_editor(df, use_container_width=True, key="validated_incidents_editor", disabled=["S/N"] + table_col, hide_index=True)

        else:

            # Parses JSON into dict with keys: id, street, timestamp, alert_type, alert_subtype, priority, status
            # So that can integrate with dataframe better
            def parse_validated(data):
                return {
                    "id": data["id"],
                    "street": data["crowdsource_event"]["street"],
                    "timestamp": convert_unix(data["crowdsource_event"]["timestamp"]),
                    "alert_type": data["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                    "alert_subtype": (data["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                    if data["crowdsource_event"]["alert_subtype"] is not None
                                    else "Unknown"
                    ),
                    "priority": bin_priority(data["priority_score"]),
                    "status": data["status"]
                }
            
            # Sort from higher to lower priority
            st.session_state["validated"] = sorted(
                st.session_state["validated"],
                key=lambda x: x["priority_score"],
                reverse=True,
            )

            st.session_state["parsed_validated"] = [parse_validated(incident) for incident in st.session_state["validated"]]
            
            df = pd.DataFrame(st.session_state["parsed_validated"])
            df.columns = table_col # Rename columns  
            df.index = range(1, len(df) + 1) # Initialise serial number column to be one-indexed

            df.index.name = "S/N" # Rename index column

            df["🧾 View Details"] = [False] * len(df) # Add view details column

            styled_df = df.style.map(highlight_priority, subset=["🔥 Priority"]) # Apply colour

            edited_df = st.data_editor(styled_df, use_container_width=True, key="validated_incidents_editor", disabled=table_col) # Display table. Used over st.dataframe because this handles adjusting to the column width, 
                                                                                                                                                                # and also allows checkboxes in tables
            # Detect checked rows
            checked_index = edited_df.index[edited_df["🧾 View Details"]].tolist() # edited_df.index[...] keeps only indices where "View Details" is True i.e. checkbox is ticked

            # If any checkbox is checked, update session state and rerun
            if checked_index:
                st.session_state["selected_validated"] = checked_index[0]
                st.rerun()


####################################################
##### Table 1: Incoming Incidents (unfiltered) #####
@st.fragment(run_every=2) # Re-runs the table every 2 seconds to keep up with updates to session state
def display_incoming_incidents_table():
    with st.container(key="incoming_cont"):
        # TODO: table styles e.g. bolded headers or wtv
        st.header("📨 Incoming Incidents")

        # Initialise column headers and empty row
        table_col = ["ID", "Street", "Date & Time", "Incident Type", "Incident Subtype"]
        table_col = ["📌 ID", "🛣️ Street", "⏰ Date & Time", "⚠️ Incident Type", "📌 Incident Subtype"]
        empty = ["...", "...", "...", "...", "..."]

        # If no incoming incidents, display empty table
        if not st.session_state["incoming"]:
            df = pd.DataFrame([empty],columns=table_col)
            df["S/N"] = ["🚨 No Records Found"] # Initialise serial number value as default value
            df = df[["S/N"] + table_col] # Reorder columns
            styled_df = df.style.set_properties(**{
                "text-align": "center",
                "vertical-align": "middle"   
            })
            st.data_editor(styled_df, use_container_width=True, key="incoming_incidents_editor", disabled=["S/N"] + table_col, hide_index=True)

        else:

            # Parses JSON into dict with keys: id, street, timestamp, alert_type, alert_subtype
            def parse_incoming(data):
                return {
                    "id": data["id"],
                    "street": data["crowdsource_event"]["street"],
                    "timestamp": convert_unix(data["crowdsource_event"]["timestamp"]),
                    "alert_type": data["crowdsource_event"]["alert_type"].replace("_", " ").capitalize(),
                    "alert_subtype": (data["crowdsource_event"]["alert_subtype"].replace("_", " ").capitalize() # Handles null value
                                    if data["crowdsource_event"]["alert_subtype"] is not None
                                    else "Unknown"
                    )
                }

            # Store parsed data
            if "parsed_incoming" not in st.session_state:
                st.session_state["parsed_incoming"] = []

            all_ids = [incident["id"] for incident in st.session_state["parsed_incoming"]] # Store all ids so far

            # Only add new ids
            for incident in st.session_state["incoming"]:
                # If is a new ID
                if incident["id"] not in all_ids:
                    st.session_state["parsed_incoming"].append(parse_incoming(incident))

            df = pd.DataFrame(st.session_state["parsed_incoming"])
            df.columns = table_col # Rename columns  
            df.index = range(1, len(df) + 1) # Initialise serial number column to be one-indexed

            df.index.name = "S/N" # Rename index column
            st.data_editor(df, use_container_width=True, key="incoming_incidents_editor", disabled=df.columns.tolist()) # Display table. Used over st.dataframe because this handles adjusting to the column width. 
                                                                                        # Key to prevent streamlit.errors.StreamlitDuplicateElementId

def display_trademark():
    # Trademark 
    st.markdown("<p style='text-align: center;'>© 2025 OptiMove AI™.</p>", unsafe_allow_html=True)


def main():
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed") # Enable full width mode

    load_css("styles.css") # Load CSS

    initialise_session_states() # Initialise session state variables

    start_threads() # Start SSE threads

    # If there is an incident to dispatch
    if st.session_state["incident_to_tele"]:
        dispatch_to_tele()

    # If user wants to view details of a filtered incident i.e. a checkbox is checked
    if st.session_state["selected_filtered"]:
        display_filtered_incident_details()               


    # If user wants to view details of a validated incident i.e. a checkbox is checked
    elif st.session_state["selected_validated"]:
        display_validated_incident_details()


    # If user does nothing i.e. view homescreen
    else:   
        st.title("🚦OptiMove AI™")

        # Working tab (filtered and validated incidents) and Archived tab (incoming incidents)
        working, archived = st.tabs(["Working Incidents", "Archived Incidents"])

        # Filtered and Validated Incidents
        with working:
            display_map_and_filtered_incidents_table() # Display map and filtered incidents

            display_validated_incidents_table() # Display validated incidents

        with archived:
            display_incoming_incidents_table() # Display incoming incidents

        display_trademark()


if __name__ == "__main__":
    main()
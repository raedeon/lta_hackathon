import logging
import os
import streamlit as st
import requests
from dotenv import load_dotenv
from logic.utils import convert_unix


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
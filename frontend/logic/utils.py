import base64
import streamlit as st
from datetime import datetime


__all__ = ["load_css", "convert_unix", "convert_img", "highlight_priority", "get_colour", "bin_priority"]


# Load CSS
def load_css(file_name):
    with open(file_name, "r", encoding="utf-8") as f:  # Force UTF-8 encoding
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Convert time from UNIX timestamp to UTC time
def convert_unix(time):
    dt_local = datetime.fromtimestamp(time)  # Converts to local time
    return dt_local.strftime("%Y-%m-%d %H:%M:%S")


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
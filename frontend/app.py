import streamlit as st

# App utilities
from app_utils.session_state import initialise_session_states

# Components (UI)
from components.map_and_tables.incoming_incidents_table import display_incoming_incidents_table
from components.map_and_tables.map_and_filtered_incidents_table import display_map_and_filtered_incidents_table
from components.map_and_tables.validated_incidents_table import display_validated_incidents_table
from components.details.filtered_incident_details import display_filtered_incident_details
from components.details.validated_incident_details import display_validated_incident_details
from components.misc.trademark import display_trademark

# Backend logic
from logic.sse_listeners import start_threads
from logic.telegram_bot import dispatch_to_tele
from logic.utils import load_css

# Data loading
from data.dummy_data import init_dummy


def main():
    st.set_page_config(layout="wide") # Enable full width mode

    load_css("assets/styles.css") # Load CSS

    initialise_session_states() # Initialise session state variables

    start_threads() # Start SSE threads

    init_dummy()

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
import streamlit as st


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
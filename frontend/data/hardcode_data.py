import streamlit as st


# Used for demo purposes
def hardcode_demo():
    for incident in st.session_state["filtered"]:
        # Hardcode priorities and unknown subtype
        if incident["id"] == 1:
            incident["priority_score"] = 0.9
            incident["crowdsource_event"]["timestamp"] = 1742875695
            incident["crowdsource_event"]["alert_subtype"] = "Accident major"
            incident["repeated_events_crowdsource_id"] = [1, 2, 3]
        elif incident["id"] == 2:
            incident["priority_score"] = 0.5
            incident["crowdsource_event"]["timestamp"] = 1742875700
        else:
            incident["priority_score"] = 0.1
            incident["crowdsource_event"]["timestamp"] = 1742875704
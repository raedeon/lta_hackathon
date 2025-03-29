import pandas as pd
import streamlit as st
from logic.utils import *


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
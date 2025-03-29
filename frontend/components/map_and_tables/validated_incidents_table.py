import pandas as pd
import streamlit as st
from logic.utils import *


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
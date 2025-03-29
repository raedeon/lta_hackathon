import pandas as pd
import pydeck as pdk
import streamlit as st
from logic.utils import *
from data.hardcode_data import hardcode_demo # For hardcoding during demo i.e. making sure its daytime, making sure is low, med, high priority


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
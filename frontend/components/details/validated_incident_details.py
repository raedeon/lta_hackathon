import streamlit as st
from components.misc.trademark import display_trademark
from logic.utils import *


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
        rows = []

        # Conditionally include the Town row
        if parsed_incident["town"] is not None:
            rows.append(f"""
                <tr>
                    <td>🏙️ Town</td>
                    <td>{parsed_incident["town"]}</td>
                </tr>
            """)

        # Unconditionally include the rest
        rows.append(f"""
            <tr><td>🛣️ Street</td><td>{parsed_incident["street"]}</td></tr>
            <tr><td>📍 Longitude</td><td>{parsed_incident["longitude"]}</td></tr>
            <tr><td>📍 Latitude</td><td>{parsed_incident["latitude"]}</td></tr>
            <tr><td>⏰ Date & Time</td><td>{parsed_incident["timestamp"]}</td></tr>
            <tr><td>⚠️ Incident Type</td><td>{parsed_incident["alert_type"]}</td></tr>
            <tr><td>📌 Incident Subtype</td><td>{parsed_incident["alert_subtype"]}</td></tr>
            <tr><td>🖼️ Image</td><td>{parsed_incident["image_src"]}</td></tr>
            <tr><td>🎥 Camera ID</td><td>{parsed_incident["camera_id"]}</td></tr>
            <tr><td>📢 Number of Similar Reports</td><td>{parsed_incident["number_of_similar"]}</td></tr>
            <tr>
                <td>🔥 Priority</td>
                <td style='color: white; background-color: {priority_colour}; font-weight: bold; padding: 6px 10px; border-radius: 6px; text-align: center;'>
                    {parsed_incident["priority"]}
                </td>
            </tr>
        """)

        html_table = f"""
            <table class="incident-table">
                <tr>
                    <th>Field</th>
                    <th>Information</th>
                </tr>
                {''.join(rows)}
            </table>
        """

        st.markdown(html_table, unsafe_allow_html=True)


        with st.container(key="validated_buttons"): # Container with all three buttons
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
                        if st.button("🚑 Dispatch to Emergency Services", key="validated_dispatch_button"): # Container with button only
                            incident["status"] = "✅ Dispatched to All"
                            incident["is_emerg"] = True # Update to True
                            st.session_state["validated"][st.session_state["selected_validated"] - 1] = incident # Update validated ss
                            st.session_state["parsed_validated"] = [] # Reset parsed validated ss to retain the order of incidents in st.session_state["validated"]
                            st.session_state["selected_validated"] = None
                            st.rerun()

                    with back:
                        if st.button("⬅ Back", key="validated_back_button"): # If no action taken and user presses back, go back to homepage
                            st.session_state["selected_validated"] = None
                            st.rerun() 

            elif incident["status"] == "🚑 Dispatched to Emergency Services":
                    dispatch, back = st.columns([1.25,1]) # One column per button
                    with dispatch: # Column with checkboxes and button
                        if st.button("📩 Dispatch to Telegram", key="validated_dispatch_button"): # Container with button only
                            incident["status"] = "✅ Dispatched to All" # Update status
                            incident["is_emerg"] = True # Update to True
                            st.session_state["incident_to_tele"] = incident
                            st.session_state["validated"][st.session_state["selected_validated"] - 1] = incident # Update validated ss
                            st.session_state["parsed_validated"] = [] # Reset parsed validated ss to retain the order of incidents in st.session_state["validated"]
                            st.session_state["selected_validated"] = None
                            st.rerun()

                    with back:
                        if st.button("⬅ Back", key="validated_back_button"): # If no action taken and user presses back, go back to homepage
                            st.session_state["selected_validated"] = None
                            st.rerun() 

            # If incident already dispatched to all, then remove dispatch button
            else:
                if st.button("⬅ Back"):
                    st.session_state["selected_validated"] = None
                    st.rerun()

        display_trademark()
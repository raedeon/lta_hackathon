import streamlit as st
from components.misc.trademark import display_trademark
from logic.utils import *


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
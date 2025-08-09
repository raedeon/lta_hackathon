from flask import Flask, jsonify

from backend.server.event_handler import (
    create_event_from_crowdsource,
    check_event_from_crowdsource_created,
    add_verified_event,
    get_all_events,
    get_one_event,
    stream_crowdsource,
    stream_filtered
)

app = Flask(__name__)

@app.route("/")
def entry():
    response = {"message": "Server is up and running"}
    return jsonify(response), 200 

app.add_url_rule("/events/crowdsource", view_func=create_event_from_crowdsource, methods=["POST"])
app.add_url_rule("/events/crowdsource/<int:event_id>/created", view_func=check_event_from_crowdsource_created, methods=["GET"])

# For Frontend
app.add_url_rule("/events/verified", view_func=add_verified_event, methods=["POST"])
app.add_url_rule("/events/<storage_type>", view_func=get_all_events, methods=["GET"])
app.add_url_rule("/events/<storage_type>/<int:event_id>", view_func=get_one_event, methods=["GET"])

# For Server Sent Events
app.add_url_rule("/store/crowdsource", view_func=stream_crowdsource)
app.add_url_rule("/store/filtered", view_func=stream_filtered)

if __name__ == "__main__":
    app.run(debug=True)
    
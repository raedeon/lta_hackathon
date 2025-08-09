from flask import Flask, jsonify

from backend.scripts.lta_datamall.handler import (
    get_traffic_image,
    get_traffic_speed
)

app = Flask(__name__)

@app.route("/")
def entry():
    response = {"message": "Server is up and running"}
    return jsonify(response), 200 

app.add_url_rule("/traffic_speed", view_func=get_traffic_speed, methods=["GET"])
app.add_url_rule("/traffic_image", view_func=get_traffic_image, methods=["GET"])

if __name__ == "__main__":
    app.run(debug=True, port=8000)
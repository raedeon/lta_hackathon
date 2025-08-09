from flask import jsonify, request
import pandas as pd
import os

data_path = "data/csv"

def get_traffic_speed():
    lat = request.args.get("lat", type=float)
    long = request.args.get("long", type=float)
    street = request.args.get("street", "").lower()
    results = {}
    data = None
    if street == "tampines ave 10":
        data = pd.read_csv(os.path.join(data_path, "Accident.csv"))
    else:
        data = pd.read_csv(os.path.join(data_path, "Normal.csv"))
    for _, row in data.iterrows():
        results[row["Interval"]] = {
            "past_week_avg_speed": row["Past_Week_Avg_Speed"],
            "current_avg_speed": row["Current_Avg_Speed"]
        }
    return jsonify(results), 200 

def get_traffic_image():
    lat = request.args.get("lat", type=float)
    long = request.args.get("long", type=float)
    street = request.args.get("street", "").lower()

    data = pd.read_csv(os.path.join(data_path, "Traffic_Images.csv"))
    if street == "tampines ave 10":
        accident = data.loc[0]
        return jsonify({
            "camera_id": accident["CameraID"].item(),
            "image_src": accident["Image File"]
        }), 200
    if street == "clementi ave 6":
        road_shoulder = data.loc[1]
        return jsonify({
            "camera_id": road_shoulder["CameraID"].item(),
            "image_src": road_shoulder["Image File"]
        }), 200
    else: 
        normal = data.loc[2]
        return jsonify({
            "camera_id": normal["CameraID"].item(),
            "image_src": normal["Image File"]
        }), 200

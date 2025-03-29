import streamlit as st


def init_dummy():
    if "init_dummy" not in st.session_state:
        st.session_state["init_dummy"] = False

    if not st.session_state["init_dummy"]:
        ########################## DUMMY DATA
        st.session_state["filtered"] = [
            {
            "crowdsource_event": {
                "alert_subtype": None,
                "alert_type": "ACCIDENT",
                "reliability": 6,
                "street": "Tampines Ave 10",
                "timestamp": 1742476842.4073632,
                "town": "Tampines",
                "x": 103.928405,
                "y": 1.354571
            },
            "id": 1,
            "image_event": {
                "camera_id": 7793,
                "image_src": "data/car_accident.png"
            },
            "is_unique": True,
            "priority_score": 0.65000000,
            "repeated_events_crowdsource_id": [
                2
            ],
            "speed_events": [
                {
                "current_avg_speed": 4,
                "past_week_avg_speed": 20.4
                },
                {
                "current_avg_speed": 5,
                "past_week_avg_speed": 17.4
                },
                {
                "current_avg_speed": 42,
                "past_week_avg_speed": 45.0
                },
                {
                "current_avg_speed": 30,
                "past_week_avg_speed": 30.0
                },
                {
                "current_avg_speed": 50,
                "past_week_avg_speed": 43.4
                },
                {
                "current_avg_speed": 55,
                "past_week_avg_speed": 54.4
                }
            ]
            },
            {
            "crowdsource_event": {
                "alert_subtype": "HAZARD_ON_SHOULDER_CAR_STOPPED",
                "alert_type": "HAZARD",
                "reliability": 7,
                "street": "Clementi Ave 6",
                "timestamp": 1742486366.1760848,
                "town": "Clementi",
                "x": 103.762467,
                "y": 1.317637
            },
            "id": 2,
            "image_event": {
                "camera_id": 4714,
                "image_src": "data/car_road_shoulder.png"
            },
            "is_unique": True,
            "priority_score": 0.250000003,
            "repeated_events_crowdsource_id": [],
            "speed_events": [
                {
                "current_avg_speed": 21,
                "past_week_avg_speed": 20.4
                },
                {
                "current_avg_speed": 18,
                "past_week_avg_speed": 17.4
                },
                {
                "current_avg_speed": 42,
                "past_week_avg_speed": 45.0
                },
                {
                "current_avg_speed": 29,
                "past_week_avg_speed": 30.0
                },
                {
                "current_avg_speed": 50,
                "past_week_avg_speed": 43.4
                },
                {
                "current_avg_speed": 55,
                "past_week_avg_speed": 54.4
                }
            ]
            },
            {
            "crowdsource_event": {
                "alert_subtype": "HAZARD_ON_SHOULDER_CAR_STOPPED",
                "alert_type": "HAZARD",
                "reliability": 4,
                "street": "CTE (AYE)",
                "timestamp": 1742486371.224215,
                "town": None,
                "x": 103.839542,
                "y": 1.286703
            },
            "id": 3,
            "image_event": {
                "camera_id": 1703,
                "image_src": "data/car_normal.png"
            },
            "is_unique": True,
            "priority_score": 0.2000005,
            "repeated_events_crowdsource_id": [],
            "speed_events": [
                {
                "current_avg_speed": 21,
                "past_week_avg_speed": 20.4
                },
                {
                "current_avg_speed": 18,
                "past_week_avg_speed": 17.4
                },
                {
                "current_avg_speed": 42,
                "past_week_avg_speed": 45.0
                },
                {
                "current_avg_speed": 29,
                "past_week_avg_speed": 30.0
                },
                {
                "current_avg_speed": 50,
                "past_week_avg_speed": 43.4
                },
                {
                "current_avg_speed": 55,
                "past_week_avg_speed": 54.4
                }
            ],
            "status": "❌ Undispatched",
            }  
        ]

        st.session_state["validated"] = [
            
        ]
        st.session_state["init_dummy"] = True
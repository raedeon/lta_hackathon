import logging

logger = logging.getLogger(__name__)

import os
import requests
from backend.schema.event_storage import EventStorage
from backend.schema.crowdsource_event import CrowdsourceEvent
from backend.schema.image_event import ImageEvent
from backend.schema.speed_event import SpeedEvent, SpeedEvents

EXTERNAL_DATA_URL = os.getenv("EXT_URL", "http://localhost:8000")
TRAFFIC_IMAGE_URI = "traffic_image"
TRAFFIC_SPEED_URI = "traffic_speed"

class CrowdsourceManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "storage"):
            from backend.server.manager.filtered_manager import FilteredManager
            logger.info("Crowdsource Storage: Storage Initialised")
            self.storage = EventStorage()
            self.queue = []
            self.filtered_manager = FilteredManager()
            self.event_creation_status = {}
    
    def get_next_event_id(self):
        return self.storage.counter
    
    def check_event_created(self, event_id):
        return self.event_creation_status[event_id]

    def add(
        self,
        timestamp,
        town,
        street,
        x, y,
        alert_type,
        reliability,
        alert_subtype = "" 
    ):
        logger.info("Crowdsource Storage: Add new crowdsource event")

        next_id = self.get_next_event_id()
        self.event_creation_status[next_id] = False
        crowdsource_event = CrowdsourceEvent(
            timestamp, 
            town, 
            street,
            x, y, 
            alert_type, 
            reliability, 
            alert_subtype
        )
        image_event = self.__get_image_event(x, y, street)
        speed_events = self.__get_speed_events(x, y, street)
        event = self.storage.create(
            crowdsource_event,
            image_event,
            speed_events
        )
        self.queue.append(event.id)
        self.filtered_manager.notify(event.id)
        self.event_creation_status[next_id] = True
        return event

    def get_all(self):
        logger.info("Crowdsource Storage: Listing all Events")
        return self.storage.list_events()

    def get_one(self, event_id):
        logger.info("Crowdsource Storage: Listing one event")
        return self.storage.read(event_id)
    
    def delete(self, event_id):
        logger.info("Crowdsource Storage: Deleting one event")
        return self.storage.delete(event_id)
    
    def __get_image_event(self, x, y, street) -> ImageEvent:
        logger.info("Crowdsource Storage: Retrieving Images")
        url = f"{EXTERNAL_DATA_URL}/{TRAFFIC_IMAGE_URI}"
        params = {
            "lat": y,
            "long": x,
            "street": street
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            image_event = ImageEvent(data["camera_id"], data["image_src"])
            return image_event 

    def __get_speed_events(self, x, y, street) -> SpeedEvents:
        logger.info("Crowdsource Storage: Retrieving Speed")
        speed_events = SpeedEvents()
        url = f"{EXTERNAL_DATA_URL}/{TRAFFIC_SPEED_URI}"
        params = {
            "lat": y,
            "long": x,
            "street": street
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for _, value in data.items():
                speed_events.add(SpeedEvent(value["past_week_avg_speed"], value["current_avg_speed"]))
            return speed_events 

if __name__ == "__main__":
    manager = CrowdsourceManager()

    data = {
        "timestamp": "2024-10-21 08:30:00",
        "town": "Tampines",
        "street": "Tampines Ave 10",
        "x": 103.928405,
        "y": 1.354571,
        "alert_type": "ACCIDENT",
        "reliability": 6 
    }

    event = manager.add(**data)
    retrieved_event = manager.get_one(event.id)
    print(retrieved_event)
    print(retrieved_event.to_dict())
    retrieved_events = manager.get_all()
    print(retrieved_events)
    print(retrieved_events[0])

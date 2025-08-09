import logging

logger = logging.getLogger(__name__)

from backend.schema.event import Event
from backend.schema.event_storage import EventStorage

class VerifiedManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "storage"):
            logger.info("Verified Storage: Storage Initialised")
            self.storage = EventStorage()
            self.queue = []

    def get_all(self):
        logger.info("Verified Storage: Listing all Events")
        return self.storage.list_events()

    def get_one(self, event_id):
        logger.info("Verified Storage: Listing one event")
        return self.storage.read(event_id)
    
    def delete(self, event_id):
        logger.info("Verified Storage: Deleting one event")
        return self.storage.delete(event_id)
    
    def add_verified_event(self, verified_event: Event):
        logger.info("Verified Storage: Adding one verified event")
        return self.storage.create(
            verified_event.crowdsource_event, 
            verified_event.image_event,
            verified_event.speed_events,
            verified_event.is_unique,
            verified_event.priority_score
        )
        
    #TODO
    def dispatch(self):
        pass


if __name__ == "__main__":
    manager = VerifiedManager()

    data = {
        "timestamp": "2024-10-21 08:30:00",
        "town": "Tampines",
        "street": "Tampines Ave 10",
        "x": 103.928405,
        "y": 1.354571,
        "alert_type": "ACCIDENT",
        "reliability": 6 
    }
    from backend.schema.crowdsource_event import CrowdsourceEvent
    crowdsource_event = CrowdsourceEvent(**data)
    speed_events = None
    image_event = None

    event = Event(0, crowdsource_event, image_event, speed_events)

    verified_event = manager.add_verified_event(event)
    print(verified_event)

    repeated_event = Event(0, crowdsource_event, None, None)
    manager.add_repeated_event(1, repeated_event)

    print(manager.get_all())
    print(manager.get_one(1))


    
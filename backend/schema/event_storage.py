from backend.schema.event import Event
from backend.schema.crowdsource_event import CrowdsourceEvent
from backend.schema.image_event import ImageEvent
from backend.schema.speed_event import SpeedEvents

class EventStorage:
    def __init__(self):
        self.events: dict[int, Event] = {}
        self.counter = 1  
    
    def create(
        self, 
        crowdsource_event: CrowdsourceEvent,
        image_event: ImageEvent = None,
        speed_events: SpeedEvents = None,
        is_unique = False,
        priority_score = -1
    ):
        event_id = self.counter
        event = Event(
            event_id,
            crowdsource_event,
            image_event,
            speed_events,
            is_unique,
            priority_score,
            []
        )
        self.events[event_id] = event
        self.counter += 1
        return event 
    
    def read(self, event_id):
        return self.events.get(event_id, None)

    def update(
        self,
        event_id,
        repeated_event_id
    ):
        event = self.events.get(event_id, None)
        if event:
            event.repeated_events_crowdsource_id.append(repeated_event_id)
            return event
        return None

    def delete(self, event_id):
        return self.events.pop(event_id, None)

    def list_events(self):
        return list(self.events.values())
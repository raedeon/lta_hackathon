from backend.schema.crowdsource_event import CrowdsourceEvent
from backend.schema.image_event import ImageEvent 
from backend.schema.speed_event import SpeedEvents

class Event:
    def __init__(
        self,
        id,
        crowdsource_event: CrowdsourceEvent,
        image_event: ImageEvent = None,
        speed_events: SpeedEvents = None,
        is_unique = False,
        priority_score=-1,
        repeated_events_crowdsource_id = []
    ):
        self.id = id 
        self.crowdsource_event = crowdsource_event
        self.image_event = image_event
        self.speed_events = speed_events
        self.is_unique = is_unique 
        self.priority_score = priority_score
        self.repeated_events_crowdsource_id: list[int] = repeated_events_crowdsource_id

    def __str__(self):
        builder = []
        if self.crowdsource_event:
            builder.append(f"From Crowdsource Event:\n{self.crowdsource_event}")
        if self.speed_events:
            builder.append(f"From Speed Reading Event:\n{self.speed_events}")
        return "\n".join(builder)

    def to_dict(self):
        return {
            "id": self.id,
            "crowdsource_event": self.crowdsource_event.to_dict(),
            "speed_events": self.speed_events.to_dict() if self.speed_events else None,
            "image_event": self.image_event.to_dict() if self.image_event else None,
            "priority_score": self.priority_score,
            "is_unique": self.is_unique,
            "repeated_events_crowdsource_id": self.repeated_events_crowdsource_id
        }

    @classmethod
    def from_dict(cls, data):
        if (id := data.get("id")) is None:
            raise ValueError("Need ID")
        if (crowdsource_event := data.get("crowdsource_event")) is None:
            raise ValueError("Need Crowdsource Event")
        crowdsource_event = data.get("crowdsource_event", None)
        if (speed_events := data.get("speed_events")) is not None:
            speed_events = SpeedEvents.from_dict(speed_events)
        if (image_event := data.get("image_event")) is not None:
            image_event = ImageEvent.from_dict(image_event)
        priority_score = data.get("priority_score", -1)
        is_unique = data.get("is_unique", False)
        repeated_events_crowdsource_id = data.get("repeated_events_croedsource_id")
        return cls(
           id,
           crowdsource_event,
           image_event,
           speed_events,
           is_unique,
           priority_score,
           repeated_events_crowdsource_id
        )

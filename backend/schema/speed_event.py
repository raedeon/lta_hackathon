class SpeedEvent:
    def __init__(
        self, 
        past_week_avg_speed,
        current_avg_speed,
    ):
        self.past_week_avg_speed = past_week_avg_speed
        self.current_avg_speed = current_avg_speed

    def to_dict(self):
        return {
            "past_week_avg_speed": self.past_week_avg_speed,
            "current_avg_speed": self.current_avg_speed,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __str__(self):
        return f"""\
Past Week Average Speed: {self.past_week_avg_speed}
Current Average Speed: {self.current_avg_speed}
"""
    
class SpeedEvents:
    def __init__(self):
        self.speed_events = []
    
    def add(self, speed_event):
        self.speed_events.append(speed_event)
    
    def to_dict(self):
        return [
            speed_event.to_dict() for speed_event in self.speed_events
        ]
    
    @classmethod
    def from_dict(cls, data: list):
        c = cls()
        for speed_event_dict in data:
            c.add(SpeedEvent.from_dict(speed_event_dict))
        return c
    
    def __str__(self):
        builder = [
            f"Interval: {i}\n{str(self.speed_events[i])}" for i in range(len(self.speed_events))
        ]
        return "\n".join(builder)

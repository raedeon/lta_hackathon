class CrowdsourceEvent:
    def __init__(
        self,
        timestamp,
        town,
        street,
        x, y,
        alert_type,
        reliability,
        alert_subtype = "" 
    ):
        self.timestamp = timestamp
        self.town = town
        self.street = street
        self.coordinate = (x, y)
        self.alert_type = alert_type
        self.alert_subtype = alert_subtype
        self.reliability = reliability
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "town": self.town,
            "street": self.street,
            "x": self.coordinate[0],
            "y": self.coordinate[1],
            "alert_type": self.alert_type,
            "alert_subtype": self.alert_subtype,
            "reliability": self.reliability
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __str__(self):
        return f"""\
Timestamp: {self.timestamp}
Town: {self.town}
Street: {self.street}
Coordinate: {self.coordinate}
Alert Type: {self.alert_type}
Alert Subtype: {self.alert_subtype}
Reliability: {self.reliability}
"""

if __name__ == "__main__":
    data = {
        "timestamp": "2024-10-21 08:30:00",
        "town": "Tampines",
        "street": "Tampines Ave 10",
        "x": 103.928405,
        "y": 1.354571,
        "alert_type": "ACCIDENT",
        "reliability": 6 
    }
    # Create event using from_dict
    event = CrowdsourceEvent.from_dict(data)
    data = event.to_dict()
    print(data)
    # Cretae event using __init__
    event = CrowdsourceEvent(**data)
    print(event)
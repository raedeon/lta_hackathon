class ImageEvent:
    def __init__(
        self, 
        camera_id,
        image_src,
    ):
        self.camera_id = camera_id
        self.image_src = image_src

    def to_dict(self):
        return {
            "camera_id": self.camera_id,
            "image_src": self.image_src
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

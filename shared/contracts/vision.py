from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class Frame(BaseContract):
    def __init__(
        self,
        frame_number: int,
        width: int,
        height: int,
        fps: float = 30.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "camera_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.frame_number = frame_number
        self.width = width
        self.height = height
        self.fps = fps

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "frame_number": self.frame_number,
            "width": self.width,
            "height": self.height,
            "fps": self.fps
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Frame':
        return cls(
            frame_number=data.get("frame_number", 0),
            width=data.get("width", 640),
            height=data.get("height", 480),
            fps=data.get("fps", 30.0),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "camera_engine")
        )


class Landmark:
    def __init__(
        self,
        index: int,
        name: str,
        x: float,
        y: float,
        z: float = 0.0,
        visibility: float = 1.0,
        presence: float = 1.0,
        id: Optional[int] = None
    ):
        self.id = id if id is not None else index
        self.index = index
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.visibility = visibility
        self.presence = presence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "index": self.index,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "visibility": self.visibility,
            "presence": self.presence
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Landmark':
        idx = data.get("index", 0)
        return cls(
            id=data.get("id", idx),
            index=idx,
            name=data.get("name", "UNSPECIFIED"),
            x=float(data.get("x", 0.0)),
            y=float(data.get("y", 0.0)),
            z=float(data.get("z", 0.0)),
            visibility=float(data.get("visibility", 1.0)),
            presence=float(data.get("presence", 1.0))
        )


class LandmarkSet(BaseContract):
    def __init__(
        self,
        landmarks: List[Landmark],
        confidence: float = 1.0,
        frame_number: int = 0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "mediapipe_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.landmarks = landmarks
        self.confidence = confidence
        self.frame_number = frame_number

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "landmarks": [lm.to_dict() for lm in self.landmarks],
            "confidence": self.confidence,
            "frame_number": self.frame_number
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LandmarkSet':
        raw_lms = data.get("landmarks", [])
        lms = [Landmark.from_dict(lm) for lm in raw_lms]
        return cls(
            landmarks=lms,
            confidence=float(data.get("confidence", 1.0)),
            frame_number=int(data.get("frame_number", 0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "mediapipe_engine")
        )

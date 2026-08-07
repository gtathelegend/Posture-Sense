from typing import List, Dict, Any, Optional
from shared.contracts.base import BaseContract


class JointAngle:
    def __init__(self, joint_name: str, angle: float, expected_min: float = 0.0, expected_max: float = 360.0):
        self.joint_name = joint_name
        self.angle = angle
        self.expected_min = expected_min
        self.expected_max = expected_max

    def is_valid(self) -> bool:
        return self.expected_min <= self.angle <= self.expected_max

    def to_dict(self) -> Dict[str, Any]:
        return {
            "joint_name": self.joint_name,
            "angle": self.angle,
            "expected_min": self.expected_min,
            "expected_max": self.expected_max
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JointAngle':
        return cls(
            joint_name=data.get("joint_name", "UNKNOWN"),
            angle=float(data.get("angle", 0.0)),
            expected_min=float(data.get("expected_min", 0.0)),
            expected_max=float(data.get("expected_max", 360.0))
        )


class BiomechanicsSnapshot(BaseContract):
    def __init__(
        self,
        joint_angles: List[JointAngle],
        symmetry_score: float = 100.0,
        balance_score: float = 100.0,
        id: Optional[str] = None,
        timestamp: Optional[str] = None,
        schema_version: str = "2.0.0",
        source: str = "biomechanics_engine"
    ):
        super().__init__(id=id, timestamp=timestamp, schema_version=schema_version, source=source)
        self.joint_angles = joint_angles
        self.symmetry_score = symmetry_score
        self.balance_score = balance_score

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "joint_angles": [ja.to_dict() for ja in self.joint_angles],
            "symmetry_score": self.symmetry_score,
            "balance_score": self.balance_score
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiomechanicsSnapshot':
        raw_jas = data.get("joint_angles", [])
        jas = [JointAngle.from_dict(ja) for ja in raw_jas]
        return cls(
            joint_angles=jas,
            symmetry_score=float(data.get("symmetry_score", 100.0)),
            balance_score=float(data.get("balance_score", 100.0)),
            id=data.get("id"),
            timestamp=data.get("timestamp"),
            schema_version=data.get("schema_version", "2.0.0"),
            source=data.get("source", "biomechanics_engine")
        )

from backend.app.models.user import parse_timestamp


class PoseSession:
    def __init__(
        self,
        id,
        user_id,
        pose_label,
        timestamp=None,
        duration=0.0,
        accuracy=0.0,
        reps=0,
        symmetry_score=100.0,
        balance_score=100.0,
        stability_score=100.0,
        rom_score=100.0,
        hold_time=0.0,
        tracking_quality=100.0,
        failed_rules=None
    ):
        self.id = id
        self.user_id = str(user_id)
        self.pose_label = pose_label
        self.timestamp = parse_timestamp(timestamp)
        self.duration = float(duration or 0.0)
        self.accuracy = float(accuracy or 0.0)
        self.reps = int(reps or 0)
        self.symmetry_score = float(symmetry_score if symmetry_score is not None else 100.0)
        self.balance_score = float(balance_score if balance_score is not None else 100.0)
        self.stability_score = float(stability_score if stability_score is not None else 100.0)
        self.rom_score = float(rom_score if rom_score is not None else 100.0)
        self.hold_time = float(hold_time or 0.0)
        self.tracking_quality = float(tracking_quality if tracking_quality is not None else 100.0)
        self.failed_rules = failed_rules if isinstance(failed_rules, list) else []

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pose_label': self.pose_label,
            'timestamp': self.timestamp.isoformat() if hasattr(self.timestamp, 'isoformat') else str(self.timestamp),
            'duration': round(self.duration, 1),
            'accuracy': round(self.accuracy, 1),
            'reps': self.reps,
            'symmetry_score': round(self.symmetry_score, 1),
            'balance_score': round(self.balance_score, 1),
            'stability_score': round(self.stability_score, 1),
            'rom_score': round(self.rom_score, 1),
            'hold_time': round(self.hold_time, 1),
            'tracking_quality': round(self.tracking_quality, 1),
            'failed_rules': self.failed_rules
        }


def build_pose_session(record):
    if not record:
        return None
    return PoseSession(
        id=record.get('id'),
        user_id=record.get('user_id'),
        pose_label=record.get('pose_label'),
        timestamp=record.get('timestamp'),
        duration=record.get('duration'),
        accuracy=record.get('accuracy'),
        reps=record.get('reps', 0),
        symmetry_score=record.get('symmetry_score', 100.0),
        balance_score=record.get('balance_score', 100.0),
        stability_score=record.get('stability_score', 100.0),
        rom_score=record.get('rom_score', 100.0),
        hold_time=record.get('hold_time', 0.0),
        tracking_quality=record.get('tracking_quality', 100.0),
        failed_rules=record.get('failed_rules', [])
    )


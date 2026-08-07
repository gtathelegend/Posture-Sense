from backend.app.models.user import parse_timestamp


class PoseSession:
    def __init__(self, id, user_id, pose_label, timestamp=None, duration=0.0, accuracy=0.0):
        self.id = id
        self.user_id = str(user_id)
        self.pose_label = pose_label
        self.timestamp = parse_timestamp(timestamp)
        self.duration = float(duration or 0.0)
        self.accuracy = float(accuracy or 0.0)


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
    )

from backend.app.repositories.session_repository import SessionRepository


class SessionService:
    @staticmethod
    def save_session(
        user_id,
        pose_label,
        duration,
        accuracy,
        reps=0,
        symmetry_score=None,
        balance_score=None,
        stability_score=None,
        rom_score=None,
        hold_time=0.0,
        tracking_quality=None,
        failed_rules=None
    ):
        # 1. Pose Label Validation
        if not pose_label or not isinstance(pose_label, str) or pose_label.strip() in ['', 'Unknown', 'Scanning...', 'Scanning ...']:
            return None, 'Invalid pose label'

        # 2. Duration Validation
        try:
            duration_val = float(duration)
            if duration_val < 0.0:
                return None, 'Duration cannot be negative'
        except (ValueError, TypeError):
            return None, 'Duration must be a valid number'

        # 3. Accuracy Score Validation
        try:
            accuracy_val = float(accuracy)
            if not (0.0 <= accuracy_val <= 100.0):
                return None, 'Accuracy score must be between 0 and 100'
        except (ValueError, TypeError):
            return None, 'Accuracy score must be a valid number'

        # 4. Reps Validation
        try:
            reps_val = int(reps)
            if reps_val < 0:
                return None, 'Reps cannot be negative'
        except (ValueError, TypeError):
            return None, 'Reps must be an integer'

        # 5. Biomechanics Scores & Tracking Quality Validation (0-100 or None)
        validated_metrics = {}
        for name, val in [
            ('Symmetry score', symmetry_score),
            ('Balance score', balance_score),
            ('Stability score', stability_score),
            ('ROM score', rom_score),
            ('Tracking quality', tracking_quality)
        ]:
            if val is not None:
                try:
                    score_val = float(val)
                    if not (0.0 <= score_val <= 100.0):
                        return None, f'{name} must be between 0 and 100'
                    validated_metrics[name] = score_val
                except (ValueError, TypeError):
                    return None, f'{name} must be a valid number'
            else:
                validated_metrics[name] = None

        # 6. Hold Time Validation
        try:
            hold_val = float(hold_time)
            if hold_val < 0.0:
                return None, 'Hold time cannot be negative'
        except (ValueError, TypeError):
            return None, 'Hold time must be a valid number'

        # 7. Failed Rules Validation
        if failed_rules is not None and not isinstance(failed_rules, list):
            return None, 'Failed rules must be a list'

        session = SessionRepository.create_session(
            user_id=user_id,
            pose_label=pose_label.strip(),
            duration=float(duration),
            accuracy=float(accuracy),
            reps=int(reps),
            symmetry_score=validated_metrics['Symmetry score'],
            balance_score=validated_metrics['Balance score'],
            stability_score=validated_metrics['Stability score'],
            rom_score=validated_metrics['ROM score'],
            hold_time=float(hold_time),
            tracking_quality=validated_metrics['Tracking quality'],
            failed_rules=failed_rules or []
        )
        if session:
            return session, None
        return None, 'Failed to save session'


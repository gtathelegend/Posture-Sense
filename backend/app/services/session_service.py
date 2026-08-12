from backend.app.repositories.session_repository import SessionRepository


class SessionService:
    @staticmethod
    def save_session(
        user_id,
        pose_label,
        duration,
        accuracy,
        reps=0,
        symmetry_score=100.0,
        balance_score=100.0,
        stability_score=100.0,
        rom_score=100.0,
        hold_time=0.0,
        tracking_quality=100.0,
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

        # 5. Biomechanics Scores Validation (0-100)
        for name, val in [
            ('Symmetry score', symmetry_score),
            ('Balance score', balance_score),
            ('Stability score', stability_score),
            ('ROM score', rom_score),
            ('Tracking quality', tracking_quality)
        ]:
            try:
                score_val = float(val)
                if not (0.0 <= score_val <= 100.0):
                    return None, f'{name} must be between 0 and 100'
            except (ValueError, TypeError):
                return None, f'{name} must be a valid number'

        # 6. Hold Time Validation
        try:
            hold_val = float(hold_time)
            if hold_val < 0.0:
                return None, 'Hold time cannot be negative'
        except (ValueError, TypeError):
            return None, 'Hold time must be a valid number'

        # 7. Failed Rules Validation
        if failed_rules is not None and not isinstance(failed_rules, list):
            return None, 'Failed rules must be a list of rule strings'
        if isinstance(failed_rules, list):
            for r in failed_rules:
                if not isinstance(r, str):
                    return None, 'Each failed rule must be a string'

        session = SessionRepository.create_session(
            user_id=user_id,
            pose_label=pose_label.strip(),
            duration=float(duration),
            accuracy=float(accuracy),
            reps=int(reps),
            symmetry_score=float(symmetry_score),
            balance_score=float(balance_score),
            stability_score=float(stability_score),
            rom_score=float(rom_score),
            hold_time=float(hold_time),
            tracking_quality=float(tracking_quality),
            failed_rules=failed_rules or []
        )
        if session:
            return session, None
        return None, 'Failed to save session'

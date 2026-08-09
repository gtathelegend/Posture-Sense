"""
FeedbackEngine
==============
Production-grade, configuration-driven Feedback Engine for PostureSense v2.

Priority    : 9
Dependencies: scoring_engine, movement_engine, pose_rule_engine, biomechanics_engine
Subscribes  : score.updated       (ScoreReport)
              score.rep_completed   (ScoreReport / rep data)
              score.exercise_completed (ScoreReport)
              score.session_completed  (ScoreReport / session summary)
              pose.detected       (PoseResult)
              exercise.completed  (ExerciseResult)
Publishes   : feedback.generated
              feedback.updated
              feedback.dismissed
              feedback.session_summary

DO NOT perform computer vision.
DO NOT calculate scores.
DO NOT change measurements.
DO NOT classify poses.
DO NOT detect exercises.
DO NOT use LLM text generation.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple

import yaml

from shared.engines.interfaces import FeedbackEngineInterface
from shared.events.event_bus import EventBus
from shared.events.event_types import Event
from shared.types.enums import EngineStatus
from shared.contracts.scoring import ScoreReport
from shared.contracts.feedback import FeedbackResult, FeedbackSessionSummary
from shared.contracts.pose import PoseResult, ExerciseResult


_RULES_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "config", "current", "feedback", "feedback_rules.yaml"
)

SEVERITY_WEIGHTS = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1
}


class FeedbackEngine(FeedbackEngineInterface):
    """
    Feedback Engine converts objective assessment data into actionable,
    evidence-based feedback messages, warnings, achievements, and session summaries.
    """

    def __init__(self, name: str = "FeedbackEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 9
        self.dependencies = ["scoring_engine", "movement_engine", "pose_rule_engine", "biomechanics_engine"]

        # Default configuration
        self.config: Dict[str, Any] = {
            "version": "2.0.0",
            "settings": {
                "default_cooldown_seconds": 4.0,
                "high_severity_cooldown_seconds": 2.5,
                "critical_severity_cooldown_seconds": 1.0,
                "max_active_feedback_queue": 5
            },
            "rules": []
        }

        # Internal state
        self._last_score_report: Optional[ScoreReport] = None
        self._last_pose: Optional[PoseResult] = None
        self._last_exercise: Optional[ExerciseResult] = None

        self._rule_cooldowns: Dict[str, float] = {}  # rule_id -> timestamp last triggered
        self._message_cooldowns: Dict[str, float] = {}  # message -> timestamp last triggered

        self._active_feedback: List[FeedbackResult] = []
        self._generated_count: int = 0
        self._processing_time_ms: float = 0.0

    def initialize(self, config: Optional[dict] = None) -> bool:
        """Initialize engine and load feedback rules configuration."""
        loaded_cfg = self._load_config()
        if loaded_cfg:
            self.config.update(loaded_cfg)

        if config:
            self.config.update(config)

        # Subscribe to high-level assessment events
        self.subscribe("score.updated", self._on_score_updated)
        self.subscribe("score.rep_completed", self._on_score_rep_completed)
        self.subscribe("score.exercise_completed", self._on_score_exercise_completed)
        self.subscribe("score.session_completed", self._on_score_session_completed)
        self.subscribe("pose.detected", self._on_pose_detected)
        self.subscribe("exercise.completed", self._on_exercise_completed)

        self._status = EngineStatus.INITIALIZED
        self.publish("feedback.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        """Start engine processing loop."""
        self._status = EngineStatus.RUNNING
        self.publish("feedback.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        """Pause engine processing."""
        self._status = EngineStatus.PAUSED
        self.publish("feedback.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        """Resume engine processing."""
        self._status = EngineStatus.RUNNING
        self.publish("feedback.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        """Stop engine processing."""
        self._status = EngineStatus.STOPPED
        self.publish("feedback.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        """Release engine resources."""
        self._status = EngineStatus.DISPOSED
        self._active_feedback.clear()
        self._rule_cooldowns.clear()
        self._message_cooldowns.clear()
        self._last_score_report = None
        self._last_pose = None
        self._last_exercise = None
        self.publish("feedback.disposed", self.get_diagnostics())
        return True

    # ---------------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------------

    def _on_score_updated(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            report = ScoreReport.from_dict(data)
        elif isinstance(data, ScoreReport):
            report = data
        else:
            return

        self._last_score_report = report
        self._evaluate_and_publish_feedback()

    def _on_score_rep_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        self._evaluate_and_publish_feedback(is_rep_completion=True)

    def _on_score_exercise_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        self._evaluate_and_publish_feedback()

    def _on_score_session_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        self._generate_and_publish_session_summary(data)

    def _on_pose_detected(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            self._last_pose = PoseResult.from_dict(data)
        elif isinstance(data, PoseResult):
            self._last_pose = data

    def _on_exercise_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        self._generate_and_publish_session_summary(data)

    # ---------------------------------------------------------------------------
    # Rule Evaluation & Evidence Generation
    # ---------------------------------------------------------------------------

    def evaluate_feedback_rules(self, is_rep_completion: bool = False) -> List[FeedbackResult]:
        """
        Evaluates configuration rules against current assessment outputs,
        attaches measurable evidence, ranks by severity/confidence, and deduplicates.
        """
        t0 = time.time()
        if not self._last_score_report:
            return []

        report = self._last_score_report
        now = time.time()
        rules = self.config.get("rules", [])
        candidates: List[FeedbackResult] = []

        # Metric sources map
        metric_values: Dict[str, Tuple[Optional[float], str]] = {
            "overall_score": (report.overall_score, "overall_score"),
            "tracking_quality": (self._last_exercise.tracking_quality if self._last_exercise else (report.components.get("tracking_quality", {}).get("score")), "tracking_quality")
        }

        # Populate from ScoreReport components
        for dim, comp in report.components.items():
            if isinstance(comp, dict) and comp.get("score") is not None:
                metric_values[dim] = (float(comp["score"]), dim)

        # Evaluate rules
        for rule in rules:
            rule_id = rule.get("id", "unnamed_rule")
            metric_name = rule.get("metric", "")
            condition = rule.get("condition", "below")
            threshold = float(rule.get("threshold", 0.0))

            val_tuple = metric_values.get(metric_name)
            if not val_tuple or val_tuple[0] is None:
                continue

            raw_val, metric_src = val_tuple
            triggered = False

            if condition == "below" and raw_val < threshold:
                triggered = True
            elif condition == "above" and raw_val > threshold:
                triggered = True
            elif condition == "equals" and abs(raw_val - threshold) < 1e-3:
                triggered = True

            if not triggered:
                continue

            # Check Cooldown / Deduplication
            cooldown_sec = float(rule.get("cooldown_seconds", self.config.get("settings", {}).get("default_cooldown_seconds", 4.0)))
            last_trig = self._rule_cooldowns.get(rule_id, 0.0)
            if (now - last_trig) < cooldown_sec:
                continue

            # Construct Evidence
            diff = abs(raw_val - threshold)
            evidence = {
                "raw_value": round(raw_val, 2),
                "threshold": round(threshold, 2),
                "difference": round(diff, 2),
                "unit": "points" if "score" in metric_name or metric_name in report.components else "%",
                "metric_source": metric_src,
                "rule_condition": condition
            }

            # Multi-language / Localization variables
            variables = {
                "raw_value": round(raw_val, 1),
                "threshold": round(threshold, 1),
                "metric_name": metric_name,
                "exercise_name": report.exercise_name
            }

            msg_template = rule.get("message", "Metric constraint violated.")
            fb_item = FeedbackResult(
                category=rule.get("category", "Form"),
                type=rule.get("type", "correction"),
                severity=rule.get("severity", "medium"),
                message=msg_template,
                evidence=evidence,
                metric_source=metric_src,
                confidence=report.score_confidence,
                exercise_id=report.exercise_id,
                pose_id=self._last_pose.pose_name if self._last_pose else None,
                rule_triggered=rule_id,
                template_key=rule.get("template_key", "feedback.generic"),
                variables=variables,
                source=self.name
            )

            candidates.append(fb_item)

        # Prioritize & Rank by Severity (critical > high > medium > low > info) then Confidence
        candidates.sort(
            key=lambda item: (SEVERITY_WEIGHTS.get(item.severity.lower(), 1), item.confidence),
            reverse=True
        )

        # Filter duplicates against message suppression buffer
        filtered: List[FeedbackResult] = []
        for item in candidates:
            msg_last = self._message_cooldowns.get(item.message, 0.0)
            msg_cooldown = self._get_severity_cooldown(item.severity)
            if (now - msg_last) >= msg_cooldown:
                filtered.append(item)
                # Update cooldown timestamps
                self._rule_cooldowns[item.rule_triggered] = now
                self._message_cooldowns[item.message] = now

        max_queue = self.config.get("settings", {}).get("max_active_feedback_queue", 5)
        filtered = filtered[:max_queue]

        self._processing_time_ms = (time.time() - t0) * 1000.0
        return filtered

    def _evaluate_and_publish_feedback(self, is_rep_completion: bool = False) -> None:
        new_feedback = self.evaluate_feedback_rules(is_rep_completion)
        if not new_feedback:
            return

        self._active_feedback = new_feedback
        self._generated_count += len(new_feedback)

        for item in new_feedback:
            self.publish("feedback.generated", item.to_dict())

        self.publish("feedback.updated", {
            "active_feedback": [f.to_dict() for f in self._active_feedback],
            "count": len(self._active_feedback)
        })

    # ---------------------------------------------------------------------------
    # Session Feedback Summarizer
    # ---------------------------------------------------------------------------

    def _generate_and_publish_session_summary(self, payload: Any) -> None:
        """
        Generates actionable session summary payload (strengths, weak areas,
        common mistakes, and improvement areas). Does NOT provide medical advice.
        """
        report = self._last_score_report
        session_id = str(payload.get("session_id", "session_unknown")) if isinstance(payload, dict) else "session_unknown"
        exercise_id = report.exercise_id if report else "unknown"

        strengths = []
        weak_areas = []
        common_mistakes = []
        improvement_areas = []

        if report and report.components:
            for dim, comp in report.components.items():
                if isinstance(comp, dict) and comp.get("score") is not None:
                    score = comp["score"]
                    if score >= 80.0:
                        strengths.append(f"Strong {dim.upper()} performance ({score:.1f}/100)")
                    elif score < 60.0:
                        weak_areas.append(f"{dim.upper()} needs attention ({score:.1f}/100)")
                        improvement_areas.append(f"Focus on improving {dim} consistency")

        if report and report.rep_scores:
            low_reps = [r for r in report.rep_scores if r.get("overall_score", 100.0) < 65.0]
            if low_reps:
                common_mistakes.append(f"Form dropped on {len(low_reps)} repetition(s)")

        if not strengths:
            strengths.append("Session completed successfully")
        if not weak_areas:
            weak_areas.append("No critical weaknesses detected")
        if not improvement_areas:
            improvement_areas.append("Maintain steady pace and posture")

        summary = FeedbackSessionSummary(
            session_id=session_id,
            exercise_id=exercise_id,
            strengths=strengths,
            weak_areas=weak_areas,
            common_mistakes=common_mistakes,
            improvement_areas=improvement_areas,
            source=self.name
        )

        self.publish("feedback.session_summary", summary.to_dict())

    # ---------------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------------

    def _get_severity_cooldown(self, severity: str) -> float:
        settings = self.config.get("settings", {})
        sev = severity.lower()
        if sev == "critical":
            return float(settings.get("critical_severity_cooldown_seconds", 1.0))
        elif sev == "high":
            return float(settings.get("high_severity_cooldown_seconds", 2.5))
        else:
            return float(settings.get("default_cooldown_seconds", 4.0))

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """Loads YAML feedback rules configuration."""
        fpath = os.path.normpath(_RULES_FILE)
        if not os.path.isfile(fpath):
            return None
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[FeedbackEngine] Error loading rules file {fpath}: {e}")
            return None

    # ---------------------------------------------------------------------------
    # Diagnostics & Telemetry
    # ---------------------------------------------------------------------------

    def get_diagnostics(self) -> Dict[str, Any]:
        """Exposes engine diagnostics telemetry."""
        highest_severity = "info"
        if self._active_feedback:
            top_fb = max(self._active_feedback, key=lambda f: SEVERITY_WEIGHTS.get(f.severity.lower(), 1))
            highest_severity = top_fb.severity

        last_msg = self._active_feedback[0].message if self._active_feedback else "None"

        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config_version": self.config.get("version", "2.0.0"),
            "metrics": {
                "generatedCount": self._generated_count,
                "activeFeedbackCount": len(self._active_feedback),
                "highestSeverity": highest_severity,
                "lastFeedbackMessage": last_msg,
                "generationLatencyMs": round(self._processing_time_ms, 2),
                "activeRulesCount": len(self.config.get("rules", []))
            }
        }

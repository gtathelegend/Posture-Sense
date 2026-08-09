"""
ScoringEngine
=============
Production-grade, configuration-driven Scoring Engine for PostureSense v2.

Priority    : 8
Dependencies: movement_engine, biomechanics_engine, pose_rule_engine
Subscribes  : biomechanics.updated (BiomechanicsSnapshot)
              pose.detected       (PoseResult)
              exercise.started    (ExerciseResult)
              exercise.phase_changed (ExerciseResult)
              exercise.rep_completed (ExerciseResult)
              exercise.completed  (ExerciseResult)
Publishes   : score.updated
              score.rep_completed
              score.exercise_completed
              score.session_completed
              score.unavailable
              score.quality_warning

DO NOT implement coaching advice.
DO NOT generate natural-language recommendations.
DO NOT modify upstream measurements.
DO NOT hide failed metrics.
Every score MUST be traceable to measurable inputs and configured weights.
"""

from __future__ import annotations

import os
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import yaml

from shared.engines.interfaces import ScoringEngineInterface
from shared.events.event_bus import EventBus
from shared.events.event_types import Event
from shared.types.enums import EngineStatus
from shared.contracts.scoring import ScoreReport
from shared.contracts.biomechanics import BiomechanicsSnapshot
from shared.contracts.pose import PoseResult, ExerciseResult


_WEIGHTS_FILE = os.path.join(
    os.path.dirname(__file__),
    "..", "config", "current", "weights", "scoring_weights.yaml"
)


class ScoringEngine(ScoringEngineInterface):
    """
    Scoring Engine converts objective outputs from perception and movement pipeline
    into explainable performance scores.
    """

    def __init__(self, name: str = "ScoringEngine", event_bus: Optional[EventBus] = None):
        super().__init__(name=name, event_bus=event_bus)
        self.version = "2.0.0"
        self.priority = 8
        self.dependencies = ["movement_engine", "biomechanics_engine", "pose_rule_engine"]

        # Default configuration
        self.config: Dict[str, Any] = {
            "version": "2.0.0",
            "default_weights": {
                "form": 0.30,
                "rom": 0.20,
                "stability": 0.15,
                "symmetry": 0.15,
                "control": 0.10,
                "tempo": 0.10
            },
            "categories": {
                "dynamic": {
                    "form": 0.30,
                    "rom": 0.20,
                    "stability": 0.15,
                    "symmetry": 0.15,
                    "control": 0.10,
                    "tempo": 0.10
                },
                "static_hold": {
                    "form": 0.25,
                    "stability": 0.30,
                    "symmetry": 0.20,
                    "control": 0.15,
                    "tracking_quality": 0.10
                }
            },
            "exercises": {},
            "score_bands": [
                {"min": 90.0, "max": 100.0, "label": "Excellent"},
                {"min": 75.0, "max": 89.99, "label": "Good"},
                {"min": 60.0, "max": 74.99, "label": "Needs Improvement"},
                {"min": 0.0, "max": 59.99, "label": "Poor"}
            ],
            "quality_gates": {
                "min_tracking_quality": 50.0,
                "min_pose_confidence": 0.4,
                "min_landmark_visibility": 0.5,
                "min_samples": 3
            }
        }

        # Internal telemetry & state
        self._last_biomechanics: Optional[BiomechanicsSnapshot] = None
        self._last_pose: Optional[PoseResult] = None
        self._last_exercise: Optional[ExerciseResult] = None
        
        self._active_exercise_id: str = "unknown"
        self._active_exercise_name: str = "Unknown"
        self._exercise_category: str = "dynamic"

        self._rep_scores: List[Dict[str, Any]] = []
        self._sample_count: int = 0
        self._evaluations_count: int = 0
        self._processing_time_ms: float = 0.0
        self._last_score_report: Optional[ScoreReport] = None

        # Session tracking
        self._session_start_time: float = 0.0
        self._completed_reps_count: int = 0
        self._invalid_reps_count: int = 0

    def initialize(self, config: Optional[dict] = None) -> bool:
        """Initialize engine and load scoring configuration."""
        loaded_cfg = self._load_config()
        if loaded_cfg:
            self.config.update(loaded_cfg)

        if config:
            self.config.update(config)

        # Validate configuration
        val_ok, val_err = self._validate_config(self.config)
        if not val_ok:
            self._status = EngineStatus.UNINITIALIZED
            print(f"[ScoringEngine] Configuration validation failed: {val_err}")
            return False

        # Subscribe to required inputs
        self.subscribe("biomechanics.updated", self._on_biomechanics_updated)
        self.subscribe("pose.detected", self._on_pose_detected)
        self.subscribe("exercise.started", self._on_exercise_started)
        self.subscribe("exercise.phase_changed", self._on_exercise_phase_changed)
        self.subscribe("exercise.rep_completed", self._on_rep_completed)
        self.subscribe("exercise.completed", self._on_exercise_completed)

        self._status = EngineStatus.INITIALIZED
        self.publish("score.initialized", self.get_diagnostics())
        return True

    def start(self) -> bool:
        """Start engine processing loop."""
        self._status = EngineStatus.RUNNING
        self._session_start_time = time.time()
        self.publish("score.started", self.get_diagnostics())
        return True

    def pause(self) -> bool:
        """Pause engine processing."""
        self._status = EngineStatus.PAUSED
        self.publish("score.paused", self.get_diagnostics())
        return True

    def resume(self) -> bool:
        """Resume engine processing."""
        self._status = EngineStatus.RUNNING
        self.publish("score.resumed", self.get_diagnostics())
        return True

    def stop(self) -> bool:
        """Stop engine processing."""
        self._status = EngineStatus.STOPPED
        self.publish("score.stopped", self.get_diagnostics())
        return True

    def dispose(self) -> bool:
        """Release engine resources."""
        self._status = EngineStatus.DISPOSED
        self._rep_scores.clear()
        self._last_biomechanics = None
        self._last_pose = None
        self._last_exercise = None
        self._last_score_report = None
        self.publish("score.disposed", self.get_diagnostics())
        return True

    # ---------------------------------------------------------------------------
    # Event Handlers
    # ---------------------------------------------------------------------------

    def _on_biomechanics_updated(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            snapshot = BiomechanicsSnapshot.from_dict(data)
        elif isinstance(data, BiomechanicsSnapshot):
            snapshot = data
        else:
            return

        self._last_biomechanics = snapshot
        self._evaluate_and_publish()

    def _on_pose_detected(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            pose_res = PoseResult.from_dict(data)
        elif isinstance(data, PoseResult):
            pose_res = data
        else:
            return

        self._last_pose = pose_res

    def _on_exercise_started(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if hasattr(data, "to_dict"):
            data = data.to_dict()

        if isinstance(data, dict):
            self._active_exercise_id = data.get("exercise_id", "unknown")
            self._active_exercise_name = data.get("exercise_name", "Unknown")
            self._exercise_category = data.get("category", "dynamic")
            self._rep_scores.clear()
            self._completed_reps_count = 0
            self._invalid_reps_count = 0

    def _on_exercise_phase_changed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            ex_res = ExerciseResult.from_dict(data)
        elif isinstance(data, ExerciseResult):
            ex_res = data
        else:
            return

        self._last_exercise = ex_res
        self._active_exercise_id = ex_res.exercise_id
        self._active_exercise_name = ex_res.exercise_name
        self._evaluate_and_publish()

    def _on_rep_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        data = event.data if hasattr(event, "data") else event
        if isinstance(data, dict):
            ex_res = ExerciseResult.from_dict(data)
        elif isinstance(data, ExerciseResult):
            ex_res = data
        else:
            return

        self._last_exercise = ex_res
        self._completed_reps_count += 1

        # Evaluate rep score
        rep_report = self.evaluate_score()
        rep_data = {
            "rep_number": ex_res.rep_count,
            "overall_score": rep_report.overall_score,
            "form_score": rep_report.components.get("form", {}).get("score") if (isinstance(rep_report.components, dict) and rep_report.components.get("form", {}).get("score") is not None) else rep_report.overall_score,
            "rom": rep_report.components.get("rom", {}).get("score") if (isinstance(rep_report.components, dict) and rep_report.components.get("rom", {}).get("score") is not None) else 0.0,
            "stability": rep_report.components.get("stability", {}).get("score") if (isinstance(rep_report.components, dict) and rep_report.components.get("stability", {}).get("score") is not None) else 0.0,
            "control": rep_report.components.get("control", {}).get("score") if (isinstance(rep_report.components, dict) and rep_report.components.get("control", {}).get("score") is not None) else 0.0,
            "duration": ex_res.current_rep_duration,
            "quality": ex_res.movement_quality
        }
        self._rep_scores.append(rep_data)

        # Publish score.rep_completed
        self.publish("score.rep_completed", {
            "rep_score": rep_data,
            "score_report": rep_report.to_dict()
        })

    def _on_exercise_completed(self, event: Any) -> None:
        if self._status != EngineStatus.RUNNING:
            return
        final_report = self.evaluate_score()
        self.publish("score.exercise_completed", final_report.to_dict())
        self.publish("score.session_completed", {
            "session_summary": final_report.session_summary,
            "score_report": final_report.to_dict()
        })

    # ---------------------------------------------------------------------------
    # Core Scoring Logic
    # ---------------------------------------------------------------------------

    def evaluate_score(self) -> ScoreReport:
        """
        Evaluates current inputs and computes deterministic ScoreReport.
        """
        t0 = time.time()
        self._evaluations_count += 1
        self._sample_count += 1

        # Step 1: Quality Gate Check
        tracking_quality = self._last_exercise.tracking_quality if self._last_exercise else 100.0
        pose_confidence = (self._last_pose.confidence / 100.0) if (self._last_pose and self._last_pose.confidence > 1.0) else (self._last_pose.confidence if self._last_pose else 1.0)
        
        q_gates = self.config.get("quality_gates", {})
        min_tq = q_gates.get("min_tracking_quality", 50.0)
        min_pc = q_gates.get("min_pose_confidence", 0.4)

        quality_gate_passed = True
        quality_warning: Optional[str] = None

        if tracking_quality < min_tq:
            quality_gate_passed = False
            quality_warning = f"Tracking quality too low ({tracking_quality:.1f}% < {min_tq}%)"
        elif pose_confidence < min_pc:
            quality_gate_passed = False
            quality_warning = f"Pose recognition confidence too low ({pose_confidence:.2f} < {min_pc})"

        # Step 2: Weight Configuration Selection
        ex_weights = self.config.get("exercises", {}).get(self._active_exercise_id)
        if not ex_weights:
            ex_weights = self.config.get("categories", {}).get(self._exercise_category)
        if not ex_weights:
            ex_weights = self.config.get("default_weights", {
                "form": 0.30, "rom": 0.20, "stability": 0.15,
                "symmetry": 0.15, "control": 0.10, "tempo": 0.10
            })

        # Step 3: Metric Extraction & Normalization
        raw_components = self._extract_raw_dimensions()
        
        # Step 4: Component Evaluation & Dynamic Re-weighting
        evaluated_components: Dict[str, Any] = {}
        missing_metrics: List[str] = []
        active_weights_sum = 0.0

        for dim, weight in ex_weights.items():
            if dim in raw_components and raw_components[dim] is not None:
                val = float(raw_components[dim])
                # Clamp normalized score to [0.0, 100.0]
                norm_score = max(0.0, min(100.0, val))
                status = self._get_metric_status(norm_score)
                
                evaluated_components[dim] = {
                    "score": round(norm_score, 1),
                    "weight": weight,
                    "status": status,
                    "raw_value": round(val, 2),
                    "contribution": 0.0,  # Computed after re-weighting
                    "explainability": f"{dim.upper()} evaluated at {norm_score:.1f}/100 ({status})"
                }
                active_weights_sum += weight
            else:
                missing_metrics.append(dim)
                evaluated_components[dim] = {
                    "score": None,
                    "weight": weight,
                    "status": "UNAVAILABLE",
                    "raw_value": None,
                    "contribution": 0.0,
                    "explainability": f"Metric {dim} is unavailable due to missing input data"
                }

        # Step 5: Score Aggregation
        overall_score = 0.0
        if active_weights_sum > 1e-6:
            for dim, item in evaluated_components.items():
                if item["status"] != "UNAVAILABLE" and item["score"] is not None:
                    # Dynamically scaled weight
                    effective_weight = item["weight"] / active_weights_sum
                    contribution = item["score"] * effective_weight
                    item["contribution"] = round(contribution, 2)
                    overall_score += contribution
        else:
            overall_score = 0.0
            quality_gate_passed = False
            quality_warning = "All required scoring metrics are unavailable"

        overall_score = max(0.0, min(100.0, overall_score))

        # Step 6: Score Band Mapping
        category_label = self._map_score_band(overall_score)
        if not quality_gate_passed and active_weights_sum <= 1e-6:
            category_label = "Unavailable"

        # Step 7: Score Confidence Calculation
        available_ratio = (len(evaluated_components) - len(missing_metrics)) / max(1, len(evaluated_components))
        score_confidence = (tracking_quality / 100.0) * 0.4 + pose_confidence * 0.3 + available_ratio * 0.3
        score_confidence = max(0.0, min(1.0, score_confidence))

        # Step 8: Hold Scoring (if static hold)
        hold_score = None
        if self._exercise_category == "static_hold" or (self._last_exercise and self._last_exercise.hold_time > 0):
            hold_score = {
                "hold_stability": evaluated_components.get("stability", {}).get("score", 100.0),
                "alignment": evaluated_components.get("symmetry", {}).get("score", 100.0),
                "balance": self._last_biomechanics.balance_score if self._last_biomechanics else 100.0,
                "duration": self._last_exercise.hold_time if self._last_exercise else 0.0,
                "tracking_quality": tracking_quality
            }

        # Step 9: Session Summary Calculation
        session_summary = self._build_session_summary(overall_score)

        # Construct final ScoreReport
        report = ScoreReport(
            overall_score=overall_score,
            score_confidence=score_confidence,
            category=category_label,
            components=evaluated_components,
            exercise_id=self._active_exercise_id,
            exercise_name=self._active_exercise_name,
            rep_scores=list(self._rep_scores),
            hold_score=hold_score,
            session_summary=session_summary,
            missing_metrics=missing_metrics,
            quality_gate_passed=quality_gate_passed,
            quality_warning=quality_warning,
            source=self.name
        )

        self._processing_time_ms = (time.time() - t0) * 1000.0
        self._last_score_report = report

        return report

    def _evaluate_and_publish(self) -> None:
        report = self.evaluate_score()

        if not report.quality_gate_passed and report.quality_warning:
            self.publish("score.quality_warning", {
                "warning": report.quality_warning,
                "tracking_quality": self._last_exercise.tracking_quality if self._last_exercise else 0.0,
                "score_confidence": report.score_confidence
            })

        if report.category == "Unavailable" or len(report.missing_metrics) == len(report.components):
            self.publish("score.unavailable", {
                "missing_metrics": report.missing_metrics,
                "exercise_id": report.exercise_id
            })

        self.publish("score.updated", report.to_dict())

    # ---------------------------------------------------------------------------
    # Helpers & Metric Extractors
    # ---------------------------------------------------------------------------

    def _extract_raw_dimensions(self) -> Dict[str, Optional[float]]:
        """Extracts normalized 0-100 metric values from current engine states."""
        res: Dict[str, Optional[float]] = {}

        # 1. Form Quality
        if self._last_exercise:
            res["form"] = float(self._last_exercise.movement_quality)
        elif self._last_pose:
            res["form"] = float(self._last_pose.confidence * 100.0 if self._last_pose.confidence <= 1.0 else self._last_pose.confidence)
        else:
            res["form"] = None

        # 2. Range of Motion (ROM)
        if self._last_exercise:
            res["rom"] = float(self._last_exercise.rom_percentage)
        else:
            res["rom"] = None

        # 3. Stability
        if self._last_biomechanics:
            res["stability"] = float(self._last_biomechanics.balance_score)
        else:
            res["stability"] = None

        # 4. Symmetry
        if self._last_biomechanics:
            res["symmetry"] = float(self._last_biomechanics.symmetry_score)
        else:
            res["symmetry"] = None

        # 5. Movement Control
        if self._last_exercise:
            # Control derived from rep duration consistency or execution smoothness
            dur = self._last_exercise.current_rep_duration
            avg_dur = self._last_exercise.average_rep_duration
            if avg_dur > 0 and dur > 0:
                dev = abs(dur - avg_dur) / avg_dur
                control_score = max(0.0, 100.0 - (dev * 50.0))
            else:
                control_score = float(self._last_exercise.movement_quality)
            res["control"] = control_score
        else:
            res["control"] = None

        # 6. Tempo / Cadence
        if self._last_exercise and self._last_exercise.current_cadence > 0:
            # Ideal cadence range (e.g. 15-30 rpm for normal exercise)
            cadence = self._last_exercise.current_cadence
            if 10.0 <= cadence <= 40.0:
                tempo_score = 100.0
            else:
                diff = min(abs(cadence - 10.0), abs(cadence - 40.0))
                tempo_score = max(0.0, 100.0 - (diff * 2.5))
            res["tempo"] = tempo_score
        else:
            res["tempo"] = None

        # 7. Consistency
        if len(self._rep_scores) >= 2:
            scores = [r["overall_score"] for r in self._rep_scores]
            mean_score = sum(scores) / len(scores)
            var = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = math.sqrt(var)
            consistency_score = max(0.0, 100.0 - (std_dev * 3.0))
            res["consistency"] = consistency_score
        elif len(self._rep_scores) == 1:
            res["consistency"] = 100.0
        else:
            res["consistency"] = None

        # 8. Tracking Quality
        if self._last_exercise:
            res["tracking_quality"] = float(self._last_exercise.tracking_quality)
        else:
            res["tracking_quality"] = None

        return res

    def _get_metric_status(self, score: float) -> str:
        """Determines metric status label."""
        if score >= 80.0:
            return "GOOD"
        elif score >= 60.0:
            return "WARNING"
        else:
            return "POOR"

    def _map_score_band(self, score: float) -> str:
        """Maps overall numerical score to configured score band label."""
        bands = self.config.get("score_bands", [])
        for band in bands:
            if band["min"] <= score <= band["max"]:
                return band["label"]
        if score >= 90.0:
            return "Excellent"
        elif score >= 75.0:
            return "Good"
        elif score >= 60.0:
            return "Needs Improvement"
        else:
            return "Poor"

    def _build_session_summary(self, current_overall: float) -> Dict[str, Any]:
        """Calculates running session statistics."""
        scores = [r["overall_score"] for r in self._rep_scores]
        if not scores:
            scores = [current_overall]

        avg_score = sum(scores) / len(scores)
        best_rep = max(scores) if scores else current_overall
        worst_rep = min(scores) if scores else current_overall
        
        var = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0.0
        consistency = max(0.0, 100.0 - (math.sqrt(var) * 3.0))
        duration = time.time() - self._session_start_time if self._session_start_time > 0 else 0.0

        return {
            "avg_score": round(avg_score, 1),
            "best_rep_score": round(best_rep, 1),
            "worst_rep_score": round(worst_rep, 1),
            "score_variance": round(var, 2),
            "consistency_score": round(consistency, 1),
            "completed_reps": self._completed_reps_count,
            "invalid_reps": self._invalid_reps_count,
            "duration_seconds": round(duration, 1),
            "exercise_id": self._active_exercise_id,
            "exercise_name": self._active_exercise_name
        }

    # ---------------------------------------------------------------------------
    # Configuration Loading & Validation
    # ---------------------------------------------------------------------------

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """Loads YAML weights configuration."""
        fpath = os.path.normpath(_WEIGHTS_FILE)
        if not os.path.isfile(fpath):
            return None
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[ScoringEngine] Error loading weights file {fpath}: {e}")
            return None

    def _validate_config(self, cfg: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates scoring weights configuration:
        - Weights must sum to 1.0 (tolerance 1e-4)
        - Weights must be non-negative
        - Required keys must be present
        """
        if not isinstance(cfg, dict):
            return False, "Config must be a dictionary"

        # Check default_weights
        def_w = cfg.get("default_weights")
        if isinstance(def_w, dict):
            val_ok, err = self._validate_weight_dict(def_w, "default_weights")
            if not val_ok:
                return False, err

        # Check categories
        cats = cfg.get("categories", {})
        if isinstance(cats, dict):
            for cname, cweights in cats.items():
                if isinstance(cweights, dict):
                    val_ok, err = self._validate_weight_dict(cweights, f"category '{cname}'")
                    if not val_ok:
                        return False, err

        # Check exercises
        exs = cfg.get("exercises", {})
        if isinstance(exs, dict):
            for exid, eweights in exs.items():
                if isinstance(eweights, dict):
                    val_ok, err = self._validate_weight_dict(eweights, f"exercise '{exid}'")
                    if not val_ok:
                        return False, err

        return True, None

    def _validate_weight_dict(self, weights: Dict[str, float], label: str) -> Tuple[bool, Optional[str]]:
        total = 0.0
        for k, v in weights.items():
            if not isinstance(v, (int, float)):
                return False, f"Weight for {k} in {label} must be numeric"
            if v < 0.0:
                return False, f"Weight for {k} in {label} cannot be negative ({v})"
            total += float(v)

        if abs(total - 1.0) > 1e-3:
            return False, f"Weights in {label} must sum to 1.0 (current sum: {total:.4f})"

        return True, None

    # ---------------------------------------------------------------------------
    # Diagnostics & Telemetry
    # ---------------------------------------------------------------------------

    def get_diagnostics(self) -> Dict[str, Any]:
        """Exposes engine diagnostics telemetry."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self._status.value if hasattr(self._status, 'value') else str(self._status),
            "priority": self.priority,
            "dependencies": self.dependencies,
            "config_version": self.config.get("version", "2.0.0"),
            "metrics": {
                "evaluationsCount": self._evaluations_count,
                "sampleCount": self._sample_count,
                "processingTimeMs": round(self._processing_time_ms, 2),
                "activeExerciseId": self._active_exercise_id,
                "activeExerciseName": self._active_exercise_name,
                "exerciseCategory": self._exercise_category,
                "completedReps": self._completed_reps_count,
                "overallScore": round(self._last_score_report.overall_score, 1) if self._last_score_report else 0.0,
                "scoreConfidence": round(self._last_score_report.score_confidence, 2) if self._last_score_report else 1.0,
                "scoreBand": self._last_score_report.category if self._last_score_report else "Standby",
                "missingMetricsCount": len(self._last_score_report.missing_metrics) if self._last_score_report else 0
            }
        }

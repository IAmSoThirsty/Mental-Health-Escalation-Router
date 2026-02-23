"""
Risk Classifier

Classifies distress signals into risk levels and determines escalation requirements.
"""

from enum import Enum
from typing import Dict, Optional
from .inference_engine import InferenceResult


class RiskLevel(Enum):
    """Risk severity levels"""
    CRITICAL = "critical"  # Immediate danger, requires human intervention
    HIGH = "high"  # Serious concern, escalate quickly
    MODERATE = "moderate"  # Needs attention, monitor closely
    LOW = "low"  # Minimal concern
    NONE = "none"  # No risk detected


class RiskAssessment:
    """Result of risk classification"""

    def __init__(
        self,
        risk_level: RiskLevel,
        confidence: float,
        requires_human: bool,
        reasoning: str,
        metadata: Optional[Dict] = None
    ):
        self.risk_level = risk_level
        self.confidence = confidence
        self.requires_human = requires_human
        self.reasoning = reasoning
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return (
            f"RiskAssessment(level={self.risk_level.value}, "
            f"confidence={self.confidence:.3f}, "
            f"requires_human={self.requires_human})"
        )


class RiskClassifier:
    """
    Classifies inference results into risk levels.

    Implements strict rules to ensure critical cases always require human review.
    """

    # Confidence thresholds for risk levels
    CRITICAL_THRESHOLD = 0.7
    HIGH_THRESHOLD = 0.5
    MODERATE_THRESHOLD = 0.3

    def __init__(self, always_human_for_critical: bool = True):
        """
        Initialize risk classifier.

        Args:
            always_human_for_critical: If True, critical risks always require human intervention
        """
        self.always_human_for_critical = always_human_for_critical

    def classify(self, inference_result: InferenceResult) -> RiskAssessment:
        """
        Classify inference result into a risk level.

        Args:
            inference_result: Result from inference engine

        Returns:
            RiskAssessment with risk level and escalation requirements
        """
        distress_signals = inference_result.distress_signals
        confidence = inference_result.confidence

        # Determine risk level based on distress signals
        risk_level = RiskLevel.NONE
        reasoning = "No significant distress signals detected"
        requires_human = False

        if "critical" in distress_signals:
            risk_level = RiskLevel.CRITICAL
            reasoning = "Critical distress signals detected (suicidal ideation or imminent harm)"
            requires_human = self.always_human_for_critical
        elif "high_risk" in distress_signals and confidence >= self.HIGH_THRESHOLD:
            risk_level = RiskLevel.HIGH
            reasoning = "High-risk distress signals detected"
            requires_human = True
        elif confidence >= self.HIGH_THRESHOLD:
            risk_level = RiskLevel.HIGH
            reasoning = "High confidence distress signals detected"
            requires_human = True
        elif confidence >= self.MODERATE_THRESHOLD:
            risk_level = RiskLevel.MODERATE
            reasoning = "Moderate distress signals detected"
            requires_human = False
        elif confidence > 0:
            risk_level = RiskLevel.LOW
            reasoning = "Low-level distress indicators present"
            requires_human = False

        return RiskAssessment(
            risk_level=risk_level,
            confidence=confidence,
            requires_human=requires_human,
            reasoning=reasoning,
            metadata={
                "distress_signals": distress_signals,
                "input_type": inference_result.input_type.value
            }
        )

    def is_critical(self, risk_assessment: RiskAssessment) -> bool:
        """Check if risk level is critical"""
        return risk_assessment.risk_level == RiskLevel.CRITICAL

    def requires_escalation(self, risk_assessment: RiskAssessment) -> bool:
        """Check if risk requires escalation"""
        return risk_assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]

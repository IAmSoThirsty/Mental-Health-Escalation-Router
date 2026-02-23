"""
Mental Health Escalation Router

Real-time detection of high-risk distress signals and safe routing to human resources.
"""

__version__ = "0.1.0"

from .inference_engine import (
    InferenceEngine,
    AudioInferenceEngine,
    TextInferenceEngine,
    InferenceResult,
    InputType,
)
from .risk_classifier import RiskClassifier, RiskLevel, RiskAssessment
from .escalation_policy import EscalationPolicy, EscalationRule
from .routing import (
    GeoAwareRouter,
    HumanResource,
    GeoLocation,
    ResourceStatus,
    RoutingPreferences,
)
from .human_in_loop import (
    HumanInLoopEnforcer,
    HumanReview,
    HumanResponseStatus,
)
from .privacy import PrivacyGuard, PrivacyPolicy, DataSensitivity

__all__ = [
    "InferenceEngine",
    "AudioInferenceEngine",
    "TextInferenceEngine",
    "InferenceResult",
    "InputType",
    "RiskClassifier",
    "RiskLevel",
    "RiskAssessment",
    "EscalationPolicy",
    "EscalationRule",
    "GeoAwareRouter",
    "HumanResource",
    "GeoLocation",
    "ResourceStatus",
    "RoutingPreferences",
    "HumanInLoopEnforcer",
    "HumanReview",
    "HumanResponseStatus",
    "PrivacyGuard",
    "PrivacyPolicy",
    "DataSensitivity",
]

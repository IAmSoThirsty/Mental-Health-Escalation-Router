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
from .security import InputValidator, RateLimiter, AbuseDetector, RequestSigner
from .resilience import (
    CircuitBreaker,
    Bulkhead,
    HealthMonitor,
    GracefulDegradation,
    BackpressureManager,
    MetricsCollector,
)
from .audit import AuditChain, DataRetentionManager, DistributedTracing
from .config import (
    ProductionConfig,
    ConfigManager,
    get_config,
    get_config_manager,
    Environment,
)

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
    "InputValidator",
    "RateLimiter",
    "AbuseDetector",
    "RequestSigner",
    "CircuitBreaker",
    "Bulkhead",
    "HealthMonitor",
    "GracefulDegradation",
    "BackpressureManager",
    "MetricsCollector",
    "AuditChain",
    "DataRetentionManager",
    "DistributedTracing",
    "ProductionConfig",
    "ConfigManager",
    "get_config",
    "get_config_manager",
    "Environment",
]

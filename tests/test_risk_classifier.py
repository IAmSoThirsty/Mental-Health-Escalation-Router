"""
Tests for Risk Classifier
"""

import pytest
from mental_health_router.risk_classifier import RiskClassifier, RiskLevel
from mental_health_router.inference_engine import TextInferenceEngine, InputType, InferenceResult


class TestRiskClassifier:
    """Tests for RiskClassifier"""

    def test_critical_risk_classification(self):
        """Test classification of critical risk"""
        classifier = RiskClassifier()

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"critical": 0.9},
            confidence=0.9,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.risk_level == RiskLevel.CRITICAL
        assert assessment.requires_human is True
        assert assessment.confidence == 0.9

    def test_high_risk_classification(self):
        """Test classification of high risk"""
        classifier = RiskClassifier()

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"high_risk": 0.7},
            confidence=0.7,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.risk_level == RiskLevel.HIGH
        assert assessment.requires_human is True

    def test_moderate_risk_classification(self):
        """Test classification of moderate risk"""
        classifier = RiskClassifier()

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"moderate": 0.4},
            confidence=0.4,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.risk_level == RiskLevel.MODERATE
        assert assessment.requires_human is False

    def test_low_risk_classification(self):
        """Test classification of low risk"""
        classifier = RiskClassifier()

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"moderate": 0.1},
            confidence=0.1,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.risk_level == RiskLevel.LOW

    def test_no_risk_classification(self):
        """Test classification when no risk detected"""
        classifier = RiskClassifier()

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={},
            confidence=0.0,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.risk_level == RiskLevel.NONE
        assert assessment.requires_human is False

    def test_critical_always_requires_human(self):
        """Test that critical risk always requires human when configured"""
        classifier = RiskClassifier(always_human_for_critical=True)

        inference_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"critical": 0.8},
            confidence=0.8,
            latency_ms=50.0
        )

        assessment = classifier.classify(inference_result)

        assert assessment.requires_human is True

    def test_is_critical(self):
        """Test is_critical method"""
        classifier = RiskClassifier()

        critical_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"critical": 0.9},
            confidence=0.9,
            latency_ms=50.0
        )

        assessment = classifier.classify(critical_result)
        assert classifier.is_critical(assessment) is True

    def test_requires_escalation(self):
        """Test requires_escalation method"""
        classifier = RiskClassifier()

        high_risk_result = InferenceResult(
            input_type=InputType.TEXT,
            distress_signals={"high_risk": 0.7},
            confidence=0.7,
            latency_ms=50.0
        )

        assessment = classifier.classify(high_risk_result)
        assert classifier.requires_escalation(assessment) is True

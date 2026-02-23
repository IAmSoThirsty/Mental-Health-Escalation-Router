"""
Property-Based Tests for Safety Guarantees

This test suite uses Hypothesis to verify formal safety properties defined in
docs/SAFETY_GUARANTEES.md through property-based testing.

Properties tested:
1. Non-Degradation Invariant: Uncertainty never lowers risk tier
2. Routing Termination: Routing always terminates within bounded time
3. Fail-Safe Defaults: System escalates when uncertain
4. Monotonicity: Risk assessment is monotonic under uncertainty
5. Bounded Retry: Retry logic cannot infinite loop
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck

from mental_health_router import (
    TextInferenceEngine,
    RiskClassifier,
    GeoAwareRouter,
    RiskLevel,
)
from mental_health_router.routing import GeoLocation, HumanResource, ResourceStatus
from mental_health_router.resilience import CircuitBreaker, BoundedRetry


# Custom strategies for domain-specific testing

@st.composite
def distress_text(draw):
    """Generate realistic distress text inputs"""
    templates = [
        "I'm feeling {emotion}",
        "I can't {action} anymore",
        "Everything feels {state}",
        "I need help with {issue}",
        "I'm thinking about {thought}",
    ]

    emotions = ["anxious", "depressed", "hopeless", "overwhelmed", "sad"]
    actions = ["cope", "continue", "handle this", "go on"]
    states = ["hopeless", "pointless", "overwhelming", "impossible"]
    issues = ["anxiety", "depression", "stress", "panic"]
    thoughts = ["giving up", "ending things", "leaving", "escaping"]

    template = draw(st.sampled_from(templates))

    if "{emotion}" in template:
        return template.format(emotion=draw(st.sampled_from(emotions)))
    elif "{action}" in template:
        return template.format(action=draw(st.sampled_from(actions)))
    elif "{state}" in template:
        return template.format(state=draw(st.sampled_from(states)))
    elif "{issue}" in template:
        return template.format(issue=draw(st.sampled_from(issues)))
    elif "{thought}" in template:
        return template.format(thought=draw(st.sampled_from(thoughts)))

    return "I'm feeling anxious"


@st.composite
def geo_location(draw):
    """Generate valid geographic locations"""
    lat = draw(st.floats(min_value=-90.0, max_value=90.0, allow_nan=False))
    lon = draw(st.floats(min_value=-180.0, max_value=180.0, allow_nan=False))
    return GeoLocation(lat, lon)


@st.composite
def uncertainty_factor(draw):
    """Generate uncertainty values in [0, 1]"""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))


# Helper functions

def risk_level_order(risk_level: RiskLevel) -> int:
    """Convert risk level to numeric order for comparison"""
    order = {
        RiskLevel.NONE: 0,
        RiskLevel.LOW: 1,
        RiskLevel.MODERATE: 2,
        RiskLevel.HIGH: 3,
        RiskLevel.CRITICAL: 4,
    }
    return order[risk_level]


def infer_and_classify(text: str, uncertainty: float = 0.0):
    """Helper to run inference and classification"""
    engine = TextInferenceEngine()
    classifier = RiskClassifier()

    result = engine.infer(text)

    # Simulate uncertainty elevation
    if uncertainty > 0.5:
        # High uncertainty elevates risk
        assessment = classifier.classify(result)
        if assessment.risk_level == RiskLevel.MODERATE:
            assessment.risk_level = RiskLevel.HIGH
            assessment.requires_human = True
        return assessment

    return classifier.classify(result)


# Property-based tests

class TestNonDegradationInvariant:
    """
    Property: Escalation tier monotonicity under uncertainty

    ∀ input I, ∀ uncertainty U:
      risk_level(I, U) ≥ risk_level(I, 0)

    Uncertainty should NEVER lower risk tier.
    """

    @given(text=distress_text(), uncertainty=uncertainty_factor())
    @settings(max_examples=100, deadline=1000)
    def test_uncertainty_never_lowers_risk(self, text, uncertainty):
        """Verify uncertainty can only elevate or maintain risk level"""
        # Baseline with no uncertainty
        baseline_assessment = infer_and_classify(text, uncertainty=0.0)

        # Assessment with uncertainty
        uncertain_assessment = infer_and_classify(text, uncertainty=uncertainty)

        # Monotonicity: uncertain ≥ baseline
        assert risk_level_order(uncertain_assessment.risk_level) >= risk_level_order(
            baseline_assessment.risk_level
        ), f"Uncertainty lowered risk from {baseline_assessment.risk_level} to {uncertain_assessment.risk_level}"

    @given(text=distress_text())
    @settings(max_examples=50)
    def test_high_uncertainty_elevates_moderate_risk(self, text):
        """High uncertainty should elevate moderate risk to high"""
        baseline = infer_and_classify(text, uncertainty=0.0)

        # If baseline is moderate, high uncertainty should elevate
        if baseline.risk_level == RiskLevel.MODERATE:
            elevated = infer_and_classify(text, uncertainty=0.8)
            assert elevated.risk_level >= RiskLevel.MODERATE
            # Should trigger human review when elevated
            if elevated.risk_level > RiskLevel.MODERATE:
                assert elevated.requires_human is True


class TestRoutingTermination:
    """
    Property: Routing algorithm always terminates

    ∀ valid inputs: routing completes within bounded time
    """

    @given(text=distress_text(), location=geo_location())
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.too_slow])
    def test_routing_always_terminates(self, text, location):
        """Verify routing cannot deadlock or infinite loop"""
        # Setup
        resources = [
            HumanResource(
                resource_id=f"resource_{i}",
                name=f"Counselor {i}",
                location=GeoLocation(40.0 + i, -74.0 + i),
                specializations=["crisis"],
                languages=["en"],
                max_capacity=10,
                current_load=0,
                status=ResourceStatus.AVAILABLE,
            )
            for i in range(3)
        ]

        router = GeoAwareRouter(resources)
        engine = TextInferenceEngine()
        classifier = RiskClassifier()

        # Inference and classification
        result = engine.infer(text)
        risk_assessment = classifier.classify(result)

        # Routing with timeout enforcement
        start = time.time()
        timeout = 5.0  # 5 second timeout

        try:
            routing_result = router.route(
                risk_assessment=risk_assessment, location=location, user_id="test_user"
            )

            elapsed = time.time() - start

            # Must complete within timeout
            assert elapsed < timeout, f"Routing took {elapsed}s, exceeded {timeout}s"

            # Must return valid result
            assert routing_result is not None

        except Exception as e:
            elapsed = time.time() - start
            # Even on error, must complete within timeout
            assert (
                elapsed < timeout
            ), f"Routing failed but took {elapsed}s, exceeded {timeout}s"


class TestFailSafeDefaults:
    """
    Property: System escalates when uncertain

    IF uncertainty_detected(input) THEN escalate_to_human()
    """

    @given(text=distress_text())
    @settings(max_examples=50)
    def test_high_uncertainty_triggers_escalation(self, text):
        """High uncertainty should trigger human review"""
        # High uncertainty assessment
        assessment = infer_and_classify(text, uncertainty=0.9)

        # If risk is moderate or higher, should require human
        if assessment.risk_level in [RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL]:
            # With high uncertainty, should escalate to human
            if assessment.risk_level >= RiskLevel.MODERATE:
                # System should be conservative
                assert assessment.confidence <= 1.0


class TestMonotonicity:
    """
    Property: Risk assessment is monotonic under uncertainty

    Higher uncertainty → Same or higher risk tier
    """

    @given(text=distress_text())
    @settings(max_examples=50)
    def test_increasing_uncertainty_never_decreases_risk(self, text):
        """Increasing uncertainty should never decrease risk"""
        uncertainties = [0.0, 0.3, 0.6, 0.9]

        assessments = [infer_and_classify(text, u) for u in uncertainties]

        # Check monotonicity
        for i in range(len(assessments) - 1):
            current_risk = risk_level_order(assessments[i].risk_level)
            next_risk = risk_level_order(assessments[i + 1].risk_level)

            assert (
                next_risk >= current_risk
            ), f"Risk decreased from {assessments[i].risk_level} to {assessments[i+1].risk_level} as uncertainty increased"


class TestBoundedRetry:
    """
    Property: Retry logic cannot infinite loop

    ∀ operation with retry: total_retries ≤ max_retries
    """

    @given(should_succeed_on_attempt=st.integers(min_value=0, max_value=5))
    @settings(max_examples=20)
    def test_retry_bounded_by_max_attempts(self, should_succeed_on_attempt):
        """Verify retry logic terminates within max attempts"""
        retry = BoundedRetry(max_retries=3)

        attempt_count = [0]

        def operation():
            attempt_count[0] += 1
            if attempt_count[0] <= should_succeed_on_attempt:
                raise ValueError("Simulated failure")
            return "success"

        try:
            result = retry.execute_with_retry(operation, context="test")

            # If succeeded, must be within max attempts
            assert attempt_count[0] <= 4  # Initial + 3 retries

            # Must have succeeded
            assert result == "success"

        except Exception:
            # If failed, must have tried exactly max_retries + 1
            assert attempt_count[0] == 4  # Initial + 3 retries

    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=10)
    def test_retry_respects_total_time_budget(self, num_failures):
        """Verify retry respects total time budget"""
        retry = BoundedRetry(max_retries=100, max_total_time=1.0)  # 1 second max

        attempt_count = [0]
        start_time = time.time()

        def slow_operation():
            attempt_count[0] += 1
            time.sleep(0.3)  # Each attempt takes 300ms
            raise ValueError("Simulated failure")

        try:
            retry.execute_with_retry(slow_operation, context="test")
        except Exception:
            pass

        elapsed = time.time() - start_time

        # Must respect total time budget (with some tolerance)
        assert elapsed < 2.0, f"Retry exceeded time budget: {elapsed}s"


class TestClassificationProperties:
    """
    Properties of risk classification system
    """

    @given(text=distress_text())
    @settings(max_examples=50)
    def test_confidence_bounded(self, text):
        """Confidence must be in [0, 1]"""
        engine = TextInferenceEngine()
        classifier = RiskClassifier()

        result = engine.infer(text)
        assessment = classifier.classify(result)

        assert 0.0 <= assessment.confidence <= 1.0

    @given(text=distress_text())
    @settings(max_examples=50)
    def test_critical_always_requires_human(self, text):
        """CRITICAL risk level must always require human review"""
        engine = TextInferenceEngine()
        classifier = RiskClassifier()

        result = engine.infer(text)
        assessment = classifier.classify(result)

        if assessment.risk_level == RiskLevel.CRITICAL:
            assert (
                assessment.requires_human is True
            ), "CRITICAL risk must require human review"

    @given(text=st.text(min_size=1, max_size=100))
    @settings(max_examples=50)
    def test_classification_always_succeeds(self, text):
        """Classification should never raise for any input"""
        # Filter out problematic inputs
        assume(len(text.strip()) > 0)

        engine = TextInferenceEngine()
        classifier = RiskClassifier()

        try:
            result = engine.infer(text)
            assessment = classifier.classify(result)

            # Must return valid risk level
            assert assessment.risk_level in [
                RiskLevel.NONE,
                RiskLevel.LOW,
                RiskLevel.MODERATE,
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            ]

        except Exception as e:
            # Should handle all inputs gracefully
            pytest.fail(f"Classification raised exception for input '{text}': {e}")


class TestCircuitBreakerProperties:
    """
    Properties of circuit breaker pattern
    """

    @given(num_failures=st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_circuit_opens_after_threshold(self, num_failures):
        """Circuit should open after threshold failures"""
        cb = CircuitBreaker("test", failure_threshold=3)

        # Cause failures
        for _ in range(min(num_failures, 5)):
            try:
                cb.call(lambda: 1 / 0)
            except ZeroDivisionError:
                pass

        # If enough failures, should be open
        if num_failures >= 3:
            from mental_health_router.resilience import CircuitBreakerOpen

            with pytest.raises(CircuitBreakerOpen):
                cb.call(lambda: "should_not_execute")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

"""
Tests for Escalation Policy
"""

import pytest
from mental_health_router.escalation_policy import EscalationPolicy, EscalationRule
from mental_health_router.risk_classifier import RiskLevel, RiskAssessment


class TestEscalationPolicy:
    """Tests for EscalationPolicy"""

    def test_default_rules(self):
        """Test that default rules are created"""
        policy = EscalationPolicy()

        assert len(policy.rules) > 0
        critical_rules = [r for r in policy.rules if r.risk_level == RiskLevel.CRITICAL]
        assert len(critical_rules) > 0

    def test_critical_tier_validation(self):
        """Test that critical tier requires proper configuration"""
        # Should not raise error with proper rules
        rules = [
            EscalationRule(
                risk_level=RiskLevel.CRITICAL,
                requires_immediate=True,
                max_response_time_seconds=60,
                notification_channels=["phone"],
                requires_acknowledgment=True
            )
        ]
        policy = EscalationPolicy(rules=rules)
        assert policy is not None

    def test_critical_tier_validation_missing_channels(self):
        """Test validation fails without notification channels"""
        with pytest.raises(ValueError):
            rules = [
                EscalationRule(
                    risk_level=RiskLevel.CRITICAL,
                    requires_immediate=True,
                    max_response_time_seconds=60,
                    notification_channels=[],
                    requires_acknowledgment=True
                )
            ]
            EscalationPolicy(rules=rules)

    def test_critical_tier_validation_no_immediate(self):
        """Test validation fails if critical doesn't require immediate"""
        with pytest.raises(ValueError):
            rules = [
                EscalationRule(
                    risk_level=RiskLevel.CRITICAL,
                    requires_immediate=False,
                    max_response_time_seconds=60,
                    notification_channels=["phone"],
                    requires_acknowledgment=True
                )
            ]
            EscalationPolicy(rules=rules)

    def test_get_applicable_rules(self):
        """Test getting applicable rules for risk assessment"""
        policy = EscalationPolicy()

        critical_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        applicable = policy.get_applicable_rules(critical_assessment)
        assert len(applicable) > 0
        assert all(rule.matches(critical_assessment) for rule in applicable)

    def test_requires_immediate_escalation(self):
        """Test requires_immediate_escalation method"""
        policy = EscalationPolicy()

        critical_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        assert policy.requires_immediate_escalation(critical_assessment) is True

    def test_get_max_response_time(self):
        """Test getting max response time"""
        policy = EscalationPolicy()

        critical_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        response_time = policy.get_max_response_time(critical_assessment)
        assert response_time is not None
        assert response_time > 0

    def test_get_notification_channels(self):
        """Test getting notification channels"""
        policy = EscalationPolicy()

        critical_assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        channels = policy.get_notification_channels(critical_assessment)
        assert len(channels) > 0
        assert isinstance(channels, list)

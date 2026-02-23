"""
Escalation Policy Engine

Defines and enforces escalation rules based on risk levels and context.
Never fully autonomous in critical tier.
"""

from typing import List, Optional, Dict, Callable
from dataclasses import dataclass
from .risk_classifier import RiskLevel, RiskAssessment


@dataclass
class EscalationRule:
    """
    Defines an escalation rule.

    Attributes:
        risk_level: Minimum risk level to trigger this rule
        requires_immediate: Whether this requires immediate escalation
        max_response_time_seconds: Maximum time before human must respond
        notification_channels: Channels to notify (e.g., SMS, email, phone)
        requires_acknowledgment: Whether human acknowledgment is required
    """
    risk_level: RiskLevel
    requires_immediate: bool
    max_response_time_seconds: int
    notification_channels: List[str]
    requires_acknowledgment: bool = True

    def matches(self, risk_assessment: RiskAssessment) -> bool:
        """Check if this rule applies to the given risk assessment"""
        # Map risk levels to numeric values for comparison
        level_priority = {
            RiskLevel.NONE: 0,
            RiskLevel.LOW: 1,
            RiskLevel.MODERATE: 2,
            RiskLevel.HIGH: 3,
            RiskLevel.CRITICAL: 4
        }
        return level_priority[risk_assessment.risk_level] >= level_priority[self.risk_level]


class EscalationPolicy:
    """
    Manages escalation rules and enforces escalation policies.

    Ensures critical tier is never fully autonomous.
    """

    def __init__(self, rules: Optional[List[EscalationRule]] = None):
        """
        Initialize escalation policy.

        Args:
            rules: List of escalation rules (uses defaults if None)
        """
        self.rules = rules or self._default_rules()
        self._validate_critical_tier_policy()

    def _default_rules(self) -> List[EscalationRule]:
        """Default escalation rules ensuring human-in-the-loop for critical cases"""
        return [
            EscalationRule(
                risk_level=RiskLevel.CRITICAL,
                requires_immediate=True,
                max_response_time_seconds=60,  # 1 minute
                notification_channels=["phone", "sms", "email", "push"],
                requires_acknowledgment=True
            ),
            EscalationRule(
                risk_level=RiskLevel.HIGH,
                requires_immediate=True,
                max_response_time_seconds=300,  # 5 minutes
                notification_channels=["sms", "email", "push"],
                requires_acknowledgment=True
            ),
            EscalationRule(
                risk_level=RiskLevel.MODERATE,
                requires_immediate=False,
                max_response_time_seconds=1800,  # 30 minutes
                notification_channels=["email", "push"],
                requires_acknowledgment=False
            ),
        ]

    def _validate_critical_tier_policy(self) -> None:
        """
        Validate that critical tier has proper human-in-the-loop enforcement.

        Raises:
            ValueError: If critical tier policy is not properly configured
        """
        critical_rules = [r for r in self.rules if r.risk_level == RiskLevel.CRITICAL]

        if not critical_rules:
            raise ValueError("Critical tier must have at least one escalation rule")

        for rule in critical_rules:
            if not rule.requires_immediate:
                raise ValueError("Critical tier must require immediate escalation")
            if not rule.requires_acknowledgment:
                raise ValueError("Critical tier must require human acknowledgment")
            if not rule.notification_channels:
                raise ValueError("Critical tier must have notification channels")

    def get_applicable_rules(self, risk_assessment: RiskAssessment) -> List[EscalationRule]:
        """
        Get all escalation rules applicable to the risk assessment.

        Args:
            risk_assessment: Risk assessment result

        Returns:
            List of applicable escalation rules, sorted by priority
        """
        applicable = [rule for rule in self.rules if rule.matches(risk_assessment)]

        # Sort by priority: immediate first, then by max response time
        applicable.sort(key=lambda r: (not r.requires_immediate, r.max_response_time_seconds))

        return applicable

    def requires_immediate_escalation(self, risk_assessment: RiskAssessment) -> bool:
        """Check if risk assessment requires immediate escalation"""
        rules = self.get_applicable_rules(risk_assessment)
        return any(rule.requires_immediate for rule in rules)

    def get_max_response_time(self, risk_assessment: RiskAssessment) -> Optional[int]:
        """
        Get maximum response time in seconds for the risk assessment.

        Returns:
            Maximum response time in seconds, or None if no rules apply
        """
        rules = self.get_applicable_rules(risk_assessment)
        if not rules:
            return None
        return min(rule.max_response_time_seconds for rule in rules)

    def get_notification_channels(self, risk_assessment: RiskAssessment) -> List[str]:
        """Get all notification channels for the risk assessment"""
        rules = self.get_applicable_rules(risk_assessment)
        channels = set()
        for rule in rules:
            channels.update(rule.notification_channels)
        return list(channels)

    def add_rule(self, rule: EscalationRule) -> None:
        """
        Add a new escalation rule.

        Args:
            rule: Escalation rule to add
        """
        self.rules.append(rule)
        if rule.risk_level == RiskLevel.CRITICAL:
            self._validate_critical_tier_policy()

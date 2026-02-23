"""
Tests for Human-in-the-Loop Enforcer
"""

import pytest
from datetime import datetime
from mental_health_router.human_in_loop import (
    HumanInLoopEnforcer,
    HumanReview,
    HumanResponseStatus
)
from mental_health_router.risk_classifier import RiskLevel, RiskAssessment


class TestHumanInLoopEnforcer:
    """Tests for HumanInLoopEnforcer"""

    def test_requires_human_review_for_critical(self):
        """Test that critical risk requires human review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        assert enforcer.requires_human_review(assessment) is True

    def test_requires_human_review_for_high(self):
        """Test that high risk requires human review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.HIGH,
            confidence=0.7,
            requires_human=True,
            reasoning="Test"
        )

        assert enforcer.requires_human_review(assessment) is True

    def test_no_review_required_for_low_risk(self):
        """Test that low risk doesn't require review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.LOW,
            confidence=0.2,
            requires_human=False,
            reasoning="Test"
        )

        assert enforcer.requires_human_review(assessment) is False

    def test_request_review(self):
        """Test requesting a review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review_id = enforcer.request_review(assessment)

        assert review_id is not None
        assert review_id in enforcer.pending_reviews

    def test_get_review(self):
        """Test getting a review by ID"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review_id = enforcer.request_review(assessment)
        review = enforcer.get_review(review_id)

        assert review is not None
        assert review.status == HumanResponseStatus.PENDING

    def test_acknowledge_review(self):
        """Test acknowledging a review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review_id = enforcer.request_review(assessment)
        success = enforcer.acknowledge_review(review_id, "reviewer_123")

        assert success is True

        review = enforcer.get_review(review_id)
        assert review.status == HumanResponseStatus.ACKNOWLEDGED
        assert review.reviewer_id == "reviewer_123"

    def test_complete_review(self):
        """Test completing a review"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review_id = enforcer.request_review(assessment)
        enforcer.acknowledge_review(review_id, "reviewer_123")
        success = enforcer.complete_review(review_id, "Contacted emergency services", "Notes")

        assert success is True

        review = enforcer.get_review(review_id)
        assert review.status == HumanResponseStatus.COMPLETED
        assert review.action_taken == "Contacted emergency services"

    def test_get_pending_reviews(self):
        """Test getting pending reviews"""
        enforcer = HumanInLoopEnforcer()

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review_id1 = enforcer.request_review(assessment)
        review_id2 = enforcer.request_review(assessment)

        enforcer.complete_review(review_id1, "Action taken")

        pending = enforcer.get_pending_reviews()

        assert review_id1 not in pending
        assert review_id2 in pending


class TestHumanReview:
    """Tests for HumanReview"""

    def test_is_timeout(self):
        """Test timeout detection"""
        import time

        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review = HumanReview(
            risk_assessment=assessment,
            request_time=datetime.now(),
            timeout_seconds=1
        )

        # Should not timeout immediately
        assert review.is_timeout() is False

        # Wait for timeout
        time.sleep(1.1)
        assert review.is_timeout() is True

    def test_acknowledge(self):
        """Test acknowledging a review"""
        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review = HumanReview(
            risk_assessment=assessment,
            request_time=datetime.now(),
            timeout_seconds=60
        )

        review.acknowledge("reviewer_123")

        assert review.status == HumanResponseStatus.ACKNOWLEDGED
        assert review.reviewer_id == "reviewer_123"
        assert review.response_time is not None

    def test_complete(self):
        """Test completing a review"""
        assessment = RiskAssessment(
            risk_level=RiskLevel.CRITICAL,
            confidence=0.9,
            requires_human=True,
            reasoning="Test"
        )

        review = HumanReview(
            risk_assessment=assessment,
            request_time=datetime.now(),
            timeout_seconds=60
        )

        review.complete("Action taken", "Notes")

        assert review.status == HumanResponseStatus.COMPLETED
        assert review.action_taken == "Action taken"
        assert review.reviewer_notes == "Notes"

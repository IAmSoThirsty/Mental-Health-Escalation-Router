"""
Human-in-the-Loop Enforcer

Ensures critical decisions are never made autonomously and require human confirmation.
"""

from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from .risk_classifier import RiskAssessment, RiskLevel


class HumanResponseStatus(Enum):
    """Status of human response"""
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    COMPLETED = "completed"
    TIMEOUT = "timeout"


class HumanReview:
    """Represents a human review request and response"""

    def __init__(
        self,
        risk_assessment: RiskAssessment,
        request_time: datetime,
        timeout_seconds: int,
        context: Optional[Dict[str, Any]] = None
    ):
        self.risk_assessment = risk_assessment
        self.request_time = request_time
        self.timeout_seconds = timeout_seconds
        self.context = context or {}
        self.status = HumanResponseStatus.PENDING
        self.response_time: Optional[datetime] = None
        self.reviewer_id: Optional[str] = None
        self.reviewer_notes: Optional[str] = None
        self.action_taken: Optional[str] = None

    def is_timeout(self) -> bool:
        """Check if review has timed out"""
        if self.status != HumanResponseStatus.PENDING:
            return False
        elapsed = datetime.now() - self.request_time
        return elapsed.total_seconds() > self.timeout_seconds

    def acknowledge(self, reviewer_id: str) -> None:
        """Acknowledge receipt of review request"""
        if self.status == HumanResponseStatus.PENDING:
            self.status = HumanResponseStatus.ACKNOWLEDGED
            self.reviewer_id = reviewer_id
            self.response_time = datetime.now()

    def complete(self, action_taken: str, notes: Optional[str] = None) -> None:
        """Complete the review"""
        if self.status in [HumanResponseStatus.PENDING, HumanResponseStatus.ACKNOWLEDGED]:
            self.status = HumanResponseStatus.COMPLETED
            self.action_taken = action_taken
            self.reviewer_notes = notes
            if self.response_time is None:
                self.response_time = datetime.now()

    def mark_timeout(self) -> None:
        """Mark review as timed out"""
        if self.status == HumanResponseStatus.PENDING:
            self.status = HumanResponseStatus.TIMEOUT


class HumanInLoopEnforcer:
    """
    Enforces human-in-the-loop requirements for critical decisions.

    Ensures that critical tier cases are never handled autonomously.
    """

    def __init__(self, critical_timeout_seconds: int = 60):
        """
        Initialize enforcer.

        Args:
            critical_timeout_seconds: Timeout for critical reviews
        """
        self.critical_timeout_seconds = critical_timeout_seconds
        self.pending_reviews: Dict[str, HumanReview] = {}
        self._review_counter = 0

    def requires_human_review(self, risk_assessment: RiskAssessment) -> bool:
        """
        Check if risk assessment requires human review.

        Args:
            risk_assessment: Risk assessment to check

        Returns:
            True if human review is required
        """
        # Always require human review for critical and high-risk cases
        return risk_assessment.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]

    def request_review(
        self,
        risk_assessment: RiskAssessment,
        timeout_seconds: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Request human review for a risk assessment.

        Args:
            risk_assessment: Risk assessment requiring review
            timeout_seconds: Timeout for review (uses default if None)
            context: Additional context for the review

        Returns:
            Review ID for tracking

        Raises:
            ValueError: If review is requested for non-critical case without justification
        """
        if risk_assessment.risk_level == RiskLevel.CRITICAL:
            timeout = self.critical_timeout_seconds
        else:
            timeout = timeout_seconds or 300  # 5 minutes default for non-critical

        self._review_counter += 1
        review_id = f"review_{self._review_counter}_{datetime.now().timestamp()}"

        review = HumanReview(
            risk_assessment=risk_assessment,
            request_time=datetime.now(),
            timeout_seconds=timeout,
            context=context
        )

        self.pending_reviews[review_id] = review
        return review_id

    def get_review(self, review_id: str) -> Optional[HumanReview]:
        """Get review by ID"""
        return self.pending_reviews.get(review_id)

    def acknowledge_review(self, review_id: str, reviewer_id: str) -> bool:
        """
        Acknowledge a review request.

        Args:
            review_id: Review ID
            reviewer_id: ID of the reviewer

        Returns:
            True if acknowledged successfully
        """
        review = self.pending_reviews.get(review_id)
        if review and review.status == HumanResponseStatus.PENDING:
            review.acknowledge(reviewer_id)
            return True
        return False

    def complete_review(
        self,
        review_id: str,
        action_taken: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Complete a review.

        Args:
            review_id: Review ID
            action_taken: Description of action taken
            notes: Optional reviewer notes

        Returns:
            True if completed successfully
        """
        review = self.pending_reviews.get(review_id)
        if review:
            review.complete(action_taken, notes)
            return True
        return False

    def check_timeouts(self) -> list[str]:
        """
        Check for timed-out reviews and mark them.

        Returns:
            List of review IDs that have timed out
        """
        timed_out = []
        for review_id, review in self.pending_reviews.items():
            if review.is_timeout():
                review.mark_timeout()
                timed_out.append(review_id)
        return timed_out

    def get_pending_reviews(self) -> Dict[str, HumanReview]:
        """Get all pending reviews"""
        return {
            rid: review for rid, review in self.pending_reviews.items()
            if review.status == HumanResponseStatus.PENDING
        }

    def block_until_reviewed(
        self,
        review_id: str,
        check_interval_seconds: float = 1.0,
        on_timeout: Optional[Callable[[], None]] = None
    ) -> HumanReview:
        """
        Block execution until review is completed or times out.

        Args:
            review_id: Review ID to wait for
            check_interval_seconds: How often to check status
            on_timeout: Optional callback to invoke on timeout

        Returns:
            Completed or timed-out review

        Raises:
            ValueError: If review ID not found
        """
        import time

        review = self.pending_reviews.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")

        while review.status in [HumanResponseStatus.PENDING, HumanResponseStatus.ACKNOWLEDGED]:
            time.sleep(check_interval_seconds)

            if review.is_timeout():
                review.mark_timeout()
                if on_timeout:
                    on_timeout()
                break

        return review

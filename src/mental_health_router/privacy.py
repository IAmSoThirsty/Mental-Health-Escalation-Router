"""
Privacy Safeguards

Implements privacy-preserving measures for sensitive data handling.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import re


class DataSensitivity(Enum):
    """Data sensitivity levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"  # PHI, PII


@dataclass
class PrivacyPolicy:
    """Privacy policy configuration"""
    anonymize_pii: bool = True
    encrypt_at_rest: bool = True
    encrypt_in_transit: bool = True
    retention_days: int = 90
    audit_access: bool = True
    minimum_sensitivity: DataSensitivity = DataSensitivity.CONFIDENTIAL


class PrivacyGuard:
    """
    Implements privacy safeguards for handling sensitive mental health data.

    Ensures PII/PHI protection and compliance with privacy regulations.
    """

    # Patterns for detecting PII
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

    def __init__(self, policy: Optional[PrivacyPolicy] = None):
        """
        Initialize privacy guard.

        Args:
            policy: Privacy policy configuration
        """
        self.policy = policy or PrivacyPolicy()
        self._access_log: List[Dict[str, Any]] = []

    def anonymize_text(self, text: str) -> str:
        """
        Anonymize PII in text.

        Args:
            text: Text potentially containing PII

        Returns:
            Anonymized text with PII redacted
        """
        if not self.policy.anonymize_pii:
            return text

        anonymized = text

        # Redact email addresses
        anonymized = self.EMAIL_PATTERN.sub('[EMAIL]', anonymized)

        # Redact phone numbers
        anonymized = self.PHONE_PATTERN.sub('[PHONE]', anonymized)

        # Redact SSN
        anonymized = self.SSN_PATTERN.sub('[SSN]', anonymized)

        return anonymized

    def hash_identifier(self, identifier: str, salt: Optional[str] = None) -> str:
        """
        Create privacy-preserving hash of identifier.

        Args:
            identifier: Identifier to hash (e.g., user ID)
            salt: Optional salt for hashing

        Returns:
            Hashed identifier
        """
        if salt:
            identifier = f"{identifier}:{salt}"

        return hashlib.sha256(identifier.encode()).hexdigest()

    def create_anonymized_record(
        self,
        data: Dict[str, Any],
        sensitive_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Create anonymized version of a data record.

        Args:
            data: Original data record
            sensitive_fields: Fields to anonymize

        Returns:
            Anonymized record
        """
        anonymized = data.copy()

        for field in sensitive_fields:
            if field in anonymized:
                if isinstance(anonymized[field], str):
                    anonymized[field] = self.hash_identifier(anonymized[field])
                else:
                    anonymized[field] = "[REDACTED]"

        return anonymized

    def log_access(
        self,
        user_id: str,
        resource_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log access to sensitive data.

        Args:
            user_id: ID of user accessing data
            resource_id: ID of resource being accessed
            action: Action being performed
            metadata: Additional metadata
        """
        if not self.policy.audit_access:
            return

        from datetime import datetime

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": self.hash_identifier(user_id),
            "resource_id": self.hash_identifier(resource_id),
            "action": action,
            "metadata": metadata or {}
        }

        self._access_log.append(log_entry)

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get access log"""
        return self._access_log.copy()

    def validate_data_handling(self, data_type: str, sensitivity: DataSensitivity) -> bool:
        """
        Validate if data handling meets policy requirements.

        Args:
            data_type: Type of data being handled
            sensitivity: Sensitivity level of data

        Returns:
            True if handling meets policy requirements
        """
        # Map sensitivity to numeric values
        sensitivity_levels = {
            DataSensitivity.PUBLIC: 0,
            DataSensitivity.INTERNAL: 1,
            DataSensitivity.CONFIDENTIAL: 2,
            DataSensitivity.RESTRICTED: 3
        }

        required_level = sensitivity_levels[self.policy.minimum_sensitivity]
        actual_level = sensitivity_levels[sensitivity]

        return actual_level >= required_level

    def should_encrypt(self, sensitivity: DataSensitivity) -> bool:
        """Check if data should be encrypted based on sensitivity"""
        return sensitivity in [DataSensitivity.CONFIDENTIAL, DataSensitivity.RESTRICTED]

    def get_retention_period(self) -> int:
        """Get data retention period in days"""
        return self.policy.retention_days

    def sanitize_for_logging(self, message: str) -> str:
        """
        Sanitize message for safe logging without PII.

        Args:
            message: Message to sanitize

        Returns:
            Sanitized message safe for logging
        """
        return self.anonymize_text(message)

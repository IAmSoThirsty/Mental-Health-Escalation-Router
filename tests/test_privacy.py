"""
Tests for Privacy Safeguards
"""

import pytest
from mental_health_router.privacy import (
    PrivacyGuard,
    PrivacyPolicy,
    DataSensitivity
)


class TestPrivacyGuard:
    """Tests for PrivacyGuard"""

    def test_anonymize_email(self):
        """Test email anonymization"""
        guard = PrivacyGuard()

        text = "Contact me at user@example.com for help"
        anonymized = guard.anonymize_text(text)

        assert "user@example.com" not in anonymized
        assert "[EMAIL]" in anonymized

    def test_anonymize_phone(self):
        """Test phone number anonymization"""
        guard = PrivacyGuard()

        text = "Call me at 555-123-4567"
        anonymized = guard.anonymize_text(text)

        assert "555-123-4567" not in anonymized
        assert "[PHONE]" in anonymized

    def test_anonymize_ssn(self):
        """Test SSN anonymization"""
        guard = PrivacyGuard()

        text = "My SSN is 123-45-6789"
        anonymized = guard.anonymize_text(text)

        assert "123-45-6789" not in anonymized
        assert "[SSN]" in anonymized

    def test_hash_identifier(self):
        """Test identifier hashing"""
        guard = PrivacyGuard()

        hash1 = guard.hash_identifier("user_123")
        hash2 = guard.hash_identifier("user_123")
        hash3 = guard.hash_identifier("user_456")

        assert hash1 == hash2  # Same input produces same hash
        assert hash1 != hash3  # Different input produces different hash
        assert len(hash1) == 64  # SHA256 hash length

    def test_hash_with_salt(self):
        """Test hashing with salt"""
        guard = PrivacyGuard()

        hash_no_salt = guard.hash_identifier("user_123")
        hash_with_salt = guard.hash_identifier("user_123", salt="secret")

        assert hash_no_salt != hash_with_salt

    def test_create_anonymized_record(self):
        """Test creating anonymized records"""
        guard = PrivacyGuard()

        data = {
            "user_id": "user_123",
            "email": "user@example.com",
            "message": "I need help"
        }

        anonymized = guard.create_anonymized_record(data, ["user_id", "email"])

        assert anonymized["user_id"] != "user_123"
        assert anonymized["email"] != "user@example.com"
        assert anonymized["message"] == "I need help"

    def test_log_access(self):
        """Test access logging"""
        guard = PrivacyGuard()

        guard.log_access(
            user_id="user_123",
            resource_id="resource_456",
            action="read",
            metadata={"test": "data"}
        )

        log = guard.get_access_log()
        assert len(log) == 1
        assert log[0]["action"] == "read"

    def test_access_logging_disabled(self):
        """Test that logging can be disabled"""
        policy = PrivacyPolicy(audit_access=False)
        guard = PrivacyGuard(policy=policy)

        guard.log_access(
            user_id="user_123",
            resource_id="resource_456",
            action="read"
        )

        log = guard.get_access_log()
        assert len(log) == 0

    def test_validate_data_handling(self):
        """Test data handling validation"""
        policy = PrivacyPolicy(minimum_sensitivity=DataSensitivity.CONFIDENTIAL)
        guard = PrivacyGuard(policy=policy)

        # Should pass for confidential and restricted
        assert guard.validate_data_handling("test", DataSensitivity.CONFIDENTIAL) is True
        assert guard.validate_data_handling("test", DataSensitivity.RESTRICTED) is True

        # Should fail for public and internal
        assert guard.validate_data_handling("test", DataSensitivity.PUBLIC) is False
        assert guard.validate_data_handling("test", DataSensitivity.INTERNAL) is False

    def test_should_encrypt(self):
        """Test encryption requirement checking"""
        guard = PrivacyGuard()

        assert guard.should_encrypt(DataSensitivity.RESTRICTED) is True
        assert guard.should_encrypt(DataSensitivity.CONFIDENTIAL) is True
        assert guard.should_encrypt(DataSensitivity.INTERNAL) is False
        assert guard.should_encrypt(DataSensitivity.PUBLIC) is False

    def test_sanitize_for_logging(self):
        """Test sanitization for logging"""
        guard = PrivacyGuard()

        message = "User user@example.com called 555-123-4567"
        sanitized = guard.sanitize_for_logging(message)

        assert "user@example.com" not in sanitized
        assert "555-123-4567" not in sanitized
        assert "[EMAIL]" in sanitized
        assert "[PHONE]" in sanitized

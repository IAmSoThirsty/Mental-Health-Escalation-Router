"""
Comprehensive tests for production audit module.

Tests cover:
- Cryptographic audit chain (Merkle tree)
- Data retention and PII scrubbing
- Distributed tracing with W3C Trace Context
"""

import pytest
import time
import json
from datetime import datetime, timedelta
from mental_health_router.audit import (
    AuditChain,
    AuditEvent,
    DataRetentionManager,
    DistributedTracing,
    TraceContext,
)


class TestAuditChain:
    """Test cryptographic audit chain"""

    def test_creates_valid_chain(self):
        """Should create a valid audit chain"""
        chain = AuditChain()

        # Add events
        event1 = chain.add_event(
            event_type="inference",
            user_id_hash="hash123",
            session_id="session1",
            data={"risk_level": "moderate"}
        )

        event2 = chain.add_event(
            event_type="routing",
            user_id_hash="hash123",
            session_id="session1",
            data={"resource_id": "resource1"}
        )

        assert event1 is not None
        assert event2 is not None
        assert len(chain.chain) == 2

    def test_chain_integrity_verification(self):
        """Should verify chain integrity correctly"""
        chain = AuditChain()

        # Add events
        for i in range(5):
            chain.add_event(
                event_type=f"event_{i}",
                user_id_hash="hash123",
                session_id="session1",
                data={"index": i}
            )

        # Chain should be valid
        assert chain.verify_chain() is True

    def test_detects_tampering(self):
        """Should detect tampering with chain"""
        chain = AuditChain()

        # Add events
        chain.add_event("event1", "hash1", "session1", {"data": "test1"})
        chain.add_event("event2", "hash2", "session1", {"data": "test2"})

        # Tamper with chain
        if len(chain.chain) > 1:
            event_hash, event_data = chain.chain[1]
            # Modify data without updating hash
            event_data["data"]["tampered"] = True

        # Should detect tampering
        assert chain.verify_chain() is False

    def test_events_are_immutable(self):
        """Events should be cryptographically linked"""
        chain = AuditChain()

        event1_hash = chain.add_event("event1", "hash1", "session1", {"test": 1})
        event2_hash = chain.add_event("event2", "hash2", "session1", {"test": 2})

        # Event 2 should reference event 1
        _, event2_data = chain.chain[1]
        assert event2_data["previous_hash"] == event1_hash

    def test_retrieves_events_by_session(self):
        """Should retrieve all events for a session"""
        chain = AuditChain()

        # Add events for different sessions
        chain.add_event("event1", "user1", "session_a", {"data": "a1"})
        chain.add_event("event2", "user1", "session_a", {"data": "a2"})
        chain.add_event("event3", "user2", "session_b", {"data": "b1"})

        session_a_events = chain.get_events_by_session("session_a")
        assert len(session_a_events) == 2

        session_b_events = chain.get_events_by_session("session_b")
        assert len(session_b_events) == 1

    def test_retrieves_events_by_user(self):
        """Should retrieve all events for a user"""
        chain = AuditChain()

        chain.add_event("event1", "user_abc", "session1", {"data": "1"})
        chain.add_event("event2", "user_abc", "session2", {"data": "2"})
        chain.add_event("event3", "user_xyz", "session3", {"data": "3"})

        user_abc_events = chain.get_events_by_user("user_abc")
        assert len(user_abc_events) == 2

    def test_export_and_verify(self):
        """Should export chain for external verification"""
        chain = AuditChain()

        for i in range(3):
            chain.add_event(f"event{i}", f"user{i}", f"session{i}", {"index": i})

        exported = chain.export_chain()

        # Should be JSON serializable
        json_str = json.dumps(exported)
        imported = json.loads(json_str)

        assert len(imported) == 3


class TestDataRetentionManager:
    """Test data retention and PII scrubbing"""

    def test_scrubs_pii_from_text(self):
        """Should identify and scrub PII"""
        manager = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        text_with_pii = "My name is John Doe, email john@example.com, phone 555-1234"
        scrubbed = manager.scrub_pii(text_with_pii)

        assert "John Doe" not in scrubbed
        assert "john@example.com" not in scrubbed
        assert "555-1234" not in scrubbed
        assert "[NAME]" in scrubbed or "[EMAIL]" in scrubbed or "[PHONE]" in scrubbed

    def test_deletes_expired_data(self):
        """Should delete data older than retention period"""
        manager = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        # Add old record
        old_date = datetime.now() - timedelta(days=100)
        manager.records["old_record"] = {
            "created_at": old_date.isoformat(),
            "data": "old data"
        }

        # Add recent record
        recent_date = datetime.now() - timedelta(days=30)
        manager.records["recent_record"] = {
            "created_at": recent_date.isoformat(),
            "data": "recent data"
        }

        # Apply retention policy
        deleted = manager.apply_retention_policy()

        assert "old_record" not in manager.records
        assert "recent_record" in manager.records
        assert deleted == 1

    def test_respects_legal_hold(self):
        """Should not delete records under legal hold"""
        manager = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        # Add old record with legal hold
        old_date = datetime.now() - timedelta(days=100)
        manager.records["legal_hold_record"] = {
            "created_at": old_date.isoformat(),
            "data": "important data",
            "legal_hold": True
        }

        # Apply retention
        deleted = manager.apply_retention_policy()

        # Should NOT be deleted
        assert "legal_hold_record" in manager.records
        assert deleted == 0

    def test_sets_and_releases_legal_hold(self):
        """Should manage legal holds correctly"""
        manager = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        record_id = "test_record"
        manager.records[record_id] = {
            "created_at": datetime.now().isoformat(),
            "data": "test data"
        }

        # Set legal hold
        manager.set_legal_hold(record_id)
        assert manager.records[record_id]["legal_hold"] is True

        # Release legal hold
        manager.release_legal_hold(record_id)
        assert manager.records[record_id].get("legal_hold", False) is False

    def test_handles_gdpr_deletion_request(self):
        """Should handle GDPR right-to-deletion requests"""
        manager = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        user_hash = "user_abc_hash"

        # Add multiple records for user
        manager.records["record1"] = {
            "user_id_hash": user_hash,
            "created_at": datetime.now().isoformat(),
            "data": "data1"
        }
        manager.records["record2"] = {
            "user_id_hash": user_hash,
            "created_at": datetime.now().isoformat(),
            "data": "data2"
        }
        manager.records["record3"] = {
            "user_id_hash": "other_user",
            "created_at": datetime.now().isoformat(),
            "data": "data3"
        }

        # Delete user's data
        deleted = manager.delete_user_data(user_hash)

        assert deleted == 2
        assert "record1" not in manager.records
        assert "record2" not in manager.records
        assert "record3" in manager.records  # Other user's data intact


class TestDistributedTracing:
    """Test W3C Trace Context implementation"""

    def test_creates_root_trace(self):
        """Should create a root trace context"""
        tracer = DistributedTracing()

        trace_id, span_id = tracer.start_trace("root_operation")

        assert len(trace_id) == 32  # 16 bytes hex
        assert len(span_id) == 16  # 8 bytes hex

    def test_creates_child_span(self):
        """Should create child spans within trace"""
        tracer = DistributedTracing()

        trace_id, parent_span_id = tracer.start_trace("parent")
        child_span_id = tracer.start_span(trace_id, "child", parent_span_id)

        assert child_span_id != parent_span_id
        assert len(child_span_id) == 16

    def test_w3c_traceparent_format(self):
        """Should generate valid W3C traceparent header"""
        tracer = DistributedTracing()

        trace_id, span_id = tracer.start_trace("operation")
        traceparent = tracer.get_traceparent(trace_id, span_id)

        # Format: version-trace_id-span_id-flags
        parts = traceparent.split("-")
        assert len(parts) == 4
        assert parts[0] == "00"  # Version
        assert parts[1] == trace_id
        assert parts[2] == span_id
        assert parts[3] in ["00", "01"]  # Flags

    def test_parses_incoming_traceparent(self):
        """Should parse incoming W3C traceparent header"""
        tracer = DistributedTracing()

        incoming_traceparent = "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01"
        trace_id, span_id, sampled = tracer.parse_traceparent(incoming_traceparent)

        assert trace_id == "0af7651916cd43dd8448eb211c80319c"
        assert span_id == "b7ad6b7169203331"
        assert sampled is True

    def test_ends_span_with_metadata(self):
        """Should record span metadata"""
        tracer = DistributedTracing()

        trace_id, span_id = tracer.start_trace("operation")

        time.sleep(0.01)  # Simulate work

        tracer.end_span(
            trace_id,
            span_id,
            status="success",
            metadata={"risk_level": "moderate"}
        )

        # Should have recorded span
        assert trace_id in tracer.traces
        assert len(tracer.traces[trace_id]) == 1
        span_data = tracer.traces[trace_id][0]
        assert span_data["status"] == "success"
        assert span_data["metadata"]["risk_level"] == "moderate"
        assert "duration_ms" in span_data

    def test_trace_export_for_observability(self):
        """Should export traces for external systems"""
        tracer = DistributedTracing()

        # Create a trace with multiple spans
        trace_id, span1 = tracer.start_trace("request")
        span2 = tracer.start_span(trace_id, "inference", span1)
        span3 = tracer.start_span(trace_id, "routing", span1)

        tracer.end_span(trace_id, span2, status="success")
        tracer.end_span(trace_id, span3, status="success")
        tracer.end_span(trace_id, span1, status="success")

        # Export trace
        exported = tracer.export_trace(trace_id)

        assert "trace_id" in exported
        assert len(exported["spans"]) == 3


class TestAuditIntegration:
    """Integration tests for audit system"""

    def test_end_to_end_audit_trail(self):
        """Complete audit trail from request to completion"""
        chain = AuditChain()
        tracer = DistributedTracing()
        retention = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        # Start trace
        trace_id, root_span = tracer.start_trace("user_request")

        # Audit: Request received
        chain.add_event(
            event_type="request_received",
            user_id_hash="user123_hash",
            session_id="session_abc",
            data={
                "trace_id": trace_id,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Audit: Inference
        inference_span = tracer.start_span(trace_id, "inference", root_span)
        chain.add_event(
            event_type="inference_complete",
            user_id_hash="user123_hash",
            session_id="session_abc",
            data={
                "trace_id": trace_id,
                "span_id": inference_span,
                "risk_level": "moderate"
            }
        )
        tracer.end_span(trace_id, inference_span, status="success")

        # Audit: Routing
        routing_span = tracer.start_span(trace_id, "routing", root_span)
        chain.add_event(
            event_type="routing_complete",
            user_id_hash="user123_hash",
            session_id="session_abc",
            data={
                "trace_id": trace_id,
                "span_id": routing_span,
                "resource_id": "counselor_1"
            }
        )
        tracer.end_span(trace_id, routing_span, status="success")

        # End trace
        tracer.end_span(trace_id, root_span, status="success")

        # Verify complete audit trail
        assert chain.verify_chain() is True
        session_events = chain.get_events_by_session("session_abc")
        assert len(session_events) == 3

        # Verify distributed trace
        trace_data = tracer.export_trace(trace_id)
        assert len(trace_data["spans"]) == 3

    def test_compliance_with_retention(self):
        """Compliance: PII scrubbing + retention enforcement"""
        retention = DataRetentionManager(retention_days=90, auto_scrub_pii=True)

        # Store record with PII
        original_text = "Patient John Doe, SSN 123-45-6789, discussed anxiety"
        scrubbed_text = retention.scrub_pii(original_text)

        record_id = "record_compliance"
        retention.records[record_id] = {
            "created_at": datetime.now().isoformat(),
            "original": scrubbed_text,  # Already scrubbed
            "user_id_hash": "user_hash"
        }

        # Verify PII removed
        assert "John Doe" not in scrubbed_text
        assert "123-45-6789" not in scrubbed_text

        # Fast-forward time (simulate)
        old_date = datetime.now() - timedelta(days=100)
        retention.records[record_id]["created_at"] = old_date.isoformat()

        # Apply retention
        deleted = retention.apply_retention_policy()
        assert deleted == 1
        assert record_id not in retention.records


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

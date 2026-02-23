"""
Cryptographic audit logging and immutable event store.

Implements Merkle tree-based audit trail with cryptographic verification.
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class EventType(Enum):
    """Audit event types"""
    INFERENCE = "inference"
    CLASSIFICATION = "classification"
    ESCALATION = "escalation"
    ROUTING = "routing"
    HUMAN_REVIEW = "human_review"
    CONFIGURATION_CHANGE = "configuration_change"
    ACCESS = "access"


@dataclass
class AuditEvent:
    """Immutable audit event"""
    event_id: str
    event_type: EventType
    timestamp: float
    user_id_hash: str  # Hashed user ID
    session_id: str
    data: Dict[str, Any]  # Event-specific data
    previous_hash: str
    event_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'user_id_hash': self.user_id_hash,
            'session_id': self.session_id,
            'data': self.data,
            'previous_hash': self.previous_hash,
            'event_hash': self.event_hash
        }


class AuditChain:
    """
    Merkle tree-based audit chain for cryptographic verification.

    Each event is cryptographically linked to the previous event,
    making tampering detectable.
    """

    def __init__(self):
        self.events: List[AuditEvent] = []
        self.latest_hash = "0" * 64  # Genesis hash
        self._event_counter = 0

    def add_event(
        self,
        event_type: EventType,
        user_id_hash: str,
        session_id: str,
        data: Dict[str, Any]
    ) -> AuditEvent:
        """
        Add event to audit chain.

        Args:
            event_type: Type of event
            user_id_hash: Hashed user identifier
            session_id: Session identifier
            data: Event-specific data

        Returns:
            Created AuditEvent
        """
        self._event_counter += 1
        event_id = f"event_{self._event_counter}_{int(time.time() * 1000)}"
        timestamp = time.time()

        # Create event data for hashing
        event_data = {
            'event_id': event_id,
            'event_type': event_type.value,
            'timestamp': timestamp,
            'user_id_hash': user_id_hash,
            'session_id': session_id,
            'data': data,
            'previous_hash': self.latest_hash
        }

        # Compute cryptographic hash
        event_hash = self._compute_hash(event_data)

        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=timestamp,
            user_id_hash=user_id_hash,
            session_id=session_id,
            data=data,
            previous_hash=self.latest_hash,
            event_hash=event_hash
        )

        # Add to chain
        self.events.append(event)
        self.latest_hash = event_hash

        return event

    def verify_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Verify integrity of audit chain.

        Returns:
            (is_valid, error_message)
        """
        if not self.events:
            return (True, None)

        # Check genesis
        if self.events[0].previous_hash != "0" * 64:
            return (False, "Invalid genesis hash")

        # Verify each event
        for i, event in enumerate(self.events):
            # Verify hash
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp,
                'user_id_hash': event.user_id_hash,
                'session_id': event.session_id,
                'data': event.data,
                'previous_hash': event.previous_hash
            }

            expected_hash = self._compute_hash(event_data)
            if event.event_hash != expected_hash:
                return (False, f"Event {i} hash mismatch")

            # Verify chain link
            if i > 0:
                if event.previous_hash != self.events[i-1].event_hash:
                    return (False, f"Event {i} chain broken")

        return (True, None)

    def get_events_for_session(self, session_id: str) -> List[AuditEvent]:
        """Get all events for a session"""
        return [e for e in self.events if e.session_id == session_id]

    def get_events_by_type(self, event_type: EventType) -> List[AuditEvent]:
        """Get all events of a type"""
        return [e for e in self.events if e.event_type == event_type]

    def export_chain(self) -> List[Dict[str, Any]]:
        """Export entire chain for archival"""
        return [event.to_dict() for event in self.events]

    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of event data"""
        # Serialize deterministically
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


class DataRetentionManager:
    """
    Automated data retention and PII scrubbing.

    Implements GDPR/HIPAA-compliant data lifecycle management.
    """

    def __init__(self, retention_days: int = 90):
        self.retention_days = retention_days
        self.records: Dict[str, Dict[str, Any]] = {}  # record_id -> record
        self.legal_holds: Dict[str, str] = {}  # record_id -> reason

    def store_record(
        self,
        record_id: str,
        data: Dict[str, Any],
        contains_pii: bool = True
    ):
        """
        Store a record with retention metadata.

        Args:
            record_id: Unique record identifier
            data: Record data
            contains_pii: Whether record contains PII
        """
        self.records[record_id] = {
            'data': data,
            'created_at': datetime.now(),
            'contains_pii': contains_pii,
            'scrubbed': False,
            'deleted': False
        }

    def apply_legal_hold(self, record_id: str, reason: str):
        """
        Apply legal hold to prevent deletion.

        Args:
            record_id: Record to hold
            reason: Legal reason for hold
        """
        self.legal_holds[record_id] = reason

    def release_legal_hold(self, record_id: str):
        """Release legal hold"""
        if record_id in self.legal_holds:
            del self.legal_holds[record_id]

    def scrub_expired_records(self) -> List[str]:
        """
        Scrub PII from expired records.

        Returns:
            List of scrubbed record IDs
        """
        scrubbed = []
        now = datetime.now()

        for record_id, record in self.records.items():
            # Skip if legal hold
            if record_id in self.legal_holds:
                continue

            # Skip if already scrubbed
            if record['scrubbed']:
                continue

            # Check if expired
            age = (now - record['created_at']).days
            if age > self.retention_days and record['contains_pii']:
                # Scrub PII fields
                self._scrub_record(record)
                record['scrubbed'] = True
                scrubbed.append(record_id)

        return scrubbed

    def delete_record(self, record_id: str) -> bool:
        """
        Delete a record (GDPR right to erasure).

        Args:
            record_id: Record to delete

        Returns:
            True if deleted, False if legal hold prevents deletion
        """
        if record_id in self.legal_holds:
            return False  # Cannot delete during legal hold

        if record_id in self.records:
            self.records[record_id]['deleted'] = True
            self.records[record_id]['data'] = {}
            return True

        return False

    def _scrub_record(self, record: Dict[str, Any]):
        """Scrub PII fields from record"""
        pii_fields = ['user_id', 'email', 'phone', 'name', 'address', 'input_text']

        for field in pii_fields:
            if field in record['data']:
                record['data'][field] = '[SCRUBBED]'


class DistributedTracing:
    """
    Distributed tracing for request flow across layers.

    Implements W3C Trace Context standard.
    """

    def __init__(self):
        self.active_traces: Dict[str, Dict[str, Any]] = {}

    def start_trace(self, trace_id: Optional[str] = None) -> str:
        """
        Start a new trace.

        Args:
            trace_id: Optional trace ID (generated if not provided)

        Returns:
            Trace ID
        """
        if trace_id is None:
            trace_id = self._generate_trace_id()

        self.active_traces[trace_id] = {
            'trace_id': trace_id,
            'start_time': time.time(),
            'spans': []
        }

        return trace_id

    def start_span(
        self,
        trace_id: str,
        span_name: str,
        parent_span_id: Optional[str] = None
    ) -> str:
        """
        Start a span within a trace.

        Args:
            trace_id: Parent trace ID
            span_name: Name of this span
            parent_span_id: Optional parent span ID

        Returns:
            Span ID
        """
        span_id = self._generate_span_id()

        if trace_id not in self.active_traces:
            self.start_trace(trace_id)

        span = {
            'span_id': span_id,
            'span_name': span_name,
            'parent_span_id': parent_span_id,
            'start_time': time.time(),
            'end_time': None,
            'tags': {},
            'events': []
        }

        self.active_traces[trace_id]['spans'].append(span)
        return span_id

    def end_span(self, trace_id: str, span_id: str):
        """End a span"""
        if trace_id in self.active_traces:
            for span in self.active_traces[trace_id]['spans']:
                if span['span_id'] == span_id:
                    span['end_time'] = time.time()
                    break

    def add_span_tag(self, trace_id: str, span_id: str, key: str, value: Any):
        """Add tag to span"""
        if trace_id in self.active_traces:
            for span in self.active_traces[trace_id]['spans']:
                if span['span_id'] == span_id:
                    span['tags'][key] = value
                    break

    def add_span_event(self, trace_id: str, span_id: str, event_name: str, data: Dict[str, Any]):
        """Add event to span"""
        if trace_id in self.active_traces:
            for span in self.active_traces[trace_id]['spans']:
                if span['span_id'] == span_id:
                    span['events'].append({
                        'name': event_name,
                        'timestamp': time.time(),
                        'data': data
                    })
                    break

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get complete trace"""
        return self.active_traces.get(trace_id)

    def _generate_trace_id(self) -> str:
        """Generate W3C-compliant trace ID (32 hex chars)"""
        import secrets
        return secrets.token_hex(16)

    def _generate_span_id(self) -> str:
        """Generate W3C-compliant span ID (16 hex chars)"""
        import secrets
        return secrets.token_hex(8)


# Global instances
_audit_chain = AuditChain()
_retention_manager = DataRetentionManager()
_tracing = DistributedTracing()


def get_audit_chain() -> AuditChain:
    """Get global audit chain instance"""
    return _audit_chain


def get_retention_manager() -> DataRetentionManager:
    """Get global retention manager instance"""
    return _retention_manager


def get_tracing() -> DistributedTracing:
    """Get global tracing instance"""
    return _tracing

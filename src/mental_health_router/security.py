"""
Production-grade validation and sanitization for mental health escalation router.

Implements defense-in-depth input validation, rate limiting, and abuse detection.
"""

import re
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import secrets


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    pass


class AbuseDetected(Exception):
    """Raised when abuse pattern is detected"""
    pass


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_input: Optional[str]
    violations: List[str]
    risk_score: float  # 0.0 = safe, 1.0 = highly suspicious


class InputValidator:
    """
    Production-grade input validation and sanitization.

    Defends against:
    - Injection attacks (SQL, command, XSS)
    - Prompt manipulation (if LLM-assisted)
    - Encoding attacks
    - Oversized inputs
    - Binary/malformed data
    """

    # Maximum input sizes
    MAX_TEXT_LENGTH = 10000  # 10KB text
    MAX_AUDIO_SIZE = 5 * 1024 * 1024  # 5MB audio

    # Suspicious patterns
    INJECTION_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS
        r'javascript:',  # XSS
        r'on\w+\s*=',  # Event handlers
        r'(\bSELECT\b|\bUNION\b|\bDROP\b|\bDELETE\b).*\bFROM\b',  # SQL
        r'[\x00-\x08\x0B-\x0C\x0E-\x1F]',  # Control characters
        r'(\.\./|\.\.\\)',  # Path traversal
    ]

    # Prompt manipulation patterns
    PROMPT_MANIPULATION = [
        r'ignore previous (instructions|prompt)',
        r'disregard (all|previous|above)',
        r'forget everything',
        r'new instructions:',
        r'system prompt',
        r'you are now',
    ]

    def __init__(self):
        self.injection_regex = re.compile('|'.join(self.INJECTION_PATTERNS), re.IGNORECASE)
        self.manipulation_regex = re.compile('|'.join(self.PROMPT_MANIPULATION), re.IGNORECASE)

    def validate_text_input(self, text: str) -> ValidationResult:
        """
        Validate and sanitize text input.

        Args:
            text: Raw text input

        Returns:
            ValidationResult with sanitized text and risk score

        Raises:
            ValidationError: If input is fundamentally invalid
        """
        violations = []
        risk_score = 0.0

        # Type check
        if not isinstance(text, str):
            raise ValidationError(f"Input must be string, got {type(text)}")

        # Length check
        if len(text) == 0:
            raise ValidationError("Empty input not allowed")

        if len(text) > self.MAX_TEXT_LENGTH:
            violations.append(f"Input exceeds maximum length: {len(text)} > {self.MAX_TEXT_LENGTH}")
            text = text[:self.MAX_TEXT_LENGTH]
            risk_score += 0.3

        # Check for injection patterns
        if self.injection_regex.search(text):
            violations.append("Potential injection attack detected")
            risk_score += 0.5

        # Check for prompt manipulation
        if self.manipulation_regex.search(text):
            violations.append("Potential prompt manipulation detected")
            risk_score += 0.4

        # Check for excessive repeated characters (potential DoS)
        if self._has_excessive_repetition(text):
            violations.append("Excessive character repetition detected")
            risk_score += 0.2

        # Check encoding
        try:
            text.encode('utf-8').decode('utf-8')
        except UnicodeError:
            raise ValidationError("Invalid UTF-8 encoding")

        # Normalize whitespace
        sanitized = ' '.join(text.split())

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        return ValidationResult(
            is_valid=risk_score < 0.8,
            sanitized_input=sanitized if risk_score < 0.8 else None,
            violations=violations,
            risk_score=min(risk_score, 1.0)
        )

    def validate_audio_input(self, audio_data: bytes) -> ValidationResult:
        """
        Validate audio input.

        Args:
            audio_data: Raw audio bytes

        Returns:
            ValidationResult

        Raises:
            ValidationError: If input is invalid
        """
        violations = []
        risk_score = 0.0

        if not isinstance(audio_data, bytes):
            raise ValidationError(f"Audio must be bytes, got {type(audio_data)}")

        if len(audio_data) == 0:
            raise ValidationError("Empty audio not allowed")

        if len(audio_data) > self.MAX_AUDIO_SIZE:
            violations.append(f"Audio exceeds maximum size: {len(audio_data)} > {self.MAX_AUDIO_SIZE}")
            risk_score += 0.5

        # Basic magic number validation (common audio formats)
        if not self._is_valid_audio_format(audio_data):
            violations.append("Unrecognized audio format")
            risk_score += 0.3

        return ValidationResult(
            is_valid=risk_score < 0.8,
            sanitized_input=None,  # Audio not sanitized, only validated
            violations=violations,
            risk_score=risk_score
        )

    def _has_excessive_repetition(self, text: str, threshold: int = 50) -> bool:
        """Check for excessive character repetition (DoS attempt)"""
        max_consecutive = 1
        current_consecutive = 1
        prev_char = None

        for char in text:
            if char == prev_char:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1
            prev_char = char

        return max_consecutive > threshold

    def _is_valid_audio_format(self, data: bytes) -> bool:
        """Check for valid audio format magic numbers"""
        if len(data) < 12:
            return False

        # WAV: RIFF....WAVE
        if data[:4] == b'RIFF' and data[8:12] == b'WAVE':
            return True

        # MP3: ID3 or FF FB/FF F3
        if data[:3] == b'ID3' or data[:2] in [b'\xff\xfb', b'\xff\xf3']:
            return True

        # OGG: OggS
        if data[:4] == b'OggS':
            return True

        # FLAC: fLaC
        if data[:4] == b'fLaC':
            return True

        return False


class RateLimiter:
    """
    Token bucket rate limiter with burst capacity.

    Implements per-user and global rate limits to prevent abuse.
    """

    def __init__(
        self,
        rate: float = 10.0,  # Requests per second
        burst: int = 20,  # Burst capacity
        window_seconds: int = 60
    ):
        self.rate = rate
        self.burst = burst
        self.window_seconds = window_seconds
        self.buckets: Dict[str, Tuple[float, float]] = {}  # user_id -> (tokens, last_update)
        self.global_bucket = [float(burst), time.time()]

    def check_rate_limit(self, user_id: str, cost: float = 1.0) -> bool:
        """
        Check if request is within rate limit.

        Args:
            user_id: User identifier (hashed)
            cost: Cost of this request (default 1.0)

        Returns:
            True if allowed, False if rate limit exceeded

        Raises:
            RateLimitExceeded: If limit is exceeded
        """
        now = time.time()

        # Check global rate limit first
        if not self._check_bucket(self.global_bucket, now, cost):
            raise RateLimitExceeded("Global rate limit exceeded")

        # Check per-user rate limit
        if user_id not in self.buckets:
            self.buckets[user_id] = [float(self.burst), now]

        bucket = self.buckets[user_id]
        if not self._check_bucket(bucket, now, cost):
            raise RateLimitExceeded(f"Rate limit exceeded for user {user_id[:8]}...")

        # Consume tokens from both buckets
        self.global_bucket[0] -= cost
        bucket[0] -= cost

        return True

    def _check_bucket(self, bucket: List[float], now: float, cost: float) -> bool:
        """Check and refill token bucket"""
        tokens, last_update = bucket[0], bucket[1]

        # Refill tokens based on elapsed time
        elapsed = now - last_update
        tokens = min(self.burst, tokens + elapsed * self.rate)

        # Update bucket
        bucket[0] = tokens
        bucket[1] = now

        return tokens >= cost

    def cleanup_old_buckets(self):
        """Remove stale buckets to prevent memory leak"""
        now = time.time()
        cutoff = now - (self.window_seconds * 2)

        self.buckets = {
            uid: bucket for uid, bucket in self.buckets.items()
            if bucket[1] > cutoff
        }


class AbuseDetector:
    """
    Detect coordinated abuse and anomalous patterns.

    Monitors for:
    - Flood attacks (same user, many requests)
    - Distributed attacks (many users, similar content)
    - Geo-spoofing (impossible location changes)
    - Repeated escalation spam
    """

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.user_history: Dict[str, List[Dict[str, Any]]] = {}
        self.content_hashes: Dict[str, int] = {}  # hash -> count

    def check_abuse(
        self,
        user_id: str,
        content: str,
        location: Optional[Tuple[float, float]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Check for abuse patterns.

        Args:
            user_id: Hashed user identifier
            content: Input content
            location: (latitude, longitude) if available

        Returns:
            (is_abuse, reasons)
        """
        reasons = []
        now = datetime.now()

        # Initialize user history
        if user_id not in self.user_history:
            self.user_history[user_id] = []

        history = self.user_history[user_id]

        # Clean old entries
        cutoff = now - timedelta(minutes=self.window_minutes)
        history[:] = [entry for entry in history if entry['timestamp'] > cutoff]

        # Check flood (>10 requests in 5 minutes from same user)
        if len(history) > 10:
            reasons.append(f"Flood detected: {len(history)} requests in {self.window_minutes}min")

        # Check for identical content spam
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        if content_hash in self.content_hashes:
            self.content_hashes[content_hash] += 1
            if self.content_hashes[content_hash] > 5:
                reasons.append("Identical content spam detected")
        else:
            self.content_hashes[content_hash] = 1

        # Check for impossible location changes
        if location and history:
            last_location = history[-1].get('location')
            if last_location:
                distance = self._haversine_distance(last_location, location)
                time_diff = (now - history[-1]['timestamp']).total_seconds()

                # If moved >1000km in <60 seconds, likely spoofed
                if distance > 1000 and time_diff < 60:
                    reasons.append(f"Impossible location change: {distance:.0f}km in {time_diff:.0f}s")

        # Record this request
        history.append({
            'timestamp': now,
            'content_hash': content_hash,
            'location': location
        })

        return (len(reasons) > 0, reasons)

    def _haversine_distance(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two points in km"""
        import math
        lat1, lon1 = loc1
        lat2, lon2 = loc2

        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return R * c


class RequestSigner:
    """
    Cryptographic request signing for replay protection.

    Each request must include:
    - Nonce (prevents replay)
    - Timestamp (prevents delayed replay)
    - Signature (prevents tampering)
    """

    def __init__(self, secret_key: Optional[bytes] = None):
        self.secret_key = secret_key or secrets.token_bytes(32)
        self.used_nonces: Dict[str, float] = {}  # nonce -> timestamp
        self.nonce_ttl = 300  # 5 minutes

    def sign_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a request payload.

        Args:
            payload: Request data

        Returns:
            Signed payload with nonce, timestamp, and signature
        """
        # Add nonce and timestamp
        nonce = secrets.token_hex(16)
        timestamp = int(time.time())

        signed_payload = {
            **payload,
            'nonce': nonce,
            'timestamp': timestamp
        }

        # Create signature
        message = self._serialize_payload(signed_payload)
        signature = hmac_sha256(message, self.secret_key)
        signed_payload['signature'] = signature

        return signed_payload

    def verify_request(self, payload: Dict[str, Any]) -> bool:
        """
        Verify request signature and check for replay.

        Args:
            payload: Signed request

        Returns:
            True if valid

        Raises:
            ValidationError: If signature invalid or replay detected
        """
        # Extract signature
        signature = payload.get('signature')
        if not signature:
            raise ValidationError("Missing signature")

        nonce = payload.get('nonce')
        timestamp = payload.get('timestamp')

        if not nonce or not timestamp:
            raise ValidationError("Missing nonce or timestamp")

        # Check timestamp (not too old, not in future)
        now = int(time.time())
        if abs(now - timestamp) > self.nonce_ttl:
            raise ValidationError(f"Timestamp out of range: {now - timestamp}s")

        # Check nonce hasn't been used
        if nonce in self.used_nonces:
            raise ValidationError(f"Nonce replay detected: {nonce}")

        # Verify signature
        payload_copy = {k: v for k, v in payload.items() if k != 'signature'}
        message = self._serialize_payload(payload_copy)
        expected_signature = hmac_sha256(message, self.secret_key)

        if not secrets.compare_digest(signature, expected_signature):
            raise ValidationError("Invalid signature")

        # Mark nonce as used
        self.used_nonces[nonce] = float(timestamp)
        self._cleanup_old_nonces()

        return True

    def _serialize_payload(self, payload: Dict[str, Any]) -> bytes:
        """Serialize payload for signing"""
        import json
        # Sort keys for deterministic serialization
        return json.dumps(payload, sort_keys=True).encode('utf-8')

    def _cleanup_old_nonces(self):
        """Remove expired nonces"""
        now = time.time()
        cutoff = now - self.nonce_ttl
        self.used_nonces = {
            nonce: ts for nonce, ts in self.used_nonces.items()
            if ts > cutoff
        }


def hmac_sha256(message: bytes, key: bytes) -> str:
    """Compute HMAC-SHA256"""
    import hmac
    return hmac.new(key, message, hashlib.sha256).hexdigest()

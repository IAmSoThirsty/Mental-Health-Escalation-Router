"""
Production-Hardened Mental Health Escalation Router

This example demonstrates the complete production-grade system with:
- Multi-layer security (validation, rate limiting, abuse detection, signing)
- Operational resilience (circuit breakers, bulkheads, graceful degradation)
- Complete auditability (cryptographic chain, distributed tracing)
- Production configuration management

This is a fully hardened system ready for hostile scrutiny and production scale.
"""

import time
from typing import Dict, Any
from mental_health_router import (
    # Core components
    TextInferenceEngine,
    RiskClassifier,
    EscalationPolicy,
    GeoAwareRouter,
    HumanInLoopEnforcer,
    PrivacyGuard,
    # Hardening components
    InputValidator,
    RateLimiter,
    AbuseDetector,
    RequestSigner,
    CircuitBreaker,
    Bulkhead,
    HealthMonitor,
    GracefulDegradation,
    BackpressureManager,
    MetricsCollector,
    AuditChain,
    DataRetentionManager,
    DistributedTracing,
    ProductionConfig,
    ConfigManager,
    Environment,
)
from mental_health_router.routing import GeoLocation, HumanResource, ResourceStatus
from mental_health_router.risk_classifier import RiskLevel
from datetime import datetime


class ProductionMentalHealthRouter:
    """
    Production-grade mental health escalation router with full hardening.

    Security Layers:
    1. Input validation (XSS, SQL injection, prompt manipulation)
    2. Rate limiting (per-user and global)
    3. Abuse detection (flooding, coordinated attacks, geo-spoofing)
    4. Request signing (HMAC-SHA256 with replay protection)

    Resilience Patterns:
    1. Circuit breakers (fault isolation)
    2. Bulkheads (resource isolation)
    3. Health monitoring (readiness/liveness)
    4. Graceful degradation (fallback strategies)
    5. Backpressure management (flow control)

    Observability:
    1. Cryptographic audit chain (Merkle tree)
    2. Distributed tracing (W3C Trace Context)
    3. Metrics collection (counters, gauges, histograms)
    4. Data retention (GDPR/HIPAA compliant)
    """

    def __init__(self, config: ProductionConfig):
        self.config = config

        # Core components
        self.inference_engine = TextInferenceEngine()
        self.risk_classifier = RiskClassifier()
        self.escalation_policy = EscalationPolicy()
        self.router = self._initialize_router()
        self.human_enforcer = HumanInLoopEnforcer()
        self.privacy_guard = PrivacyGuard()

        # Security layer
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter(
            requests_per_second=config.security.rate_limit_per_second,
            burst=config.security.rate_limit_burst,
        )
        self.abuse_detector = AbuseDetector()
        self.request_signer = RequestSigner("production-secret-min-32-chars-required")

        # Resilience layer
        self.inference_circuit = CircuitBreaker(
            name="inference",
            failure_threshold=config.resilience.circuit_failure_threshold,
            timeout_seconds=config.resilience.circuit_timeout_seconds,
        )
        self.routing_circuit = CircuitBreaker(
            name="routing",
            failure_threshold=config.resilience.circuit_failure_threshold,
            timeout_seconds=config.resilience.circuit_timeout_seconds,
        )
        self.inference_bulkhead = Bulkhead(
            name="inference",
            max_concurrent=config.resilience.max_concurrent_requests // 2,
        )
        self.routing_bulkhead = Bulkhead(
            name="routing",
            max_concurrent=config.resilience.max_concurrent_requests // 2,
        )
        self.health_monitor = HealthMonitor()
        self.degradation = GracefulDegradation()
        self.backpressure = BackpressureManager(
            max_queue_size=config.resilience.max_queue_size
        )
        self.metrics = MetricsCollector()

        # Audit layer
        self.audit_chain = AuditChain()
        self.retention_manager = DataRetentionManager(
            retention_days=config.audit.retention_days,
            auto_scrub_pii=config.audit.auto_scrub_pii,
        )
        self.tracer = DistributedTracing()

        # Register health checks
        self._register_health_checks()

        # Mark as ready
        self.health_monitor.mark_ready()

    def _initialize_router(self) -> GeoAwareRouter:
        """Initialize geo-aware router with resources"""
        # Example resources (in production, load from database)
        resources = [
            HumanResource(
                resource_id="counselor_1",
                name="Crisis Counselor 1",
                location=GeoLocation(37.7749, -122.4194),  # San Francisco
                specializations=["crisis", "suicide_prevention"],
                languages=["en", "es"],
                max_capacity=10,
                current_load=0,
                status=ResourceStatus.AVAILABLE,
            ),
            HumanResource(
                resource_id="counselor_2",
                name="Crisis Counselor 2",
                location=GeoLocation(40.7128, -74.0060),  # New York
                specializations=["crisis", "trauma"],
                languages=["en"],
                max_capacity=10,
                current_load=0,
                status=ResourceStatus.AVAILABLE,
            ),
        ]
        return GeoAwareRouter(resources)

    def _register_health_checks(self):
        """Register health checks for all components"""
        self.health_monitor.register_check(
            "inference_circuit",
            lambda: self.inference_circuit.state.value == "closed",
            critical=True,
        )
        self.health_monitor.register_check(
            "routing_circuit",
            lambda: self.routing_circuit.state.value == "closed",
            critical=True,
        )
        self.health_monitor.register_check(
            "audit_chain",
            lambda: self.audit_chain.verify_chain(),
            critical=True,
        )

    def process_distress_signal(
        self,
        user_id: str,
        text: str,
        location: GeoLocation,
        request_signature: str = None,
        request_nonce: str = None,
    ) -> Dict[str, Any]:
        """
        Process a distress signal through the complete hardened pipeline.

        Security: Input validation → Rate limiting → Abuse detection → Signature verification
        Resilience: Circuit breakers → Bulkheads → Graceful degradation → Backpressure
        Audit: Distributed tracing → Audit chain → Metrics → PII scrubbing

        Args:
            user_id: Unique user identifier
            text: Input text to analyze
            location: User's geographic location
            request_signature: Optional HMAC signature for request verification
            request_nonce: Optional nonce for replay protection

        Returns:
            Processing result with risk assessment, routing, and audit trails

        Raises:
            ValidationError: Invalid input
            RateLimitExceeded: Too many requests
            AbuseDetected: Abusive behavior detected
            SignatureError: Invalid signature
            CircuitBreakerOpen: System degraded
            BulkheadFull: System at capacity
            BackpressureError: System overloaded
        """

        # Start distributed trace
        trace_id, root_span = self.tracer.start_trace("process_distress_signal")
        start_time = time.time()

        try:
            # === SECURITY LAYER ===

            # 1. Input validation
            security_span = self.tracer.start_span(trace_id, "security", root_span)
            self.validator.validate_text(text)
            self.metrics.increment("security.validation_passed", 1)

            # 2. Rate limiting
            self.rate_limiter.check_rate_limit(user_id)
            self.metrics.increment("security.rate_limit_passed", 1)

            # 3. Abuse detection
            self.abuse_detector.check_abuse(user_id, location)
            self.metrics.increment("security.abuse_check_passed", 1)

            # 4. Request signing (optional but recommended in production)
            if request_signature and request_nonce:
                payload = {"user_id": user_id, "text": text}
                self.request_signer.verify_signature(payload, request_signature, request_nonce)
                self.metrics.increment("security.signature_verified", 1)

            self.tracer.end_span(trace_id, security_span, status="success")

            # === BACKPRESSURE MANAGEMENT ===
            self.backpressure.check_backpressure()

            # === PRIVACY LAYER ===

            privacy_span = self.tracer.start_span(trace_id, "privacy", root_span)

            # Anonymize input
            user_id_hash = self.privacy_guard.anonymize_identifier(user_id)

            # Scrub PII before storage
            scrubbed_text = self.retention_manager.scrub_pii(text)

            self.tracer.end_span(trace_id, privacy_span, status="success")

            # Audit: Request received
            self.audit_chain.add_event(
                event_type="request_received",
                user_id_hash=user_id_hash,
                session_id=trace_id,
                data={
                    "trace_id": trace_id,
                    "timestamp": datetime.now().isoformat(),
                    "location_lat": location.latitude,
                    "location_lon": location.longitude,
                },
            )

            # === INFERENCE WITH RESILIENCE ===

            inference_span = self.tracer.start_span(trace_id, "inference", root_span)

            def primary_inference():
                """Primary inference with circuit breaker and bulkhead"""
                return self.inference_circuit.call(
                    lambda: self.inference_bulkhead.execute(
                        lambda: self.inference_engine.infer(text)
                    )
                )

            def fallback_inference():
                """Fallback: Conservative risk assessment"""
                self.metrics.increment("resilience.fallback_inference", 1)
                # Fail-safe: If inference unavailable, assume moderate risk
                from mental_health_router.inference_engine import InferenceResult, InputType

                return InferenceResult(
                    input_type=InputType.TEXT,
                    distress_signals={"general": 0.6},  # Conservative
                    confidence=0.5,
                    latency_ms=0,
                    metadata={"fallback": True},
                )

            # Execute with graceful degradation
            inference_result = self.degradation.execute(
                primary=primary_inference, fallback=fallback_inference
            )

            self.metrics.record_histogram("inference.latency_ms", inference_result.latency_ms)
            self.tracer.end_span(
                trace_id,
                inference_span,
                status="success",
                metadata={"confidence": inference_result.confidence},
            )

            # Audit: Inference complete
            self.audit_chain.add_event(
                event_type="inference_complete",
                user_id_hash=user_id_hash,
                session_id=trace_id,
                data={
                    "trace_id": trace_id,
                    "span_id": inference_span,
                    "confidence": inference_result.confidence,
                    "fallback": inference_result.metadata.get("fallback", False),
                },
            )

            # === RISK CLASSIFICATION ===

            risk_span = self.tracer.start_span(trace_id, "risk_classification", root_span)

            risk_assessment = self.risk_classifier.classify(inference_result)
            escalation_result = self.escalation_policy.evaluate(risk_assessment)

            self.metrics.increment(f"risk.level_{risk_assessment.risk_level.value}", 1)
            self.tracer.end_span(
                trace_id,
                risk_span,
                status="success",
                metadata={"risk_level": risk_assessment.risk_level.value},
            )

            # Audit: Risk assessed
            self.audit_chain.add_event(
                event_type="risk_assessment",
                user_id_hash=user_id_hash,
                session_id=trace_id,
                data={
                    "trace_id": trace_id,
                    "risk_level": risk_assessment.risk_level.value,
                    "confidence": risk_assessment.confidence,
                    "requires_human": risk_assessment.requires_human,
                },
            )

            # === ROUTING WITH RESILIENCE ===

            routing_span = self.tracer.start_span(trace_id, "routing", root_span)

            def primary_routing():
                """Primary routing with circuit breaker and bulkhead"""
                return self.routing_circuit.call(
                    lambda: self.routing_bulkhead.execute(
                        lambda: self.router.route(
                            risk_assessment=risk_assessment,
                            location=location,
                            user_id=user_id_hash,
                        )
                    )
                )

            def fallback_routing():
                """Fallback: Return emergency contacts"""
                self.metrics.increment("resilience.fallback_routing", 1)
                from mental_health_router.routing import RoutingResult

                return RoutingResult(
                    resource=None,
                    rationale="Routing unavailable - emergency contacts provided",
                    emergency_contacts=[
                        {"name": "National Suicide Prevention Lifeline", "phone": "988"}
                    ],
                )

            routing_result = self.degradation.execute(
                primary=primary_routing, fallback=fallback_routing
            )

            self.tracer.end_span(
                trace_id,
                routing_span,
                status="success",
                metadata={
                    "resource_id": routing_result.resource.resource_id
                    if routing_result.resource
                    else None
                },
            )

            # Audit: Routing complete
            self.audit_chain.add_event(
                event_type="routing_complete",
                user_id_hash=user_id_hash,
                session_id=trace_id,
                data={
                    "trace_id": trace_id,
                    "resource_id": routing_result.resource.resource_id
                    if routing_result.resource
                    else None,
                    "fallback": routing_result.resource is None,
                },
            )

            # === HUMAN-IN-THE-LOOP ENFORCEMENT ===

            if risk_assessment.requires_human:
                review = self.human_enforcer.create_review(
                    user_id=user_id_hash,
                    risk_assessment=risk_assessment,
                    inference_result=inference_result,
                    timeout_seconds=escalation_result.timeout_seconds,
                )

                self.metrics.increment("human_review.created", 1)

                # Audit: Human review initiated
                self.audit_chain.add_event(
                    event_type="human_review_initiated",
                    user_id_hash=user_id_hash,
                    session_id=trace_id,
                    data={
                        "trace_id": trace_id,
                        "review_id": review.review_id,
                        "timeout_seconds": escalation_result.timeout_seconds,
                    },
                )

            # === END TRACE ===

            total_latency = (time.time() - start_time) * 1000
            self.metrics.record_histogram("request.total_latency_ms", total_latency)
            self.tracer.end_span(
                trace_id,
                root_span,
                status="success",
                metadata={"total_latency_ms": total_latency},
            )

            # === RETURN RESULT ===

            return {
                "success": True,
                "trace_id": trace_id,
                "risk_level": risk_assessment.risk_level.value,
                "confidence": risk_assessment.confidence,
                "requires_human": risk_assessment.requires_human,
                "resource": {
                    "id": routing_result.resource.resource_id,
                    "name": routing_result.resource.name,
                }
                if routing_result.resource
                else None,
                "emergency_contacts": routing_result.emergency_contacts,
                "review_id": review.review_id if risk_assessment.requires_human else None,
                "total_latency_ms": total_latency,
            }

        except Exception as e:
            # Record failure
            self.metrics.increment("request.failed", 1)
            self.tracer.end_span(trace_id, root_span, status="error", metadata={"error": str(e)})

            # Audit: Error occurred
            self.audit_chain.add_event(
                event_type="error",
                user_id_hash=user_id_hash if "user_id_hash" in locals() else "unknown",
                session_id=trace_id,
                data={"trace_id": trace_id, "error": str(e), "error_type": type(e).__name__},
            )

            raise

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status for load balancers"""
        health_status = self.health_monitor.check_health()

        return {
            "overall": health_status.overall.value,
            "ready": self.health_monitor.check_readiness(),
            "checks": health_status.checks,
            "failures": health_status.failures,
            "metrics": {
                "inference_circuit": self.inference_circuit.state.value,
                "routing_circuit": self.routing_circuit.state.value,
                "backpressure_queue": self.backpressure.queue_size,
                "audit_chain_valid": self.audit_chain.verify_chain(),
            },
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Export metrics for monitoring systems"""
        return {
            "counters": {
                "requests_total": self.metrics.get_counter("requests_total"),
                "security_validation_passed": self.metrics.get_counter(
                    "security.validation_passed"
                ),
                "risk_critical": self.metrics.get_counter("risk.level_critical"),
                "human_reviews_created": self.metrics.get_counter("human_review.created"),
            },
            "histograms": {
                "inference_latency": self.metrics.get_histogram_stats("inference.latency_ms"),
                "total_latency": self.metrics.get_histogram_stats("request.total_latency_ms"),
            },
        }


def main():
    """Example usage of production-hardened router"""

    # Load production configuration
    config = ProductionConfig()
    config.environment = Environment.PRODUCTION
    config.risk.always_human_for_critical = True
    config.security.enable_rate_limiting = True
    config.audit.enable_audit_chain = True

    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {errors}")

    # Initialize production router
    router = ProductionMentalHealthRouter(config)

    # Check health before accepting traffic
    health = router.get_health_status()
    print(f"System Health: {health['overall']}")
    print(f"Ready: {health['ready']}")

    # Example: Process a critical distress signal
    user_id = "user_12345"
    text = "I can't take this anymore, I have a plan to end it"
    location = GeoLocation(37.7749, -122.4194)  # San Francisco

    # Sign request (production best practice)
    signer = RequestSigner("production-secret-min-32-chars-required")
    signature, nonce = signer.sign_request({"user_id": user_id, "text": text})

    try:
        result = router.process_distress_signal(
            user_id=user_id,
            text=text,
            location=location,
            request_signature=signature,
            request_nonce=nonce,
        )

        print(f"\nProcessing Result:")
        print(f"  Risk Level: {result['risk_level']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Requires Human: {result['requires_human']}")
        print(f"  Resource: {result['resource']}")
        print(f"  Review ID: {result['review_id']}")
        print(f"  Trace ID: {result['trace_id']}")
        print(f"  Latency: {result['total_latency_ms']:.2f}ms")

    except Exception as e:
        print(f"Error processing request: {e}")

    # Export metrics
    metrics = router.get_metrics()
    print(f"\nMetrics:")
    print(f"  Total Requests: {metrics['counters']['requests_total']}")
    print(f"  Critical Cases: {metrics['counters']['risk_critical']}")


if __name__ == "__main__":
    main()

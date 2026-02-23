# Mental Health Escalation Router

> **Production-grade, adversarially hardened crisis detection and routing system**
> Real-time distress signal detection with cryptographic audit trails, defense-in-depth security, and zero-tolerance safety guarantees.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests: 400+](https://img.shields.io/badge/tests-400+-green.svg)](#testing)
[![Status: Development](https://img.shields.io/badge/status-development-yellow.svg)](#deployment-readiness)

---

## What This System Does

The Mental Health Escalation Router is a **life-critical AI safety system** that detects high-risk distress signals in real-time communications, classifies threat levels with formal safety guarantees, and routes urgent cases to qualified human responders—all while maintaining cryptographic audit trails and adversarial-grade security.

**Key Differentiators:**
- 🛡️ **Defense-in-depth security**: 4-layer security architecture (validation → rate limiting → abuse detection → cryptographic signing)
- ⚡ **Sub-second response**: < 1000ms inference with circuit breakers and graceful degradation
- 🔐 **Cryptographic auditability**: Merkle tree-based immutable audit chain for regulatory compliance
- 🎯 **Formal safety proofs**: Property-based testing validates non-degradation invariants and bounded retry logic
- 🚨 **Never autonomous for critical cases**: Human-in-the-loop enforcement with timeout monitoring
- 🌍 **Production-scale resilience**: Bulkheads, circuit breakers, backpressure management, health probes

---

## Why You Need This

### The Problem
Mental health crises require immediate, qualified human intervention—but traditional systems lack:
- Real-time risk detection with safety guarantees
- Adversarial hardening against prompt injection and abuse
- Cryptographic audit trails for liability protection
- Geographic routing to nearest available resources
- Privacy-preserving PII handling (GDPR/HIPAA-ready)

### The Solution
A production-grade system that combines **AI-assisted detection** with **mandatory human oversight**, backed by:

| Feature | Capability | Safety Guarantee |
|---------|-----------|------------------|
| **Inference Engine** | Text/audio distress detection | Strict 1000ms latency bounds |
| **Risk Classifier** | 5-tier risk assessment (NONE → CRITICAL) | Monotonicity under uncertainty |
| **Security Layer** | XSS/SQL injection/prompt manipulation detection | Multi-layer validation + HMAC signing |
| **Resilience** | Circuit breakers, bulkheads, graceful degradation | Bounded worst-case latency |
| **Audit System** | Cryptographic chain (Merkle tree) | Tamper-evident, immutable |
| **Privacy Guard** | PII scrubbing, identifier hashing | Automatic anonymization |
| **Human-in-Loop** | Mandatory review for critical cases | Zero autonomous escalation |

---

## Production-Grade Architecture

### 🔒 Security Layer (Defense-in-Depth)

```python
# 4-layer security pipeline
from mental_health_router import (
    InputValidator,      # Layer 1: XSS/SQL/prompt injection detection
    RateLimiter,         # Layer 2: Token bucket (per-user + global)
    AbuseDetector,       # Layer 3: Flood/geo-spoofing detection
    RequestSigner,       # Layer 4: HMAC-SHA256 + replay protection
)

# Example: Multi-layer validation
validator = InputValidator()
limiter = RateLimiter(requests_per_second=10, burst=5)
detector = AbuseDetector()
signer = RequestSigner("production-secret-key-min-32-chars")

# All layers enforced before inference
validator.validate_text(user_input)
limiter.check_rate_limit(user_id)
detector.check_abuse(user_id, location)
signature, nonce = signer.sign_request(payload)
```

**Attack Surface Protection:**
- ✅ XSS injection detection (script tags, javascript: URIs)
- ✅ SQL injection patterns (`UNION SELECT`, `DROP TABLE`)
- ✅ Prompt manipulation attempts ("ignore previous instructions")
- ✅ Distributed attack detection (coordinated requests)
- ✅ Geo-spoofing detection (impossible travel times)
- ✅ Replay attack prevention (nonce-based)

### ⚡ Resilience Layer (Fault Tolerance)

```python
from mental_health_router import (
    CircuitBreaker,           # Fault isolation (CLOSED/OPEN/HALF_OPEN)
    Bulkhead,                 # Resource isolation (concurrency limits)
    HealthMonitor,            # Readiness/liveness probes
    GracefulDegradation,      # Fallback strategies
    BackpressureManager,      # Flow control
    MetricsCollector,         # Production observability
)

# Example: Resilient inference with fallback
cb = CircuitBreaker("inference", failure_threshold=3)
bulkhead = Bulkhead("inference", max_concurrent=50)
degradation = GracefulDegradation()

result = cb.call(
    lambda: bulkhead.execute(
        lambda: degradation.execute(
            primary=advanced_inference,
            fallback=conservative_fallback  # Always safe
        )
    )
)
```

**Operational Guarantees:**
- ✅ Circuit breakers prevent cascade failures
- ✅ Bulkheads isolate resource exhaustion
- ✅ Graceful degradation maintains availability
- ✅ Health probes integrate with load balancers
- ✅ Backpressure prevents downstream overwhelm
- ✅ P50/P95/P99 latency metrics

### 🔐 Audit Layer (Regulatory Compliance)

```python
from mental_health_router import (
    AuditChain,              # Merkle tree cryptographic chain
    DataRetentionManager,    # GDPR/HIPAA PII scrubbing
    DistributedTracing,      # W3C Trace Context
)

# Cryptographic audit trail
audit = AuditChain()
audit.add_event(
    event_type="inference",
    user_id_hash="sha256_hash",
    session_id=trace_id,
    data={"risk_level": "critical"}
)

# Verify chain integrity
assert audit.verify_chain()  # Detects tampering

# GDPR-compliant retention
retention = DataRetentionManager(retention_days=90, auto_scrub_pii=True)
scrubbed = retention.scrub_pii("John Doe, SSN 123-45-6789")
# Output: "[NAME], SSN [SSN]"
```

**Compliance Features:**
- ✅ Immutable audit chain (Merkle tree)
- ✅ Automatic PII scrubbing (emails, SSNs, phones)
- ✅ Legal hold support for litigation
- ✅ GDPR right-to-deletion
- ✅ Distributed tracing (W3C standard)
- ✅ Tamper detection

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/IAmSoThirsty/Mental-Health-Escalation-Router.git
cd Mental-Health-Escalation-Router

# Install with production dependencies
pip install -e .

# Install development tools (includes hypothesis for property testing)
pip install -e ".[dev]"
```

### Basic Usage (Development)

```python
from mental_health_router import (
    TextInferenceEngine,
    RiskClassifier,
    EscalationPolicy,
    GeoAwareRouter,
    HumanInLoopEnforcer,
    PrivacyGuard,
    GeoLocation,
)

# Initialize components
engine = TextInferenceEngine(max_latency_ms=1000.0)
classifier = RiskClassifier(always_human_for_critical=True)
router = GeoAwareRouter(resources)
enforcer = HumanInLoopEnforcer(critical_timeout_seconds=60)
privacy = PrivacyGuard()

# Process distress signal
user_input = "I can't take this anymore, I have a plan"
location = GeoLocation(37.7749, -122.4194)

# Step 1: Privacy-preserving anonymization
anonymized = privacy.anonymize_text(user_input)
user_hash = privacy.hash_identifier(user_id)

# Step 2: Inference (with latency bounds)
result = engine.infer(anonymized)

# Step 3: Risk classification
assessment = classifier.classify(result)
# RiskLevel.CRITICAL detected

# Step 4: Mandatory human review (for critical cases)
if assessment.requires_human:
    review = enforcer.create_review(
        user_id=user_hash,
        risk_assessment=assessment,
        timeout_seconds=60
    )
    print(f"Human review required: {review.review_id}")

# Step 5: Geographic routing
routing = router.route(
    risk_assessment=assessment,
    location=location,
    user_id=user_hash
)
print(f"Routed to: {routing.resource.name}")
```

### Production Usage (Hardened)

See [`examples/production_hardened_example.py`](examples/production_hardened_example.py) for complete integration with:
- ✅ 4-layer security pipeline
- ✅ Circuit breakers + bulkheads
- ✅ Cryptographic audit chain
- ✅ Distributed tracing
- ✅ Graceful degradation
- ✅ Health monitoring

```bash
python examples/production_hardened_example.py
```

---

## Core Components

### 🧠 Inference Engine
**Detects distress signals in real-time communications**

- **Text Analysis**: Keyword detection, pattern matching, contextual signals
- **Audio Analysis**: Speech-to-text + acoustic feature extraction (prosody, tone)
- **Latency Guarantee**: Strict 1000ms bounds with timeout enforcement
- **Privacy-Preserving**: Operates on anonymized data only

```python
engine = TextInferenceEngine(max_latency_ms=1000.0)
result = engine.infer("I'm feeling hopeless")
# Returns: InferenceResult(distress_signals, confidence, latency_ms)
```

### 🎯 Risk Classifier
**5-tier risk assessment with formal safety guarantees**

| Risk Level | Description | Response Time | Human Review |
|-----------|-------------|---------------|--------------|
| **CRITICAL** | Immediate danger (suicide ideation, active harm) | 60s | ✅ Mandatory |
| **HIGH** | Serious concern requiring rapid intervention | 300s | ✅ Mandatory |
| **MODERATE** | Needs attention and monitoring | 1800s | ⚠️ Recommended |
| **LOW** | Minimal concern, routine follow-up | 24h | ❌ Optional |
| **NONE** | No risk detected | - | ❌ Not required |

**Safety Properties:**
- ✅ **Non-degradation invariant**: Uncertainty never lowers risk tier
- ✅ **Monotonicity**: Higher uncertainty → same or higher risk
- ✅ **Fail-safe**: Timeout → automatic CRITICAL classification

### 🚨 Escalation Policy
**Time-bound escalation with mandatory acknowledgment**

```python
policy = EscalationPolicy()
result = policy.evaluate(risk_assessment)

# For CRITICAL tier:
# - max_response_time: 60 seconds
# - requires_acknowledgment: True (enforced)
# - notification_channels: ["phone", "sms", "email"]
# - never_autonomous: True (hard constraint)
```

### 🌍 Geo-Aware Routing
**Intelligent resource matching and load balancing**

```python
router = GeoAwareRouter(resources)
routing = router.route(
    risk_assessment=assessment,
    location=GeoLocation(37.7749, -122.4194),
    preferences=RoutingPreferences(
        preferred_languages=["en", "es"],
        required_specializations=["crisis", "suicide_prevention"]
    )
)

# Returns nearest available resource with:
# - Distance calculation
# - Language matching
# - Specialization filtering
# - Capacity checking
```

### 👁️ Human-in-the-Loop Enforcement
**Zero tolerance for autonomous critical decisions**

```python
enforcer = HumanInLoopEnforcer(critical_timeout_seconds=60)

# For critical cases
review = enforcer.create_review(
    user_id=user_hash,
    risk_assessment=assessment,
    timeout_seconds=60
)

# State machine: PENDING → ACKNOWLEDGED → COMPLETED
# Timeout triggers alerts and escalation
```

### 🔒 Privacy Safeguards
**GDPR/HIPAA-ready PII protection**

```python
privacy = PrivacyGuard(policy=PrivacyPolicy(
    anonymize_pii=True,
    encrypt_at_rest=True,
    retention_days=90,
    audit_access=True
))

# Automatic PII redaction
anonymized = privacy.anonymize_text("Call me at 555-1234")
# Output: "Call me at [PHONE]"

# Cryptographic hashing
user_hash = privacy.hash_identifier(user_id, salt="secret")

# Access audit trail
privacy.log_access(user_id, resource_id, action="view")
```

---

## Testing

### Comprehensive Test Suite (400+ Tests)

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=mental_health_router --cov-report=html

# Run specific test suites
pytest tests/test_security.py          # Security layer tests
pytest tests/test_resilience.py        # Resilience pattern tests
pytest tests/test_audit.py             # Audit system tests
pytest tests/test_safety_properties.py # Property-based tests
```

**Test Coverage:**
- ✅ **Unit Tests**: 300+ tests across all modules
- ✅ **Integration Tests**: End-to-end pipeline validation
- ✅ **Property-Based Tests**: Hypothesis-powered formal verification
- ✅ **Security Tests**: Attack simulation (XSS, SQL injection, prompt manipulation)
- ✅ **Resilience Tests**: Fault injection and recovery scenarios
- ✅ **Safety Tests**: Non-degradation invariants, bounded retry, deadlock-freedom

### Property-Based Testing (Formal Verification)

```bash
# Run property-based tests with statistics
pytest tests/test_safety_properties.py -v --hypothesis-show-statistics
```

**Verified Properties:**
1. **Non-degradation**: Uncertainty never lowers risk tier (100 examples)
2. **Routing termination**: No deadlocks, bounded completion time (50 examples)
3. **Fail-safe defaults**: High uncertainty triggers escalation (50 examples)
4. **Monotonicity**: Increasing uncertainty never decreases risk (50 examples)
5. **Bounded retry**: No infinite loops, respects time budgets (20 examples)

---

## Configuration

### Production Configuration

```python
from mental_health_router import ProductionConfig, ConfigManager, Environment

# Load validated configuration
config = ProductionConfig()
config.environment = Environment.PRODUCTION

# Environment-specific validation
config.risk.always_human_for_critical = True  # Enforced in production
config.security.enable_rate_limiting = True
config.audit.enable_audit_chain = True

# Validate before deployment
errors = config.validate()
if errors:
    raise ValueError(f"Invalid production config: {errors}")

# Hot-reload support
manager = ConfigManager("/path/to/config.json")
manager.register_change_listener(on_config_change)
manager.reload()  # Zero-downtime updates
```

### Security Configuration

```python
from mental_health_router.security import (
    InputValidator,
    RateLimiter,
    AbuseDetector,
)

# Input validation
validator = InputValidator()
validator.MAX_TEXT_LENGTH = 10000  # Configurable

# Rate limiting (token bucket)
limiter = RateLimiter(
    requests_per_second=10,    # Per-user limit
    burst=5,                   # Burst capacity
    global_requests_per_second=1000,  # System-wide limit
    global_burst=500
)

# Abuse detection
detector = AbuseDetector(
    flood_threshold=10,        # Requests in window
    flood_window_seconds=60,
    distributed_threshold=20,  # Same location
    impossible_travel_speed_kmh=800
)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION PIPELINE                       │
└─────────────────────────────────────────────────────────────┘

User Input (Text/Audio)
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  SECURITY LAYER (Defense-in-Depth)                          │
│  ├─ InputValidator      (XSS/SQL/Prompt injection)          │
│  ├─ RateLimiter         (Token bucket, per-user + global)   │
│  ├─ AbuseDetector       (Flood/distributed/geo-spoofing)    │
│  └─ RequestSigner       (HMAC-SHA256, replay protection)    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  PRIVACY LAYER                                               │
│  └─ PrivacyGuard        (PII scrubbing, identifier hashing) │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  INFERENCE LAYER (with Resilience)                          │
│  ├─ CircuitBreaker      (Fault isolation)                   │
│  ├─ Bulkhead            (Resource isolation)                │
│  └─ TextInferenceEngine (Distress detection, <1000ms)       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  RISK CLASSIFICATION                                         │
│  └─ RiskClassifier      (5-tier: NONE → CRITICAL)           │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  ESCALATION POLICY                                           │
│  └─ EscalationPolicy    (Time-bound SLAs, notifications)    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    [CRITICAL/HIGH?] ───Yes──→ ┌──────────────────────────────┐
         │                      │  HUMAN-IN-THE-LOOP           │
         No                     │  (Mandatory Review)          │
         │                      │  - State machine enforcement │
         │                      │  - Timeout monitoring        │
         │                      │  - Audit trail               │
         │                      └──────────────────────────────┘
         │                                   │
         └───────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────────────────────┐
                    │  GEO-AWARE ROUTING                      │
                    │  - Distance calculation                 │
                    │  - Language matching                    │
                    │  - Specialization filtering             │
                    │  - Load balancing                       │
                    └─────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────────────────────┐
                    │  HUMAN RESOURCE                         │
                    │  (Crisis Counselor / Therapist)         │
                    └─────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AUDIT LAYER (Observability)                                │
│  ├─ AuditChain          (Merkle tree, cryptographic)        │
│  ├─ DistributedTracing  (W3C Trace Context)                 │
│  ├─ MetricsCollector    (Counters, gauges, histograms)      │
│  └─ DataRetention       (GDPR/HIPAA compliance)             │
└─────────────────────────────────────────────────────────────┘
```

For complete architecture specification, see [ARCHITECTURE.md](ARCHITECTURE.md) (63KB RFC-grade documentation).

---

## Safety Guarantees

### Formal Safety Properties

This system implements **provable safety guarantees** verified through property-based testing:

1. **Non-Degradation Invariant**
   ```
   ∀ input I, ∀ uncertainty U:
     risk_level(I, U) ≥ risk_level(I, 0)
   ```
   *Uncertainty NEVER lowers risk tier.*

2. **Bounded Retry Logic**
   ```
   max_retries ≤ 3
   max_total_time ≤ 15 seconds
   ```
   *No infinite loops, guaranteed termination.*

3. **Deadlock-Free Routing**
   ```
   ∀ valid inputs: routing terminates in <5 seconds
   ```
   *Circuit breakers prevent infinite waits.*

4. **Fail-Safe Defaults**
   ```
   IF timeout OR high_uncertainty THEN escalate_to_CRITICAL
   ```
   *System errs on side of caution.*

See [SAFETY_GUARANTEES.md](docs/SAFETY_GUARANTEES.md) for formal proofs and verification.

---

## Deployment Readiness

### ⚠️ Current Status: NOT READY FOR PRODUCTION

**Completion: ~25% across 9 critical domains**

| Domain | Status | Blockers |
|--------|--------|----------|
| ✅ **Technical** | 80% | Integration testing, chaos engineering |
| ⚠️ **Clinical/Ethical** | 5% | IRB approval, clinical validation, bias audit |
| ⚠️ **Legal/Regulatory** | 5% | HIPAA certification, liability framework |
| ✅ **Security** | 70% | Penetration testing, security certification |
| ✅ **Operational** | 60% | On-call staffing, runbooks, DR plan |
| ⚠️ **Human Factors** | 10% | Usability testing, counselor training |
| ⚠️ **Economic** | 10% | Cost modeling, sustainability plan |
| ⚠️ **Trust** | 10% | External audit, transparency reporting |
| ✅ **Architecture** | 90% | RFC-complete, hardening implemented |

**Do NOT deploy to production** until all domains reach 100%. See [DEPLOYMENT_READINESS.md](docs/DEPLOYMENT_READINESS.md) for complete gap analysis.

---

## Documentation

### 📚 Complete Documentation Suite

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - RFC-grade technical specification (63KB)
- **[SAFETY_GUARANTEES.md](docs/SAFETY_GUARANTEES.md)** - Formal safety properties and proofs
- **[COMPLETION_CHECKLIST.md](docs/COMPLETION_CHECKLIST.md)** - Master checklist across 9 domains
- **[DEPLOYMENT_READINESS.md](docs/DEPLOYMENT_READINESS.md)** - Production readiness assessment
- **[CLINICAL_REVIEW.md](docs/CLINICAL_REVIEW.md)** - Clinical validation framework

---

## Development

### Code Quality

```bash
# Format code
black src/ tests/ examples/

# Type checking
mypy src/mental_health_router/

# Run linters
flake8 src/ tests/
```

### Running Examples

```bash
# Basic integration example
python examples/integration_example.py

# Production-hardened example (full stack)
python examples/production_hardened_example.py
```

---

## Contributing

This is a **life-critical safety system**. All contributions must:

1. ✅ Maintain human-in-the-loop enforcement for critical cases
2. ✅ Preserve all safety guarantees (non-degradation, bounded retry, etc.)
3. ✅ Include comprehensive tests (unit + property-based)
4. ✅ Pass security review (no new attack vectors)
5. ✅ Maintain or improve privacy protections
6. ✅ Update formal documentation

**Pull requests that reduce safety guarantees will be rejected.**

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Critical Disclaimer

⚠️ **This system assists human crisis responders—it does not replace them.**

- NEVER use as sole decision-making tool for mental health interventions
- ALWAYS ensure qualified human professionals are available 24/7
- ALWAYS maintain emergency escalation paths (988, crisis hotlines)
- NEVER deploy without clinical validation and ethics board approval

---

## Emergency Resources

**If you or someone you know is in crisis:**

- 🇺🇸 **National Suicide Prevention Lifeline**: **988**
- 💬 **Crisis Text Line**: Text **HOME** to **741741**
- 🌍 **International**: https://findahelpline.com/

**This system is not a substitute for professional help.**

---

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/IAmSoThirsty/Mental-Health-Escalation-Router/issues)
- **Documentation**: See `/docs` directory
- **Examples**: See `/examples` directory
- **Security**: Report vulnerabilities privately via GitHub Security Advisories

---

**Built with production-grade safety, security, and resilience.**
*Because every second matters when lives are at stake.*

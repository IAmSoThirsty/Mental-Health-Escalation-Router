# Mental Health Escalation Router

Real-time detection of high-risk distress signals and safe routing to human resources.

## Overview

The Mental Health Escalation Router is a critical safety system designed to detect distress signals in text and audio communications, classify risk levels, and route high-risk cases to appropriate human resources while maintaining strict privacy and safety guardrails.

## Core Components

### 1. Text/Audio Inference Engine
- **TextInferenceEngine**: Analyzes text for distress signals using keyword detection and pattern matching
- **AudioInferenceEngine**: Placeholder for audio analysis (speech-to-text + acoustic features)
- **Strict Latency Bounds**: Configurable maximum inference time (default: 1000ms)
- **Privacy-Preserving**: Works with anonymized data

### 2. Risk Classifier
Classifies distress signals into five risk levels:
- **CRITICAL**: Immediate danger (suicidal ideation, imminent harm)
- **HIGH**: Serious concern requiring rapid escalation
- **MODERATE**: Needs attention and monitoring
- **LOW**: Minimal concern
- **NONE**: No risk detected

Key features:
- Confidence scoring
- Automatic human review requirement for critical/high risks
- Reasoning explanations for transparency

### 3. Escalation Policy Engine
Manages escalation rules with strict enforcement:
- **Critical Tier**: NEVER fully autonomous - always requires human acknowledgment
- **Time-Based SLAs**: Maximum response times per risk level (60s for critical)
- **Multi-Channel Notifications**: Phone, SMS, email, push notifications
- **Validation**: Ensures critical tier policies meet safety requirements

### 4. Geo-Aware Routing
Routes cases to appropriate human resources:
- **Distance-Based Matching**: Finds nearest available resources
- **Language Preferences**: Matches resources by language capabilities
- **Specialization Filtering**: Routes to specialists (crisis, suicide prevention, etc.)
- **Availability Management**: Tracks resource capacity and status

### 5. Human-in-the-Loop Enforcement
Ensures critical decisions are never autonomous:
- **Required Review**: Critical/high-risk cases require human acknowledgment
- **Timeout Monitoring**: Tracks and alerts on review timeouts
- **Audit Trail**: Complete tracking of human reviews and actions
- **Blocking Mode**: Can halt processing until human review is complete

### 6. Privacy Safeguards
Comprehensive privacy protection:
- **PII Anonymization**: Automatic redaction of emails, phone numbers, SSNs
- **Identifier Hashing**: Privacy-preserving hashing with optional salting
- **Access Logging**: Audit trail of all data access
- **Configurable Policies**: Encryption, retention, sensitivity levels
- **HIPAA/GDPR Considerations**: Designed for healthcare data compliance

## Constraints & Safety Features

### Never Fully Autonomous in Critical Tier
- Critical risk assessments ALWAYS require human review
- System will block or timeout if human doesn't acknowledge
- Multiple notification channels ensure human awareness
- Validation prevents misconfiguration that bypasses human review

### Strict Latency Bounds
- Configurable maximum inference time (default: 1000ms for text)
- TimeoutError raised if bounds exceeded
- Latency tracking included in all results
- Optimized for real-time processing

### Privacy Safeguards
- Automatic PII detection and anonymization
- All identifiers can be hashed
- Access logging for compliance
- Configurable data retention policies
- Sanitization for logs to prevent PII leakage

## Installation

```bash
# Clone the repository
git clone https://github.com/IAmSoThirsty/Mental-Health-Escalation-Router.git
cd Mental-Health-Escalation-Router

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

## Quick Start

```python
from mental_health_router import (
    TextInferenceEngine,
    RiskClassifier,
    EscalationPolicy,
    GeoAwareRouter,
    HumanInLoopEnforcer,
    PrivacyGuard,
    GeoLocation,
    HumanResource,
    ResourceStatus,
)

# Initialize components
inference_engine = TextInferenceEngine(max_latency_ms=1000.0)
risk_classifier = RiskClassifier(always_human_for_critical=True)
escalation_policy = EscalationPolicy()
router = GeoAwareRouter()
human_enforcer = HumanInLoopEnforcer(critical_timeout_seconds=60)
privacy_guard = PrivacyGuard()

# Add human resources
router.add_resource(HumanResource(
    id="hr_001",
    name="Crisis Counselor",
    location=GeoLocation(latitude=37.7749, longitude=-122.4194),
    status=ResourceStatus.AVAILABLE,
    specializations=["crisis", "suicide_prevention"],
))

# Process input
user_input = "I'm feeling hopeless and can't go on"
user_location = GeoLocation(latitude=37.7749, longitude=-122.4194)

# Step 1: Anonymize for privacy
anonymized = privacy_guard.anonymize_text(user_input)

# Step 2: Run inference
inference_result = inference_engine.infer(anonymized)

# Step 3: Classify risk
risk_assessment = risk_classifier.classify(inference_result)

# Step 4: Check if human review required
if human_enforcer.requires_human_review(risk_assessment):
    review_id = human_enforcer.request_review(risk_assessment)
    print(f"Human review required: {review_id}")

# Step 5: Route to appropriate resource
if escalation_policy.requires_immediate_escalation(risk_assessment):
    routing_result = router.route(user_location)
    print(f"Routed to: {routing_result['resource'].name}")
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mental_health_router --cov-report=html

# Run specific test file
pytest tests/test_inference_engine.py
```

## Examples

See `examples/integration_example.py` for a complete end-to-end example:

```bash
python examples/integration_example.py
```

## Architecture

```
User Input (Text/Audio)
    ↓
Privacy Guard (Anonymize PII)
    ↓
Inference Engine (Detect Distress Signals)
    ↓
Risk Classifier (Determine Risk Level)
    ↓
Escalation Policy (Check Rules)
    ↓
[If Critical/High Risk]
    ↓
Human-in-the-Loop Enforcer (Request Review)
    ↓
Geo-Aware Router (Find Nearest Resource)
    ↓
Human Resource (Crisis Counselor/Therapist)
```

## API Reference

### TextInferenceEngine

```python
engine = TextInferenceEngine(max_latency_ms=1000.0)
result = engine.infer("text to analyze")
# Returns: InferenceResult with distress_signals, confidence, latency_ms
```

### RiskClassifier

```python
classifier = RiskClassifier(always_human_for_critical=True)
assessment = classifier.classify(inference_result)
# Returns: RiskAssessment with risk_level, confidence, requires_human
```

### EscalationPolicy

```python
policy = EscalationPolicy()  # Uses default rules
rules = policy.get_applicable_rules(risk_assessment)
requires_immediate = policy.requires_immediate_escalation(risk_assessment)
```

### GeoAwareRouter

```python
router = GeoAwareRouter()
router.add_resource(human_resource)
result = router.route(user_location, preferences)
# Returns: routing result with resource and distance
```

### HumanInLoopEnforcer

```python
enforcer = HumanInLoopEnforcer(critical_timeout_seconds=60)
review_id = enforcer.request_review(risk_assessment)
enforcer.acknowledge_review(review_id, reviewer_id)
enforcer.complete_review(review_id, action_taken, notes)
```

### PrivacyGuard

```python
guard = PrivacyGuard()
anonymized = guard.anonymize_text(text)
hashed_id = guard.hash_identifier(user_id)
guard.log_access(user_id, resource_id, action)
```

## Configuration

### Latency Configuration

```python
# Adjust max latency for inference
engine = TextInferenceEngine(max_latency_ms=500.0)  # 500ms max
```

### Escalation Rules

```python
from mental_health_router.escalation_policy import EscalationRule
from mental_health_router.risk_classifier import RiskLevel

custom_rule = EscalationRule(
    risk_level=RiskLevel.CRITICAL,
    requires_immediate=True,
    max_response_time_seconds=30,  # 30 seconds
    notification_channels=["phone", "sms"],
    requires_acknowledgment=True
)

policy = EscalationPolicy(rules=[custom_rule])
```

### Privacy Policy

```python
from mental_health_router.privacy import PrivacyPolicy, DataSensitivity

policy = PrivacyPolicy(
    anonymize_pii=True,
    encrypt_at_rest=True,
    retention_days=90,
    audit_access=True,
    minimum_sensitivity=DataSensitivity.RESTRICTED
)

guard = PrivacyGuard(policy=policy)
```

## Safety Considerations

1. **Never Disable Human Review**: The system is designed to ALWAYS require human review for critical cases. Disabling this would be dangerous.

2. **Latency vs. Accuracy**: While latency bounds are enforced, ensure they're not so strict that accuracy suffers.

3. **Privacy First**: Always anonymize before processing. Never log PII.

4. **Resource Availability**: Ensure adequate human resources are available and monitoring is in place for timeouts.

5. **Escalation Coverage**: Test escalation paths thoroughly, especially notification channels.

6. **False Negatives**: The system is tuned to err on the side of caution (more false positives than false negatives).

## Development

### Code Formatting
```bash
black src/ tests/
```

### Type Checking
```bash
mypy src/mental_health_router/
```

### Running Examples
```bash
python examples/integration_example.py
```

## License

MIT License - see LICENSE file for details

## Contributing

This is a critical safety system. All contributions must:
1. Maintain strict human-in-the-loop enforcement for critical cases
2. Preserve privacy safeguards
3. Include comprehensive tests
4. Not reduce safety guarantees

## Disclaimer

This system is designed to assist human crisis responders, not replace them. It should never be used as the sole decision-making tool for mental health interventions. Always ensure qualified human professionals are available to respond to escalated cases.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Crisis Resources

If you or someone you know is in crisis:
- **National Suicide Prevention Lifeline**: 988 (US)
- **Crisis Text Line**: Text HOME to 741741 (US)
- **International**: https://findahelpline.com/

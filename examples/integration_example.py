"""
Integration Example: Mental Health Escalation Router

Demonstrates how all components work together for real-time distress detection
and safe routing to human resources.
"""

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
    RoutingPreferences,
)


def process_distress_signal(
    input_text: str,
    user_location: GeoLocation,
    user_id: str
) -> dict:
    """
    Complete end-to-end processing of a distress signal.

    Args:
        input_text: Text input from user
        user_location: User's geographical location
        user_id: User identifier

    Returns:
        Dictionary containing processing results and actions taken
    """
    # Initialize components
    inference_engine = TextInferenceEngine(max_latency_ms=1000.0)
    risk_classifier = RiskClassifier(always_human_for_critical=True)
    escalation_policy = EscalationPolicy()
    router = GeoAwareRouter()
    human_enforcer = HumanInLoopEnforcer(critical_timeout_seconds=60)
    privacy_guard = PrivacyGuard()

    # Add some human resources (in production, these would come from a database)
    router.add_resource(HumanResource(
        id="hr_001",
        name="Crisis Counselor A",
        location=GeoLocation(latitude=37.7749, longitude=-122.4194),  # San Francisco
        status=ResourceStatus.AVAILABLE,
        specializations=["crisis", "suicide_prevention"],
        max_concurrent_cases=3,
        current_cases=1
    ))

    router.add_resource(HumanResource(
        id="hr_002",
        name="Therapist B",
        location=GeoLocation(latitude=40.7128, longitude=-74.0060),  # New York
        status=ResourceStatus.AVAILABLE,
        specializations=["crisis", "depression"],
        max_concurrent_cases=2,
        current_cases=0
    ))

    # Step 1: Privacy protection - anonymize input before processing
    anonymized_text = privacy_guard.anonymize_text(input_text)
    privacy_guard.log_access(
        user_id=user_id,
        resource_id="distress_signal",
        action="process",
        metadata={"text_length": len(input_text)}
    )

    # Step 2: Run inference engine with strict latency bounds
    try:
        inference_result = inference_engine.infer(anonymized_text)
    except TimeoutError as e:
        return {
            "success": False,
            "error": str(e),
            "action": "timeout_fallback"
        }

    # Step 3: Classify risk level
    risk_assessment = risk_classifier.classify(inference_result)

    # Step 4: Check escalation policy
    applicable_rules = escalation_policy.get_applicable_rules(risk_assessment)
    requires_immediate = escalation_policy.requires_immediate_escalation(risk_assessment)

    # Step 5: Human-in-the-loop enforcement for critical cases
    review_id = None
    if human_enforcer.requires_human_review(risk_assessment):
        review_id = human_enforcer.request_review(
            risk_assessment=risk_assessment,
            context={
                "user_location": {
                    "lat": user_location.latitude,
                    "lon": user_location.longitude
                },
                "inference_latency_ms": inference_result.latency_ms
            }
        )

    # Step 6: Geo-aware routing to appropriate resources
    routing_result = None
    if requires_immediate:
        preferences = RoutingPreferences(
            max_distance_km=100.0,
            preferred_language="en",
            required_specializations=["crisis"]
        )
        routing_result = router.route(user_location, preferences)

    # Step 7: Compile results
    result = {
        "success": True,
        "risk_level": risk_assessment.risk_level.value,
        "confidence": risk_assessment.confidence,
        "requires_human": risk_assessment.requires_human,
        "reasoning": risk_assessment.reasoning,
        "inference_latency_ms": inference_result.latency_ms,
        "requires_immediate_escalation": requires_immediate,
        "review_id": review_id,
        "notification_channels": escalation_policy.get_notification_channels(risk_assessment),
        "max_response_time_seconds": escalation_policy.get_max_response_time(risk_assessment),
        "routing": routing_result
    }

    return result


def main():
    """Example usage of the Mental Health Escalation Router"""

    print("Mental Health Escalation Router - Example Usage\n")
    print("=" * 60)

    # Example 1: Low-risk message
    print("\n1. Processing low-risk message...")
    result1 = process_distress_signal(
        input_text="I'm feeling a bit down today, but I'll be okay.",
        user_location=GeoLocation(latitude=37.7749, longitude=-122.4194),
        user_id="user_123"
    )
    print(f"   Risk Level: {result1['risk_level']}")
    print(f"   Confidence: {result1['confidence']:.3f}")
    print(f"   Requires Human: {result1['requires_human']}")
    print(f"   Latency: {result1['inference_latency_ms']:.1f}ms")

    # Example 2: High-risk message
    print("\n2. Processing high-risk message...")
    result2 = process_distress_signal(
        input_text="I feel completely hopeless and don't know how to go on.",
        user_location=GeoLocation(latitude=40.7128, longitude=-74.0060),
        user_id="user_456"
    )
    print(f"   Risk Level: {result2['risk_level']}")
    print(f"   Confidence: {result2['confidence']:.3f}")
    print(f"   Requires Human: {result2['requires_human']}")
    print(f"   Review ID: {result2['review_id']}")
    print(f"   Notification Channels: {result2['notification_channels']}")
    print(f"   Max Response Time: {result2['max_response_time_seconds']}s")

    # Example 3: Critical message (requires immediate human intervention)
    print("\n3. Processing CRITICAL message...")
    result3 = process_distress_signal(
        input_text="I want to kill myself. I can't take this anymore.",
        user_location=GeoLocation(latitude=37.7749, longitude=-122.4194),
        user_id="user_789"
    )
    print(f"   Risk Level: {result3['risk_level']}")
    print(f"   Confidence: {result3['confidence']:.3f}")
    print(f"   Requires Human: {result3['requires_human']}")
    print(f"   Requires Immediate Escalation: {result3['requires_immediate_escalation']}")
    print(f"   Review ID: {result3['review_id']}")
    print(f"   Max Response Time: {result3['max_response_time_seconds']}s (URGENT)")
    if result3['routing'] and result3['routing']['success']:
        print(f"   Routed to: {result3['routing']['resource'].name}")
        print(f"   Distance: {result3['routing']['distance_km']:.1f} km")

    print("\n" + "=" * 60)
    print("\nKey Safety Features:")
    print("  ✓ Strict latency bounds enforced")
    print("  ✓ Never fully autonomous in critical tier")
    print("  ✓ Human-in-the-loop enforcement")
    print("  ✓ Privacy safeguards (PII anonymization)")
    print("  ✓ Geo-aware routing to closest resources")
    print("  ✓ Escalation policy with time constraints")


if __name__ == "__main__":
    main()

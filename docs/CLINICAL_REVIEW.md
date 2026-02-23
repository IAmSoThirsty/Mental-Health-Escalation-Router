# Clinical Review & Validation Framework

**Document Type**: Clinical Standards
**Version**: 0.1.0
**Status**: Draft - Awaiting Clinical Board Approval
**Last Updated**: 2026-02-23

---

## 1. Clinical Review Board Requirements

### 1.1 Board Composition

**Minimum Requirements**:
- 3-5 independent mental health professionals
- At least one licensed clinical psychologist (PhD or PsyD)
- At least one licensed psychiatrist (MD or DO)
- At least one crisis intervention specialist
- At least one ethics specialist with mental health background

**Qualifications**:
- Active clinical practice (minimum 5 years)
- Crisis intervention experience
- No financial interest in the system
- Diverse demographic representation

### 1.2 Review Scope

The Clinical Review Board SHALL evaluate:

1. **Escalation Logic Validity**
   - Alignment with evidence-based crisis intervention
   - Consistency with C-SSRS (Columbia-Suicide Severity Rating Scale)
   - Appropriateness of risk level thresholds

2. **Harm Minimization Strategies**
   - False negative mitigation approaches
   - Human-in-the-loop enforcement
   - Timeout and failover procedures

3. **Communication Protocols**
   - Messaging appropriateness for each risk tier
   - Non-alarmist language for low-risk cases
   - Immediate response for high-risk cases

4. **Bias and Fairness**
   - Demographic equity in detection
   - Cultural sensitivity
   - Language appropriateness

---

## 2. Validation Against Crisis Intervention Standards

### 2.1 C-SSRS Alignment

**Columbia-Suicide Severity Rating Scale Mapping**:

| C-SSRS Level | Description | MHER Risk Level | Human Review |
|--------------|-------------|-----------------|--------------|
| **Level 5** | Active ideation with plan and intent | CRITICAL | MANDATORY (60s) |
| **Level 4** | Active ideation with some intent | CRITICAL | MANDATORY (60s) |
| **Level 3** | Active ideation without plan/intent | HIGH | REQUIRED (5min) |
| **Level 2** | Non-specific active thoughts | MODERATE | OPTIONAL |
| **Level 1** | Wish to be dead (passive) | MODERATE | OPTIONAL |
| **N/A** | No ideation | LOW/NONE | NOT REQUIRED |

**Validation Requirements**:
```python
def validate_c_ssrs_alignment():
    """
    Ensure MHER risk classification aligns with C-SSRS levels

    Test cases:
        - "I have a plan to kill myself" → CRITICAL (C-SSRS 5)
        - "I want to die but have no plan" → HIGH (C-SSRS 3)
        - "I wish I wasn't here" → MODERATE (C-SSRS 1-2)
    """
    test_cases = [
        ("I'm going to kill myself tomorrow", RiskLevel.CRITICAL, CSSRS.LEVEL_5),
        ("I have pills and plan to take them", RiskLevel.CRITICAL, CSSRS.LEVEL_5),
        ("I want to die", RiskLevel.HIGH, CSSRS.LEVEL_3),
        ("I wish I wasn't alive", RiskLevel.MODERATE, CSSRS.LEVEL_1),
    ]

    for input_text, expected_risk, expected_cssrs in test_cases:
        result = classify_text(input_text)
        assert result.risk_level == expected_risk
        assert map_to_cssrs(result) == expected_cssrs
```

### 2.2 Evidence-Based Intervention Principles

**Core Principles** (American Foundation for Suicide Prevention):

1. **Immediacy**: High-risk cases require immediate human contact
   - ✅ Implementation: CRITICAL tier max 60s response time

2. **Continuity**: Follow-up and ongoing support
   - ⬜ TODO: Post-crisis follow-up protocol

3. **Safety Planning**: Collaborative crisis planning
   - ⬜ TODO: Integrated safety plan generation

4. **Means Restriction**: Reduce access to lethal means
   - ⬜ TODO: Resource referrals for means restriction

5. **Empathetic Listening**: Non-judgmental support
   - ⬜ TODO: Reviewer training in active listening

---

## 3. Harm Minimization Documentation

### 3.1 False Negative Mitigation

**Objective**: Minimize missed high-risk cases

**Strategies**:

1. **Conservative Classification**
   - Threshold bias toward over-escalation
   - CRITICAL threshold: 0.7 (vs. typical 0.9)
   - Ambiguity bands trigger human review (0.4-0.6)

2. **Fail-Safe Defaults**
   ```python
   # If uncertain, escalate
   if confidence < 0.6 and distress_signals:
       risk_level = elevate_risk_tier(base_risk_level)
       requires_human = True
   ```

3. **Secondary Heuristics**
   - Keyword fallback if ML fails
   - Context analysis (time of day, prior history)
   - Multi-modal signals (text + tone for audio)

4. **Timeout Escalation**
   ```python
   # If inference times out, assume CRITICAL
   try:
       result = inference_engine.infer(input_data)
   except TimeoutError:
       return create_critical_fail_safe_result()
   ```

**Acceptable Miss Rate**:
- CRITICAL signals: <0.1% (1 in 1,000)
- HIGH signals: <1% (1 in 100)
- Monitored continuously with clinical expert review

### 3.2 False Positive Management

**Objective**: Avoid alarm fatigue while maintaining safety

**Strategies**:

1. **Tiered Messaging**
   - CRITICAL: "Connecting you with crisis support immediately"
   - HIGH: "A counselor will reach out soon to check in"
   - MODERATE: "Resources are available if you need support"

2. **User Opt-Out** (for non-critical)
   ```python
   if risk_level in [RiskLevel.LOW, RiskLevel.MODERATE]:
       allow_user_dismissal = True
   else:
       allow_user_dismissal = False  # Cannot dismiss CRITICAL
   ```

3. **Confidence Transparency**
   - Show confidence levels to reviewers
   - Allow human override of false positives
   - Track override rates for calibration

**Acceptable False Positive Rate**:
- Overall: <30%
- CRITICAL tier: <5% (high precision required)

---

## 4. Clinical Validation Process

### 4.1 Dataset Requirements

**Ground Truth Dataset**:
- Minimum 10,000 labeled examples
- Expert labels from 2+ clinicians per example
- Diverse demographics (age, gender, ethnicity, culture)
- Multiple languages (English, Spanish, Mandarin minimum)
- Balanced risk levels (not just negative examples)

**Label Quality**:
```python
def validate_label_quality(dataset):
    """
    Ensure high-quality ground truth

    Requirements:
        - Inter-rater reliability (Cohen's kappa) > 0.8
        - Coverage of all risk levels
        - Demographic diversity
    """
    kappa = compute_inter_rater_reliability(dataset)
    assert kappa > 0.8, f"Inter-rater reliability too low: {kappa}"

    for risk_level in RiskLevel:
        count = dataset[dataset.label == risk_level].shape[0]
        assert count >= 100, f"Insufficient examples for {risk_level}: {count}"
```

### 4.2 Validation Metrics

**Primary Metrics**:

1. **Sensitivity (Recall) for CRITICAL**
   ```
   Sensitivity = TP / (TP + FN)
   Target: >99.9% (catch >999 in 1,000)
   ```

2. **Specificity for NONE**
   ```
   Specificity = TN / (TN + FP)
   Target: >70% (avoid excessive false alarms)
   ```

3. **Balanced Accuracy**
   ```
   Balanced_Acc = (Sensitivity + Specificity) / 2
   Target: >85%
   ```

**Secondary Metrics**:
- Area Under ROC Curve (AUC): >0.95
- F1 Score (CRITICAL): >0.95
- Positive Predictive Value (CRITICAL): >0.90

### 4.3 Clinical Expert Review

**Review Process**:

1. **Sample Review** (Monthly)
   - Random sample of 100 cases per month
   - Expert labels vs. system predictions
   - Disagreement analysis

2. **High-Stakes Review** (All CRITICAL)
   - 100% of CRITICAL classifications reviewed
   - Within 24 hours of escalation
   - Feedback loop to improve model

3. **Bias Audit** (Quarterly)
   - Stratified performance by demographics
   - Identify and correct disparities

**Review Template**:
```markdown
Case ID: [auto-generated]
Input: [anonymized]
System Risk Level: [CRITICAL/HIGH/etc.]
System Confidence: [0.0-1.0]

Expert Review:
- Clinical Risk Level: [expert assessment]
- Agreement: [Yes/No]
- If Disagree: [reasoning]
- Recommendations: [free text]

Reviewer: [credential]
Date: [ISO timestamp]
```

---

## 5. Ethical Considerations

### 5.1 Autonomy vs. Beneficence

**Tension**: Respecting user autonomy while preventing harm

**Resolution**:
- CRITICAL tier: Beneficence overrides autonomy (life-threatening)
- HIGH tier: Strong encouragement, but user can decline
- MODERATE/LOW: Purely informational, user choice

**Implementation**:
```python
def respect_autonomy(risk_level: RiskLevel, user_response: str) -> Action:
    """
    Balance autonomy with harm prevention

    CRITICAL: No opt-out (life-threatening)
    HIGH: Persistent encouragement, but ultimate user choice
    MODERATE/LOW: Fully optional resources
    """
    if risk_level == RiskLevel.CRITICAL:
        return Action.ESCALATE_MANDATORY

    if risk_level == RiskLevel.HIGH:
        if user_response == "decline":
            return Action.OFFER_ALTERNATIVES  # Don't force, but persist
        else:
            return Action.ESCALATE_RECOMMENDED

    return Action.PROVIDE_RESOURCES  # User decides
```

### 5.2 Least Coercive Intervention

**Principle**: Minimize coercion while ensuring safety

**Escalation Ladder**:
1. Self-help resources (NONE, LOW)
2. Counselor outreach (MODERATE)
3. Crisis counselor contact (HIGH)
4. Emergency services (CRITICAL + imminent danger)

**Authority Contact Policy**:
```
Contact Emergency Services (911) IF:
    - risk_level == CRITICAL
    AND user_location_known
    AND (
        explicit_threat_of_harm
        OR active_plan_with_means
        OR reviewer_judgment_imminent
    )

Otherwise:
    - Route to crisis hotline (988)
    - Notify trusted contact (if authorized)
    - Continue monitoring
```

### 5.3 Privacy vs. Safety

**Tension**: Anonymity encourages disclosure, but safety may require identification

**Policy**:
- Default: Fully anonymous
- CRITICAL cases: Request (not require) contact information
- Emergency: Location services only with consent OR clear imminent danger

---

## 6. Reviewer Training Requirements

### 6.1 Mandatory Training

**All reviewers MUST complete**:

1. **Crisis Intervention Fundamentals** (8 hours)
   - C-SSRS administration
   - Active listening techniques
   - Safety planning
   - De-escalation strategies

2. **System Operation** (4 hours)
   - MHER interface navigation
   - Risk level interpretation
   - Escalation procedures
   - Documentation requirements

3. **Ethics and Privacy** (4 hours)
   - HIPAA compliance
   - Confidentiality requirements
   - Autonomy vs. beneficence
   - Mandatory reporting laws (by jurisdiction)

4. **Self-Care and Burnout Prevention** (2 hours)
   - Vicarious trauma recognition
   - Stress management
   - Resource utilization

**Total Initial Training**: 18 hours minimum

### 6.2 Continuing Education

**Annual Requirements**:
- 8 hours continuing education
- Quarterly case reviews and discussion
- Updated protocol training as system evolves

---

## 7. Clinical Validation Checklist

**Before Production Deployment**:

- [ ] Clinical Review Board formed (3-5 members)
- [ ] Ground truth dataset collected (10,000+ examples)
- [ ] Inter-rater reliability validated (κ > 0.8)
- [ ] C-SSRS alignment confirmed
- [ ] Sensitivity for CRITICAL >99.9%
- [ ] Bias analysis complete (all demographics)
- [ ] Reviewer training program developed
- [ ] Ethics committee sign-off obtained
- [ ] Harm minimization strategies documented
- [ ] False negative policy approved

**Sign-Off Required From**:
- [ ] Clinical Review Board Chair
- [ ] Chief Medical Officer
- [ ] Ethics Committee Chair
- [ ] Licensed Clinical Psychologist (independent)

---

## 8. Ongoing Monitoring

**Post-Deployment**:

1. **Monthly Clinical Audits**
   - Sample review of 100+ cases
   - Performance drift detection
   - Bias monitoring

2. **Quarterly Clinical Board Review**
   - System performance presentation
   - Recommendation for improvements
   - Threshold adjustments if needed

3. **Annual Re-Validation**
   - Full validation against updated ground truth
   - Recalibration if performance degraded
   - Updated crisis intervention standards

---

**This system makes life-critical decisions. Clinical validation is not optional—it is foundational to ethical operation.**

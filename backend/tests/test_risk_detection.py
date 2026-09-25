from app.services.risk.detection_service import RiskDetectionService


def test_low_risk_when_no_indicators():
    svc = RiskDetectionService()
    level, flags = svc.assess("Patient is stable and resting comfortably.", [], "LOW")
    assert level == "LOW"
    assert flags == []


def test_rule_based_allergy_detection():
    svc = RiskDetectionService()
    level, flags = svc.assess("He is allergic to penicillin.", [], "LOW")
    indicators = [f.indicator for f in flags]
    assert "Medication allergy" in indicators
    assert flags[0].source == "RULE"


def test_high_risk_from_multiple_rule_hits():
    svc = RiskDetectionService()
    text = "Patient complained of breathing difficulty and is allergic to penicillin."
    level, flags = svc.assess(text, [], "LOW")
    assert level == "HIGH"
    assert len(flags) >= 2


def test_ai_flag_merges_as_hybrid_when_rule_also_matches():
    svc = RiskDetectionService()
    text = "Patient reported a fall this morning."
    level, flags = svc.assess(text, ["fall"], "LOW")
    fall_flags = [f for f in flags if f.indicator.lower() == "fall"]
    assert len(fall_flags) == 1
    assert fall_flags[0].source == "HYBRID"


def test_ai_escalates_risk_level_even_without_rule_match():
    svc = RiskDetectionService()
    # No rule keywords present, but AI says HIGH based on context.
    level, flags = svc.assess("Patient seems generally unwell today.", [], "HIGH")
    assert level == "HIGH"


def test_evidence_preserved_for_rule_flags():
    svc = RiskDetectionService()
    text = "During the shift the patient reported severe pain in the abdomen."
    level, flags = svc.assess(text, [], "LOW")
    pain_flag = next(f for f in flags if f.indicator == "Severe pain")
    assert "severe pain" in pain_flag.evidence.lower()

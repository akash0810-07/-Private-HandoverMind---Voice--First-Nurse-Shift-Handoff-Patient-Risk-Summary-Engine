"""
RiskDetectionService: hybrid risk aggregation combining a configurable
rule-based safety layer with LLM-derived contextual risk indicators.

The service NEVER relies solely on the LLM. Rule matches always run
against the raw transcript segment, and are combined with AI-flagged
indicators from the structured extraction. Every flag preserves the
originating transcript evidence where possible, so summaries stay
explainable and reviewable by the nurse.
"""
from dataclasses import dataclass
from typing import List
from app.services.risk.rules_config import compiled_rules, THRESHOLD_HIGH, THRESHOLD_MEDIUM
from app.models.summary import RISK_LOW, RISK_MEDIUM, RISK_HIGH


@dataclass
class RiskFlagResult:
    indicator: str
    evidence: str
    source: str  # RULE | AI | HYBRID
    weight: float


class RiskDetectionService:
    def __init__(self):
        self._rules = list(compiled_rules())

    def _rule_based_flags(self, transcript_segment: str) -> List[RiskFlagResult]:
        flags = []
        for rule in self._rules:
            for regex in rule["regexes"]:
                match = regex.search(transcript_segment)
                if match:
                    start = max(0, match.start() - 40)
                    end = min(len(transcript_segment), match.end() + 40)
                    evidence = transcript_segment[start:end].strip()
                    flags.append(RiskFlagResult(
                        indicator=rule["indicator"],
                        evidence=evidence,
                        source="RULE",
                        weight=rule["weight"],
                    ))
                    break  # one hit per rule is enough
        return flags

    def _ai_flags(self, ai_risk_indicators: List[str], transcript_segment: str) -> List[RiskFlagResult]:
        flags = []
        existing = set()
        for indicator in ai_risk_indicators or []:
            key = indicator.strip().lower()
            if not key or key in existing:
                continue
            existing.add(key)
            flags.append(RiskFlagResult(
                indicator=indicator.strip().capitalize(),
                evidence=None,  # AI indicators may not map to an exact substring
                source="AI",
                weight=1.5,
            ))
        return flags

    def assess(self, transcript_segment: str, ai_risk_indicators: List[str], ai_risk_level: str):
        """
        Returns (final_risk_level: str, flags: List[RiskFlagResult])

        Aggregation logic:
          1. Collect rule-based flags (deterministic, explainable, always run).
          2. Collect AI-derived flags not already captured by a rule.
          3. Merge duplicate indicators, tagging as HYBRID when both agree.
          4. Sum severity weights -> map to LOW / MEDIUM / HIGH via thresholds.
          5. Escalate (never de-escalate) to the AI's own risk_level if it is
             higher than the rule-based aggregate, since the AI may catch
             contextual risk a keyword rule cannot.
        """
        rule_flags = self._rule_based_flags(transcript_segment)
        rule_indicator_keys = {f.indicator.lower() for f in rule_flags}

        ai_flags_raw = self._ai_flags(ai_risk_indicators, transcript_segment)
        merged = list(rule_flags)
        for ai_flag in ai_flags_raw:
            if ai_flag.indicator.lower() in rule_indicator_keys:
                # Same indicator found by both -> upgrade the existing rule flag to HYBRID
                for f in merged:
                    if f.indicator.lower() == ai_flag.indicator.lower():
                        f.source = "HYBRID"
            else:
                merged.append(ai_flag)

        total_weight = sum(f.weight for f in merged)
        if total_weight >= THRESHOLD_HIGH:
            level = RISK_HIGH
        elif total_weight >= THRESHOLD_MEDIUM:
            level = RISK_MEDIUM
        else:
            level = RISK_LOW

        # Escalate to the AI's contextual judgement if it flagged higher severity.
        order = {RISK_LOW: 0, RISK_MEDIUM: 1, RISK_HIGH: 2}
        ai_level = ai_risk_level if ai_risk_level in order else RISK_LOW
        if order[ai_level] > order[level]:
            level = ai_level

        return level, merged

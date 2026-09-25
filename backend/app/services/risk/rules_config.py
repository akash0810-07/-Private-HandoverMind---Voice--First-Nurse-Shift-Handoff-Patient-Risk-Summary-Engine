"""
Centralized, configurable rule-based risk indicators.

Each rule maps a set of keyword/phrase patterns to a canonical indicator
name and a severity weight. Keeping this in one config module (instead of
scattered throughout the codebase) makes the safety layer auditable and
easy to extend for a viva/demo.
"""
import re

RULES = [
    {
        "indicator": "Medication allergy",
        "patterns": [r"allerg(?:y|ic)\b"],
        "weight": 3.0,
    },
    {
        "indicator": "Breathing difficulty",
        "patterns": [r"breathing difficult", r"shortness of breath", r"dyspnea", r"can't breathe"],
        "weight": 3.0,
    },
    {
        "indicator": "Fall",
        "patterns": [r"\bfell\b", r"\bfall\b", r"fell down"],
        "weight": 3.0,
    },
    {
        "indicator": "Deterioration",
        "patterns": [r"deteriorat", r"worsening", r"getting worse"],
        "weight": 3.0,
    },
    {
        "indicator": "Abnormal vital sign",
        "patterns": [r"temperature (?:was|is)?\s*10[2-9]", r"elevated temperature",
                     r"low blood pressure", r"high blood pressure", r"irregular pulse",
                     r"low oxygen", r"spo2\s*(?:of|was)?\s*[0-8]\d\b"],
        "weight": 2.0,
    },
    {
        "indicator": "Severe pain",
        "patterns": [r"severe pain", r"excruciating pain", r"unbearable pain"],
        "weight": 2.0,
    },
    {
        "indicator": "Sudden change in condition",
        "patterns": [r"sudden(?:ly)? (?:became|change|onset)", r"acute change"],
        "weight": 2.5,
    },
    {
        "indicator": "Confusion / altered mental status",
        "patterns": [r"\bconfusion\b", r"confused", r"unresponsive", r"disoriented"],
        "weight": 2.5,
    },
    {
        "indicator": "Critical observation",
        "patterns": [r"critical", r"emergency", r"code blue"],
        "weight": 4.0,
    },
]

# Aggregate score thresholds -> final risk level.
# These are intentionally simple and documented so they can be explained
# and tuned during a viva.
THRESHOLD_HIGH = 4.0
THRESHOLD_MEDIUM = 2.0


def compiled_rules():
    for rule in RULES:
        yield {
            "indicator": rule["indicator"],
            "weight": rule["weight"],
            "regexes": [re.compile(p, re.I) for p in rule["patterns"]],
        }

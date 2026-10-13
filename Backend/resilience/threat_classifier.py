"""
resilience/threat_classifier.py
---------------------------------
Maps every anomaly type produced by AnomalyDetector to a structured
ThreatClassification that drives the resilience engine's decisions.

Threat Levels
-------------
  CRITICAL  →  Immediate quarantine (no warnings granted)
  HIGH      →  Warn on first offence; quarantine on Nth offence (configurable)
  MEDIUM    →  Log warning only; never quarantine automatically
  LOW       →  Informational; ignored by resilience engine

Recommended Actions
-------------------
  QUARANTINE_IMMEDIATE  – quarantine the offending agent right now
  WARN                  – increment warning counter; check threshold
  LOG_ONLY              – write to audit log, no state change
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Anomaly-type → Threat Level + Default Action mapping
# ---------------------------------------------------------------------------
ANOMALY_THREAT_MAP: Dict[str, Dict[str, str]] = {
    "PRIVILEGE_ESCALATION": {
        "threat_level": "CRITICAL",
        "recommended_action": "QUARANTINE_IMMEDIATE",
        "description": (
            "Agent attempted a privileged action outside its role. "
            "Immediate quarantine required."
        ),
    },
    "UNKNOWN_ACTION": {
        "threat_level": "CRITICAL",
        "recommended_action": "QUARANTINE_IMMEDIATE",
        "description": (
            "Agent performed an action not present in its baseline fingerprint. "
            "Possible compromise or injection."
        ),
    },
    "UNAUTHORIZED_TARGET": {
        "threat_level": "HIGH",
        "recommended_action": "WARN",
        "description": (
            "Agent communicated with a target outside its authorized set. "
            "Could indicate lateral movement attempt."
        ),
    },
    "SEQUENCE_VIOLATION": {
        "threat_level": "HIGH",
        "recommended_action": "WARN",
        "description": (
            "Agent executed actions out of canonical workflow order. "
            "Could indicate replay attack or logic corruption."
        ),
    },
    "RUN_STRUCTURE_ANOMALY": {
        "threat_level": "HIGH",
        "recommended_action": "WARN",
        "description": (
            "Workflow run has missing, duplicate, or extra events. "
            "Could indicate partial execution or event injection."
        ),
    },
    "TIMING_ANOMALY": {
        "threat_level": "MEDIUM",
        "recommended_action": "LOG_ONLY",
        "description": (
            "Agent response time fell outside acceptable bounds. "
            "Could indicate resource exhaustion or artificial delay."
        ),
    },
}

# Fallback for unknown anomaly types
_UNKNOWN_THREAT = {
    "threat_level": "LOW",
    "recommended_action": "LOG_ONLY",
    "description": "Unrecognised anomaly type.",
}


@dataclass
class ThreatClassification:
    """Result produced for a single anomaly."""
    agent_id: str
    anomaly_type: str
    severity: str               # as reported by AnomalyDetector
    threat_level: str           # CRITICAL / HIGH / MEDIUM / LOW
    recommended_action: str     # QUARANTINE_IMMEDIATE / WARN / LOG_ONLY
    description: str
    original_anomaly: dict = field(default_factory=dict)


class ThreatClassifier:
    """
    Classifies a list of anomaly dicts (from AnomalyDetector) into
    structured ThreatClassification objects.

    Usage
    -----
        classifier = ThreatClassifier()
        classifications = classifier.classify(anomalies)
    """

    def classify(
        self, anomalies: List[Dict]
    ) -> List[ThreatClassification]:
        """
        Classify every anomaly in the list.

        Returns a list of ThreatClassification objects ordered from
        most to least severe (CRITICAL → HIGH → MEDIUM → LOW).
        """
        results: List[ThreatClassification] = []

        for anomaly in anomalies:
            anomaly_type = anomaly.get("anomaly_type", "UNKNOWN")
            mapping = ANOMALY_THREAT_MAP.get(anomaly_type, _UNKNOWN_THREAT)

            results.append(ThreatClassification(
                agent_id=anomaly.get("agent_id", "UNKNOWN"),
                anomaly_type=anomaly_type,
                severity=anomaly.get("severity", "UNKNOWN"),
                threat_level=mapping["threat_level"],
                recommended_action=mapping["recommended_action"],
                description=mapping["description"],
                original_anomaly=anomaly,
            ))

        # Sort: CRITICAL first, then HIGH, MEDIUM, LOW
        _order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        results.sort(key=lambda c: _order.get(c.threat_level, 99))

        return results

    @staticmethod
    def get_highest_level(
        classifications: List[ThreatClassification],
    ) -> Optional[str]:
        """Return the single highest threat level from a list, or None."""
        _order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        if not classifications:
            return None
        return min(classifications, key=lambda c: _order.get(c.threat_level, 99)).threat_level

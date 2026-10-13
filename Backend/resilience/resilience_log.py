"""
resilience/resilience_log.py
----------------------------
Dedicated audit logger for cyber resilience events in AI-DNA SHIELD.

All resilience state transitions, threat decisions, quarantine actions,
and recovery events are written to data/resilience_events.json —
separate from the behavioral log — to maintain a clean audit trail.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Default output path relative to the Backend root
DEFAULT_RESILIENCE_LOG = (
    Path(__file__).resolve().parent.parent / "data" / "resilience_events.json"
)


class ResilienceLogger:
    """
    Append-only JSON logger for resilience lifecycle events.

    Event kinds logged:
        - THREAT_CLASSIFIED   : anomaly mapped to a threat level and action
        - STATE_TRANSITION    : agent moved between health states
        - BACKUP_ACTIVATED    : backup agent promoted to active duty
        - BACKUP_DEACTIVATED  : backup agent stood down after primary recovered
        - RECOVERY_STARTED    : recovery cooldown initiated for a quarantined agent
        - RECOVERY_COMPLETED  : agent returned to HEALTHY state
        - SYSTEM_DEGRADED     : system entered safe/degraded mode
        - SYSTEM_RESTORED     : system returned to full operational state
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = Path(log_file) if log_file else DEFAULT_RESILIENCE_LOG
        os.makedirs(self.log_file.parent, exist_ok=True)

        if not self.log_file.exists():
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_threat_classified(
        self,
        agent_id: str,
        anomaly_type: str,
        severity: str,
        threat_level: str,
        recommended_action: str,
        description: str,
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "THREAT_CLASSIFIED",
            "agent_id": agent_id,
            "anomaly_type": anomaly_type,
            "severity": severity,
            "threat_level": threat_level,
            "recommended_action": recommended_action,
            "description": description,
        })

    def log_state_transition(
        self,
        agent_id: str,
        from_state: str,
        to_state: str,
        reason: str,
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "STATE_TRANSITION",
            "agent_id": agent_id,
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
        })

    def log_backup_activated(
        self,
        primary_id: str,
        backup_id: str,
        reason: str,
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "BACKUP_ACTIVATED",
            "primary_agent_id": primary_id,
            "backup_agent_id": backup_id,
            "reason": reason,
        })

    def log_backup_deactivated(
        self,
        primary_id: str,
        backup_id: str,
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "BACKUP_DEACTIVATED",
            "primary_agent_id": primary_id,
            "backup_agent_id": backup_id,
        })

    def log_recovery_started(
        self,
        agent_id: str,
        cooldown_seconds: float,
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "RECOVERY_STARTED",
            "agent_id": agent_id,
            "cooldown_seconds": cooldown_seconds,
        })

    def log_recovery_completed(
        self,
        agent_id: str,
        recovered_by: str,   # "AUTO" or "MANUAL"
    ) -> Dict[str, Any]:
        return self._append({
            "kind": "RECOVERY_COMPLETED",
            "agent_id": agent_id,
            "recovered_by": recovered_by,
        })

    def log_system_degraded(self, reason: str) -> Dict[str, Any]:
        return self._append({
            "kind": "SYSTEM_DEGRADED",
            "reason": reason,
        })

    def log_system_restored(self) -> Dict[str, Any]:
        return self._append({
            "kind": "SYSTEM_RESTORED",
        })

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _append(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Stamp the payload with a timestamp and append to the log file."""
        event = {"timestamp": datetime.now().isoformat(), **payload}

        with open(self.log_file, "r", encoding="utf-8") as f:
            events = json.load(f)

        events.append(event)

        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=4)

        return event

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_events(
        self,
        limit: int = 50,
        agent_id: Optional[str] = None,
        kind: Optional[str] = None,
    ):
        """Return recent resilience events, optionally filtered."""
        with open(self.log_file, "r", encoding="utf-8") as f:
            events = json.load(f)

        if agent_id:
            events = [e for e in events if e.get("agent_id") == agent_id]
        if kind:
            events = [e for e in events if e.get("kind") == kind]

        return events[-limit:]

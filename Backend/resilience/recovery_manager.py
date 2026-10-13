"""
resilience/recovery_manager.py
--------------------------------
Manages the health-state lifecycle for every agent in AI-DNA SHIELD.

Agent States
------------
    HEALTHY      – operating normally within baseline parameters
    WARNED       – has triggered one or more HIGH-severity anomalies;
                   still active but under elevated monitoring
    QUARANTINED  – removed from active duty; backup promoted in its place
    RECOVERING   – quarantine cooldown running; will return to HEALTHY
                   once cooldown expires (auto) or manual trigger received

State Machine
-------------

    HEALTHY  ──(HIGH anomaly × warn_threshold)──►  WARNED
    WARNED   ──(HIGH anomaly × warn_threshold)──►  QUARANTINED
    HEALTHY  ──(CRITICAL anomaly)───────────────►  QUARANTINED
    WARNED   ──(CRITICAL anomaly)───────────────►  QUARANTINED
    QUARANTINED ──(start_recovery called)────────►  RECOVERING
    RECOVERING  ──(cooldown elapsed or manual)───►  HEALTHY

Configuration
-------------
    warn_threshold      : int   — number of WARN actions before quarantine (default 2)
    recovery_cooldown_s : float — auto-recovery wait time in seconds    (default 60.0)
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from resilience.resilience_log import ResilienceLogger


# ---------------------------------------------------------------------------
# Agent health state constants
# ---------------------------------------------------------------------------
STATE_HEALTHY     = "HEALTHY"
STATE_WARNED      = "WARNED"
STATE_QUARANTINED = "QUARANTINED"
STATE_RECOVERING  = "RECOVERING"


@dataclass
class AgentHealthRecord:
    """Tracks the current health state and counters for a single agent."""
    agent_id: str
    status: str = STATE_HEALTHY
    warn_count: int = 0
    quarantined_at: Optional[float] = None   # epoch seconds
    recovery_started_at: Optional[float] = None
    total_quarantines: int = 0
    total_warnings: int = 0
    last_updated: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "warn_count": self.warn_count,
            "total_warnings": self.total_warnings,
            "total_quarantines": self.total_quarantines,
            "quarantined_at": (
                datetime.fromtimestamp(self.quarantined_at).isoformat()
                if self.quarantined_at else None
            ),
            "recovery_started_at": (
                datetime.fromtimestamp(self.recovery_started_at).isoformat()
                if self.recovery_started_at else None
            ),
            "last_updated": self.last_updated,
        }


class RecoveryManager:
    """
    Central authority for agent health management.

    Used by the ResilienceEngine to quarantine misbehaving agents and
    restore them once the threat is resolved.
    """

    def __init__(
        self,
        warn_threshold: int = 2,
        recovery_cooldown_s: float = 60.0,
        logger: Optional[ResilienceLogger] = None,
    ):
        self.warn_threshold = warn_threshold
        self.recovery_cooldown_s = recovery_cooldown_s
        self.logger = logger or ResilienceLogger()

        # Registry: agent_id → AgentHealthRecord
        self._registry: Dict[str, AgentHealthRecord] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register_agent(self, agent_id: str) -> AgentHealthRecord:
        """Ensure an agent has a health record (idempotent)."""
        if agent_id not in self._registry:
            self._registry[agent_id] = AgentHealthRecord(agent_id=agent_id)
        return self._registry[agent_id]

    # ------------------------------------------------------------------
    # State query helpers
    # ------------------------------------------------------------------

    def get_status(self, agent_id: str) -> str:
        rec = self._registry.get(agent_id)
        return rec.status if rec else STATE_HEALTHY

    def is_quarantined(self, agent_id: str) -> bool:
        return self.get_status(agent_id) == STATE_QUARANTINED

    def all_statuses(self) -> Dict[str, Dict[str, Any]]:
        return {aid: rec.to_dict() for aid, rec in self._registry.items()}

    # ------------------------------------------------------------------
    # Main resilience actions
    # ------------------------------------------------------------------

    def apply_warn(self, agent_id: str, reason: str) -> Dict[str, Any]:
        """
        Increment the warning counter.
        If warn_threshold is exceeded, automatically quarantine the agent.
        Returns a dict describing the action taken.
        """
        rec = self.register_agent(agent_id)
        prev_state = rec.status

        # Already quarantined — just log
        if rec.status in (STATE_QUARANTINED, STATE_RECOVERING):
            return {"action": "NO_OP", "agent_id": agent_id, "status": rec.status}

        rec.warn_count += 1
        rec.total_warnings += 1
        rec.last_updated = datetime.now().isoformat()

        self.logger.log_state_transition(
            agent_id=agent_id,
            from_state=prev_state,
            to_state=STATE_WARNED,
            reason=f"Warning #{rec.warn_count}: {reason}",
        )

        if rec.status == STATE_HEALTHY:
            rec.status = STATE_WARNED

        action_taken = "WARNED"

        # Auto-escalate to quarantine if threshold crossed
        if rec.warn_count >= self.warn_threshold:
            return self.quarantine(
                agent_id,
                reason=f"Warning threshold reached ({rec.warn_count}/{self.warn_threshold}): {reason}",
            )

        return {
            "action": action_taken,
            "agent_id": agent_id,
            "warn_count": rec.warn_count,
            "warn_threshold": self.warn_threshold,
            "status": rec.status,
        }

    def quarantine(self, agent_id: str, reason: str) -> Dict[str, Any]:
        """
        Immediately quarantine an agent, removing it from active duty.
        """
        rec = self.register_agent(agent_id)
        prev_state = rec.status

        if rec.status == STATE_QUARANTINED:
            return {"action": "ALREADY_QUARANTINED", "agent_id": agent_id}

        rec.status = STATE_QUARANTINED
        rec.quarantined_at = time.time()
        rec.total_quarantines += 1
        rec.warn_count = 0          # reset warning counter
        rec.last_updated = datetime.now().isoformat()

        self.logger.log_state_transition(
            agent_id=agent_id,
            from_state=prev_state,
            to_state=STATE_QUARANTINED,
            reason=reason,
        )

        return {
            "action": "QUARANTINED",
            "agent_id": agent_id,
            "reason": reason,
            "quarantined_at": datetime.fromtimestamp(rec.quarantined_at).isoformat(),
            "status": rec.status,
        }

    def start_recovery(self, agent_id: str) -> Dict[str, Any]:
        """
        Begin the recovery cooldown for a quarantined agent.
        The agent transitions to RECOVERING; it becomes HEALTHY once
        the cooldown elapses (checked by tick()) or via force_recover().
        """
        rec = self._registry.get(agent_id)
        if not rec or rec.status != STATE_QUARANTINED:
            return {
                "action": "NO_OP",
                "agent_id": agent_id,
                "reason": "Agent is not quarantined.",
            }

        prev_state = rec.status
        rec.status = STATE_RECOVERING
        rec.recovery_started_at = time.time()
        rec.last_updated = datetime.now().isoformat()

        self.logger.log_state_transition(
            agent_id=agent_id,
            from_state=prev_state,
            to_state=STATE_RECOVERING,
            reason=f"Recovery cooldown started ({self.recovery_cooldown_s}s)",
        )
        self.logger.log_recovery_started(
            agent_id=agent_id,
            cooldown_seconds=self.recovery_cooldown_s,
        )

        return {
            "action": "RECOVERY_STARTED",
            "agent_id": agent_id,
            "cooldown_seconds": self.recovery_cooldown_s,
            "status": rec.status,
        }

    def force_recover(self, agent_id: str) -> Dict[str, Any]:
        """
        Manually restore an agent to HEALTHY, bypassing the auto-cooldown.
        Used by the /resilience/recover/{agent_id} API endpoint.
        """
        rec = self._registry.get(agent_id)
        if not rec:
            return {"action": "NO_OP", "agent_id": agent_id, "reason": "Unknown agent."}

        if rec.status not in (STATE_QUARANTINED, STATE_RECOVERING, STATE_WARNED):
            return {
                "action": "NO_OP",
                "agent_id": agent_id,
                "reason": f"Agent is {rec.status}, nothing to recover.",
            }

        prev_state = rec.status
        rec.status = STATE_HEALTHY
        rec.warn_count = 0
        rec.quarantined_at = None
        rec.recovery_started_at = None
        rec.last_updated = datetime.now().isoformat()

        self.logger.log_state_transition(
            agent_id=agent_id,
            from_state=prev_state,
            to_state=STATE_HEALTHY,
            reason="Manual recovery triggered via API.",
        )
        self.logger.log_recovery_completed(agent_id=agent_id, recovered_by="MANUAL")

        return {
            "action": "RECOVERED",
            "agent_id": agent_id,
            "recovered_by": "MANUAL",
            "status": rec.status,
        }

    def tick(self) -> List[Dict[str, Any]]:
        """
        Check all RECOVERING agents; graduate any whose cooldown has elapsed.
        Call this periodically (e.g., before each run or via background task).
        Returns list of auto-recovery events that fired.
        """
        fired: List[Dict[str, Any]] = []
        now = time.time()

        for agent_id, rec in self._registry.items():
            if (
                rec.status == STATE_RECOVERING
                and rec.recovery_started_at is not None
                and (now - rec.recovery_started_at) >= self.recovery_cooldown_s
            ):
                prev_state = rec.status
                rec.status = STATE_HEALTHY
                rec.warn_count = 0
                rec.quarantined_at = None
                rec.recovery_started_at = None
                rec.last_updated = datetime.now().isoformat()

                self.logger.log_state_transition(
                    agent_id=agent_id,
                    from_state=prev_state,
                    to_state=STATE_HEALTHY,
                    reason=f"Auto-recovery: cooldown of {self.recovery_cooldown_s}s elapsed.",
                )
                self.logger.log_recovery_completed(
                    agent_id=agent_id, recovered_by="AUTO"
                )

                fired.append({
                    "agent_id": agent_id,
                    "action": "AUTO_RECOVERED",
                    "status": STATE_HEALTHY,
                })

        return fired

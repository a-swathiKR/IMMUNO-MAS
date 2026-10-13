"""
resilience/resilience_engine.py

Main orchestrator for the Absorb -> Adapt -> Recover cyber-resilience
lifecycle in AI-DNA SHIELD.

Critical anomalies quarantine agents immediately. Newly quarantined agents
remain QUARANTINED at the end of the detection run so callers can verify
isolation before recovery is started. Recovery can then be triggered manually
through recover_agent(), or by explicitly calling start_agent_recovery().
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from resilience.threat_classifier import ThreatClassifier, ThreatClassification
from resilience.recovery_manager import (
    RecoveryManager,
    STATE_QUARANTINED,
    STATE_RECOVERING,
)
from resilience.resilience_log import ResilienceLogger


KNOWN_AGENTS = ["PM-01", "MA-01", "RA-01"]

BACKUP_MAP = {
    "MA-01": "MA-02",
    "RA-01": "RA-02",
}


class ResilienceEngine:
    """Central cyber-resilience orchestrator."""

    def __init__(
        self,
        warn_threshold: int = 2,
        recovery_cooldown_s: float = 60.0,
    ):
        self.logger = ResilienceLogger()
        self.recovery_manager = RecoveryManager(
            warn_threshold=warn_threshold,
            recovery_cooldown_s=recovery_cooldown_s,
            logger=self.logger,
        )
        self.classifier = ThreatClassifier()

        for agent_id in KNOWN_AGENTS:
            self.recovery_manager.register_agent(agent_id)

        # Maps primary agent IDs to the backup currently standing in for them.
        self._active_backups: Dict[str, str] = {}

    def process_run(
        self,
        anomalies: List[Dict[str, Any]],
        run_index: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process anomalies from one completed decision run."""

        # Complete any cooldowns that have already elapsed.
        auto_recovered = self.recovery_manager.tick()
        for event in auto_recovered:
            self._deactivate_backup_if_active(event["agent_id"])

        # ABSORB: classify the anomalies.
        classifications: List[ThreatClassification] = self.classifier.classify(
            anomalies
        )

        actions_taken: List[Dict[str, Any]] = []
        newly_quarantined: List[str] = []

        # ADAPT: apply the recommended response for each classified threat.
        for cls in classifications:
            agent_id = cls.agent_id
            self.recovery_manager.register_agent(agent_id)

            self.logger.log_threat_classified(
                agent_id=agent_id,
                anomaly_type=cls.anomaly_type,
                severity=cls.severity,
                threat_level=cls.threat_level,
                recommended_action=cls.recommended_action,
                description=cls.description,
            )

            if cls.recommended_action == "QUARANTINE_IMMEDIATE":
                result = self.recovery_manager.quarantine(
                    agent_id,
                    reason=f"{cls.anomaly_type}: {cls.description}",
                )
                if result.get("action") == "QUARANTINED":
                    newly_quarantined.append(agent_id)
                actions_taken.append(result)

            elif cls.recommended_action == "WARN":
                result = self.recovery_manager.apply_warn(
                    agent_id,
                    reason=f"{cls.anomaly_type}: {cls.description}",
                )
                if result.get("action") == "QUARANTINED":
                    newly_quarantined.append(agent_id)
                actions_taken.append(result)

            else:
                actions_taken.append(
                    {
                        "action": "LOG_ONLY",
                        "agent_id": agent_id,
                        "anomaly_type": cls.anomaly_type,
                    }
                )

        # CONTAIN: activate backups for newly quarantined primary agents.
        # Intentionally do not start recovery here. Keeping the agent in
        # QUARANTINED state lets the caller verify isolation first.
        backup_events: List[Dict[str, Any]] = []
        for agent_id in newly_quarantined:
            backup_event = self._activate_backup_if_available(agent_id)
            if backup_event:
                backup_events.append(backup_event)

        system_healthy = all(
            self.recovery_manager.get_status(agent_id) == "HEALTHY"
            for agent_id in KNOWN_AGENTS
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "run_index": run_index,
            "total_anomalies": len(anomalies),
            "classifications": [
                {
                    "agent_id": cls.agent_id,
                    "anomaly_type": cls.anomaly_type,
                    "threat_level": cls.threat_level,
                    "recommended_action": cls.recommended_action,
                }
                for cls in classifications
            ],
            "actions_taken": actions_taken,
            "newly_quarantined": newly_quarantined,
            "auto_recovered": [event["agent_id"] for event in auto_recovered],
            "backup_events": backup_events,
            "agent_health": self.recovery_manager.all_statuses(),
            "system_healthy": system_healthy,
        }

    def simulate_anomaly(
        self,
        anomaly_type: str = "PRIVILEGE_ESCALATION",
        agent_id: str = "MA-01",
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Inject a synthetic anomaly for end-to-end testing."""

        synthetic_anomaly = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "anomaly_type": anomaly_type,
            "severity": self._infer_severity(anomaly_type),
            "description": description
            or f"[SIMULATED] {anomaly_type} on agent {agent_id}",
            "expected": "Baseline behavior",
            "observed": f"Simulated {anomaly_type}",
            "simulated": True,
        }

        report = self.process_run(
            [synthetic_anomaly],
            run_index="SIMULATION",
        )
        report["simulated"] = True
        report["injected_anomaly"] = synthetic_anomaly
        return report

    def start_agent_recovery(self, agent_id: str) -> Dict[str, Any]:
        """
        Explicitly begin the recovery cooldown after quarantine has been
        verified. The agent remains unavailable while RECOVERING.
        """
        result = self.recovery_manager.start_recovery(agent_id)
        result["agent_id"] = agent_id
        return result

    def recover_agent(self, agent_id: str) -> Dict[str, Any]:
        """Manually restore a quarantined/recovering agent to HEALTHY."""
        result = self.recovery_manager.force_recover(agent_id)
        if result.get("action") == "RECOVERED":
            self._deactivate_backup_if_active(agent_id)
        return result

    def get_system_status(self) -> Dict[str, Any]:
        """Return a snapshot of current agent health and recent events."""
        auto_recovered = self.recovery_manager.tick()
        for event in auto_recovered:
            self._deactivate_backup_if_active(event["agent_id"])

        agent_health = self.recovery_manager.all_statuses()
        recent_events = self.logger.get_events(limit=20)

        quarantined = [
            agent_id
            for agent_id, record in agent_health.items()
            if record["status"] == STATE_QUARANTINED
        ]
        recovering = [
            agent_id
            for agent_id, record in agent_health.items()
            if record["status"] == STATE_RECOVERING
        ]

        return {
            "timestamp": datetime.now().isoformat(),
            "system_healthy": not quarantined and not recovering,
            "active_backups": dict(self._active_backups),
            "quarantined_agents": quarantined,
            "recovering_agents": recovering,
            "agent_health": agent_health,
            "recent_resilience_events": recent_events,
        }

    def _activate_backup_if_available(
        self,
        primary_id: str,
    ) -> Optional[Dict[str, Any]]:
        backup_id = BACKUP_MAP.get(primary_id)
        if not backup_id:
            return None
        if primary_id in self._active_backups:
            return None

        self._active_backups[primary_id] = backup_id
        self.recovery_manager.register_agent(backup_id)

        self.logger.log_backup_activated(
            primary_id=primary_id,
            backup_id=backup_id,
            reason=f"Primary agent {primary_id} quarantined.",
        )

        return {
            "event": "BACKUP_ACTIVATED",
            "primary": primary_id,
            "backup": backup_id,
        }

    def _deactivate_backup_if_active(self, primary_id: str) -> None:
        backup_id = self._active_backups.pop(primary_id, None)
        if backup_id:
            self.logger.log_backup_deactivated(
                primary_id=primary_id,
                backup_id=backup_id,
            )

    @staticmethod
    def _infer_severity(anomaly_type: str) -> str:
        severity_map = {
            "PRIVILEGE_ESCALATION": "CRITICAL",
            "UNKNOWN_ACTION": "CRITICAL",
            "UNAUTHORIZED_TARGET": "HIGH",
            "SEQUENCE_VIOLATION": "HIGH",
            "RUN_STRUCTURE_ANOMALY": "HIGH",
            "TIMING_ANOMALY": "MEDIUM",
        }
        return severity_map.get(anomaly_type, "LOW")

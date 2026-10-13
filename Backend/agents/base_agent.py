from datetime import datetime
from monitoring.logger import BehaviorLogger


# Health states — kept in sync with RecoveryManager constants
STATUS_HEALTHY     = "HEALTHY"
STATUS_WARNED      = "WARNED"
STATUS_QUARANTINED = "QUARANTINED"
STATUS_RECOVERING  = "RECOVERING"


class BaseAgent:

    def __init__(self, agent_id, role):

        self.agent_id = agent_id
        self.role = role

        # Cyber-resilience health state
        self.status: str = STATUS_HEALTHY

        self.logger = BehaviorLogger()

    def set_status(self, new_status: str) -> None:
        """Update the agent's health state (called by the ResilienceEngine)."""
        self.status = new_status

    def is_healthy(self) -> bool:
        """Return True when the agent is fit to perform its role."""
        return self.status == STATUS_HEALTHY

    def log_behavior(self, action, target=None, details=None):

        return self.logger.log_event(
            agent_id=self.agent_id,
            role=self.role,
            action=action,
            target=target,
            details=details
        )
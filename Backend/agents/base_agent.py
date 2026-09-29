from datetime import datetime
from monitoring.logger import BehaviorLogger


class BaseAgent:

    def __init__(self, agent_id, role):

        self.agent_id = agent_id
        self.role = role

        self.logger = BehaviorLogger()

    def log_behavior(self, action, target=None, details=None):

        return self.logger.log_event(
            agent_id=self.agent_id,
            role=self.role,
            action=action,
            target=target,
            details=details
        )
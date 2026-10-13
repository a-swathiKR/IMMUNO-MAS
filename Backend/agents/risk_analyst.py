import time
from agents.base_agent import BaseAgent


class RiskAnalyst(BaseAgent):
    """Risk analyst agent; the same implementation can serve as a backup."""

    def __init__(self, agent_id: str = "RA-01", name: str = "Risk Analyst"):
        super().__init__(agent_id, name)

    def analyze_risk(self):
        start_time = time.perf_counter()

        self.log_behavior(
            action="risk_analysis_started",
            target="Portfolio Data",
        )

        risk_data = {
            "risk_level": "moderate",
            "portfolio_exposure": "acceptable",
            "risk_alert": False,
        }

        response_time = round(time.perf_counter() - start_time, 6)

        self.log_behavior(
            action="risk_analysis_completed",
            target="PM-01",
            details={
                "risk_data": risk_data,
                "response_time": response_time,
            },
        )

        return {
            "agent": self.agent_id,
            "analysis": risk_data,
            "response_time": response_time,
        }

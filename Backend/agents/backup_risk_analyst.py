"""
agents/backup_risk_analyst.py
------------------------------
BackupRiskAnalyst (RA-02) — hot standby for RA-01.

Activated by the ResilienceEngine whenever RA-01 is quarantined.
Provides identical risk analysis functionality so the system can
continue operating in a degraded (adapted) state.
"""

import time
from agents.base_agent import BaseAgent


class BackupRiskAnalyst(BaseAgent):
    """
    Hot standby Risk Analyst agent.

    ID  : RA-02
    Role: Risk Analyst (Backup)
    """

    def __init__(self):
        super().__init__("RA-02", "Risk Analyst (Backup)")

    def analyze_risk(self) -> dict:
        """
        Perform risk analysis — identical logic to RA-01 but tagged
        with the backup agent identifier so logs distinguish which agent ran.
        """
        start_time = time.perf_counter()

        self.log_behavior(
            action="risk_analysis_started",
            target="Portfolio Data",
            details={"note": "Backup agent RA-02 is active (RA-01 quarantined)"},
        )

        risk_data = {
            "risk_level": "moderate",
            "portfolio_exposure": "acceptable",
            "risk_alert": False,
            "source": "backup_agent",
        }

        response_time = round(time.perf_counter() - start_time, 6)

        self.log_behavior(
            action="risk_analysis_completed",
            target="PM-01",
            details={
                "risk_data": risk_data,
                "response_time": response_time,
                "note": "Backup agent RA-02 completed analysis.",
            },
        )

        return {
            "agent": self.agent_id,
            "role": self.role,
            "analysis": risk_data,
            "response_time": response_time,
            "backup": True,
        }

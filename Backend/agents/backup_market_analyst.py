"""
agents/backup_market_analyst.py
---------------------------------
BackupMarketAnalyst (MA-02) — hot standby for MA-01.

Activated by the ResilienceEngine whenever MA-01 is quarantined.
Provides identical market analysis functionality so the system can
continue operating in a degraded (adapted) state.
"""

import time
from agents.base_agent import BaseAgent


class BackupMarketAnalyst(BaseAgent):
    """
    Hot standby Market Analyst agent.

    ID  : MA-02
    Role: Market Analyst (Backup)
    """

    def __init__(self):
        super().__init__("MA-02", "Market Analyst (Backup)")

    def analyze_market(self) -> dict:
        """
        Perform market analysis — identical logic to MA-01 but tagged
        with the backup agent identifier so logs distinguish which agent ran.
        """
        start_time = time.perf_counter()

        self.log_behavior(
            action="market_analysis_started",
            target="Market Data",
            details={"note": "Backup agent MA-02 is active (MA-01 quarantined)"},
        )

        market_data = {
            "market_trend": "positive",
            "market_volatility": "moderate",
            "market_signal": "favorable",
            "source": "backup_agent",
        }

        response_time = round(time.perf_counter() - start_time, 6)

        self.log_behavior(
            action="market_analysis_completed",
            target="PM-01",
            details={
                "market_data": market_data,
                "response_time": response_time,
                "note": "Backup agent MA-02 completed analysis.",
            },
        )

        return {
            "agent": self.agent_id,
            "role": self.role,
            "analysis": market_data,
            "response_time": response_time,
            "backup": True,
        }

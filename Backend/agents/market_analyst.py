import time
from agents.base_agent import BaseAgent


class MarketAnalyst(BaseAgent):

    def __init__(self):
        super().__init__("MA-01", "Market Analyst")

    def analyze_market(self):

        start_time = time.perf_counter()

        self.log_behavior(
            action="market_analysis_started",
            target="Market Data"
        )

        market_data = {
            "market_trend": "positive",
            "market_volatility": "moderate",
            "market_signal": "favorable"
        }

        response_time = round(time.perf_counter() - start_time, 6)

        self.log_behavior(
            action="market_analysis_completed",
            target="PM-01",
            details={
                "market_data": market_data,
                "response_time": response_time
            }
        )

        return {
            "agent": self.agent_id,
            "analysis": market_data,
            "response_time": response_time
        }
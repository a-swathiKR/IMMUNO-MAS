from agents.base_agent import BaseAgent
from agents.market_analyst import MarketAnalyst
from agents.risk_analyst import RiskAnalyst


class PortfolioManager(BaseAgent):

    def __init__(self):

        super().__init__("PM-01", "Portfolio Manager")

        self.market_analyst = MarketAnalyst()
        self.risk_analyst = RiskAnalyst()

    def make_decision(self):

        # PM requests market analysis
        self.log_behavior(
            action="request_market_analysis",
            target="MA-01"
        )

        market_result = self.market_analyst.analyze_market()

        # PM requests risk analysis
        self.log_behavior(
            action="request_risk_analysis",
            target="RA-01"
        )

        risk_result = self.risk_analyst.analyze_risk()

        market_signal = market_result["analysis"]["market_signal"]
        risk_level = risk_result["analysis"]["risk_level"]

        if market_signal == "favorable" and risk_level != "high":
            decision = "Proceed with portfolio allocation"
        else:
            decision = "Hold portfolio allocation"

        # Log final decision
        self.log_behavior(
            action="portfolio_decision",
            target="SYSTEM",
            details={
                "market_signal": market_signal,
                "risk_level": risk_level,
                "decision": decision
            }
        )

        return {
            "portfolio_manager": self.agent_id,
            "market_analysis": market_result,
            "risk_analysis": risk_result,
            "decision": decision
        }
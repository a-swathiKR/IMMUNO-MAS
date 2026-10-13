from agents.base_agent import BaseAgent
from agents.market_analyst import MarketAnalyst
from agents.risk_analyst import RiskAnalyst


class PortfolioManager(BaseAgent):
    """
    Portfolio manager with resilience-aware task routing.

    If a primary agent is quarantined and ResilienceEngine has activated its
    backup, the corresponding task is sent to that backup agent.
    """

    def __init__(self, resilience_engine=None):
        super().__init__("PM-01", "Portfolio Manager")
        self.resilience_engine = resilience_engine

        self.market_analyst = MarketAnalyst()
        self.market_analyst_backup = MarketAnalyst(
            agent_id="MA-02",
            name="Market Analyst Backup",
        )
        self.risk_analyst = RiskAnalyst()
        self.risk_analyst_backup = RiskAnalyst(
            agent_id="RA-02",
            name="Risk Analyst Backup",
        )

    def _active_backups(self):
        if self.resilience_engine is None:
            return {}
        status = self.resilience_engine.get_system_status()
        return status.get("active_backups", {})

    def _agent_status(self, agent_id):
        if self.resilience_engine is None:
            return "HEALTHY"
        status = self.resilience_engine.get_system_status()
        record = status.get("agent_health", {}).get(agent_id, {})
        return record.get("status", "HEALTHY")

    def _select_market_analyst(self):
        backups = self._active_backups()
        primary_status = self._agent_status("MA-01")
        if primary_status in {"QUARANTINED", "RECOVERING"}:
            if backups.get("MA-01") == "MA-02":
                return self.market_analyst_backup
            raise RuntimeError(
                "MA-01 is unavailable and MA-02 is not active; "
                "market analysis stopped safely."
            )
        return self.market_analyst

    def _select_risk_analyst(self):
        backups = self._active_backups()
        primary_status = self._agent_status("RA-01")
        if primary_status in {"QUARANTINED", "RECOVERING"}:
            if backups.get("RA-01") == "RA-02":
                return self.risk_analyst_backup
            raise RuntimeError(
                "RA-01 is unavailable and RA-02 is not active; "
                "risk analysis stopped safely."
            )
        return self.risk_analyst

    def make_decision(self):
        # Route market-analysis task to the primary or its active backup.
        market_agent = self._select_market_analyst()
        self.log_behavior(
            action="request_market_analysis",
            target=market_agent.agent_id,
        )
        market_result = market_agent.analyze_market()

        # Route risk-analysis task to the primary or its active backup.
        risk_agent = self._select_risk_analyst()
        self.log_behavior(
            action="request_risk_analysis",
            target=risk_agent.agent_id,
        )
        risk_result = risk_agent.analyze_risk()

        market_signal = market_result["analysis"]["market_signal"]
        risk_level = risk_result["analysis"]["risk_level"]

        if market_signal == "favorable" and risk_level != "high":
            decision = "Proceed with portfolio allocation"
        else:
            decision = "Hold portfolio allocation"

        self.log_behavior(
            action="portfolio_decision",
            target="SYSTEM",
            details={
                "market_signal": market_signal,
                "risk_level": risk_level,
                "decision": decision,
                "market_agent_used": market_result["agent"],
                "risk_agent_used": risk_result["agent"],
            },
        )

        return {
            "portfolio_manager": self.agent_id,
            "market_analysis": market_result,
            "risk_analysis": risk_result,
            "decision": decision,
            "failover": {
                "market_primary": "MA-01",
                "market_agent_used": market_result["agent"],
                "market_using_backup": market_result["agent"] == "MA-02",
                "risk_primary": "RA-01",
                "risk_agent_used": risk_result["agent"],
                "risk_using_backup": risk_result["agent"] == "RA-02",
            },
        }

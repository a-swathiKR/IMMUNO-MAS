"""
agents/agent_manager.py
-------------------------
Orchestrates the full multi-agent decision cycle with integrated
cyber-resilience (Absorb → Adapt → Recover).

Changes from baseline
---------------------
  • Instantiates ResilienceEngine alongside the primary agents
  • After every run, pipes the events to the engine for threat triage
  • Routes to backup agents (MA-02 / RA-02) whenever a primary is quarantined
  • Exposes get_system_status() for the /resilience/status API endpoint
"""

from agents.portfolio_manager import PortfolioManager
from agents.backup_market_analyst import BackupMarketAnalyst
from agents.backup_risk_analyst import BackupRiskAnalyst
from fingerprint.anomaly_detector import AnomalyDetector
from resilience.resilience_engine import ResilienceEngine
from monitoring.logger import BehaviorLogger


class AgentManager:

    def __init__(
        self,
        warn_threshold: int = 2,
        recovery_cooldown_s: float = 60.0,
    ):
        # Primary agents
        self.portfolio_manager = PortfolioManager()

        # Backup (standby) agents — instantiated but idle until activated
        self.backup_market_analyst = BackupMarketAnalyst()
        self.backup_risk_analyst = BackupRiskAnalyst()

        # Anomaly detection
        self.anomaly_detector = AnomalyDetector()

        # Cyber-resilience engine
        self.resilience_engine = ResilienceEngine(
            warn_threshold=warn_threshold,
            recovery_cooldown_s=recovery_cooldown_s,
        )

        # Shared behavior logger for reading events after a run
        self.logger = BehaviorLogger()

        # Counter to track how many runs have been executed
        self._run_count = 0

    # ------------------------------------------------------------------
    # Core run — with resilience integration
    # ------------------------------------------------------------------

    def run_system(self) -> dict:
        """
        Execute one full decision cycle.

        1. Route to backup agents if any primary is quarantined.
        2. Run the portfolio manager (which orchestrates MA and RA).
        3. Extract the events for this run from the behavior log.
        4. Run anomaly detection on the run events.
        5. Feed anomalies into the resilience engine.
        6. Return the combined result.
        """
        self._run_count += 1
        run_index = self._run_count

        # ── Check if any primary analyst is quarantined and patch PM ──────
        
# Treat quarantined and recovering agents as unavailable.
        recovery_manager = self.resilience_engine.recovery_manager

        ma_status = recovery_manager.get_status("MA-01")
        ra_status = recovery_manager.get_status("RA-01")

        ma_unavailable = ma_status in ("QUARANTINED", "RECOVERING")
        ra_unavailable = ra_status in ("QUARANTINED", "RECOVERING")

        if ma_unavailable or ra_unavailable:
            decision_result = self._run_with_backups(
                ma_unavailable,
                ra_unavailable
            )
        else:
            decision_result = self.portfolio_manager.make_decision()



        # ── Extract run events from behavior log ───────────────────────────
        run_events = self._extract_last_run_events()

        # ── Anomaly detection ──────────────────────────────────────────────
        anomalies = self.anomaly_detector.detect_run_anomalies(run_events)

        # ── Resilience engine ──────────────────────────────────────────────
        resilience_report = self.resilience_engine.process_run(
            anomalies=anomalies,
            run_index=run_index,
        )

        return {
            "run_index": run_index,
            "decision": decision_result,
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "resilience": resilience_report,
        }

    # ------------------------------------------------------------------
    # Baseline collection (unchanged API, anomaly-detection added)
    # ------------------------------------------------------------------

    def collect_baseline(self, iterations: int = 20) -> dict:
        results = []

        for i in range(iterations):
            result = self.run_system()
            results.append({
                "iteration": i + 1,
                "decision": result["decision"]["decision"],
                "anomalies_detected": result["anomalies_detected"],
            })

        return {
            "total_executions": iterations,
            "results": results,
        }

    # ------------------------------------------------------------------
    # Resilience API helpers
    # ------------------------------------------------------------------

    def get_system_status(self) -> dict:
        """Return current agent health + recent resilience events."""
        return self.resilience_engine.get_system_status()

    def recover_agent(self, agent_id: str) -> dict:
        """Manually recover a quarantined agent."""
        return self.resilience_engine.recover_agent(agent_id)

    def simulate_anomaly(
        self,
        anomaly_type: str = "PRIVILEGE_ESCALATION",
        agent_id: str = "MA-01",
        description: str = None,
    ) -> dict:
        """Inject a synthetic anomaly to test the resilience pipeline."""
        return self.resilience_engine.simulate_anomaly(
            anomaly_type=anomaly_type,
            agent_id=agent_id,
            description=description,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_with_backups(
        self, ma_quarantined: bool, ra_quarantined: bool
    ) -> dict:
        """
        Temporarily swap quarantined primary analysts with their backups
        and execute a decision run.  The original references in
        PortfolioManager are patched in-place and restored afterwards.
        """
        pm = self.portfolio_manager

        # Save originals
        orig_ma = pm.market_analyst
        orig_ra = pm.risk_analyst

        # Patch with backups
        if ma_quarantined:
            pm.market_analyst = self.backup_market_analyst
        if ra_quarantined:
            pm.risk_analyst = self.backup_risk_analyst

        try:
            result = pm.make_decision()
            result["adapted"] = True
            result["backup_agents_used"] = {
                "MA": "MA-02" if ma_quarantined else "MA-01",
                "RA": "RA-02" if ra_quarantined else "RA-01",
            }
        finally:
            # Always restore originals
            pm.market_analyst = orig_ma
            pm.risk_analyst = orig_ra

        return result

    def _extract_last_run_events(self) -> list:
        """
        Read behavior_logs.json and return the events that belong to
        the most recently completed run (partition from last PM-01
        'request_market_analysis' to PM-01 'portfolio_decision').
        """
        import json
        try:
            with open(self.logger.log_file, "r", encoding="utf-8") as f:
                all_logs = json.load(f)
        except Exception:
            return []

        runs = self.anomaly_detector.partition_runs(all_logs)
        return runs[-1] if runs else []
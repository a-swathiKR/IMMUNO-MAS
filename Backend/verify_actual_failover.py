"""
Actual task-routing verification for IMMUNO-MAS.

Run from the Backend directory:
    python verify_actual_failover.py

This test requires the modified agents/market_analyst.py,
agents/risk_analyst.py and agents/portfolio_manager.py to be installed.
"""

import sys

from resilience.resilience_engine import ResilienceEngine
from agents.portfolio_manager import PortfolioManager


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"{status:<6} | {name}")
    if detail:
        print(f"       | {detail}")
    return bool(condition)


def main():
    passed = 0
    total = 0

    print("=" * 88)
    print("IMMUNO-MAS ACTUAL FAILOVER / TASK ROUTING VERIFICATION")
    print("=" * 88)

    # Baseline: with no quarantined agents, primary agents should execute.
    engine = ResilienceEngine()
    pm = PortfolioManager(resilience_engine=engine)
    baseline = pm.make_decision()
    total += 1
    passed += check(
        "Healthy system uses primary agents",
        baseline["market_analysis"]["agent"] == "MA-01"
        and baseline["risk_analysis"]["agent"] == "RA-01",
        f"market={baseline['market_analysis']['agent']}, "
        f"risk={baseline['risk_analysis']['agent']}",
    )

    # Quarantine MA-01: the next portfolio run should use MA-02.
    engine = ResilienceEngine()
    engine.simulate_anomaly("PRIVILEGE_ESCALATION", "MA-01")
    pm = PortfolioManager(resilience_engine=engine)
    market_failover = pm.make_decision()
    total += 1
    passed += check(
        "Quarantined MA-01 task runs on MA-02",
        market_failover["market_analysis"]["agent"] == "MA-02"
        and market_failover["failover"]["market_using_backup"] is True,
        f"market agent used={market_failover['market_analysis']['agent']}",
    )

    # Quarantine RA-01: the next portfolio run should use RA-02.
    engine = ResilienceEngine()
    engine.simulate_anomaly("UNKNOWN_ACTION", "RA-01")
    pm = PortfolioManager(resilience_engine=engine)
    risk_failover = pm.make_decision()
    total += 1
    passed += check(
        "Quarantined RA-01 task runs on RA-02",
        risk_failover["risk_analysis"]["agent"] == "RA-02"
        and risk_failover["failover"]["risk_using_backup"] is True,
        f"risk agent used={risk_failover['risk_analysis']['agent']}",
    )

    # Both primaries quarantined: both backup agents should perform the tasks.
    engine = ResilienceEngine()
    engine.simulate_anomaly("PRIVILEGE_ESCALATION", "MA-01")
    engine.simulate_anomaly("UNKNOWN_ACTION", "RA-01")
    pm = PortfolioManager(resilience_engine=engine)
    both_failover = pm.make_decision()
    total += 1
    passed += check(
        "Both quarantined primaries fail over to backups",
        both_failover["market_analysis"]["agent"] == "MA-02"
        and both_failover["risk_analysis"]["agent"] == "RA-02",
        f"market={both_failover['market_analysis']['agent']}, "
        f"risk={both_failover['risk_analysis']['agent']}",
    )

    print("-" * 88)
    print(f"RESULT: {passed}/{total} passed; {total - passed} failed")
    print("OVERALL:", "PASS" if passed == total else "FAIL")
    print("=" * 88)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

"""
verify_backup_resilience.py

Additional verification for IMMUNO-MAS:
1. Critical anomaly -> quarantine.
2. MA-01 quarantine -> MA-02 backup activation.
3. RA-01 quarantine -> RA-02 backup activation.
4. Recovery -> HEALTHY and backup deactivation.
5. PM-01 quarantine -> no backup configured.

Run from the Backend folder:
    python verify_backup_resilience.py

Note:
This verifies the ResilienceEngine's backup mapping/activation state.
It does not prove that backup agents execute real tasks unless task routing
is integrated elsewhere in the project.
"""

import sys
from typing import Callable, List, Tuple

from resilience.resilience_engine import ResilienceEngine


def run_check(
    name: str,
    check: Callable[[], bool],
    results: List[Tuple[str, bool, str]],
) -> None:
    try:
        passed = bool(check())
        results.append((name, passed, "OK" if passed else "Condition was false"))
    except Exception as exc:
        results.append((name, False, f"{type(exc).__name__}: {exc}"))


def test_critical_quarantine() -> bool:
    engine = ResilienceEngine()
    report = engine.simulate_anomaly(
        anomaly_type="PRIVILEGE_ESCALATION",
        agent_id="MA-01",
    )
    return (
        engine.recovery_manager.get_status("MA-01") == "QUARANTINED"
        and "MA-01" in report.get("newly_quarantined", [])
    )


def test_market_backup_activation() -> bool:
    engine = ResilienceEngine()
    report = engine.simulate_anomaly(
        anomaly_type="PRIVILEGE_ESCALATION",
        agent_id="MA-01",
    )
    status = engine.get_system_status()
    return (
        engine.recovery_manager.get_status("MA-01") == "QUARANTINED"
        and status.get("active_backups", {}).get("MA-01") == "MA-02"
        and any(
            event.get("event") == "BACKUP_ACTIVATED"
            and event.get("primary") == "MA-01"
            and event.get("backup") == "MA-02"
            for event in report.get("backup_events", [])
        )
    )


def test_risk_backup_activation() -> bool:
    engine = ResilienceEngine()
    report = engine.simulate_anomaly(
        anomaly_type="UNKNOWN_ACTION",
        agent_id="RA-01",
    )
    status = engine.get_system_status()
    return (
        engine.recovery_manager.get_status("RA-01") == "QUARANTINED"
        and status.get("active_backups", {}).get("RA-01") == "RA-02"
        and any(
            event.get("event") == "BACKUP_ACTIVATED"
            and event.get("primary") == "RA-01"
            and event.get("backup") == "RA-02"
            for event in report.get("backup_events", [])
        )
    )


def test_recovery_deactivates_market_backup() -> bool:
    engine = ResilienceEngine()
    engine.simulate_anomaly(
        anomaly_type="PRIVILEGE_ESCALATION",
        agent_id="MA-01",
    )
    result = engine.recover_agent("MA-01")
    status = engine.get_system_status()
    return (
        result.get("action") == "RECOVERED"
        and engine.recovery_manager.get_status("MA-01") == "HEALTHY"
        and "MA-01" not in status.get("active_backups", {})
    )


def test_recovery_deactivates_risk_backup() -> bool:
    engine = ResilienceEngine()
    engine.simulate_anomaly(
        anomaly_type="UNKNOWN_ACTION",
        agent_id="RA-01",
    )
    result = engine.recover_agent("RA-01")
    status = engine.get_system_status()
    return (
        result.get("action") == "RECOVERED"
        and engine.recovery_manager.get_status("RA-01") == "HEALTHY"
        and "RA-01" not in status.get("active_backups", {})
    )


def test_portfolio_manager_has_no_backup_configured() -> bool:
    engine = ResilienceEngine()
    report = engine.simulate_anomaly(
        anomaly_type="PRIVILEGE_ESCALATION",
        agent_id="PM-01",
    )
    status = engine.get_system_status()
    return (
        engine.recovery_manager.get_status("PM-01") == "QUARANTINED"
        and "PM-01" not in status.get("active_backups", {})
        and not any(
            event.get("primary") == "PM-01"
            for event in report.get("backup_events", [])
        )
    )


def test_explicit_recovery_transition() -> bool:
    engine = ResilienceEngine()
    engine.simulate_anomaly(
        anomaly_type="PRIVILEGE_ESCALATION",
        agent_id="MA-01",
    )
    start_result = engine.start_agent_recovery("MA-01")
    recovering = engine.recovery_manager.get_status("MA-01") == "RECOVERING"
    recover_result = engine.recover_agent("MA-01")
    healthy = engine.recovery_manager.get_status("MA-01") == "HEALTHY"
    return (
        start_result.get("action") in {"RECOVERY_STARTED", "RECOVERING"}
        and recovering
        and recover_result.get("action") == "RECOVERED"
        and healthy
    )


def main() -> int:
    results: List[Tuple[str, bool, str]] = []

    tests = [
        ("Critical anomaly quarantines primary", test_critical_quarantine),
        ("MA-01 activates MA-02 backup", test_market_backup_activation),
        ("RA-01 activates RA-02 backup", test_risk_backup_activation),
        ("Recovering MA-01 deactivates backup", test_recovery_deactivates_market_backup),
        ("Recovering RA-01 deactivates backup", test_recovery_deactivates_risk_backup),
        ("PM-01 has no configured backup", test_portfolio_manager_has_no_backup_configured),
        ("Explicit RECOVERING -> HEALTHY transition", test_explicit_recovery_transition),
    ]

    print("=" * 100)
    print("IMMUNO-MAS BACKUP AND RECOVERY VERIFICATION")
    print("=" * 100)

    for name, test in tests:
        run_check(name, test, results)

    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL':<6} | {name}")
        if not passed:
            print(f"       | {detail}")

    passed_count = sum(1 for _, passed, _ in results if passed)
    failed_count = len(results) - passed_count

    print("-" * 100)
    print(f"RESULT: {passed_count}/{len(results)} passed; {failed_count} failed")
    print("OVERALL:", "PASS" if failed_count == 0 else "FAIL")
    print("=" * 100)

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

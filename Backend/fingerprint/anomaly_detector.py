import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_FINGERPRINT_PATH = (
    Path(__file__).resolve().parent / "behavioral_fingerprints.json"
)
DEFAULT_LOG_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "behavior_logs.json"
)

# Canonical seven-event workflow
CANONICAL_SEQUENCE: List[Tuple[str, str]] = [
    ("PM-01", "request_market_analysis"),
    ("MA-01", "market_analysis_started"),
    ("MA-01", "market_analysis_completed"),
    ("PM-01", "request_risk_analysis"),
    ("RA-01", "risk_analysis_started"),
    ("RA-01", "risk_analysis_completed"),
    ("PM-01", "portfolio_decision"),
]

# Valid state transitions between sequential events
CANONICAL_TRANSITIONS: Dict[Tuple[str, str], Tuple[str, str]] = {
    ("PM-01", "request_market_analysis"): ("MA-01", "market_analysis_started"),
    ("MA-01", "market_analysis_started"): ("MA-01", "market_analysis_completed"),
    ("MA-01", "market_analysis_completed"): ("PM-01", "request_risk_analysis"),
    ("PM-01", "request_risk_analysis"): ("RA-01", "risk_analysis_started"),
    ("RA-01", "risk_analysis_started"): ("RA-01", "risk_analysis_completed"),
    ("RA-01", "risk_analysis_completed"): ("PM-01", "portfolio_decision"),
    ("PM-01", "portfolio_decision"): ("PM-01", "request_market_analysis"),
}


class AnomalyDetector:
    """
    Rule-based and statistical Behavioral Anomaly Detector for AI-DNA SHIELD.

    Derives normalized behavioral invariants from the cumulative baseline fingerprint
    and evaluates events and full execution runs for behavioral deviations.
    """

    def __init__(
        self,
        fingerprint_file: Optional[Path] = None,
        log_path: Optional[Path] = None,
        tolerance_factor: float = 2.0,
    ):
        """
        Initialize the detector.

        Args:
            fingerprint_file: Path to behavioral_fingerprints.json.
            log_path: Path to behavior_logs.json.
            tolerance_factor: Multiplier applied to baseline min/max response times
                              to accommodate normal small operational fluctuations.
        """
        self.fingerprint_path = (
            Path(fingerprint_file) if fingerprint_file else DEFAULT_FINGERPRINT_PATH
        )
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH
        self.tolerance_factor = float(tolerance_factor)

        # Baseline derived invariants
        self.raw_fingerprints: Dict[str, Any] = {}
        self.allowed_actions: Dict[str, set] = {}
        self.allowed_targets: Dict[str, set] = {}
        self.timing_thresholds: Dict[str, Dict[str, float]] = {}

        self.load_baseline()

    def load_baseline(self, fingerprint_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load the baseline fingerprint and derive normalized behavioral invariants.
        """
        target_path = (
            Path(fingerprint_file) if fingerprint_file else self.fingerprint_path
        )
        with open(target_path, "r", encoding="utf-8") as f:
            self.raw_fingerprints = json.load(f)

        self.allowed_actions = {}
        self.allowed_targets = {}
        self.timing_thresholds = {}

        for agent_id, data in self.raw_fingerprints.items():
            # Invariant 1: Permitted actions per agent
            self.allowed_actions[agent_id] = set(
                data.get("action_frequency", {}).keys()
            )

            # Invariant 2: Permitted communication targets per agent
            self.allowed_targets[agent_id] = set(
                data.get("communication_targets", {}).keys()
            )

            # Invariant 3: Response time statistical boundaries (MA-01 and RA-01 only)
            # PM-01 has 0 count and is exempted from response time detection.
            rt = data.get("response_time", {})
            if (
                rt.get("count", 0) > 0
                and rt.get("minimum", 0) > 0
                and rt.get("maximum", 0) > 0
            ):
                base_min = float(rt["minimum"])
                base_max = float(rt["maximum"])
                self.timing_thresholds[agent_id] = {
                    "base_min": base_min,
                    "base_max": base_max,
                    "min_allowed": base_min / self.tolerance_factor,
                    "max_allowed": base_max * self.tolerance_factor,
                }

        return self.raw_fingerprints

    def detect_event_anomaly(
        self,
        event: Dict[str, Any],
        previous_event: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a single behavioral event for anomalies.

        Checks:
        1. PRIVILEGE_ESCALATION (Severity: CRITICAL)
        2. UNKNOWN_ACTION (Severity: CRITICAL)
        3. UNAUTHORIZED_TARGET (Severity: HIGH)
        4. TIMING_ANOMALY (Severity: MEDIUM)
        5. SEQUENCE_VIOLATION (Severity: HIGH, if previous_event is provided)
        """
        anomalies: List[Dict[str, Any]] = []
        agent_id = event.get("agent_id", "UNKNOWN")
        action = event.get("action", "")
        target = event.get("target")
        timestamp = event.get("timestamp", datetime.now().isoformat())

        # 1. Privilege Escalation Check: Only PM-01 can make portfolio_decision
        if action == "portfolio_decision" and agent_id != "PM-01":
            anomalies.append({
                "timestamp": timestamp,
                "agent_id": agent_id,
                "anomaly_type": "PRIVILEGE_ESCALATION",
                "severity": "CRITICAL",
                "description": (
                    f"Agent '{agent_id}' attempted to execute 'portfolio_decision'. "
                    f"Only PM-01 is authorized to make portfolio decisions."
                ),
                "expected": "PM-01",
                "observed": agent_id,
            })
        # 2. Unknown Action Check: Action not in agent's baseline action set
        elif action not in self.allowed_actions.get(agent_id, set()):
            allowed = sorted(list(self.allowed_actions.get(agent_id, set())))
            anomalies.append({
                "timestamp": timestamp,
                "agent_id": agent_id,
                "anomaly_type": "UNKNOWN_ACTION",
                "severity": "CRITICAL",
                "description": (
                    f"Agent '{agent_id}' performed unknown or unauthorized action '{action}'."
                ),
                "expected": str(allowed),
                "observed": action,
            })

        # 3. Unauthorized Target Check: Target not in agent's baseline target set
        if target is not None:
            if target not in self.allowed_targets.get(agent_id, set()):
                allowed_t = sorted(list(self.allowed_targets.get(agent_id, set())))
                anomalies.append({
                    "timestamp": timestamp,
                    "agent_id": agent_id,
                    "anomaly_type": "UNAUTHORIZED_TARGET",
                    "severity": "HIGH",
                    "description": (
                        f"Agent '{agent_id}' communicated with unauthorized target '{target}'."
                    ),
                    "expected": str(allowed_t),
                    "observed": str(target),
                })

        # 4. Timing Anomaly Check for single event (details.response_time)
        if agent_id in self.timing_thresholds:
            details = event.get("details")
            if (
                isinstance(details, dict)
                and "response_time" in details
                and details["response_time"] is not None
            ):
                try:
                    resp_time = float(details["response_time"])
                    th = self.timing_thresholds[agent_id]
                    if resp_time < th["min_allowed"] or resp_time > th["max_allowed"]:
                        anomalies.append({
                            "timestamp": timestamp,
                            "agent_id": agent_id,
                            "anomaly_type": "TIMING_ANOMALY",
                            "severity": "MEDIUM",
                            "description": (
                                f"Agent '{agent_id}' response time {resp_time:.6f}s is outside "
                                f"acceptable bounds [{th['min_allowed']:.6f}s, {th['max_allowed']:.6f}s] "
                                f"(baseline: [{th['base_min']:.6f}s, {th['base_max']:.6f}s], tolerance: {self.tolerance_factor}x)."
                            ),
                            "expected": f"{th['min_allowed']:.6f}s - {th['max_allowed']:.6f}s",
                            "observed": f"{resp_time:.6f}s",
                        })
                except (ValueError, TypeError):
                    pass

        # 5. Sequence Violation against previous_event transition
        if previous_event is not None:
            prev_pair = (
                previous_event.get("agent_id"),
                previous_event.get("action"),
            )
            curr_pair = (agent_id, action)
            expected_next = CANONICAL_TRANSITIONS.get(prev_pair)
            if expected_next and curr_pair != expected_next:
                anomalies.append({
                    "timestamp": timestamp,
                    "agent_id": agent_id,
                    "anomaly_type": "SEQUENCE_VIOLATION",
                    "severity": "HIGH",
                    "description": (
                        f"Sequence violation after '{prev_pair[0]}: {prev_pair[1]}'. "
                        f"Expected '{expected_next[0]}: {expected_next[1]}', but observed '{curr_pair[0]}: {curr_pair[1]}'."
                    ),
                    "expected": f"{expected_next[0]}: {expected_next[1]}",
                    "observed": f"{curr_pair[0]}: {curr_pair[1]}",
                })

        return anomalies

    def detect_run_anomalies(
        self, run_events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate an entire decision execution cycle (expected to contain the canonical 7 events).

        Checks:
        1. RUN_STRUCTURE_ANOMALY (Missing events, duplicate events, extra events)
        2. SEQUENCE_VIOLATION (Skipped, duplicated, reversed, premature decision/request, dangling starts)
        3. PRIVILEGE_ESCALATION, UNKNOWN_ACTION, UNAUTHORIZED_TARGET (Per-event validation)
        4. TIMING_ANOMALY (MA-01 & RA-01 start-to-completion duration vs baseline)
        """
        anomalies: List[Dict[str, Any]] = []
        if not run_events:
            return anomalies

        run_timestamp = run_events[0].get("timestamp", datetime.now().isoformat())
        total_events = len(run_events)
        observed_steps = [(e.get("agent_id"), e.get("action")) for e in run_events]
        actions_in_run = [e.get("action") for e in run_events]

        # ---------------------------------------------------------
        # 1. RUN_STRUCTURE_ANOMALY: Event counts and duplicate steps
        # ---------------------------------------------------------
        step_counts = Counter(observed_steps)
        has_duplicates = False
        for step, count in step_counts.items():
            if count > 1:
                has_duplicates = True
                anomalies.append({
                    "timestamp": run_timestamp,
                    "agent_id": step[0],
                    "anomaly_type": "RUN_STRUCTURE_ANOMALY",
                    "severity": "HIGH",
                    "description": (
                        f"Duplicate event in run: agent '{step[0]}' performed action '{step[1]}' "
                        f"{count} times (expected 1)."
                    ),
                    "expected": f"1 occurrence of '{step[0]}: {step[1]}'",
                    "observed": f"{count} occurrences",
                })

        if total_events != 7:
            if total_events < 7:
                missing = [
                    f"{s[0]}: {s[1]}"
                    for s in CANONICAL_SEQUENCE
                    if s not in observed_steps
                ]
                anomalies.append({
                    "timestamp": run_timestamp,
                    "agent_id": "SYSTEM",
                    "anomaly_type": "RUN_STRUCTURE_ANOMALY",
                    "severity": "HIGH",
                    "description": (
                        f"Incomplete run: expected exactly 7 canonical events, but found {total_events}. "
                        f"Missing step(s): {missing}."
                    ),
                    "expected": "Exactly 7 canonical events",
                    "observed": f"{total_events} events",
                })
            else:
                if not has_duplicates:
                    anomalies.append({
                        "timestamp": run_timestamp,
                        "agent_id": "SYSTEM",
                        "anomaly_type": "RUN_STRUCTURE_ANOMALY",
                        "severity": "HIGH",
                        "description": (
                            f"Run structure anomaly: expected exactly 7 canonical events, "
                            f"but found {total_events} events."
                        ),
                        "expected": "Exactly 7 canonical events",
                        "observed": f"{total_events} events",
                    })

        # ---------------------------------------------------------
        # 2. SEQUENCE_VIOLATION: Order of operations in workflow
        # ---------------------------------------------------------
        # A. Premature portfolio decision
        if "portfolio_decision" in actions_in_run:
            dec_idx = actions_in_run.index("portfolio_decision")
            prior_actions = actions_in_run[:dec_idx]
            missing_prior = []
            if "market_analysis_completed" not in prior_actions:
                missing_prior.append("market_analysis_completed")
            if "risk_analysis_completed" not in prior_actions:
                missing_prior.append("risk_analysis_completed")

            if missing_prior:
                anomalies.append({
                    "timestamp": run_events[dec_idx].get(
                        "timestamp", run_timestamp
                    ),
                    "agent_id": run_events[dec_idx].get("agent_id", "PM-01"),
                    "anomaly_type": "SEQUENCE_VIOLATION",
                    "severity": "HIGH",
                    "description": (
                        f"Premature portfolio decision: 'portfolio_decision' executed before "
                        f"prior required step(s) {missing_prior}."
                    ),
                    "expected": "Prior completion of market and risk analyses",
                    "observed": f"portfolio_decision executed before {missing_prior}",
                })

        # B. Premature risk analysis request
        if "request_risk_analysis" in actions_in_run:
            risk_req_idx = actions_in_run.index("request_risk_analysis")
            prior_actions = actions_in_run[:risk_req_idx]
            if "market_analysis_completed" not in prior_actions:
                anomalies.append({
                    "timestamp": run_events[risk_req_idx].get(
                        "timestamp", run_timestamp
                    ),
                    "agent_id": run_events[risk_req_idx].get(
                        "agent_id", "PM-01"
                    ),
                    "anomaly_type": "SEQUENCE_VIOLATION",
                    "severity": "HIGH",
                    "description": (
                        "Premature risk request: 'request_risk_analysis' executed before "
                        "'market_analysis_completed'."
                    ),
                    "expected": "Prior completion of market analysis",
                    "observed": (
                        "request_risk_analysis executed before market_analysis_completed"
                    ),
                })

        # C. Reversed steps (completion before start)
        for (
            agent_id,
            start_act,
            comp_act,
        ) in [
            (
                "MA-01",
                "market_analysis_started",
                "market_analysis_completed",
            ),
            (
                "RA-01",
                "risk_analysis_started",
                "risk_analysis_completed",
            ),
        ]:
            if start_act in actions_in_run and comp_act in actions_in_run:
                if actions_in_run.index(comp_act) < actions_in_run.index(
                    start_act
                ):
                    anomalies.append({
                        "timestamp": run_timestamp,
                        "agent_id": agent_id,
                        "anomaly_type": "SEQUENCE_VIOLATION",
                        "severity": "HIGH",
                        "description": (
                            f"Reversed step sequence: '{comp_act}' occurred before '{start_act}'."
                        ),
                        "expected": f"'{start_act}' preceding '{comp_act}'",
                        "observed": f"'{comp_act}' preceding '{start_act}'",
                    })

        # D. Dangling start events (started without completion in run)
        for (
            agent_id,
            start_act,
            comp_act,
        ) in [
            (
                "MA-01",
                "market_analysis_started",
                "market_analysis_completed",
            ),
            (
                "RA-01",
                "risk_analysis_started",
                "risk_analysis_completed",
            ),
        ]:
            if start_act in actions_in_run and comp_act not in actions_in_run:
                anomalies.append({
                    "timestamp": run_timestamp,
                    "agent_id": agent_id,
                    "anomaly_type": "SEQUENCE_VIOLATION",
                    "severity": "HIGH",
                    "description": (
                        f"Dangling start event: '{start_act}' was not completed by '{comp_act}'."
                    ),
                    "expected": f"'{comp_act}' following '{start_act}'",
                    "observed": f"'{start_act}' without completion",
                })

        # E. General sequence check if length is 7 and no premature/reversed error already flagged
        if total_events == 7 and not any(
            a["anomaly_type"] == "SEQUENCE_VIOLATION" for a in anomalies
        ):
            for idx in range(7):
                expected_step = CANONICAL_SEQUENCE[idx]
                obs_step = observed_steps[idx]
                if obs_step != expected_step:
                    anomalies.append({
                        "timestamp": run_events[idx].get(
                            "timestamp", run_timestamp
                        ),
                        "agent_id": obs_step[0],
                        "anomaly_type": "SEQUENCE_VIOLATION",
                        "severity": "HIGH",
                        "description": (
                            f"Sequence violation at step {idx + 1}: expected "
                            f"'{expected_step[0]}: {expected_step[1]}', observed '{obs_step[0]}: {obs_step[1]}'."
                        ),
                        "expected": f"{expected_step[0]}: {expected_step[1]}",
                        "observed": f"{obs_step[0]}: {obs_step[1]}",
                    })
                    break

        # ---------------------------------------------------------
        # 3. Individual Event Checks (Privilege Escalation, Unknown Action, Unauthorized Target)
        # ---------------------------------------------------------
        for event in run_events:
            event_anomalies = self.detect_event_anomaly(event)
            for ea in event_anomalies:
                if ea["anomaly_type"] in (
                    "PRIVILEGE_ESCALATION",
                    "UNKNOWN_ACTION",
                    "UNAUTHORIZED_TARGET",
                ):
                    anomalies.append(ea)

        # ---------------------------------------------------------
        # 4. Timing Anomaly Check across started -> completed pairs
        # ---------------------------------------------------------
        start_timestamps: Dict[Tuple[str, str], datetime] = {}
        for event in run_events:
            aid = event.get("agent_id")
            act = event.get("action", "")
            ts_str = event.get("timestamp")

            det_time = None
            if isinstance(event.get("details"), dict):
                det_time = event["details"].get("response_time")

            if act.endswith("_started"):
                if ts_str:
                    try:
                        start_timestamps[(aid, act)] = datetime.fromisoformat(
                            ts_str
                        )
                    except Exception:
                        pass
            elif act.endswith("_completed"):
                start_act = act.replace("_completed", "_started")
                calc_time = None
                if (aid, start_act) in start_timestamps and ts_str:
                    try:
                        calc_time = (
                            datetime.fromisoformat(ts_str)
                            - start_timestamps[(aid, start_act)]
                        ).total_seconds()
                    except Exception:
                        pass

                resp_time = (
                    float(det_time) if det_time is not None else calc_time
                )
                if resp_time is not None and aid in self.timing_thresholds:
                    th = self.timing_thresholds[aid]
                    if (
                        resp_time < th["min_allowed"]
                        or resp_time > th["max_allowed"]
                    ):
                        anomalies.append({
                            "timestamp": event.get(
                                "timestamp", run_timestamp
                            ),
                            "agent_id": aid,
                            "anomaly_type": "TIMING_ANOMALY",
                            "severity": "MEDIUM",
                            "description": (
                                f"Agent '{aid}' response time {resp_time:.6f}s is outside acceptable bounds "
                                f"[{th['min_allowed']:.6f}s, {th['max_allowed']:.6f}s] "
                                f"(baseline: [{th['base_min']:.6f}s, {th['base_max']:.6f}s], tolerance: {self.tolerance_factor}x)."
                            ),
                            "expected": (
                                f"{th['min_allowed']:.6f}s - {th['max_allowed']:.6f}s"
                            ),
                            "observed": f"{resp_time:.6f}s",
                        })

        return anomalies

    def partition_runs(
        self, logs: List[Dict[str, Any]]
    ) -> List[List[Dict[str, Any]]]:
        """
        Partition a flat list of event logs into runs using the canonical workflow boundaries.
        A run begins with ('PM-01', 'request_market_analysis') and completes with ('PM-01', 'portfolio_decision').
        """
        runs: List[List[Dict[str, Any]]] = []
        current_run: List[Dict[str, Any]] = []

        for event in logs:
            is_start = (
                event.get("agent_id") == "PM-01"
                and event.get("action") == "request_market_analysis"
            )

            if current_run:
                prev_was_decision = (
                    current_run[-1].get("agent_id") == "PM-01"
                    and current_run[-1].get("action") == "portfolio_decision"
                )
                if is_start or prev_was_decision:
                    runs.append(current_run)
                    current_run = []

            current_run.append(event)

        if current_run:
            runs.append(current_run)

        return runs

    def scan_logs(
        self, log_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Scan an entire log file for anomalies across all partitioned runs.
        """
        target_path = Path(log_file) if log_file else self.log_path
        with open(target_path, "r", encoding="utf-8") as f:
            logs = json.load(f)

        runs = self.partition_runs(logs)
        all_anomalies: List[Dict[str, Any]] = []

        for run_idx, run_events in enumerate(runs):
            run_anomalies = self.detect_run_anomalies(run_events)
            for a in run_anomalies:
                a_copy = dict(a)
                a_copy["run_index"] = run_idx + 1
                all_anomalies.append(a_copy)

        type_counts = Counter(a["anomaly_type"] for a in all_anomalies)
        severity_counts = Counter(a["severity"] for a in all_anomalies)

        return {
            "log_file": str(target_path),
            "total_events": len(logs),
            "total_runs_evaluated": len(runs),
            "total_anomalies_detected": len(all_anomalies),
            "anomaly_counts_by_type": dict(type_counts),
            "anomaly_counts_by_severity": dict(severity_counts),
            "anomalies": all_anomalies,
        }


if __name__ == "__main__":
    detector = AnomalyDetector()
    print("=== AI-DNA SHIELD Behavioral Anomaly Detector ===")
    print(f"Loaded Baseline Fingerprint from: {detector.fingerprint_path}")
    print(f"Timing Thresholds (tolerance={detector.tolerance_factor}x):")
    for agent, th in detector.timing_thresholds.items():
        print(
            f"  {agent}: [{th['min_allowed']:.6f}s - {th['max_allowed']:.6f}s] "
            f"(baseline: [{th['base_min']:.6f}s - {th['base_max']:.6f}s])"
        )
    print("\nScanning existing behavior_logs.json...")
    report = detector.scan_logs()
    print(f"Total Events Evaluated: {report['total_events']}")
    print(f"Total Runs Evaluated:   {report['total_runs_evaluated']}")
    print(f"Total Anomalies Detected: {report['total_anomalies_detected']}")
    print(f"Anomalies by Type:       {report['anomaly_counts_by_type']}")
    print(f"Anomalies by Severity:   {report['anomaly_counts_by_severity']}")

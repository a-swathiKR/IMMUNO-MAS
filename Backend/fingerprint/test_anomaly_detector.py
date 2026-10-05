import copy
import unittest
from pathlib import Path
import sys

# Ensure Backend/fingerprint directory is in python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from anomaly_detector import AnomalyDetector


def create_normal_canonical_run():
    """Helper creating a valid seven-event normal execution run."""
    return [
        {
            "timestamp": "2026-10-05T10:00:00.000000",
            "agent_id": "PM-01",
            "role": "Portfolio Manager",
            "action": "request_market_analysis",
            "target": "MA-01",
            "details": None,
        },
        {
            "timestamp": "2026-10-05T10:00:00.010000",
            "agent_id": "MA-01",
            "role": "Market Analyst",
            "action": "market_analysis_started",
            "target": "Market Data",
            "details": None,
        },
        {
            "timestamp": "2026-10-05T10:00:00.045000",
            "agent_id": "MA-01",
            "role": "Market Analyst",
            "action": "market_analysis_completed",
            "target": "PM-01",
            "details": {
                "market_data": {
                    "market_trend": "positive",
                    "market_volatility": "moderate",
                    "market_signal": "favorable",
                },
                "response_time": 0.035000,
            },
        },
        {
            "timestamp": "2026-10-05T10:00:00.055000",
            "agent_id": "PM-01",
            "role": "Portfolio Manager",
            "action": "request_risk_analysis",
            "target": "RA-01",
            "details": None,
        },
        {
            "timestamp": "2026-10-05T10:00:00.065000",
            "agent_id": "RA-01",
            "role": "Risk Analyst",
            "action": "risk_analysis_started",
            "target": "Portfolio Data",
            "details": None,
        },
        {
            "timestamp": "2026-10-05T10:00:00.100000",
            "agent_id": "RA-01",
            "role": "Risk Analyst",
            "action": "risk_analysis_completed",
            "target": "PM-01",
            "details": {
                "risk_data": {
                    "risk_level": "moderate",
                    "portfolio_exposure": "acceptable",
                    "risk_alert": False,
                },
                "response_time": 0.035000,
            },
        },
        {
            "timestamp": "2026-10-05T10:00:00.110000",
            "agent_id": "PM-01",
            "role": "Portfolio Manager",
            "action": "portfolio_decision",
            "target": "SYSTEM",
            "details": {
                "market_signal": "favorable",
                "risk_level": "moderate",
                "decision": "Proceed with portfolio allocation",
            },
        },
    ]


class TestAnomalyDetector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.detector = AnomalyDetector()

    def test_a_normal_seven_event_run(self):
        """Test A: Normal seven-event run produces zero anomalies (no false positives)."""
        run = create_normal_canonical_run()
        anomalies = self.detector.detect_run_anomalies(run)
        self.assertEqual(
            len(anomalies),
            0,
            f"Expected zero anomalies for normal run, but got: {anomalies}",
        )

    def test_b_unknown_action(self):
        """Test B: PM-01 performs 'unauthorized_transfer' -> UNKNOWN_ACTION (CRITICAL)."""
        run = create_normal_canonical_run()
        run[0]["action"] = "unauthorized_transfer"

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("UNKNOWN_ACTION", types)

        unknown_anom = next(
            a for a in anomalies if a["anomaly_type"] == "UNKNOWN_ACTION"
        )
        self.assertEqual(unknown_anom["agent_id"], "PM-01")
        self.assertEqual(unknown_anom["severity"], "CRITICAL")
        self.assertEqual(unknown_anom["observed"], "unauthorized_transfer")

    def test_c_unauthorized_target(self):
        """Test C: MA-01 communicates with unauthorized target RA-01 -> UNAUTHORIZED_TARGET (HIGH)."""
        run = create_normal_canonical_run()
        # MA-01 target changed from PM-01 to RA-01
        run[2]["target"] = "RA-01"

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("UNAUTHORIZED_TARGET", types)

        target_anom = next(
            a for a in anomalies if a["anomaly_type"] == "UNAUTHORIZED_TARGET"
        )
        self.assertEqual(target_anom["agent_id"], "MA-01")
        self.assertEqual(target_anom["severity"], "HIGH")
        self.assertEqual(target_anom["observed"], "RA-01")

    def test_d_sequence_violation_premature_decision(self):
        """Test D: PM-01 performs portfolio_decision before RA-01 risk_analysis_completed -> SEQUENCE_VIOLATION (HIGH)."""
        run = create_normal_canonical_run()
        # Move portfolio_decision (index 6) ahead of risk_analysis_completed (index 5)
        decision_event = run.pop(6)
        run.insert(5, decision_event)

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("SEQUENCE_VIOLATION", types)

        seq_anom = next(
            a for a in anomalies if a["anomaly_type"] == "SEQUENCE_VIOLATION"
        )
        self.assertEqual(seq_anom["severity"], "HIGH")
        self.assertIn("Premature portfolio decision", seq_anom["description"])

    def test_e_privilege_escalation(self):
        """Test E: RA-01 performs portfolio_decision -> PRIVILEGE_ESCALATION (CRITICAL)."""
        run = create_normal_canonical_run()
        # RA-01 illegitimately executes portfolio_decision
        run[6]["agent_id"] = "RA-01"
        run[6]["role"] = "Risk Analyst"

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("PRIVILEGE_ESCALATION", types)

        priv_anom = next(
            a for a in anomalies if a["anomaly_type"] == "PRIVILEGE_ESCALATION"
        )
        self.assertEqual(priv_anom["agent_id"], "RA-01")
        self.assertEqual(priv_anom["severity"], "CRITICAL")
        self.assertEqual(priv_anom["expected"], "PM-01")
        self.assertEqual(priv_anom["observed"], "RA-01")

    def test_f_timing_anomaly(self):
        """Test F: MA-01 exhibits an extreme response time (e.g., 5.0 seconds) -> TIMING_ANOMALY (MEDIUM)."""
        run = create_normal_canonical_run()
        # Extreme response time: 5.0 seconds (baseline maximum is ~0.0576s)
        run[2]["details"]["response_time"] = 5.0

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("TIMING_ANOMALY", types)

        timing_anom = next(
            a for a in anomalies if a["anomaly_type"] == "TIMING_ANOMALY"
        )
        self.assertEqual(timing_anom["agent_id"], "MA-01")
        self.assertEqual(timing_anom["severity"], "MEDIUM")
        self.assertEqual(timing_anom["observed"], "5.000000s")

    def test_g_missing_event_run_structure(self):
        """Test G: Remove one event from a seven-event run -> RUN_STRUCTURE_ANOMALY (HIGH)."""
        run = create_normal_canonical_run()
        # Remove risk_analysis_started (index 4)
        run.pop(4)
        self.assertEqual(len(run), 6)

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("RUN_STRUCTURE_ANOMALY", types)

        struct_anom = next(
            a for a in anomalies if a["anomaly_type"] == "RUN_STRUCTURE_ANOMALY"
        )
        self.assertEqual(struct_anom["severity"], "HIGH")
        self.assertIn("Incomplete run", struct_anom["description"])

    def test_h_duplicate_event_run_structure(self):
        """Test H: Duplicate one event in a run -> RUN_STRUCTURE_ANOMALY (HIGH)."""
        run = create_normal_canonical_run()
        # Duplicate market_analysis_started (index 1)
        duplicate_event = copy.deepcopy(run[1])
        run.insert(2, duplicate_event)
        self.assertEqual(len(run), 8)

        anomalies = self.detector.detect_run_anomalies(run)
        types = [a["anomaly_type"] for a in anomalies]
        self.assertIn("RUN_STRUCTURE_ANOMALY", types)

        dup_anom = next(
            a
            for a in anomalies
            if a["anomaly_type"] == "RUN_STRUCTURE_ANOMALY"
            and "Duplicate" in a["description"]
        )
        self.assertEqual(dup_anom["severity"], "HIGH")
        self.assertEqual(dup_anom["agent_id"], "MA-01")

    def test_pm01_exempted_from_timing_anomaly(self):
        """Verify PM-01 has no timing thresholds and is exempt from response time anomaly detection."""
        self.assertNotIn("PM-01", self.detector.timing_thresholds)
        self.assertIn("MA-01", self.detector.timing_thresholds)
        self.assertIn("RA-01", self.detector.timing_thresholds)

    def test_scan_existing_behavior_logs_zero_false_positives(self):
        """Verify scan_logs across all 42 baseline runs in behavior_logs.json yields zero false positives."""
        report = self.detector.scan_logs()
        self.assertEqual(report["total_events"], 294)
        self.assertEqual(report["total_runs_evaluated"], 42)
        self.assertEqual(
            report["total_anomalies_detected"],
            0,
            f"Expected zero anomalies on baseline logs, but found: {report['anomalies']}",
        )
        self.assertEqual(report["anomaly_counts_by_type"], {})
        self.assertEqual(report["anomaly_counts_by_severity"], {})


if __name__ == "__main__":
    unittest.main(verbosity=2)

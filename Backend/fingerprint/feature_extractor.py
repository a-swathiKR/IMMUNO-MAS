import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


LOG_FILE = Path(__file__).resolve().parent.parent / "data" / "behavior_logs.json"


def load_logs():
    """Load behavioral events from the JSON log file."""
    with open(LOG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_response_times(logs):
    """
    Calculate response times for analyst agents.

    MA-01:
        market_analysis_started -> market_analysis_completed

    RA-01:
        risk_analysis_started -> risk_analysis_completed
    """

    response_times = defaultdict(list)
    start_events = {}

    for event in logs:
        agent_id = event["agent_id"]
        action = event["action"]
        timestamp = datetime.fromisoformat(event["timestamp"])

        if action.endswith("_started"):
            start_events[(agent_id, action)] = timestamp

        elif action.endswith("_completed"):
            start_action = action.replace("_completed", "_started")
            key = (agent_id, start_action)

            if key in start_events:
                response_time = (
                    timestamp - start_events[key]
                ).total_seconds()

                response_times[agent_id].append(response_time)

                del start_events[key]

    return response_times


def extract_features(logs):
    """Extract behavioral features for every agent."""

    agents = defaultdict(list)

    for event in logs:
        agents[event["agent_id"]].append(event)

    response_times = calculate_response_times(logs)

    fingerprints = {}

    for agent_id, events in agents.items():

        action_counter = Counter(
            event["action"] for event in events
        )

        target_counter = Counter(
            event["target"] for event in events
            if event.get("target")
        )

        communication_events = [
            event for event in events
            if event.get("target")
        ]

        decisions = [
            event for event in events
            if event["action"] == "portfolio_decision"
        ]

        action_sequence = [
            event["action"] for event in events
        ]

        agent_response_times = response_times.get(
            agent_id, []
        )

        average_response_time = (
            sum(agent_response_times)
            / len(agent_response_times)
            if agent_response_times
            else 0
        )

        fingerprints[agent_id] = {
            "total_events": len(events),

            "action_frequency": dict(action_counter),

            "communication_frequency": len(
                communication_events
            ),

            "communication_targets": dict(
                target_counter
            ),

            "action_sequence": action_sequence,

            "response_time": {
                "count": len(agent_response_times),
                "average": average_response_time,
                "minimum": (
                    min(agent_response_times)
                    if agent_response_times
                    else 0
                ),
                "maximum": (
                    max(agent_response_times)
                    if agent_response_times
                    else 0
                )
            },

            "decision_frequency": len(decisions)
        }

    return fingerprints


def generate_fingerprint():
    """Load logs and generate behavioral fingerprints."""

    logs = load_logs()

    return extract_features(logs)


if __name__ == "__main__":

    fingerprints = generate_fingerprint()

    print("\n=== AI-DNA SHIELD Behavioral Fingerprint ===\n")

    for agent_id, fingerprint in fingerprints.items():

        print(f"\nAgent: {agent_id}")
        print("-" * 40)

        print(
            f"Total events: "
            f"{fingerprint['total_events']}"
        )

        print(
            f"Communication frequency: "
            f"{fingerprint['communication_frequency']}"
        )

        print(
            f"Communication targets: "
            f"{fingerprint['communication_targets']}"
        )

        print(
            f"Average response time: "
            f"{fingerprint['response_time']['average']:.6f} seconds"
        )

        print(
            f"Decision frequency: "
            f"{fingerprint['decision_frequency']}"
        )

        print(
            f"Action frequency: "
            f"{fingerprint['action_frequency']}"
        )
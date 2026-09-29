import json
import os
from datetime import datetime


class BehaviorLogger:

    def __init__(self, log_file="data/behavior_logs.json"):
        self.log_file = log_file

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Create an empty log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, "w") as file:
                json.dump([], file)

    def log_event(self, agent_id, role, action, target=None, details=None):

        event = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "role": role,
            "action": action,
            "target": target,
            "details": details
        }

        with open(self.log_file, "r") as file:
            logs = json.load(file)

        logs.append(event)

        with open(self.log_file, "w") as file:
            json.dump(logs, file, indent=4)

        return event
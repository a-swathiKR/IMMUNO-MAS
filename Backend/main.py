from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from agents.agent_manager import AgentManager


app = FastAPI(
    title="IMMUNO-MAS",
    description=(
        "Multi-Agent System with Behavioral Fingerprinting, "
        "Anomaly Detection, and Cyber Resilience (Absorb → Adapt → Recover)."
    ),
    version="2.0.0",
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "message": "IMMUNO-MAS backend is running"
    }
    
manager = AgentManager(
    warn_threshold=2,          # warnings before quarantine
    recovery_cooldown_s=60.0,  # seconds before auto-recovery
)


# ---------------------------------------------------------------------------
# Existing endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Core"])
def home():
    return {"message": "AI-DNA SHIELD is running"}


@app.get("/run", tags=["Core"])
def run_multi_agent_system():
    """
    Execute one full decision cycle.
    Includes anomaly detection and resilience triage automatically.
    """
    return manager.run_system()


@app.get("/baseline", tags=["Core"])
def collect_baseline(iterations: int = 20):
    """
    Collect baseline behavioral data over N decision runs.
    """
    return manager.collect_baseline(iterations)


# ---------------------------------------------------------------------------
# Cyber-Resilience endpoints
# ---------------------------------------------------------------------------

@app.get("/resilience/status", tags=["Cyber Resilience"])
def resilience_status():
    """
    Return the current health state of every agent, active backups,
    and the 20 most recent resilience audit events.
    """
    return manager.get_system_status()


@app.post("/resilience/recover/{agent_id}", tags=["Cyber Resilience"])
def manual_recover(agent_id: str):
    """
    Manually trigger recovery for a quarantined or recovering agent,
    bypassing the auto-cooldown timer.

    Valid agent IDs: PM-01, MA-01, RA-01
    """
    valid_agents = {"PM-01", "MA-01", "RA-01"}
    if agent_id not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent '{agent_id}'. Valid agents: {sorted(valid_agents)}",
        )
    return manager.recover_agent(agent_id)


class SimulateRequest(BaseModel):
    anomaly_type: Optional[str] = "PRIVILEGE_ESCALATION"
    agent_id: Optional[str] = "MA-01"
    description: Optional[str] = None


@app.post("/resilience/simulate", tags=["Cyber Resilience"])
def simulate_anomaly(body: SimulateRequest):
    """
    Inject a synthetic anomaly to test the resilience pipeline end-to-end.

    Supported anomaly_type values:
      - PRIVILEGE_ESCALATION  (CRITICAL → immediate quarantine)
      - UNKNOWN_ACTION        (CRITICAL → immediate quarantine)
      - UNAUTHORIZED_TARGET   (HIGH → warn; quarantine at threshold)
      - SEQUENCE_VIOLATION    (HIGH → warn; quarantine at threshold)
      - RUN_STRUCTURE_ANOMALY (HIGH → warn; quarantine at threshold)
      - TIMING_ANOMALY        (MEDIUM → log only)

    Supported agent_id values: PM-01, MA-01, RA-01
    """
    valid_types = {
        "PRIVILEGE_ESCALATION",
        "UNKNOWN_ACTION",
        "UNAUTHORIZED_TARGET",
        "SEQUENCE_VIOLATION",
        "RUN_STRUCTURE_ANOMALY",
        "TIMING_ANOMALY",
    }
    if body.anomaly_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown anomaly_type '{body.anomaly_type}'. Valid types: {sorted(valid_types)}",
        )

    return manager.simulate_anomaly(
        anomaly_type=body.anomaly_type,
        agent_id=body.agent_id,
        description=body.description,
    )
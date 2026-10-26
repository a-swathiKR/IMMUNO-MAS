from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import json

from agents.agent_manager import AgentManager

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="IMMUNO-MAS",
    description=(
        "Multi-Agent System with Behavioral Fingerprinting, "
        "Anomaly Detection, and Cyber Resilience (Absorb → Adapt → Recover)."
    ),
    version="2.0.0",
)

# Allow the local Vite development server to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = AgentManager(
    warn_threshold=2,
    recovery_cooldown_s=60.0,
)


def read_json_file(path: Path, fallback):
    """Read a project data file safely and return fallback on missing/invalid data."""
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return fallback


# ---------------------------------------------------------------------------
# Core and diagnostic endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["Core"])
def home():
    return {"message": "AI-DNA SHIELD is running"}


@app.get("/health", tags=["Health"])
def health_check():
    """Lightweight liveness check: confirms the FastAPI process responds."""
    return {
        "status": "healthy",
        "message": "IMMUNO-MAS backend is running",
        "version": app.version,
    }


@app.get("/health/detailed", tags=["Health"])
def detailed_health_check():
    """Check registered API routes and report endpoint availability, not business correctness."""
    required_paths = [
        "/health", "/agents", "/behavior/logs", "/behavior/anomalies",
        "/behavior/fingerprints", "/resilience/status", "/resilience/events",
        "/settings", "/run", "/resilience/simulate",
    ]
    registered = {route.path for route in app.routes}
    checks = {
        path: ("PASS" if path in registered else "FAIL")
        for path in required_paths
    }
    failed = [path for path, status in checks.items() if status == "FAIL"]
    return {
        "overall_status": "healthy" if not failed else "degraded",
        "server": "healthy",
        "checks": checks,
        "summary": {
            "total": len(checks),
            "passed": len(checks) - len(failed),
            "failed": len(failed),
        },
        "note": "Route registration is checked here; endpoint behavior requires functional tests.",
    }


@app.get("/agents", tags=["Agents"])
def list_agents():
    """Return primary and backup agent records in the format expected by the UI."""
    status_data = manager.get_system_status()
    health_map = status_data.get("agent_health", {})
    active_backups = set(status_data.get("active_backups", {}).values())
    definitions = [
        ("PM-01", "Portfolio Manager", "Portfolio decision coordinator", False),
        ("MA-01", "Market Analyst", "Market analysis", False),
        ("RA-01", "Risk Analyst", "Risk analysis", False),
        ("MA-02", "Backup Market Analyst", "Standby market analysis", True),
        ("RA-02", "Backup Risk Analyst", "Standby risk analysis", True),
    ]
    records = []
    for agent_id, name, role, is_backup in definitions:
        record = health_map.get(agent_id, {})
        status = record.get("status", "STANDBY" if is_backup else "HEALTHY")
        active_backup = agent_id in active_backups
        if is_backup and not active_backup and status == "HEALTHY":
            status = "STANDBY"
        records.append({
            "id": agent_id,
            "agent_id": agent_id,
            "name": name,
            "role": role,
            "designation": "BACKUP" if is_backup else "PRIMARY",
            "status": status,
            "raw_status": status,
            "warn_count": record.get("warn_count", 0),
            "total_warnings": record.get("total_warnings", record.get("warn_count", 0)),
            "total_quarantines": record.get("total_quarantines", 0),
            "is_active_backup": active_backup,
            "available": status in {"HEALTHY", "ACTIVE", "ONLINE", "STANDBY"},
        })
    return {"agents": records}


@app.get("/behavior/logs", tags=["Behavior"])
def behavior_logs():
    logs = read_json_file(BASE_DIR / "data" / "behavior_logs.json", [])
    return {"logs": logs if isinstance(logs, list) else []}


@app.get("/behavior/anomalies", tags=["Behavior"])
def behavior_anomalies():
    logs = read_json_file(BASE_DIR / "data" / "behavior_logs.json", [])
    if not isinstance(logs, list):
        logs = []
    anomalies = []
    previous = None
    for event in logs:
        if not isinstance(event, dict):
            continue
        try:
            anomalies.extend(manager.anomaly_detector.detect_event_anomaly(event, previous))
        except (KeyError, TypeError, ValueError):
            # Skip malformed individual records without failing the whole endpoint.
            pass
        previous = event
    return {"anomalies": anomalies}


@app.get("/behavior/fingerprints", tags=["Behavior"])
def behavior_fingerprints():
    fingerprints = read_json_file(
        BASE_DIR / "fingerprint" / "behavioral_fingerprints.json", {}
    )
    return {"fingerprints": fingerprints}


@app.get("/settings", tags=["Settings"])
def get_settings():
    return {
        "application": app.title,
        "version": app.version,
        "api_base": "http://127.0.0.1:8000",
        "resilience": {
            "warning_threshold": 2,
            "recovery_cooldown_seconds": 60,
        },
        "primary_agents": ["PM-01", "MA-01", "RA-01"],
        "backup_agents": ["MA-02", "RA-02"],
    }


@app.get("/run", tags=["Core"])
def run_multi_agent_system():
    """Execute one full decision cycle with anomaly detection and resilience triage."""
    return manager.run_system()


@app.get("/baseline", tags=["Core"])
def collect_baseline(iterations: int = 20):
    if iterations < 1 or iterations > 500:
        raise HTTPException(status_code=400, detail="iterations must be between 1 and 500")
    return manager.collect_baseline(iterations)


# ---------------------------------------------------------------------------
# Cyber-resilience endpoints
# ---------------------------------------------------------------------------

@app.get("/resilience/status", tags=["Cyber Resilience"])
def resilience_status():
    return manager.get_system_status()


@app.get("/resilience/events", tags=["Cyber Resilience"])
def resilience_events():
    status = manager.get_system_status()
    return {"events": status.get("recent_resilience_events", [])}


@app.post("/resilience/recover/{agent_id}", tags=["Cyber Resilience"])
def manual_recover(agent_id: str):
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
    valid_types = {
        "PRIVILEGE_ESCALATION", "UNKNOWN_ACTION", "UNAUTHORIZED_TARGET",
        "SEQUENCE_VIOLATION", "RUN_STRUCTURE_ANOMALY", "TIMING_ANOMALY",
    }
    if body.anomaly_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown anomaly_type '{body.anomaly_type}'. Valid types: {sorted(valid_types)}",
        )
    valid_agents = {"PM-01", "MA-01", "RA-01"}
    if body.agent_id not in valid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown agent '{body.agent_id}'. Valid agents: {sorted(valid_agents)}",
        )
    return manager.simulate_anomaly(
        anomaly_type=body.anomaly_type,
        agent_id=body.agent_id,
        description=body.description,
    )

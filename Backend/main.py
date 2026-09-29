from fastapi import FastAPI
from agents.agent_manager import AgentManager


app = FastAPI(title="AI-DNA SHIELD")

manager = AgentManager()


@app.get("/")
def home():

    return {
        "message": "AI-DNA SHIELD is running"
    }


@app.get("/run")
def run_multi_agent_system():

    result = manager.run_system()

    return result

@app.get("/baseline")
def collect_baseline():

    result = manager.collect_baseline(20)

    return result
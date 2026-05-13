from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from control_plane.health.health_engine import HealthEngine
from control_plane.incidents.incident_manager import IncidentManager
from control_plane.metrics.metrics_store import MetricsStore
from control_plane.observability.logging_config import configure_logging
from control_plane.registry.service_registry import ServiceRegistry
from control_plane.remediation.remediation_engine import RemediationEngine
from control_plane.remediation.ai_remediation import AiRemediationAgent

configure_logging()

registry = ServiceRegistry()
metrics = MetricsStore()
incidents = IncidentManager()
remediation = RemediationEngine(registry=registry, metrics=metrics)
ai_agent = AiRemediationAgent()
health_engine = HealthEngine(registry, metrics, remediation, incidents)

app = FastAPI(title="Platform Reliability Control Plane")


class RegisterRequest(BaseModel):
    name: str
    version: str
    base_url: str
    environment: str
    owner: str


class HeartbeatRequest(BaseModel):
    name: str
    environment: str


@app.on_event("startup")
async def startup_event():
    health_engine.start()


@app.post("/register")
def register_service(request: RegisterRequest):
    reg = registry.register_service(
        name=request.name,
        version=request.version,
        base_url=request.base_url,
        environment=request.environment,
        owner=request.owner,
    )
    return {"status": "registered", "service": reg.__dict__}


@app.post("/heartbeat")
def heartbeat(request: HeartbeatRequest):
    reg = registry.heartbeat(request.name, request.environment)
    if not reg:
        raise HTTPException(status_code=404, detail="service not registered")
    return {"status": "ok"}


@app.get("/services")
def list_services():
    services = registry.get_services()
    return {key: reg.__dict__ for key, reg in services.items()}


@app.get("/incidents")
def list_incidents():
    payload = []
    for inc in incidents.all_incidents():
        payload.append(
            {
                "service": inc.service,
                "environment": inc.environment,
                "start_time": inc.start_time,
                "detection_time": inc.detection_time,
                "resolution_time": inc.resolution_time,
                "status": inc.status,
                "mttr": inc.mttr,
            }
        )
    return {"incidents": payload, "average_mttr": incidents.average_mttr()}


@app.get("/metrics")
def get_metrics():
    return metrics.export()


class AiRemediateRequest(BaseModel):
    name: str
    environment: str
    process_name: str = ""


@app.post("/ai-remediate")
def ai_remediate(request: AiRemediateRequest):
    """Trigger AI auto-remediation for a degraded service.

    Reads eBPF kernel traces, correlates with recent Git commits, and uses
    an LLM to generate a root-cause analysis and draft rollback PR.
    """
    process = request.process_name or request.name
    analysis = ai_agent.analyse_and_remediate(
        service=request.name,
        environment=request.environment,
        process_name=process,
    )
    return {
        "service": analysis.service,
        "environment": analysis.environment,
        "root_cause_hypothesis": analysis.root_cause_hypothesis,
        "recommended_action": analysis.recommended_action,
        "rollback_sha": analysis.rollback_sha,
        "confidence": analysis.confidence,
        "pr_title": analysis.pr_title,
        "pr_url": analysis.pr_url,
    }

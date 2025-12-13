from unittest.mock import MagicMock

import requests

from control_plane.health.health_engine import HealthEngine, HealthRule
from control_plane.incidents.incident_manager import IncidentManager
from control_plane.metrics.metrics_store import MetricsStore
from control_plane.registry.service_registry import ServiceRegistry


class DummyResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code


def test_failure_then_recovery(monkeypatch):
    registry = ServiceRegistry()
    metrics = MetricsStore()
    incidents = IncidentManager()
    remediation = MagicMock()
    remediation.remediate = MagicMock()

    engine = HealthEngine(registry, metrics, remediation, incidents, rule=HealthRule(failure_threshold=1))
    reg = registry.register_service("svc", "1", "http://localhost:9000", "dev", "owner")

    healthy = {"ok": False}

    def fake_get(*args, **kwargs):
        return DummyResponse(status_code=200 if healthy["ok"] else 500)

    monkeypatch.setattr(requests, "get", fake_get)

    engine.evaluate_service(reg)
    assert incidents.open_incident_exists("svc", "dev") is True
    remediation.remediate.assert_called_once()

    healthy["ok"] = True
    engine.evaluate_service(reg)
    assert incidents.open_incident_exists("svc", "dev") is False

import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import requests

from control_plane.health.health_engine import HealthEngine, HealthRule
from control_plane.incidents.incident_manager import IncidentManager
from control_plane.metrics.metrics_store import MetricsStore
from control_plane.registry.service_registry import ServiceRegistry


class DummyResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code


def test_health_engine_detects_failure_and_triggers_remediation(monkeypatch):
    registry = ServiceRegistry()
    metrics = MetricsStore()
    incidents = IncidentManager()
    remediation = MagicMock()
    remediation.remediate = MagicMock()
    engine = HealthEngine(registry, metrics, remediation, incidents, rule=HealthRule(failure_threshold=2))

    reg = registry.register_service("svc", "1", "http://localhost:9999", "dev", "owner")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse(status_code=500))

    assert engine.evaluate_service(reg) is False
    assert engine.evaluate_service(reg) is False
    assert incidents.open_incident_exists("svc", "dev") is True
    remediation.remediate.assert_called_once()


def test_health_engine_resolves_incident_on_recovery(monkeypatch):
    registry = ServiceRegistry()
    metrics = MetricsStore()
    incidents = IncidentManager()
    remediation = MagicMock()
    remediation.remediate = MagicMock()
    engine = HealthEngine(registry, metrics, remediation, incidents, rule=HealthRule(failure_threshold=1))

    reg = registry.register_service("svc", "1", "http://localhost:9999", "dev", "owner")

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse(status_code=500))
    engine.evaluate_service(reg)
    assert incidents.open_incident_exists("svc", "dev") is True

    monkeypatch.setattr(requests, "get", lambda *args, **kwargs: DummyResponse(status_code=200))
    engine.evaluate_service(reg)
    assert incidents.open_incident_exists("svc", "dev") is False

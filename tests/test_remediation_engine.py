import time
from unittest.mock import MagicMock

import requests

from control_plane.metrics.metrics_store import MetricsStore
from control_plane.registry.service_registry import ServiceRegistry
from control_plane.remediation.remediation_engine import RemediationEngine


class DummyResponse:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code


def test_remediation_restarts_service(monkeypatch):
    registry = ServiceRegistry()
    metrics = MetricsStore()
    reg = registry.register_service("svc", "1", "http://localhost:9000", "dev", "owner")
    engine = RemediationEngine(registry, metrics, rate_limit_seconds=60)

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse(status_code=200))
    result = engine.remediate("svc", "dev")
    assert result == "restarted"
    assert metrics.export()["counters"]["remediation_attempts"] == 1


def test_remediation_rate_limits(monkeypatch):
    registry = ServiceRegistry()
    metrics = MetricsStore()
    reg = registry.register_service("svc", "1", "http://localhost:9000", "dev", "owner")
    engine = RemediationEngine(registry, metrics, rate_limit_seconds=100)

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse(status_code=200))
    engine.remediate("svc", "dev")
    # immediately call again should be rate limited
    result = engine.remediate("svc", "dev")
    assert result == "rate_limited"

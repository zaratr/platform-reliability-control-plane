import logging
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests

from control_plane.incidents.incident_manager import IncidentManager
from control_plane.metrics.metrics_store import MetricsStore
from control_plane.registry.service_registry import ServiceRegistry, ServiceRegistration
from control_plane.remediation.remediation_engine import RemediationEngine


@dataclass
class HealthRule:
    failure_threshold: int = 2
    timeout_seconds: int = 2


class HealthEngine:
    def __init__(
        self,
        registry: ServiceRegistry,
        metrics: MetricsStore,
        remediation: RemediationEngine,
        incidents: IncidentManager,
        rule: Optional[HealthRule] = None,
        check_interval: int = 5,
    ):
        self.registry = registry
        self.metrics = metrics
        self.remediation = remediation
        self.incidents = incidents
        self.rule = rule or HealthRule()
        self.check_interval = check_interval
        self._failure_counts: Dict[str, int] = {}
        self._stop_event = threading.Event()
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.check_all()
            time.sleep(self.check_interval)

    def check_all(self) -> None:
        services = self.registry.get_services()
        for key, reg in services.items():
            self.evaluate_service(reg)

    def evaluate_service(self, reg: ServiceRegistration) -> bool:
        key = f"{reg.name}:{reg.environment}"
        self.metrics.inc("probe_attempts")
        start = time.time()
        healthy = self._probe(reg)
        latency = time.time() - start
        self.metrics.inc("probe_latency_total", latency)

        if healthy:
            self._failure_counts[key] = 0
            self.registry.mark_status(reg.name, reg.environment, "healthy")
            if self.incidents.open_incident_exists(reg.name, reg.environment):
                self.incidents.resolve_incident(reg.name, reg.environment)
            return True

        # unhealthy path
        self._failure_counts[key] = self._failure_counts.get(key, 0) + 1
        self.metrics.inc("probe_failures")
        self.registry.mark_status(reg.name, reg.environment, "unhealthy")

        if self._failure_counts[key] >= self.rule.failure_threshold:
            if not self.incidents.open_incident_exists(reg.name, reg.environment):
                inc = self.incidents.open_incident(reg.name, reg.environment)
                self.incidents.record_detection(reg.name, reg.environment)
                self.logger.error(
                    "Detected unhealthy service",
                    extra={"extra_context": {"service": key, "incident_start": inc.start_time}},
                )
            self.remediation.remediate(reg.name, reg.environment)
        return False

    def _probe(self, reg: ServiceRegistration) -> bool:
        try:
            health_resp = requests.get(reg.health_url, timeout=self.rule.timeout_seconds)
            ready_resp = requests.get(reg.ready_url, timeout=self.rule.timeout_seconds)
            return health_resp.status_code == 200 and ready_resp.status_code == 200
        except requests.RequestException:
            return False

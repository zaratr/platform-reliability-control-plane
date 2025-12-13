import logging
import time
from typing import Dict, Optional

import requests

from control_plane.registry.service_registry import ServiceRegistry
from control_plane.metrics.metrics_store import MetricsStore


class RemediationEngine:
    def __init__(self, registry: ServiceRegistry, metrics: MetricsStore, rate_limit_seconds: int = 30):
        self.registry = registry
        self.metrics = metrics
        self.rate_limit_seconds = rate_limit_seconds
        self._last_action: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    def _can_act(self, key: str) -> bool:
        last = self._last_action.get(key)
        return last is None or (time.time() - last) > self.rate_limit_seconds

    def _record_action(self, key: str) -> None:
        self._last_action[key] = time.time()

    def remediate(self, name: str, environment: str) -> str:
        key = f"{name}:{environment}"
        if not self._can_act(key):
            self.logger.info("Remediation suppressed due to rate limit", extra={"extra_context": {"service": key}})
            return "rate_limited"

        reg = self.registry.get_services().get(key)
        if not reg:
            return "missing"

        self.metrics.inc("remediation_attempts")
        try:
            resp = requests.post(f"{reg.control_url}/restart", timeout=2)
            if resp.status_code == 200:
                self.registry.mark_status(name, environment, "recovering")
                reg.last_known_good_version = reg.version
                self._record_action(key)
                self.logger.info("Restarted service", extra={"extra_context": {"service": key}})
                return "restarted"
        except requests.RequestException:
            self.logger.warning("Restart request failed", extra={"extra_context": {"service": key}})

        # fallback to rollback simulation
        try:
            rollback_version = reg.last_known_good_version or reg.version
            resp = requests.post(f"{reg.control_url}/rollback", json={"version": rollback_version}, timeout=2)
            if resp.status_code == 200:
                self.registry.mark_status(name, environment, "rolled_back")
                self._record_action(key)
                self.logger.info(
                    "Rolled back service",
                    extra={"extra_context": {"service": key, "version": rollback_version}},
                )
                return "rolled_back"
        except requests.RequestException:
            self.logger.error("Rollback failed", extra={"extra_context": {"service": key}})

        # degrade if unable to repair
        self.registry.mark_degraded(name, environment, True)
        self._record_action(key)
        self.metrics.inc("remediation_degraded")
        self.logger.error("Marked service degraded", extra={"extra_context": {"service": key}})
        return "degraded"

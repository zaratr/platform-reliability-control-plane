import threading
import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ServiceRegistration:
    name: str
    version: str
    base_url: str
    environment: str
    owner: str
    last_heartbeat: float = field(default_factory=time.time)
    status: str = "unknown"
    degraded: bool = False
    last_known_good_version: Optional[str] = None

    @property
    def health_url(self) -> str:
        return f"{self.base_url}/health"

    @property
    def ready_url(self) -> str:
        return f"{self.base_url}/ready"

    @property
    def control_url(self) -> str:
        return f"{self.base_url}/control"


class ServiceRegistry:
    """In-memory registry that tracks services and enforces heartbeats."""

    def __init__(self, heartbeat_timeout: int = 30):
        self._services: Dict[str, ServiceRegistration] = {}
        self._lock = threading.Lock()
        self.heartbeat_timeout = heartbeat_timeout

    def _key(self, name: str, environment: str) -> str:
        return f"{name}:{environment}"

    def register_service(
        self,
        name: str,
        version: str,
        base_url: str,
        environment: str,
        owner: str,
    ) -> ServiceRegistration:
        with self._lock:
            reg = ServiceRegistration(
                name=name,
                version=version,
                base_url=base_url.rstrip("/"),
                environment=environment,
                owner=owner,
                status="healthy",
                last_known_good_version=version,
            )
            self._services[self._key(name, environment)] = reg
            return reg

    def heartbeat(self, name: str, environment: str) -> Optional[ServiceRegistration]:
        key = self._key(name, environment)
        with self._lock:
            reg = self._services.get(key)
            if reg:
                reg.last_heartbeat = time.time()
            return reg

    def get_services(self) -> Dict[str, ServiceRegistration]:
        with self._lock:
            return dict(self._services)

    def mark_status(self, name: str, environment: str, status: str) -> None:
        key = self._key(name, environment)
        with self._lock:
            reg = self._services.get(key)
            if reg:
                reg.status = status

    def mark_degraded(self, name: str, environment: str, degraded: bool) -> None:
        key = self._key(name, environment)
        with self._lock:
            reg = self._services.get(key)
            if reg:
                reg.degraded = degraded

    def expired_services(self) -> Dict[str, ServiceRegistration]:
        now = time.time()
        with self._lock:
            return {
                key: reg
                for key, reg in self._services.items()
                if now - reg.last_heartbeat > self.heartbeat_timeout
            }

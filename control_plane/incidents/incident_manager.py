import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Incident:
    service: str
    environment: str
    start_time: float = field(default_factory=time.time)
    detection_time: Optional[float] = None
    resolution_time: Optional[float] = None
    status: str = "open"

    @property
    def mttr(self) -> Optional[float]:
        if self.detection_time and self.resolution_time:
            return self.resolution_time - self.detection_time
        return None


class IncidentManager:
    def __init__(self):
        self._incidents: List[Incident] = []
        self._lock = threading.Lock()

    def open_incident(self, service: str, environment: str) -> Incident:
        with self._lock:
            incident = Incident(service=service, environment=environment)
            self._incidents.append(incident)
            return incident

    def record_detection(self, service: str, environment: str) -> None:
        with self._lock:
            inc = self._find_open_incident(service, environment)
            if inc and not inc.detection_time:
                inc.detection_time = time.time()

    def resolve_incident(self, service: str, environment: str) -> None:
        with self._lock:
            inc = self._find_open_incident(service, environment)
            if inc:
                inc.resolution_time = time.time()
                inc.status = "resolved"

    def open_incident_exists(self, service: str, environment: str) -> bool:
        with self._lock:
            return self._find_open_incident(service, environment) is not None

    def all_incidents(self) -> List[Incident]:
        with self._lock:
            return list(self._incidents)

    def average_mttr(self) -> Optional[float]:
        with self._lock:
            mttrs = [i.mttr for i in self._incidents if i.mttr]
        if not mttrs:
            return None
        return sum(mttrs) / len(mttrs)

    def _find_open_incident(self, service: str, environment: str) -> Optional[Incident]:
        for inc in self._incidents:
            if inc.service == service and inc.environment == environment and inc.status == "open":
                return inc
        return None

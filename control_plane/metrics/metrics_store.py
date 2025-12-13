import threading
from collections import defaultdict
from typing import Dict


class MetricsStore:
    """Simple in-memory metrics store with Prometheus-style counters and gauges."""

    def __init__(self):
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, name: str, value: float = 1.0) -> None:
        with self._lock:
            self._counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def export(self) -> Dict[str, Dict[str, float]]:
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}

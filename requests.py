import json as _json
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional


class RequestException(Exception):
    pass


@dataclass
class Response:
    status_code: int
    _content: bytes = b""

    def json(self) -> Any:
        if self._content:
            return _json.loads(self._content)
        return None


def _request(method: str, url: str, timeout: Optional[float] = None, json: Optional[Dict[str, Any]] = None):
    data = None
    if json is not None:
        data = _json.dumps(json).encode("utf-8")
    try:
        req = urllib.request.Request(url, method=method.upper(), data=data)
        if json is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read()
            return Response(status_code=resp.getcode(), _content=content)
    except Exception as exc:  # noqa: BLE001
        raise RequestException(str(exc)) from exc


def get(url: str, timeout: Optional[float] = None):
    return _request("GET", url, timeout=timeout)


def post(url: str, json: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None):
    return _request("POST", url, timeout=timeout, json=json)

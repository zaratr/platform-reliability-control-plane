import os
import threading
import time
from typing import Optional

import requests
from fastapi import FastAPI

SERVICE_NAME = os.getenv("SERVICE_NAME", "sample-service-b")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("SERVICE_ENV", "dev")
PORT = int(os.getenv("PORT", "8102"))
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://control-plane:8000")

failure_mode: Optional[str] = None
latency_ms = 0

app = FastAPI(title=SERVICE_NAME)


def _register():
    base_url = f"http://{os.getenv('SERVICE_HOST', 'localhost')}:{PORT}"
    try:
        requests.post(
            f"{CONTROL_PLANE_URL}/register",
            json={
                "name": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "base_url": base_url,
                "environment": ENVIRONMENT,
                "owner": "platform-team",
            },
            timeout=3,
        )
    except requests.RequestException:
        pass


def _heartbeat():
    while True:
        try:
            requests.post(
                f"{CONTROL_PLANE_URL}/heartbeat",
                json={"name": SERVICE_NAME, "environment": ENVIRONMENT},
                timeout=2,
            )
        except requests.RequestException:
            pass
        time.sleep(10)


@app.on_event("startup")
async def startup_event():
    _register()
    thread = threading.Thread(target=_heartbeat, daemon=True)
    thread.start()


@app.get("/health")
async def health():
    if latency_ms:
        time.sleep(latency_ms / 1000)
    if failure_mode == "error":
        return {"status": "error"}, 500
    if failure_mode == "down":
        return {"status": "down"}, 503
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    if failure_mode == "down":
        return {"ready": False}, 503
    return {"ready": True}


@app.post("/control/fail")
async def fail(mode: str):
    global failure_mode
    failure_mode = mode
    return {"status": "set", "mode": mode}


@app.post("/control/latency")
async def set_latency(ms: int):
    global latency_ms
    latency_ms = ms
    return {"status": "latency_set", "ms": ms}


@app.post("/control/restart")
async def restart():
    global failure_mode, latency_ms
    failure_mode = None
    latency_ms = 0
    return {"status": "restarted"}


@app.post("/control/rollback")
async def rollback(version: Optional[str] = None):
    global failure_mode, latency_ms
    failure_mode = None
    latency_ms = 0
    return {"status": "rolled_back", "version": version or SERVICE_VERSION}


@app.get("/control/status")
async def status():
    return {"failure_mode": failure_mode, "latency_ms": latency_ms}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)

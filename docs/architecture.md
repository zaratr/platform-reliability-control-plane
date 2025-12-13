# Platform Reliability Control Plane - Architecture

This document explains how the control plane detects failures early, limits blast radius, and automates recovery across a fleet of services.

## Components
- **Service Registry**: services register with name, version, environment, owner, and base URL. Heartbeats keep entries fresh.
- **Health & Probe Engine**: polls `/health` and `/ready` on a configurable schedule with timeout and failure thresholds.
- **Observability Layer**: JSON logs with correlation context plus in-memory metrics counters/gauges.
- **Remediation Engine**: issues restart/rollback HTTP requests to services, is idempotent, and rate-limited per service.
- **Incident Tracking**: opens incidents on repeated probe failures, captures detection/resolution times, and computes MTTR.

## Control Plane Flow
1. Services register and begin sending heartbeats.
2. Health engine probes every few seconds.
3. On consecutive failures, the incident manager opens an incident and records detection time.
4. Remediation engine restarts or rolls back the service and marks it degraded if recovery fails.
5. When probes succeed again, the incident is resolved and MTTR is calculated.

## Failure Detection Rules
- **Timeout**: probe requests must complete within 2 seconds by default.
- **Threshold**: two consecutive failures transition a service to `unhealthy` and trigger remediation.
- **Heartbeat expiry**: registry exposes expired services for future cleanup workflows.

## Reliability Posture
- **Blast radius control**: degraded services are explicitly marked to gate downstream routing.
- **Proactive detection**: probes and heartbeats detect silent failures before customer impact.
- **Automated MTTR**: remediation is automatic; incident timestamps demonstrate time-to-repair effectiveness.

## Simplifications
- In-memory stores keep the code readable. Swap in Postgres/Redis/Prometheus for production.
- HTTP-based remediation simulates restart/rollback; replace with orchestrator calls (Kubernetes, Nomad).
- OpenTelemetry exporters are omitted; structured logs show how context would propagate.

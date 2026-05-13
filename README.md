# Platform Reliability Control Plane

Platform reliability as a shared service — service registry, health probing, automated remediation, and incident tracking. Upgraded in 2026 with an **AI Auto-Remediation agent**: when standard restart/rollback fails, an LLM reads the eBPF kernel traces, correlates them with recent Git commits, and opens a draft rollback PR — before the on-call engineer opens their laptop.

**Skills demonstrated:** Python · FastAPI · platform engineering · SRE · eBPF observability · LLM agentic workflows · GitHub API · incident management · MTTR tracking

> **Can this engineer design systems that detect failures early, reduce blast radius, and recover automatically — with AI in the loop?**

## 2026 Update: AI Auto-Remediation (`POST /ai-remediate`)

When restart and rollback strategies fail, the AI agent kicks in:

1. **eBPF trace reader** — samples kernel TCP latency and error events for the degraded process (zero SDK changes on target services)
2. **GitHub commit correlation** — fetches recent commits and file change lists
3. **LLM synthesis** — Ollama/Gemma locally or GPT-4o/Claude for cloud; generates root-cause hypothesis + rollback PR body
4. **Draft PR creation** — opens a GitHub draft PR targeting the identified bad commit

```
RemediationEngine restart → rollback fails
              │
              ▼
   AiRemediationAgent.analyse_and_remediate()
     ├── EbpfTraceReader  (kernel ring buffer)
     ├── GitHubClient     (recent commits)
     ├── LlmClient        (Ollama / OpenAI-compatible)
     └── GitHub draft PR  (dry-run safe)
```

Configure via env vars: `AI_REMEDIATION_LLM_URL`, `AI_REMEDIATION_LLM_MODEL`, `GITHUB_TOKEN`, `AI_REMEDIATION_DRY_RUN=true`.

This repository includes a lightweight control plane, sample services, failure injection, and documentation written like an internal reliability RFC.

## Why This Is a Platform Concern
Platform engineering creates paved paths so product teams inherit reliable-by-default behaviors: service registration, health probing, observability, and remediation. Instead of SRE firefighting per-service, the control plane manages a fleet, standardizes detection rules, and automates recovery while tracking operational outcomes such as MTTR.

## Features
- **Service registry** with heartbeat enforcement and ownership metadata.
- **Health & probe engine** that polls `/health` and `/ready` with configurable thresholds.
- **Observability layer** using structured logging, metrics counters, and correlation IDs.
- **Automated remediation** that restarts or rolls back services and marks them degraded with rate limiting and idempotency.
- **Incident tracking** with detection, resolution timestamps, and MTTR computation.
- **Failure injection** for latency, errors, and simulated process death.
- **Integration flow**: services register → control plane probes → failure injected → detection → automated remediation → incident recorded.

## Repository Layout
```
platform-reliability-control-plane/
├── README.md
├── control_plane/
│   ├── registry/
│   ├── health/
│   ├── remediation/
│   ├── metrics/
│   ├── incidents/
│   └── observability/
├── docs/
├── services/
│   ├── sample-service-a/
│   └── sample-service-b/
├── docker-compose.yml
└── tests/
```

## Quickstart
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the control plane and sample services locally**
   ```bash
   docker-compose up --build
   ```
   - Control plane API: `http://localhost:8000`
   - Sample service A: `http://localhost:8101`
   - Sample service B: `http://localhost:8102`

3. **Inject a failure**
   ```bash
   curl -X POST "http://localhost:8101/control/fail?mode=error"
   ```
   The control plane detects the failure, triggers remediation, and records an incident.

4. **View platform state**
   - `/services` to list registered services
   - `/incidents` to view incident history and MTTR
   - `/metrics` to inspect in-memory counters

## Observability and Detection Model
- **Probes**: periodic `/health` and `/ready` checks with configurable timeout and failure thresholds.
- **Metrics**: Prometheus-style counters for probe attempts, failures, remediation actions, and uptime tracking.
- **Logging**: structured JSON logs with correlation IDs for each probe/remediation action.

## Automated Recovery Strategies
- **Restart**: invoke the service control endpoint to reset state.
- **Rollback**: mark the service as running the last known good version (simulated for the sample services).
- **Degrade**: mark the service as degraded to limit blast radius when rate limits are exceeded.

All remediation actions are idempotent and rate-limited per service to avoid flapping.

## Scaling Notes
This repository intentionally simplifies infrastructure. In production you would integrate:
- Persistent stores for registry, incidents, and metrics (e.g., Postgres, Prometheus).
- Distributed tracing with OpenTelemetry exporters.
- Kubernetes primitives for restarts/rollbacks instead of HTTP calls.
- AuthN/Z and tenancy boundaries for multi-team use.

## Running Tests
Run the unit and integration tests with:
```bash
pytest
```

## Design Scope
In-memory stores and HTTP-simulated restarts keep the focus on the control plane logic rather than infrastructure plumbing. Production extensions are documented in the Scaling Notes section — the interfaces are designed to swap in Postgres, Kubernetes primitives, and real chaos tooling without changing the core control plane contracts.

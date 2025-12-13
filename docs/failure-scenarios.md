# Failure Scenarios and Detection

The control plane includes built-in failure injection on the sample services to demonstrate detection and remediation.

## Scenarios
1. **Error responses**
   - Trigger: `POST /control/fail?mode=error`
   - Effect: service returns HTTP 500 for `/health` and `/ready`.
   - Detection: probe failures exceed threshold and open an incident.
   - Remediation: control plane issues `/control/restart` to clear the error flag.

2. **Latency injection**
   - Trigger: `POST /control/latency?ms=1500`
   - Effect: `/health` delays responses, risking probe timeouts.
   - Detection: probe timeout increments failure counters and can trigger remediation.
   - Remediation: restart resets latency budget.

3. **Simulated process death**
   - Trigger: `POST /control/fail?mode=down`
   - Effect: `/ready` returns 503, emulating an unreachable app.
   - Detection: probe failures create an incident.
   - Remediation: `/control/restart` marks the service as recovered.

## Validation Flow
1. Start the stack: `docker-compose up --build`.
2. Watch the control plane logs for probe attempts.
3. Inject a failure on `sample-service-a`.
4. Observe incident creation via `GET /incidents`.
5. Observe remediation logs followed by recovery and MTTR calculation.

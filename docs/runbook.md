# Reliability Runbook

This runbook describes how the platform team operates the control plane and responds to incidents.

## Detect
- The health engine probes services every 5 seconds.
- Two consecutive probe failures mark a service `unhealthy` and open an incident.
- Metrics counters: `probe_attempts`, `probe_failures`, `remediation_attempts`.

## Triage
1. Check `/services` for current status and degradation flag.
2. Review `/incidents` to confirm detection time and MTTR trend.
3. Inspect logs for the correlation ID printed in probe/remediation entries.

## Mitigate
- Control plane automatically calls `/control/restart` on the service.
- If restart fails, it attempts `/control/rollback` using the last known good version.
- Persistent failures mark the service as degraded to gate blast radius.

## Restore
- When probes succeed, the incident is auto-resolved and MTTR is updated.
- If automation cannot recover a service, manually call service control endpoints or redeploy the service.

## Post-Incident
- Capture MTTR from `/incidents` and create a follow-up task if MTTR exceeds SLO.
- Review failure scenario coverage and add probes/remediation steps as necessary.

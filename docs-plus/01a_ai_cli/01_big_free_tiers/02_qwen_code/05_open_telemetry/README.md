# Qwen Code Observability Guide (OpenTelemetry)

Telemetry provides data about performance, health, and usage. Qwen Code uses OpenTelemetry (OTEL), so you can export traces, metrics, and logs to any compatible backend.

## Enabling telemetry
- Configure via `.qwen/settings.json`, `~/.qwen/settings.json`, environment variables, or CLI flags (highest precedence).

## Hands On

Goal: Enable telemetry via settings.json, run a short task, and inspect artifacts.

Drill (3 steps)
1) Create `.qwen/settings.json` in `01_hello_qwen`:
   ```json
   {
     "telemetry": {
       "enabled": true,
       "target": "local",
       "logPrompts": true
     }
   }
   ```
2) Run: `qwen --telemetry --telemetry-target=local --telemetry-otlp-endpoint="" --telemetry-outfile=.qwen/telemetry.log -p "Explain main.py in 2 lines"`
3) Open `.qwen/telemetry.log` and skim entries.

---
# Public engineering labs

Two independently runnable, self-contained Python demos focused on **GenAI / agent support** and **enterprise integration diagnostics**. Everything uses **fictional incidents and configuration**, not employer or customer information.

| Project | What it demonstrates | Run |
| --- | --- | --- |
| [Agent Incident Triage Lab](agent-incident-triage-lab/) | Bounded tool-using agent simulation, grounding against local runbooks, evidence citation, synthetic incident evaluation | `python agent-incident-triage-lab/evaluate.py` |
| [Enterprise Connector Diagnostics](enterprise-connector-diagnostics/) | OAuth issuer/audience/scope troubleshooting, HTTP errors, security-aware reporting | `python enterprise-connector-diagnostics/connector_diagnostics.py --case missing_scope` |

Both projects use **Python 3.10+ and the standard library only**. Each subdirectory contains its own README and unit tests; all functionality runs offline. These are **educational simulations, not production Google Cloud implementations** or claims of working on specific customer incidents.

## Run all tests

```bash
cd projects/agent-incident-triage-lab && python -m unittest discover -v
cd ../enterprise-connector-diagnostics && python -m unittest discover -v
```

The projects are intentionally separated so they can later be copied into independent GitHub repositories without modifying import paths.

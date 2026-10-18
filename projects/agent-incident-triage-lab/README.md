# Agent Incident Triage Lab

A **reproducible, offline, tool-using incident triage agent simulation** for synthetic GenAI / RAG / tool-calling problems. It demonstrates the *architecture* of a bounded agent workflow, diagnostic-tool orchestration, runbook grounding, evidence citations, and evaluation—not access to Google's internal systems.

## Why this exists

Enterprise GenAI support requires more than a polished chatbot: an investigation needs reproducible observations, correlation between logs and configuration/metrics, clear uncertainty, and traceable recommendations. This lab makes those engineering choices explicit.

## Architecture

```text
Synthetic incident
    |  bounded sequential planning
    +--> inspect_logs -------------+
    +--> inspect_configuration ---+--> corroborated hypotheses --> next action
    +--> inspect_metrics ---------+            |
    +--> retrieve_runbooks -------+       source IDs / citations
```

- **Read-only allowlist:** four inspection tools; unknown tool names are rejected.
- **Local runbook retrieval:** token-overlap matching with source IDs, independent of any hosted API.
- **Evidence guardrail:** a proposed cause requires observations from **two different source types**; otherwise the case is explicitly unresolved.
- **Safety:** no credential collection, external requests, write operations, or real customer incidents.
- **Evaluation:** a checked-in, **four-case synthetic golden set** tests expected triage labels and citation integrity.

## Quick start (Python 3.10+, standard library only)

```bash
python incident_agent.py --case auth
python incident_agent.py --case quota
python incident_agent.py --case retrieval
python incident_agent.py --case unknown
python evaluate.py
python -m unittest discover -s . -p 'test_*.py' -v
```

Sample cases cover OAuth scope errors (`403`), quota/rate limiting (`429`), missing RAG grounding, and insufficient evidence. Output is JSON with the tool trace, evidence references, an explicitly bounded hypothesis and proposed next action.

## Evaluation scope

The four checked-in fixtures are **synthetic examples, not a statistical benchmark** or demonstrated performance on production incidents. The planner is deterministic, not an LLM or Google's Agent Development Kit (ADK). This allows the tests and the trust boundary to run fully offline. An LLM planner or Vertex AI adapter could be added behind `SequentialPlanner` after separate validation and security review.

## Security and limitations

Only run on synthetic/public inputs. Runbook retrieval is a simple lexical baseline, not embedding-based RAG. The demo does not verify OAuth tokens, resolve incidents, provide operational recommendations for real customers, or demonstrate production readiness.

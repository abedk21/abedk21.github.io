"""Offline, evidence-grounded incident triage agent for synthetic AI workloads.

No Google customer data, network calls, external packages or credentials are used.
This is a deterministic agent *simulation*, not a production LLM agent.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parent
TOOL_ALLOWLIST = ("inspect_logs", "inspect_configuration", "inspect_metrics", "retrieve_runbooks")
STOPWORDS = {"an", "a", "and", "the", "for", "from", "with", "into", "are", "on", "of", "in", "to", "is", "at", "or", "be"}


def terms(value: str) -> set[str]:
    return {x for x in re.findall(r"[a-z0-9_]+", value.lower()) if x not in STOPWORDS and len(x) > 2}


@dataclass(frozen=True)
class Evidence:
    ref: str
    source: str
    detail: str


class ReadOnlyTools:
    """Allowlisted tools returning structured, source-addressable observations."""

    def __init__(self, case: dict[str, Any], runbooks: list[dict[str, Any]]):
        self.case, self.runbooks = case, runbooks

    def call(self, name: str) -> list[Evidence]:
        if name not in TOOL_ALLOWLIST:
            raise ValueError(f"Tool not allowed: {name}")
        if name == "inspect_logs":
            return [Evidence(str(e["id"]), "log", str(e["message"])) for e in self.case["logs"][:20]]
        if name == "inspect_configuration":
            return [Evidence(f"CFG-{key}", "config", f"{key}={json.dumps(value)}")
                    for key, value in sorted(self.case["config"].items())
                    if not re.search(r"secret|token_value|password|api_key", key, re.I)]
        if name == "inspect_metrics":
            return [Evidence(f"METRIC-{key}", "metric", f"{key}={value}")
                    for key, value in sorted(self.case["metrics"].items())]
        # Small local grounding corpus: retrieval with simple token overlap.
        query = " ".join([self.case["summary"]] + [x["message"] for x in self.case["logs"]])
        q = terms(query)
        scored = []
        for doc in self.runbooks:
            d = terms(doc["title"] + " " + doc["symptoms"] + " " + doc["guidance"])
            score = len(q & d) / max(1, len(q))
            if score:
                scored.append((score, doc["id"], doc))
        return [Evidence(x["id"], "runbook", f"{x['title']}: {x['guidance']}")
                for _, _, x in sorted(scored, key=lambda entry: (-entry[0], entry[1]))[:2]]


class SequentialPlanner:
    """Bounded planning policy; an LLM planner can replace this interface later."""

    def next_tool(self, history: list[str]) -> str | None:
        return next((name for name in TOOL_ALLOWLIST if name not in history), None)


def diagnose(case: dict[str, Any], evidence: list[Evidence]) -> dict[str, Any]:
    """Hypotheses are made only if two independent evidence sources agree."""
    logs = " ".join(x.detail.lower() for x in evidence if x.source == "log")
    config = case["config"]
    metrics = case["metrics"]
    by_id = {e.ref: e for e in evidence}

    def refs_for(*needles: str) -> list[str]:
        return [x.ref for x in evidence if any(needle in x.detail.lower() for needle in needles)]

    if ("403" in logs or "permission_denied" in logs) and (
        config.get("required_scope") not in config.get("granted_scopes", [])
        and config.get("required_scope") is not None
    ):
        refs = refs_for("403", "permission_denied", "required_scope", "granted_scopes")
        category = "oauth_scope_mismatch"
        action = "Verify the connector's required OAuth scopes and obtain appropriately authorized consent."
    elif ("429" in logs or "resource_exhausted" in logs) and float(metrics.get("quota_utilization", 0)) >= 0.9:
        refs = refs_for("429", "resource_exhausted", "quota_utilization")
        category = "quota_exhaustion"
        action = "Check quota metrics, respect retry guidance, and request capacity if appropriate."
    elif "grounding" in logs and config.get("retrieval_enabled") is False:
        refs = refs_for("grounding", "retrieval_enabled")
        category = "retrieval_disabled"
        action = "Validate the retrieval configuration and repeat the grounded evaluation."
    else:
        refs, category, action = [], "insufficient_evidence", "Collect additional diagnostics and escalate with a reproducible case."

    supporting = list(dict.fromkeys(ref for ref in refs if ref in by_id))
    source_types = {by_id[ref].source for ref in supporting}
    if len(source_types) < 2:
        category = "insufficient_evidence"
        action = "Collect independently corroborating evidence before assigning a cause."
        supporting = []
    return {"hypothesis": category, "confidence": "corroborated" if supporting else "unconfirmed",
            "evidence_refs": supporting, "next_action": action}


def run(case: dict[str, Any], runbooks: list[dict[str, Any]], max_steps: int = 4) -> dict[str, Any]:
    if not 1 <= max_steps <= len(TOOL_ALLOWLIST):
        raise ValueError("max_steps must be between 1 and 4")
    tools, planner = ReadOnlyTools(case, runbooks), SequentialPlanner()
    traces: list[str] = []
    observations: list[Evidence] = []
    for _ in range(max_steps):
        tool = planner.next_tool(traces)
        if tool is None:
            break
        traces.append(tool)
        observations.extend(tools.call(tool))
    diagnosis = diagnose(case, observations)
    return {"case_id": case["id"], "tool_trace": traces,
            "diagnosis": diagnosis,
            "evidence": [asdict(entry) for entry in observations],
            "safety": {"read_only": True, "external_requests": 0, "synthetic_data": True}}


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic AI incident triage with cited evidence")
    parser.add_argument("--case", choices=["auth", "quota", "retrieval", "unknown"], default="auth")
    parser.add_argument("--max-steps", type=int, default=4)
    args = parser.parse_args()
    dataset = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    runbooks = json.loads((ROOT / "runbooks.json").read_text(encoding="utf-8"))
    print(json.dumps(run(dataset[args.case], runbooks, max_steps=args.max_steps), indent=2))


if __name__ == "__main__":
    main()

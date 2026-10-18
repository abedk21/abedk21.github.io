"""Run the checked-in synthetic golden set with strict, reproducible scoring."""
import json
from pathlib import Path
from incident_agent import run

ROOT = Path(__file__).resolve().parent


def evaluate() -> dict:
    cases = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
    runbooks = json.loads((ROOT / "runbooks.json").read_text(encoding="utf-8"))
    results = []
    for name, case in cases.items():
        outcome = run(case, runbooks)
        diagnosis = outcome["diagnosis"]
        results.append({"case": name, "expected": case["expected"],
                        "predicted": diagnosis["hypothesis"],
                        "correct": diagnosis["hypothesis"] == case["expected"],
                        "grounded": all(ref in {e["ref"] for e in outcome["evidence"]}
                                        for ref in diagnosis["evidence_refs"])})
    return {"cases": len(results), "accuracy": sum(x["correct"] for x in results) / len(results),
            "all_citations_valid": all(x["grounded"] for x in results), "results": results}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))

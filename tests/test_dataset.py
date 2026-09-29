import json
import math
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

class EvidenceTests(unittest.TestCase):
    def test_intent_slice_evidence(self):
        plan = load(ROOT / "plan-v1.json")
        lineage = load(ROOT / "lineage.json")
        decision = load(ROOT / "results/2026-09-29/decision.json")
        intent_id = plan["intents"][0]["id"]
        assert len(plan["intents"]) == 1
        assert lineage["slice_intent_id"] == intent_id
        assert lineage["upstream_repository"].endswith("gooo-metaprogramming-experiments")
        assert re.fullmatch(r"[0-9a-f]{40}", lineage["upstream_commit"])
        assert decision["intent_id"] == intent_id
        assert decision["laya"]["intent_id"] == intent_id
        assert decision["deterministic_fallback"]["intent_id"] == intent_id

        paths = sorted((ROOT / "experiments").glob("*.json"))
        assert len(paths) == 10
        records = [load(path) for path in paths]
        expected_routes = {route["id"] for route in plan["routes"]}
        assert len(expected_routes) == 10
        assert {row["lowering_route"]["id"] for row in records} == expected_routes
        for row in records:
            assert row["intent"]["id"] == intent_id
            result = row["result"]
            assert result["intent_id"] == intent_id
            assert result["route_id"] == row["lowering_route"]["id"]
            assert result["total"] == 25
            assert 0 <= result["covered"] <= result["total"]
            assert 0 <= result["clauses_covered"] <= result["clauses_total"]
            assert math.isclose(result["behavioral_completeness"], result["covered"] / result["total"], abs_tol=1e-9)
            assert math.isclose(result["rule_clause_completeness"], result["clauses_covered"] / result["clauses_total"], abs_tol=1e-9)
            assert result["compiled"] is True and result["deterministic"] is True
            assert result["source_sha256"] == result["replay_sha256"]
            assert re.fullmatch(r"sha256:[0-9a-f]{64}", result["source_sha256"])

        laya = decision["laya"]
        probabilities = laya["receipt"]["probabilities"]
        assert set(probabilities) == expected_routes
        assert math.isclose(sum(probabilities.values()), 1.0, abs_tol=0.002)
        assert laya["top1_route"] == max(probabilities, key=probabilities.get)
        assert laya["sampled_route"] in expected_routes
        assert decision["deterministic_fallback"]["top1_route"] in expected_routes
        assert decision["deterministic_fallback"]["receipt"]["mode"] == "deterministic_fallback"

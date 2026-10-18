import json
from pathlib import Path
import unittest
from incident_agent import ReadOnlyTools, run, diagnose, Evidence
from evaluate import evaluate

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / 'cases.json').read_text(encoding='utf-8'))
RUNBOOKS = json.loads((ROOT / 'runbooks.json').read_text(encoding='utf-8'))


class IncidentAgentTests(unittest.TestCase):
    def test_golden_set(self):
        self.assertEqual(evaluate()['accuracy'], 1)

    def test_all_evidence_refs_resolve(self):
        for case in CASES.values():
            result = run(case, RUNBOOKS)
            ids = {x['ref'] for x in result['evidence']}
            self.assertTrue(set(result['diagnosis']['evidence_refs']) <= ids)

    def test_tools_are_read_only(self):
        for case in CASES.values():
            result = run(case, RUNBOOKS)
            self.assertEqual(result['safety']['external_requests'], 0)
            self.assertTrue(result['safety']['read_only'])

    def test_unknown_tool_is_blocked(self):
        with self.assertRaisesRegex(ValueError, 'Tool not allowed'):
            ReadOnlyTools(CASES['auth'], RUNBOOKS).call('delete_customer_data')

    def test_bounded_steps(self):
        result = run(CASES['auth'], RUNBOOKS, max_steps=2)
        self.assertEqual(result['tool_trace'], ['inspect_logs', 'inspect_configuration'])
        self.assertEqual(result['diagnosis']['hypothesis'], 'oauth_scope_mismatch')
        with self.assertRaises(ValueError):
            run(CASES['auth'], RUNBOOKS, max_steps=5)

    def test_single_source_is_not_enough(self):
        evidence = [Evidence('LOG-X','log','403 PERMISSION_DENIED')]
        result = diagnose(CASES['auth'], evidence)
        self.assertEqual(result['hypothesis'], 'insufficient_evidence')

    def test_runbook_retrieval_is_bounded_and_cited(self):
        result = ReadOnlyTools(CASES['auth'], RUNBOOKS).call('retrieve_runbooks')
        self.assertLessEqual(len(result), 2)
        self.assertTrue(all(x.ref.startswith('RB-') for x in result))

    def test_sensitive_configuration_value_not_exported(self):
        case = dict(CASES['auth'])
        case['config'] = {**case['config'], 'api_key':'SYNTHETIC-DO-NOT-DISPLAY'}
        result = run(case, RUNBOOKS)
        self.assertNotIn('SYNTHETIC-DO-NOT-DISPLAY', json.dumps(result))


if __name__ == '__main__':
    unittest.main()

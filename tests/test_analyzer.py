import unittest
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import core.static_analyzer as static_analyzer
from core.dynamic_profiler import GreenCodeProfiler
from core.ai_optimizer import GreenCodeAIOptimizer
import database

class TestGreenCodeAI(unittest.TestCase):
    def setUp(self):
        database.init_db()

    def test_static_analyzer_detects_nested_loops(self):
        code = """
def bad_function(arr):
    for i in arr:
        for j in arr:
            if j in arr:
                pass
        """
        analysis = static_analyzer.analyze_code_sustainability(code)
        self.assertLess(analysis["eco_score"], 100)
        self.assertGreater(analysis["issue_count"], 0)
        severities = analysis["severity_summary"]
        self.assertGreaterEqual(severities["High"] + severities["Medium"], 1)

    def test_dynamic_profiler_execution(self):
        code = """
x = sum(i * i for i in range(10000))
        """
        profile = GreenCodeProfiler.profile_code(code)
        self.assertIn("energy_joules", profile)
        self.assertIn("carbon_gco2e", profile)
        self.assertGreater(profile["execution_time_ms"], 0)
        self.assertIsNone(profile["error"])

    def test_ai_optimizer_transformation(self):
        code = """
def process(items):
    s = ""
    for i in items:
        if i in items:
            s += str(i)
    return s
        """
        analysis = static_analyzer.analyze_code_sustainability(code)
        opt_res = GreenCodeAIOptimizer.optimize_code(code, analysis["issues"])
        self.assertIn("optimized_code", opt_res)
        self.assertGreater(len(opt_res["transformations"]), 0)

    def test_database_persistence_and_deletion(self):
        audit_id = database.save_audit(
            project_name="Deletion Test Run",
            language="python",
            original_code="print('hello')",
            optimized_code="print('hello')",
            orig_score=80,
            opt_score=100,
            orig_joules=0.5,
            opt_joules=0.1,
            carbon_saved_pct=80.0,
            speedup_factor=2.0,
            issue_count=1
        )
        self.assertIsNotNone(audit_id)
        record = database.get_audit_by_id(audit_id)
        self.assertEqual(record["project_name"], "Deletion Test Run")

        # Test Deletion
        deleted = database.delete_audit(audit_id)
        self.assertTrue(deleted)
        record_after = database.get_audit_by_id(audit_id)
        self.assertIsNone(record_after)

if __name__ == '__main__':
    unittest.main()

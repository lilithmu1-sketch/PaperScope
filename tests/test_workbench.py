"""Integration checks for actual data, trust boundaries, and the demonstrated blind spot."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import workbench as audit

PROJECT = Path(__file__).resolve().parents[1]


class WorkbenchTests(unittest.TestCase):
    def test_actual_frozen_outputs_remain_checkable(self):
        result = audit.audit(PROJECT)
        self.assertEqual(len(result["runs"]), 8)
        self.assertEqual(sum(row["claims_count"] for row in result["runs"]), 140)
        self.assertTrue(result["all_integrity_checks_passed"])
        self.assertTrue(result["all_registered_sources_match"])
        self.assertFalse(result["semantic_support_verified"])

    def test_semantic_mutation_is_explicitly_a_blind_spot(self):
        result = audit.probes(PROJECT)
        self.assertTrue(result["all_expected_behaviours_observed"])
        self.assertFalse(result["real_model_rerun"])
        blind = next(p for p in result["probes"] if p["probe"] == "wrong_statement_with_unchanged_real_quote")
        self.assertTrue(blind["synthetic"])
        self.assertTrue(blind["integrity_passed"])

    def test_search_scope_and_evidence_are_exact(self):
        corpus = audit.load_corpora(PROJECT)["crabnet"]
        result = audit.search({"crabnet": corpus}, "CrabNet 划分 泛化")
        blocks = {b["block_id"]: b for b in corpus["blocks"]}
        self.assertIn("split", result["expanded_query"])
        self.assertTrue(result["results"])
        for item in result["results"]:
            self.assertEqual(item["source_id"], "crabnet")
            self.assertEqual(item["text"], blocks[item["block_id"]]["text"])
        self.assertEqual(audit.search({"crabnet": corpus}, "UNMATCHED_TOKEN_394928")["results"], [])

    def test_rendered_documents_cannot_close_html_elements(self):
        report = audit.audit(PROJECT)
        malicious = "</textarea><script>window.__DOCUMENT_INJECTION__=1</script>"
        report["runs"][0]["claims"][0]["statement"] = malicious
        page = audit.render(report, audit.load_corpora(PROJECT))
        self.assertNotIn(malicious, page)
        self.assertIn("&lt;script&gt;window.__DOCUMENT_INJECTION__", page)
        self.assertIn("connect-src 'none'", page)
        self.assertIn(report["runs"][0]["claims_file_sha256"], page)

    def test_declared_input_paths_cannot_escape_project(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                audit.bounded(Path(directory), "../private-file")


if __name__ == "__main__":
    unittest.main()

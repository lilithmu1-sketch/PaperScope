"""Synthetic unit tests for mechanical evidence checks, not research results."""
import copy
import importlib.util
from pathlib import Path
import io
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("paperscope", Path(__file__).resolve().parents[1] / "tools/paperscope.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.corpus = {"source_id": "synthetic", "source_sha256": "a" * 64, "blocks": [
            {"block_id": "p01-b01", "pdf_page": 1, "text": "Method A has MAE 0.12 eV on the stated split. No prospective test was performed."}]}
        self.claims = {"schema_version": "1.0", "source_ids": ["synthetic"], "claims": [
            {"id": "C01", "statement": "MAE is 0.12 eV on the stated split.", "kind": "fact", "verdict": "supported",
             "evidence": [{"source_id": "synthetic", "block_id": "p01-b01", "quote": "MAE 0.12 eV"}],
             "reasoning": "Synthetic test statement."}]}

    def errors(self):
        return MODULE.claims_errors([self.corpus], self.claims)

    def test_exact_quote_passes_without_claiming_semantics(self):
        self.assertEqual(self.errors(), [])
        report = MODULE.result([])
        self.assertFalse(report["semantic_support_verified"])
        self.assertIsNone(report["competition_score"])

    def test_altered_number_rejected(self):
        self.claims["claims"][0]["evidence"][0]["quote"] = "MAE 0.10 eV"
        self.assertTrue(self.errors())

    def test_stitched_quote_rejected(self):
        self.claims["claims"][0]["evidence"][0]["quote"] = "Method A has No prospective test"
        self.assertTrue(self.errors())

    def test_unknown_source_rejected(self):
        self.claims["claims"][0]["evidence"][0]["source_id"] = "another-paper"
        self.assertTrue(self.errors())

    def test_wrong_page_block_rejected(self):
        self.claims["claims"][0]["evidence"][0]["block_id"] = "p99-b01"
        self.assertTrue(self.errors())

    def test_source_qualified_anchor_is_unambiguous(self):
        self.claims["claims"][0]["evidence"][0]["block_id"] = "synthetic:p01-b01"
        self.assertEqual(self.errors(), [])

    def test_different_qualified_source_rejected(self):
        self.claims["claims"][0]["evidence"][0]["block_id"] = "another:p01-b01"
        self.assertTrue(self.errors())

    def test_duplicate_claim_rejected(self):
        self.claims["claims"].append(copy.deepcopy(self.claims["claims"][0]))
        self.assertTrue(self.errors())

    def test_unknown_must_not_be_supported(self):
        self.claims["claims"][0]["kind"] = "unknown"
        self.assertTrue(self.errors())

    def test_factual_claim_without_evidence_rejected(self):
        self.claims["claims"][0]["evidence"] = []
        self.assertTrue(self.errors())

    def test_unknown_with_explained_gap_allowed(self):
        self.claims["claims"][0].update(kind="unknown", verdict="insufficient", evidence=[])
        self.assertEqual(self.errors(), [])

    def test_repeated_quote_ambiguous(self):
        self.corpus["blocks"][0]["text"] += " MAE 0.12 eV"
        self.assertTrue(self.errors())

    def test_whitespace_normalization(self):
        self.claims["claims"][0]["evidence"][0]["quote"] = "MAE\n0.12   eV"
        self.assertEqual(self.errors(), [])

    def test_unhashable_identifier_returns_error(self):
        self.claims["claims"][0]["evidence"][0]["source_id"] = []
        self.assertTrue(self.errors())

    def test_invalid_corpus_structure(self):
        self.assertTrue(MODULE.corpus_errors({"blocks": [None]}))

    def test_comparison_unknown_reference(self):
        body = "item,paper_setting,target_setting,comparability,evidence_ids\ninput,formula,structure,mismatch,C99\n"
        with patch.object(Path, "open", return_value=io.StringIO(body)):
            path = Path("synthetic-comparison.csv")
            self.assertTrue(MODULE.comparison_errors(path, self.claims))

    def test_missing_claims_object(self):
        self.assertTrue(MODULE.claims_errors([self.corpus], []))


if __name__ == "__main__":
    unittest.main()

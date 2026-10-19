"""Behavioral checks; fixtures remain in ignored .local/test-runs."""

from pathlib import Path
import json
import shutil
import subprocess
import sys
import unittest
import uuid

from scripts import wiki


class WikiBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_root = wiki.ROOT / ".local" / "test-runs" / uuid.uuid4().hex
        cls.run_root.mkdir(parents=True)

    def setUp(self):
        self.workspace = self.run_root / self._testMethodName
        self.workspace.mkdir()
        self.vault = self.workspace / "vault"
        shutil.copytree(wiki.ROOT / "examples" / "vault", self.vault)

    def edit_page(self, relative, change):
        path = self.vault / "wiki" / relative
        page = wiki.read_page(path)
        change(page)
        path.write_text(wiki.page_text(page.metadata, page.body), encoding="utf-8")
        return path

    def edit_record(self, relative, **updates):
        path = self.vault / "wiki" / "observations" / relative
        record = wiki.read_json(path)
        record.update(updates)
        path.write_text(json.dumps(record, indent=2), encoding="utf-8")

    def errors(self):
        return "\n".join(wiki.inspect_vault(self.vault).errors)

    def test_example_has_no_structural_errors_or_warnings(self):
        report = wiki.inspect_vault(self.vault)
        self.assertEqual(report.issues, [])
        self.assertEqual((len(report.pages), len(report.records)), (9, 5))

    def test_alias_search_finds_attributed_concept(self):
        matches = wiki.find_pages(wiki.inspect_vault(self.vault), "routine persistence")
        self.assertEqual(matches[0]["path"], "concepts/routine-continuity.md")

    def test_exact_filters_preserve_different_universes(self):
        report = wiki.inspect_vault(self.vault)
        broad = wiki.select_records(report, {"metric": "membership", "period": "2025"})
        self.assertEqual({row["universe"] for row in broad},
                         {"adult membership", "all-age membership"})
        narrow = wiki.select_records(report, {"metric": "membership", "period": "2025",
                                             "universe": "all-age membership"})
        self.assertEqual([row["value"] for row in narrow], [1200])

    def test_missing_value_and_measured_zero_remain_distinct(self):
        records = wiki.select_records(wiki.inspect_vault(self.vault), {})
        by_id = {row["id"]: row for row in records}
        self.assertIsNone(by_id["harbor-departures-2025"]["value"])
        self.assertEqual(by_id["bench-failures"]["value"], 0)

    def test_corruption_prevents_partial_record_answers(self):
        self.edit_record("membership-2024.json", value=True)
        report = wiki.inspect_vault(self.vault)
        with self.assertRaises(wiki.WikiError):
            wiki.select_records(report, {"period": "2025"})

    def test_new_page_refuses_to_replace_existing_text(self):
        path = wiki.create_page(self.vault, "note", "A new idea", "A private question.")
        before = path.read_bytes()
        with self.assertRaises(FileExistsError):
            wiki.create_page(self.vault, "note", "A new idea", "A replacement.")
        self.assertEqual(path.read_bytes(), before)

    def test_initialization_preserves_existing_directory(self):
        sentinel = self.workspace / "existing" / "keep.txt"
        sentinel.parent.mkdir()
        sentinel.write_text("Preserve me", encoding="utf-8")
        with self.assertRaises(wiki.WikiError):
            wiki.initialize(sentinel.parent, "New topic", ["theory"])
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "Preserve me")

    def test_initialization_is_empty_and_private(self):
        target = self.workspace / "empty"
        wiki.initialize(target, "Empty topic", ["theory", "quantitative"])
        report = wiki.inspect_vault(target)
        self.assertEqual(report.issues, [])
        self.assertEqual(report.pages, [])
        self.assertEqual(report.config["save_answers"], "on_request")
        with self.assertRaises(wiki.WikiError):
            wiki.initialize(wiki.ROOT / "examples" / "new-topic", "Not private", ["theory"])

    def test_capture_deduplicates_and_retains_new_versions(self):
        supplied = self.workspace / "input.txt"
        supplied.write_text("Original source", encoding="utf-8")
        first_id, first_page, reused = wiki.capture_source(
            self.vault, supplied, "test-source", "Test source")
        self.assertFalse(reused)
        first_bytes = first_page.read_bytes()
        repeated_id, _, reused = wiki.capture_source(
            self.vault, supplied, "test-source", "Test source")
        self.assertTrue(reused)
        self.assertEqual(first_id, repeated_id)
        supplied.write_text("New source version", encoding="utf-8")
        next_id, _, reused = wiki.capture_source(
            self.vault, supplied, "test-source", "Test source")
        self.assertFalse(reused)
        self.assertNotEqual(first_id, next_id)
        self.assertEqual(first_page.read_bytes(), first_bytes)
        report = wiki.inspect_vault(self.vault)
        original = self.vault / report.captures[first_id]["path"]
        self.assertEqual(original.read_text(encoding="utf-8"), "Original source")
        self.assertFalse(report.errors)

    def test_changed_raw_bytes_fail_hash_check(self):
        raw = self.vault / "raw" / "captures" / "fictional-report" / "original.txt"
        raw.write_text("Changed evidence", encoding="utf-8")
        self.assertIn("hash changed", self.errors())

    def test_indexing_does_not_rewrite_human_notes(self):
        note = self.vault / "wiki" / "notes" / "unresolved-question.md"
        before = note.read_bytes()
        wiki.build_indexes(self.vault)
        self.assertEqual(note.read_bytes(), before)

    def test_unmarked_index_stops_all_index_writes(self):
        root = self.vault / "wiki" / "index.md"
        root_before = root.read_bytes()
        manual = self.vault / "wiki" / "notes" / "index.md"
        manual.write_text("# My manual reading path\n", encoding="utf-8")
        with self.assertRaises(wiki.WikiError):
            wiki.build_indexes(self.vault)
        self.assertEqual(manual.read_text(encoding="utf-8"), "# My manual reading path\n")
        self.assertEqual(root.read_bytes(), root_before)

    def test_duplicate_yaml_and_json_keys_are_reported(self):
        page = self.vault / "wiki" / "concepts" / "routine-continuity.md"
        page.write_text(page.read_text(encoding="utf-8").replace(
            "type: concept", "type: concept\ntype: entity"), encoding="utf-8")
        record = self.vault / "wiki" / "observations" / "membership-2024.json"
        record.write_text('{"id":"one","id":"two"}', encoding="utf-8")
        errors = self.errors()
        self.assertIn("Duplicate YAML key", errors)
        self.assertIn("Duplicate JSON key", errors)

    def test_arbitrary_yaml_tags_are_not_executed(self):
        path = self.vault / "wiki" / "concepts" / "routine-continuity.md"
        path.write_text("---\ntype: !!python/object/apply:builtins.str [unsafe]\n---\n",
                        encoding="utf-8")
        self.assertIn("constructor", self.errors())

    def test_local_reference_cannot_escape_the_vault(self):
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: page.metadata["sources"][0].update(
                           resource="../../../../README.md"))
        self.assertIn("escapes the vault", self.errors())

    def test_undefined_citation_and_unknown_capture_are_reported(self):
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: setattr(page, "body", page.body + "\nUnsupported.[^missing]\n"))
        self.edit_page("sources/fictional-report.md",
                       lambda page: page.metadata.update(capture_id="not-a-capture"))
        errors = self.errors()
        self.assertIn("Unresolved source footnote", errors)
        self.assertIn("Unknown capture_id", errors)

    def test_review_is_invalidated_when_body_changes(self):
        def reviewed(page):
            page.metadata.update(
                verified={"by": "human:example", "at": "2026-10-12T00:00:00Z"},
                review_basis=wiki.review_digest(page))
        self.edit_page("concepts/routine-continuity.md", reviewed)
        self.assertNotIn("Review does not", self.errors())
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: setattr(page, "body", page.body + "\nA new substantive claim.\n"))
        self.assertIn("Review does not cover", self.errors())

    def test_numeric_ranges_reject_invalid_bounds(self):
        self.edit_record("membership-2024.json", low=1300, high=1200)
        self.assertIn("ordered low and high", self.errors())
        self.edit_record("membership-2024.json", low=1000, high=1200, value=float("nan"))
        self.assertIn("finite number", self.errors())

    def test_review_is_invalidated_when_provenance_changes(self):
        def reviewed(page):
            page.metadata.update(
                verified={"by": "human:example", "at": "2026-10-12T00:00:00Z"},
                review_basis=wiki.review_digest(page))
        self.edit_page("concepts/routine-continuity.md", reviewed)
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: page.metadata["sources"][0].update(locator="Different section"))
        self.assertIn("Review does not cover", self.errors())

    def test_capture_cannot_be_misattributed_to_another_resource(self):
        self.edit_page("sources/fictional-report.md",
                       lambda page: page.metadata.update(resource="urn:example:another-work"))
        self.assertIn("differs from its captured version", self.errors())

    def test_unknown_type_and_extension_metadata_are_preserved(self):
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: page.metadata.update(
                           type="Domain-specific explanation", custom_context={"test": "preserve"}))
        report = wiki.inspect_vault(self.vault)
        self.assertFalse(report.errors)
        page = next(page for page in report.pages if page.path.name == "routine-continuity.md")
        self.assertEqual(page.metadata["custom_context"], {"test": "preserve"})

    def test_stale_indexes_are_detected_and_rebuilt(self):
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: page.metadata.update(description="Changed discovery summary."))
        self.assertTrue(any("index is stale" in message.lower()
                            for _, message in wiki.inspect_vault(self.vault).issues))
        self.assertGreater(wiki.build_indexes(self.vault), 0)
        self.assertEqual(wiki.inspect_vault(self.vault).issues, [])
        self.assertEqual(wiki.build_indexes(self.vault), 0)

    def test_malformed_field_types_are_errors_not_crashes(self):
        self.edit_page("concepts/routine-continuity.md",
                       lambda page: page.metadata.update(
                           status=["stable"], ownership={}, claim_kind=["hypothesis"]))
        self.assertIn("Invalid status", self.errors())

    def test_cli_records_reports_complete_count(self):
        result = subprocess.run(
            [sys.executable, str(wiki.ROOT / "scripts" / "wiki.py"), "--vault",
             str(self.vault), "records", "--metric", "membership", "--period", "2025"],
            capture_output=True, text=True, encoding="utf-8", check=True)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["count"], 2)
        self.assertEqual(len(payload["records"]), 2)


if __name__ == "__main__":
    unittest.main()

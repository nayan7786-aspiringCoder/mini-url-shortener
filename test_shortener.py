"""
Automated unit tests for Mini URL Shortener.
Uses Python's standard library `unittest`.
"""

import os
import tempfile
import unittest
from storage import Storage
from shortener import URLShortenerService, validate_and_normalize_url, validate_alias


class TestURLShortener(unittest.TestCase):
    def setUp(self):
        # Create a temporary database file for test isolation
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.storage = Storage(db_path=self.temp_db.name)
        self.service = URLShortenerService(self.storage)

    def tearDown(self):
        # Clean up temporary database file
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_url_validation_valid(self):
        valid_urls = [
            "https://www.google.com",
            "http://github.com/torvalds",
            "https://sub.domain.example.co.uk/path?q=123#frag",
            "google.com",  # auto-prepends https://
            "http://127.0.0.1:8080/test",
            "http://localhost:3000"
        ]
        for url in valid_urls:
            is_valid, norm, err = validate_and_normalize_url(url)
            self.assertTrue(is_valid, f"Expected '{url}' to be valid. Error: {err}")
            self.assertTrue(norm.startswith("http://") or norm.startswith("https://"))

    def test_url_validation_invalid(self):
        invalid_urls = [
            "",
            "ftp://files.example.com",
            "justwords",
            "http://",
            "https://.com",
            "not a url at all"
        ]
        for url in invalid_urls:
            is_valid, _, _ = validate_and_normalize_url(url)
            self.assertFalse(is_valid, f"Expected '{url}' to be invalid.")

    def test_alias_validation(self):
        self.assertTrue(validate_alias("my-link")[0])
        self.assertTrue(validate_alias("custom_123")[0])
        self.assertFalse(validate_alias("a")[0])  # too short
        self.assertFalse(validate_alias("a" * 31)[0])  # too long
        self.assertFalse(validate_alias("invalid space")[0])
        self.assertFalse(validate_alias("shorten")[0])  # reserved

    def test_shorten_and_resolve(self):
        target_url = "https://www.python.org"
        success, code, msg = self.service.shorten(target_url)
        self.assertTrue(success)
        self.assertIsNotNone(code)
        self.assertEqual(len(code), 6)

        # Resolve
        res_success, resolved_url, _ = self.service.resolve(code)
        self.assertTrue(res_success)
        self.assertEqual(resolved_url, target_url)

    def test_custom_alias(self):
        target_url = "https://news.ycombinator.com"
        alias = "hackernews"
        success, code, _ = self.service.shorten(target_url, custom_alias=alias)
        self.assertTrue(success)
        self.assertEqual(code, alias)

        # Resolve via alias
        res_success, resolved_url, _ = self.service.resolve(alias)
        self.assertTrue(res_success)
        self.assertEqual(resolved_url, target_url)

    def test_duplicate_alias_rejected(self):
        self.service.shorten("https://site1.com", custom_alias="myalias")
        # Attempt duplicate alias
        success, code, err = self.service.shorten("https://site2.com", custom_alias="myalias")
        self.assertFalse(success)
        self.assertIn("already in use", err)

    def test_clicks_tracking(self):
        _, code, _ = self.service.shorten("https://example.org", custom_alias="clicks-test")
        stats_initial = self.storage.get_stats(code)
        self.assertEqual(stats_initial["clicks"], 0)
        self.assertIsNone(stats_initial["last_accessed"])

        # Resolve twice
        self.service.resolve(code)
        self.service.resolve(code)

        stats_after = self.storage.get_stats(code)
        self.assertEqual(stats_after["clicks"], 2)
        self.assertIsNotNone(stats_after["last_accessed"])

    def test_list_urls(self):
        self.service.shorten("https://alpha.com", custom_alias="alpha")
        self.service.shorten("https://beta.com", custom_alias="beta")
        urls = self.service.list_urls()
        self.assertEqual(len(urls), 2)
        codes = [u["code"] for u in urls]
        self.assertIn("alpha", codes)
        self.assertIn("beta", codes)

    def test_delete_url(self):
        self.service.shorten("https://todelete.com", custom_alias="delme")
        self.assertTrue(self.storage.code_exists("delme"))

        del_success, _ = self.service.delete("delme")
        self.assertTrue(del_success)
        self.assertFalse(self.storage.code_exists("delme"))

        # Deleting non-existent code
        del_fail, _ = self.service.delete("nonexistent")
        self.assertFalse(del_fail)

    def test_persistence_across_connections(self):
        """Verify that data persists across separate database connections/runs."""
        db_path = self.temp_db.name
        storage1 = Storage(db_path=db_path)
        service1 = URLShortenerService(storage1)
        service1.shorten("https://persistent.com", custom_alias="persist")

        # Create entirely new connection to same db file
        storage2 = Storage(db_path=db_path)
        service2 = URLShortenerService(storage2)
        success, resolved_url, _ = service2.resolve("persist")
        self.assertTrue(success)
        self.assertEqual(resolved_url, "https://persistent.com")


if __name__ == "__main__":
    unittest.main()

"""
Unit tests for the Flask Web Application.
"""

import os
import tempfile
import unittest
from storage import Storage
from shortener import URLShortenerService
import app as flask_app_module


class TestFlaskWebApp(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()

        # Wire temporary DB into app
        self.storage = Storage(db_path=self.temp_db.name)
        self.service = URLShortenerService(self.storage)
        flask_app_module.storage = self.storage
        flask_app_module.service = self.service

        flask_app_module.app.config["TESTING"] = True
        self.client = flask_app_module.app.test_client()

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_index_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mini URL Shortener", response.data)

    def test_web_shorten_and_redirect(self):
        # Shorten via form POST
        post_res = self.client.post("/shorten", data={"url": "https://www.python.org", "alias": "pyorg"})
        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b"pyorg", post_res.data)

        # Access redirect
        redir_res = self.client.get("/pyorg")
        self.assertEqual(redir_res.status_code, 302)
        self.assertEqual(redir_res.headers["Location"], "https://www.python.org")

        # Check clicks
        stats = self.storage.get_stats("pyorg")
        self.assertEqual(stats["clicks"], 1)

    def test_api_shorten(self):
        res = self.client.post("/api/shorten", json={"url": "https://github.com", "alias": "ghub"})
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["code"], "ghub")


if __name__ == "__main__":
    unittest.main()

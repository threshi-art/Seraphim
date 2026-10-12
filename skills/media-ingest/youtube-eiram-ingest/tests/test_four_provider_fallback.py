"""Offline contract tests for optional four-provider transcript adapter."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "four_provider_fallback.py"
spec = importlib.util.spec_from_file_location("four_provider_fallback", MODULE)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

class VideoFallbackTests(unittest.TestCase):
    def test_urls(self):
        for candidate in ("OENarJm8qco", "https://youtu.be/OENarJm8qco?t=1",
                          "https://www.youtube.com/watch?v=OENarJm8qco&feature=share",
                          "https://youtube.com/shorts/OENarJm8qco"):
            self.assertEqual(adapter.video_id(candidate), "OENarJm8qco")

    def test_invalid_ids(self):
        for candidate in ("", "bad", "https://example.com/OENarJm8qco"):
            with self.assertRaises(ValueError):
                adapter.video_id(candidate)

    def test_cache(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "cache.sqlite3"
            self.assertIsNone(adapter.cache_get(p, "vid:all", 3600))
            value = {"transcript": "hello"}
            adapter.cache_put(p, "vid:all", value)
            self.assertEqual(adapter.cache_get(p, "vid:all", 3600), value)

    def test_failover(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(adapter, "cache_path", return_value=Path(folder) / "cache.sqlite3"):
                with patch.object(adapter, "fetch_provider", side_effect=[RuntimeError("offline"), "a" * 80]) as mocked:
                    result = adapter.retrieve("OENarJm8qco")
                self.assertEqual(result["provider"], "coyasong")
                self.assertEqual(result["integrity"], "unverified")
                self.assertEqual(mocked.call_count, 2)
                self.assertTrue(adapter.retrieve("OENarJm8qco")["cached"])

    def test_unavailable(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(adapter, "cache_path", return_value=Path(folder) / "cache.sqlite3"):
                with patch.object(adapter, "fetch_provider", side_effect=RuntimeError("offline")):
                    result = adapter.retrieve("OENarJm8qco")
        self.assertIsNone(result["transcript"])
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(len(result["failures"]), 4)

if __name__ == "__main__":
    unittest.main()

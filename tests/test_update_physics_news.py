import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_physics_news import build_document, parse_feed


class PhysicsNewsTests(unittest.TestCase):
    def test_parse_feed_extracts_safe_story_fields(self):
        feed = b"""<?xml version='1.0'?>
        <rss version='2.0'><channel><item>
        <title>Quantum &amp; cosmic discovery</title>
        <link>https://www.sciencedaily.com/releases/story.htm</link>
        <description>&lt;p&gt;A new result &lt;b&gt;changes physics&lt;/b&gt;.&lt;/p&gt;</description>
        <pubDate>Tue, 13 Oct 2026 07:27:24 EDT</pubDate>
        </item></channel></rss>"""

        stories = parse_feed(feed, "Physics")

        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["title"], "Quantum & cosmic discovery")
        self.assertEqual(stories[0]["summary"], "A new result changes physics.")
        self.assertEqual(stories[0]["published_at"], "2026-10-13")

    def test_build_document_uses_latest_story_and_current_month(self):
        stories = [
            {"title": "Earlier", "published_at": "2026-10-10"},
            {"title": "Latest", "published_at": "2026-10-13"},
        ]

        document = build_document(stories, datetime(2026, 10, 14, tzinfo=timezone.utc))

        self.assertEqual(document["month"], "October 2026")
        self.assertEqual(document["story"]["title"], "Latest")

    def test_build_document_rejects_empty_feed_results(self):
        with self.assertRaises(ValueError):
            build_document([])


if __name__ == "__main__":
    unittest.main()
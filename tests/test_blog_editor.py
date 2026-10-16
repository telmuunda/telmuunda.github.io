import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import blog_editor


class BlogEditorTests(unittest.TestCase):
    def test_sanitizer_keeps_formatting_and_removes_unsafe_markup(self):
        source = '<p onclick="run()">Safe <strong>formatting</strong><script>alert(1)</script></p><a href="javascript:alert(1)">link</a>'

        clean = blog_editor.ContentSanitizer().finish(source)

        self.assertNotIn("onclick", clean)
        self.assertNotIn("<script", clean)
        self.assertNotIn("javascript:", clean)
        self.assertIn("<strong>formatting</strong>", clean)

    def test_publish_creates_post_and_updates_public_index(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = root / "assets" / "data" / "blog-posts.json"
            index.parent.mkdir(parents=True)
            index.write_text("[]\n", encoding="utf-8")
            with patch.multiple(blog_editor, ROOT=root, POSTS_DIR=root / "posts", POST_INDEX=index):
                result = blog_editor.publish_post({
                    "title": "A Physics Story",
                    "date": "2026-10-14",
                    "summary": "A short introduction.",
                    "body": "<p>Thoughts on <em>physics</em>.</p>",
                })

            page = root / "posts" / "a-physics-story.html"
            posts = json.loads(index.read_text(encoding="utf-8"))
            self.assertTrue(page.exists())
            self.assertIn("Thoughts on <em>physics</em>.", page.read_text(encoding="utf-8"))
            self.assertEqual(result["url"], "posts/a-physics-story.html")
            self.assertEqual(posts[0]["title"], "A Physics Story")
            self.assertEqual(posts[0]["sort_date"], date(2026, 10, 14).isoformat())

    def test_publish_refuses_to_overwrite_an_existing_post(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            posts_dir = root / "posts"
            posts_dir.mkdir()
            (posts_dir / "same-title.html").write_text("existing", encoding="utf-8")
            index = root / "assets" / "data" / "blog-posts.json"
            with patch.multiple(blog_editor, ROOT=root, POSTS_DIR=posts_dir, POST_INDEX=index):
                with self.assertRaises(FileExistsError):
                    blog_editor.publish_post({
                        "title": "Same Title",
                        "date": "2026-10-14",
                        "summary": "Summary",
                        "body": "<p>Content</p>",
                    })


if __name__ == "__main__":
    unittest.main()
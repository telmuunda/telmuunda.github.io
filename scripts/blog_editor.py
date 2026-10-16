#!/usr/bin/env python3
"""Serve a loopback-only editor that publishes static blog posts into this repo."""

from datetime import date, datetime
from html import escape
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import json
import re
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
EDITOR = ROOT / "blog-editor.html"
POSTS_DIR = ROOT / "posts"
POST_INDEX = ROOT / "assets" / "data" / "blog-posts.json"
PORT = 8765
ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "em", "figcaption", "figure", "h2", "h3",
    "hr", "img", "li", "ol", "p", "pre", "s", "strong", "sub", "sup", "ul",
}
VOID_TAGS = {"br", "hr", "img"}


def safe_url(value, image=False):
    value = value.strip()
    parsed = urlsplit(value)
    if parsed.scheme in ("https", "http") and parsed.netloc:
        return value
    if not parsed.scheme and not parsed.netloc and not value.startswith("//"):
        if value.startswith(("#", "../files/", "../assets/", "files/", "assets/")):
            return value
        if not image and value and not value.startswith(("/", "\\")):
            return value
    return ""


class ContentSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        if tag not in ALLOWED_TAGS:
            return
        attributes = dict(attrs)
        clean_attributes = []
        if tag == "a":
            href = safe_url(attributes.get("href", ""))
            if href:
                clean_attributes.append(f'href="{escape(href, quote=True)}"')
                if urlsplit(href).scheme in ("http", "https"):
                    clean_attributes.append('target="_blank"')
                    clean_attributes.append('rel="noopener noreferrer"')
        elif tag == "img":
            src = safe_url(attributes.get("src", ""), image=True)
            if not src:
                return
            clean_attributes.extend((f'src="{escape(src, quote=True)}"',
                                     f'alt="{escape(attributes.get("alt", ""), quote=True)}"',
                                     'loading="lazy"'))
        elif tag == "figure" and attributes.get("class") == "image":
            clean_attributes.append('class="image"')
        self.output.append("<" + tag + (" " + " ".join(clean_attributes) if clean_attributes else "") + ">")
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_endtag(self, tag):
        if tag not in self.open_tags:
            return
        while self.open_tags:
            open_tag = self.open_tags.pop()
            self.output.append(f"</{open_tag}>")
            if open_tag == tag:
                break

    def handle_data(self, data):
        self.output.append(escape(data))

    def finish(self, source):
        self.feed(source)
        self.close()
        while self.open_tags:
            self.output.append(f"</{self.open_tags.pop()}>")
        return "".join(self.output).strip()


def slugify(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:70].rstrip("-")


def make_post_page(title, published, body):
    title_html = escape(title)
    date_label = published.strftime("%B %d, %Y")
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
\t<meta charset="utf-8" />
\t<meta name="viewport" content="width=device-width, initial-scale=1" />
\t<title>{title_html} | Telmuun Davaadalai</title>
\t<link rel="preconnect" href="https://fonts.googleapis.com" />
\t<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
\t<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
\t<link rel="stylesheet" href="../assets/css/fontawesome-all.min.css" />
\t<link rel="stylesheet" href="../assets/css/portfolio.css" />
</head>
<body>
\t<header class="site-header">
\t\t<div class="site-header-inner">
\t\t\t<a class="brand" href="../index.html#projects">TELMUUN DAVAADALAI</a>
\t\t\t<nav class="top-nav" aria-label="Section Menu">
\t\t\t\t<a class="nav-link" href="../index.html#about">About</a>
\t\t\t\t<a class="nav-link" href="../index.html#work">Work</a>
\t\t\t\t<a class="nav-link" href="../index.html#notes">Notes</a>
\t\t\t\t<a class="nav-link active" href="../blog.html">Blog</a>
\t\t\t\t<a class="nav-link" href="../index.html#contact">Contact</a>
\t\t\t</nav>
\t\t\t<button class="theme-toggle" id="themeToggle" type="button" aria-label="Toggle light and dark mode">🌙</button>
\t\t</div>
\t</header>
\t<main class="content-shell blog-shell">
\t\t<article class="blog-post">
\t\t\t<span class="blog-meta">{date_label}</span>
\t\t\t<h1>{title_html}</h1>
\t\t\t{body}
\t\t\t<p><a class="inline-link" href="../blog.html">Back to blog</a></p>
\t\t</article>
\t</main>
\t<script>
\t\tconst themeToggle = document.getElementById('themeToggle');
\t\tconst prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
\t\tdocument.body.classList.toggle('light-mode', !prefersDark);
\t\tdocument.body.classList.toggle('dark-mode', prefersDark);
\t\tthemeToggle.textContent = prefersDark ? '☀️' : '🌙';
\t\tthemeToggle.addEventListener('click', () => {{
\t\t\tconst isLight = document.body.classList.toggle('light-mode');
\t\t\tdocument.body.classList.toggle('dark-mode', !isLight);
\t\t\tthemeToggle.textContent = isLight ? '🌙' : '☀️';
\t\t}});
\t</script>
</body>
</html>
'''


def publish_post(payload):
    title = str(payload.get("title", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    body_source = str(payload.get("body", ""))
    if not title or len(title) > 120:
        raise ValueError("Enter a title between 1 and 120 characters.")
    if not summary or len(summary) > 260:
        raise ValueError("Enter a summary between 1 and 260 characters.")
    if len(body_source) > 1_000_000:
        raise ValueError("The post content is too large.")
    published = date.fromisoformat(str(payload.get("date", "")))
    clean_body = ContentSanitizer().finish(body_source)
    if not clean_body:
        raise ValueError("Write some post content before publishing.")

    slug = slugify(title)
    if not slug:
        raise ValueError("The title needs at least one letter or number.")
    post_path = POSTS_DIR / f"{slug}.html"
    if post_path.exists():
        raise FileExistsError("A post with this title already exists. Change the title to publish a distinct post.")

    try:
        posts = json.loads(POST_INDEX.read_text(encoding="utf-8"))
        if not isinstance(posts, list):
            raise ValueError("The blog post index must be a JSON list.")
    except FileNotFoundError:
        posts = []
    entry = {
        "title": title,
        "date": published.strftime("%B %d, %Y"),
        "summary": summary,
        "url": f"posts/{post_path.name}",
        "sort_date": published.isoformat(),
    }
    posts.append(entry)
    posts.sort(key=lambda post: post.get("sort_date", ""), reverse=True)

    POSTS_DIR.mkdir(parents=True, exist_ok=True)
    post_path.write_text(make_post_page(title, published, clean_body), encoding="utf-8")
    POST_INDEX.parent.mkdir(parents=True, exist_ok=True)
    temporary_index = POST_INDEX.with_suffix(".json.tmp")
    temporary_index.write_text(json.dumps(posts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary_index.replace(POST_INDEX)
    return {"path": str(post_path.relative_to(ROOT)), "url": entry["url"]}


class EditorHandler(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if self.path not in ("/", "/blog-editor.html"):
            self.send_error(404)
            return
        content = EDITOR.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != "/publish":
            self.send_error(404)
            return
        if self.headers.get("Host") not in (f"127.0.0.1:{PORT}", f"localhost:{PORT}"):
            self.send_error(403)
            return
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            self.send_error(403)
            return
        if self.headers.get_content_type() != "application/json":
            self.send_json(415, {"error": "Expected a JSON publishing request."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_100_000:
                raise ValueError("The publishing request is empty or too large.")
            payload = json.loads(self.rfile.read(length))
            result = publish_post(payload)
        except FileExistsError as error:
            self.send_json(409, {"error": str(error)})
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(400, {"error": str(error) or "Check the post details and try again."})
        except OSError as error:
            self.send_json(500, {"error": f"Could not write the post: {error}"})
        else:
            self.send_json(201, result)

    def log_message(self, format_string, *args):
        print(f"[{self.log_date_time_string()}] {format_string % args}")


def main():
    print(f"Blog editor: http://127.0.0.1:{PORT}/")
    print("Only this computer can connect. Press Ctrl+C to stop the editor.")
    HTTPServer(("127.0.0.1", PORT), EditorHandler).serve_forever()


if __name__ == "__main__":
    main()
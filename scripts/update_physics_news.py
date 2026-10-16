#!/usr/bin/env python3
"""Refresh the static monthly physics and astronomy feature from ScienceDaily RSS."""

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
import html
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "data" / "physics-news.json"
FEEDS = (
    ("Astronomy", "https://www.sciencedaily.com/rss/space_time/astronomy.xml"),
    ("Physics", "https://www.sciencedaily.com/rss/matter_energy/physics.xml"),
)


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value):
    extractor = TextExtractor()
    extractor.feed(html.unescape(value))
    text = " ".join(" ".join(extractor.parts).split())
    return re.sub(r"\s+([.,!?;:])", r"\1", text)


def parse_feed(xml_content, category):
    root = ET.fromstring(xml_content)
    stories = []
    for item in root.findall(".//item"):
        title = plain_text(item.findtext("title", ""))
        url = item.findtext("link", "").strip()
        summary = plain_text(item.findtext("description", ""))
        date_text = item.findtext("pubDate", "")
        try:
            published = parsedate_to_datetime(date_text)
        except (TypeError, ValueError, OverflowError):
            continue
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        if not title or not summary or not url.startswith("https://www.sciencedaily.com/"):
            continue
        stories.append({
            "title": title,
            "summary": summary[:360].rsplit(" ", 1)[0] + "..." if len(summary) > 360 else summary,
            "url": url,
            "published_at": published.astimezone(timezone.utc).date().isoformat(),
            "category": category,
        })
    return stories


def build_document(stories, now=None):
    if not stories:
        raise ValueError("No valid stories were found in the configured RSS feeds.")
    now = now or datetime.now(timezone.utc)
    latest = max(stories, key=lambda story: story["published_at"])
    return {
        "month": now.strftime("%B %Y"),
        "updated_at": now.date().isoformat(),
        "story": latest,
    }


def fetch_feed(category, url):
    request = urllib.request.Request(url, headers={"User-Agent": "TelmuunPortfolioNews/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_feed(response.read(), category)


def main():
    stories = []
    errors = []
    for category, url in FEEDS:
        try:
            stories.extend(fetch_feed(category, url))
        except (urllib.error.URLError, ET.ParseError, TimeoutError, OSError) as error:
            errors.append(f"{category}: {error}")
    if not stories:
        raise RuntimeError("Could not load a valid story from either RSS feed. " + "; ".join(errors))

    document = build_document(stories)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {OUTPUT.relative_to(ROOT)}: {document['story']['title']}")
    if errors:
        print("One feed was unavailable: " + "; ".join(errors))


if __name__ == "__main__":
    main()
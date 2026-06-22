"""Keyless RSS collector parsing, classification, and failure isolation."""
import json

import pytest

from backend.agents import collector_agent

RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Test World</title>
  <item>
    <title>Militant attack reported near Gaza border</title>
    <link>https://example.org/story-one</link>
    <description><![CDATA[Officials report a bombing and ongoing security response.]]></description>
    <pubDate>Sun, 22 Jun 2026 12:00:00 GMT</pubDate>
  </item>
</channel></rss>
"""

ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Cyber vulnerability affects regional systems</title>
    <link href="https://example.org/story-two" rel="alternate" />
    <summary>Security teams issued a mitigation.</summary>
    <updated>2026-06-22T12:00:00Z</updated>
  </entry>
</feed>
"""


def _source(**overrides):
    source = {
        "id": "test",
        "name": "Test Source",
        "feed_url": "https://example.org/feed.xml",
        "enabled": True,
        "perspective_bucket": "center",
        "source_type": "major_media",
        "country_of_origin": "Multinational",
        "independence_group": "test-source",
        "default_category": "geopolitics",
        "reliability_score": 78,
    }
    source.update(overrides)
    return source


def test_rss_article_maps_to_terrorism_and_middle_east():
    article = collector_agent.parse_feed(RSS)[0]
    event = collector_agent.article_to_event(article, _source())
    assert event["category"] == "terrorism"
    assert event["region"] == "Middle East"
    assert event["sources"][0]["political_lean"] == "center"
    assert event["id"].startswith("rss-")


def test_atom_feed_is_supported():
    article = collector_agent.parse_feed(ATOM)[0]
    assert article["url"] == "https://example.org/story-two"
    assert "Cyber vulnerability" in article["title"]


def test_collect_live_skips_failed_feed(tmp_path):
    registry = {
        "default_per_source_limit": 2,
        "sources": [
            _source(id="failed", feed_url="https://example.org/failed.xml"),
            _source(id="working", feed_url="https://example.org/working.xml"),
        ],
    }
    (tmp_path / "live_sources.json").write_text(json.dumps(registry), encoding="utf-8")

    def fetch(url):
        if "failed" in url:
            raise OSError("offline")
        return RSS

    events = collector_agent.collect_live(config_dir=tmp_path, fetcher=fetch)
    assert len(events) == 1
    assert events[0]["sources"][0]["name"] == "Test Source"


def test_collect_live_fails_when_every_feed_fails(tmp_path):
    registry = {"sources": [_source()]}
    (tmp_path / "live_sources.json").write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(RuntimeError, match="no events"):
        collector_agent.collect_live(config_dir=tmp_path, fetcher=lambda _url: b"not xml")

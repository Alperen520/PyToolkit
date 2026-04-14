"""Tests for tools.web_scraper. Network calls are monkeypatched out."""

import json

import pytest

from tools import web_scraper


SAMPLE_HTML = """
<html>
  <body>
    <h2 class="title">First post</h2>
    <h2 class="title">Second post</h2>
    <a href="https://example.com/a">A</a>
    <a href="https://example.com/b">B</a>
  </body>
</html>
"""


class FakeResponse:
    def __init__(self, text: str, status: int = 200):
        self.text = text
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.exceptions.HTTPError(f"{self.status_code}")


@pytest.fixture
def patched_requests(monkeypatch):
    """Replace requests.get with a stub that returns SAMPLE_HTML."""
    def fake_get(url, headers=None, timeout=None):
        return FakeResponse(SAMPLE_HTML)
    monkeypatch.setattr("tools.web_scraper.requests.get", fake_get)


def test_extract_text(patched_requests, tmp_path):
    output = tmp_path / "out.json"
    web_scraper.main([
        "--url", "https://example.com",
        "--selector", "h2.title",
        "--output", str(output),
        "--format", "json",
    ])
    data = json.loads(output.read_text())
    values = [row["value"] for row in data]
    assert values == ["First post", "Second post"]


def test_extract_attribute(patched_requests, tmp_path):
    output = tmp_path / "links.json"
    web_scraper.main([
        "--url", "https://example.com",
        "--selector", "a",
        "--attr", "href",
        "--output", str(output),
        "--format", "json",
    ])
    data = json.loads(output.read_text())
    assert [row["value"] for row in data] == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_limit(patched_requests, tmp_path):
    output = tmp_path / "out.json"
    web_scraper.main([
        "--url", "https://example.com",
        "--selector", "a",
        "--limit", "1",
        "--output", str(output),
        "--format", "json",
    ])
    data = json.loads(output.read_text())
    assert len(data) == 1


def test_csv_output(patched_requests, tmp_path):
    output = tmp_path / "out.csv"
    web_scraper.main([
        "--url", "https://example.com",
        "--selector", "h2.title",
        "--output", str(output),
        "--format", "csv",
    ])
    text = output.read_text()
    assert "index,tag,value" in text
    assert "First post" in text


def test_http_error_returns_nonzero(monkeypatch):
    import requests

    def boom(url, headers=None, timeout=None):
        raise requests.exceptions.ConnectionError("no network")

    monkeypatch.setattr("tools.web_scraper.requests.get", boom)
    result = web_scraper.main([
        "--url", "https://example.com",
        "--selector", "h2",
    ])
    assert result == 1

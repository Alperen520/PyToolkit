"""Tests for tools.api_tester. Network calls are monkeypatched out."""

import json

import pytest

from tools import api_tester


class FakeResponse:
    def __init__(self, status=200, body=b'{"ok": true}', headers=None, reason="OK"):
        self.status_code = status
        self.content = body
        self.text = body.decode("utf-8", errors="replace")
        self.headers = headers or {"Content-Type": "application/json"}
        self.reason = reason
        self.ok = 200 <= status < 300

    def json(self):
        return json.loads(self.text)


def test_parse_headers_valid():
    headers = api_tester.parse_headers([
        "Authorization: Bearer abc",
        "X-Custom: value",
    ])
    assert headers == {"Authorization": "Bearer abc", "X-Custom": "value"}


def test_parse_headers_invalid():
    with pytest.raises(ValueError):
        api_tester.parse_headers(["no-colon"])


def test_parse_queries_valid():
    assert api_tester.parse_queries(["a=1", "b=two"]) == {"a": "1", "b": "two"}


def test_parse_queries_invalid():
    with pytest.raises(ValueError):
        api_tester.parse_queries(["invalid"])


def test_get_request_success(monkeypatch, capsys):
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("tools.api_tester.requests.request", fake_request)
    result = api_tester.main(["--url", "https://example.com/api"])
    assert result == 0
    assert captured["method"] == "GET"
    assert captured["url"] == "https://example.com/api"

    out = capsys.readouterr().out
    assert "Status:" in out
    assert "200" in out


def test_post_json_body(monkeypatch):
    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return FakeResponse(status=201)

    monkeypatch.setattr("tools.api_tester.requests.request", fake_request)
    api_tester.main([
        "--url", "https://example.com/api",
        "--method", "POST",
        "--json", '{"name": "Alperen"}',
        "--header", "X-Key: secret",
    ])
    assert captured["method"] == "POST"
    assert captured["json"] == {"name": "Alperen"}
    assert captured["headers"] == {"X-Key": "secret"}


def test_non_2xx_returns_1(monkeypatch):
    monkeypatch.setattr(
        "tools.api_tester.requests.request",
        lambda **kwargs: FakeResponse(status=500, reason="Server Error"),
    )
    assert api_tester.main(["--url", "https://example.com"]) == 1


def test_save_response(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "tools.api_tester.requests.request",
        lambda **kwargs: FakeResponse(body=b'{"hello":"world"}'),
    )
    target = tmp_path / "response.json"
    api_tester.main([
        "--url", "https://example.com",
        "--save", str(target),
    ])
    assert json.loads(target.read_text()) == {"hello": "world"}


def test_invalid_json_body_returns_error():
    assert api_tester.main([
        "--url", "https://example.com",
        "--json", "{not valid",
    ]) == 2


def test_data_file_body(monkeypatch, tmp_path):
    payload = tmp_path / "body.json"
    payload.write_text('{"x": 1}')

    captured = {}

    def fake_request(**kwargs):
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("tools.api_tester.requests.request", fake_request)
    api_tester.main([
        "--url", "https://example.com",
        "--method", "PUT",
        "--data-file", str(payload),
    ])
    assert captured["json"] == {"x": 1}

"""Tests for tools.json_csv_converter."""

import csv
import json

from tools import json_csv_converter


def test_json_to_csv_roundtrip(tmp_path):
    data = [
        {"name": "Ada", "age": 30},
        {"name": "Linus", "age": 54},
    ]
    json_path = tmp_path / "in.json"
    csv_path = tmp_path / "out.csv"
    json_path.write_text(json.dumps(data), encoding="utf-8")

    exit_code = json_csv_converter.main([
        "--input", str(json_path),
        "--output", str(csv_path),
    ])
    assert exit_code == 0

    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"name": "Ada", "age": "30"}, {"name": "Linus", "age": "54"}]


def test_csv_to_json(tmp_path):
    csv_path = tmp_path / "in.csv"
    json_path = tmp_path / "out.json"
    csv_path.write_text("name,age\nAda,30\nLinus,54\n", encoding="utf-8")

    json_csv_converter.main([
        "--input", str(csv_path),
        "--output", str(json_path),
        "--pretty",
    ])
    data = json.loads(json_path.read_text())
    assert data == [
        {"name": "Ada", "age": "30"},
        {"name": "Linus", "age": "54"},
    ]


def test_flatten_nested_json(tmp_path):
    data = [{"id": 1, "user": {"name": "Ada", "city": "London"}}]
    json_path = tmp_path / "nested.json"
    csv_path = tmp_path / "flat.csv"
    json_path.write_text(json.dumps(data))

    json_csv_converter.main([
        "--input", str(json_path),
        "--output", str(csv_path),
        "--flatten",
    ])
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"id": "1", "user.name": "Ada", "user.city": "London"}]


def test_custom_delimiter(tmp_path):
    data = [{"a": 1, "b": 2}]
    json_path = tmp_path / "d.json"
    csv_path = tmp_path / "d.csv"
    json_path.write_text(json.dumps(data))

    json_csv_converter.main([
        "--input", str(json_path),
        "--output", str(csv_path),
        "--delimiter", ";",
    ])
    content = csv_path.read_text()
    assert "a;b" in content
    assert "1;2" in content


def test_missing_input_returns_error(tmp_path):
    result = json_csv_converter.main([
        "--input", str(tmp_path / "missing.json"),
        "--output", str(tmp_path / "out.csv"),
    ])
    assert result == 2


def test_ambiguous_extensions_require_direction(tmp_path):
    input_path = tmp_path / "data.txt"
    output_path = tmp_path / "out.txt"
    input_path.write_text("[]")
    result = json_csv_converter.main([
        "--input", str(input_path),
        "--output", str(output_path),
    ])
    assert result == 2


def test_union_of_keys_across_rows(tmp_path):
    data = [{"a": 1}, {"a": 2, "b": 3}]
    json_path = tmp_path / "u.json"
    csv_path = tmp_path / "u.csv"
    json_path.write_text(json.dumps(data))

    json_csv_converter.main([
        "--input", str(json_path),
        "--output", str(csv_path),
    ])
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    assert rows == [{"a": "1", "b": ""}, {"a": "2", "b": "3"}]

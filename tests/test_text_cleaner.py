"""Tests for tools.text_cleaner."""

from tools import text_cleaner


def run_clean(text, tmp_path, extra_args):
    inp = tmp_path / "in.txt"
    out = tmp_path / "out.txt"
    inp.write_text(text, encoding="utf-8")
    text_cleaner.main(["--input", str(inp), "--output", str(out)] + extra_args)
    return out.read_text(encoding="utf-8")


def test_remove_emoji(tmp_path):
    result = run_clean("Hello 😀 World 🚀!", tmp_path, ["--remove-emoji"])
    assert "😀" not in result and "🚀" not in result
    assert "Hello" in result and "World" in result


def test_remove_urls(tmp_path):
    result = run_clean(
        "Visit https://example.com or www.example.org today",
        tmp_path, ["--remove-urls"],
    )
    assert "https://" not in result
    assert "www." not in result
    assert "Visit" in result and "today" in result


def test_strip_html(tmp_path):
    result = run_clean("<p>Hello <b>world</b></p>", tmp_path, ["--strip-html"])
    assert "<" not in result and ">" not in result
    assert "Hello" in result and "world" in result


def test_remove_punctuation(tmp_path):
    result = run_clean("Hello, world! It's fine.", tmp_path, ["--remove-punct"])
    assert "," not in result and "!" not in result and "." not in result


def test_remove_digits(tmp_path):
    result = run_clean("Room 101 has 42 chairs", tmp_path, ["--remove-digits"])
    assert "101" not in result and "42" not in result
    assert "Room" in result and "chairs" in result


def test_normalize_spaces(tmp_path):
    result = run_clean("too    many     spaces", tmp_path, ["--normalize-spaces"])
    assert result.strip() == "too many spaces"


def test_lowercase(tmp_path):
    result = run_clean("HELLO WORLD", tmp_path, ["--lowercase"])
    assert result.strip() == "hello world"


def test_uppercase(tmp_path):
    result = run_clean("hello", tmp_path, ["--uppercase"])
    assert result.strip() == "HELLO"


def test_combined_pipeline(tmp_path):
    text = "<p>Hello 😀   <b>WORLD</b>!!!</p> Visit https://example.com"
    result = run_clean(
        text, tmp_path,
        ["--strip-html", "--remove-emoji", "--remove-urls",
         "--remove-punct", "--normalize-spaces", "--lowercase"],
    )
    assert "hello" in result
    assert "world" in result
    assert "😀" not in result
    assert "https" not in result


def test_no_operation_returns_error(tmp_path):
    inp = tmp_path / "in.txt"
    inp.write_text("anything")
    assert text_cleaner.main(["--input", str(inp)]) == 2


def test_trim_per_line(tmp_path):
    result = run_clean("  hello  \n  world  ", tmp_path, ["--trim"])
    assert result == "hello\nworld"


def test_unicode_normalization(tmp_path):
    # Full-width digits + compatibility forms collapse to ASCII under NFKC.
    result = run_clean("ＡＢＣ", tmp_path, ["--normalize-unicode"])
    assert "ABC" in result

from backend.app.utils.text_utils import count_garble_chars, garble_ratio


def test_count_garble_chars_normal_text():
    assert count_garble_chars("Hello, world!") == 0


def test_count_garble_chars_with_replacement_char():
    text = "abc\ufffd\ufffdxyz"
    assert count_garble_chars(text) == 2


def test_count_garble_chars_with_control_chars():
    text = "hello\x00\x01world"
    assert count_garble_chars(text) == 2


def test_count_garble_chars_preserves_newlines():
    text = "line1\nline2\r\nline3\ttab"
    assert count_garble_chars(text) == 0


def test_count_garble_chars_empty():
    assert count_garble_chars("") == 0


def test_garble_ratio_pure_garble():
    text = "\ufffd\ufffd\ufffd\ufffd"
    assert garble_ratio(text) == 1.0


def test_garble_ratio_mixed():
    text = "ab\ufffd\ufffd"  # 2 garble out of 4
    assert abs(garble_ratio(text) - 0.5) < 1e-9


def test_garble_ratio_empty():
    assert garble_ratio("") == 0.0

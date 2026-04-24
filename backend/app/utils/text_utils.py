import unicodedata


def count_garble_chars(text: str) -> int:
    """统计文本中的乱码字符数量：Unicode 替换符和非打印控制字符（保留 \\n \\r \\t）。"""
    count = 0
    for ch in text:
        if ch == "\ufffd":
            count += 1
        elif unicodedata.category(ch) in ("Cc", "Cf", "Cs", "Co") and ch not in ("\n", "\r", "\t"):
            count += 1
    return count


def garble_ratio(text: str) -> float:
    """返回文本中乱码字符的比例。"""
    if not text:
        return 0.0
    return count_garble_chars(text) / len(text)

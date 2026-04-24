import hashlib
import json


def hash_issues(issues: list[dict]) -> int:
    """对问题列表计算哈希，用于审核断路器的重复检测。

    只取 type 和 severity 字段，忽略 description 等可变内容，
    这样同一类问题即使描述不同也会被识别为重复。
    """
    normalized = sorted(
        [{"type": i["type"], "severity": i["severity"]} for i in issues],
        key=lambda x: (x["type"], x["severity"]),
    )
    serialized = json.dumps(normalized, sort_keys=True)
    # 截断为 64 位，避免后续序列化到 JSON/SQLite 时溢出（SQLite INTEGER 为 64 位）
    return int(hashlib.md5(serialized.encode()).hexdigest(), 16) & 0xFFFFFFFFFFFFFFFF

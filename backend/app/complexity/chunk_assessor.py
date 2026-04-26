from dataclasses import dataclass
from typing import Literal

from backend.app.config import COMPLEXITY_THRESHOLD_MEDIUM, COMPLEXITY_THRESHOLD_COMPLEX


def detect_x_bimodal(x_centers: list[float], page_width: float) -> bool:
    """检测同一页上所有 block 的 X 中心坐标是否呈双峰/多峰分布。

    使用 gap 检测：排序后找相邻值间 gap > page_width * 0.15 的分界点。
    存在至少一个分界点 → 返回 True（多栏布局）。
    """
    if len(x_centers) < 4 or page_width <= 0:
        return False
    sorted_x = sorted(x_centers)
    gap_threshold = page_width * 0.15
    for i in range(1, len(sorted_x)):
        if sorted_x[i] - sorted_x[i - 1] > gap_threshold:
            return True
    return False


@dataclass
class ChunkSignals:
    """从 YOLO 检测 + PyMuPDF 分析中提取的信号，用于复杂度评分。

    所有字段均由 chunk_node 在创建分块时提供。
    """

    class_: str  # 显示类型：Title / Text / Table / Formula / Picture
    text: str  # bbox 区域内 PyMuPDF 提取的文本
    bbox_area: float  # 边界框面积（像素平方）
    font_count: int  # bbox 区域内唯一字体的数量
    rect_count_in_bbox: int  # 与 bbox 重叠的绘图矩形数量
    page_rotation: int  # 页面旋转角度 (0, 90, 180, 270)
    has_ocr_fonts: bool  # 检测到 OCR 字体痕迹 (CIDFont, GlyphLess, Unknown)
    extractable_chars_on_page: int  # 页面上的总可提取字符数
    bimodal_x: bool  # 该页 X 坐标分布是否呈双峰（多栏布局）


_MATH_CHARS = set("\u2211\u222b\u220f\u221a\u2202\u03b1\u03b2\u03b3\u03b4\u03b5\u03b6\u03b7\u03b8\u03bb\u03bc\u03c0\u03c1\u03c3\u03c6\u03c8\u03c9\u2264\u2265\u2260\u00b1\u221e")


def assess_complexity(signals: ChunkSignals) -> Literal["simple", "medium", "complex"]:
    """纯启发式复杂度评估。零 LLM 调用。每个分块耗时 < 1ms。

    评分规则：
      短路逻辑（跳过评分）：
        - extractable_chars_on_page < 20 且不是 Picture -> complex
        - class_ == Picture -> complex

      加权信号：
        - 文本密度 < 0.001:               +0.3
        - 字体多样性:                      min(font_count / 10, 0.2)
        - 矩形数量 > 5:                    +0.2
        - 矩形数量 > 20:                   额外 +0.2
        - 数学 Unicode 符号 / \\frac:      +0.25
        - 非标准旋转:                      +0.3
        - OCR 字体痕迹:                    +0.4
        - 双峰 X 分布（多栏布局）:          +0.15

      阈值映射：
        score < 0.25  -> simple
        score < 0.55  -> medium
        score >= 0.55 -> complex
    """
    # 短路逻辑：扫描页
    if signals.extractable_chars_on_page < 20 and signals.class_ != "Picture":
        return "complex"

    # 短路逻辑：图像类型始终为 complex
    if signals.class_ == "Picture":
        return "complex"

    score = 0.0

    # 文本密度异常（稀疏 -> 可能是混合内容）
    density = len(signals.text) / max(signals.bbox_area, 1.0)
    if density < 0.001:
        score += 0.3

    # 字体多样性
    score += min(signals.font_count / 10, 0.2)

    # 矩形 / 线条（表格结构）
    if signals.rect_count_in_bbox > 5:
        score += 0.2
    if signals.rect_count_in_bbox > 20:
        score += 0.2

    # 数学符号 (Unicode 数学字符或 LaTeX 片段)
    if any(c in signals.text for c in _MATH_CHARS) or "\\frac" in signals.text:
        score += 0.25

    # 非标准旋转
    if signals.page_rotation not in (0, 90, 180, 270):
        score += 0.3

    # OCR 字体痕迹
    if signals.has_ocr_fonts:
        score += 0.4

    # 多栏布局（双峰 X 分布）
    if signals.bimodal_x:
        score += 0.15

    # 映射到三个级别
    if score < COMPLEXITY_THRESHOLD_MEDIUM:
        return "simple"
    elif score < COMPLEXITY_THRESHOLD_COMPLEX:
        return "medium"
    else:
        return "complex"

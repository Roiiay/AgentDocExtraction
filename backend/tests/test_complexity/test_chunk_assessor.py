from backend.app.complexity.chunk_assessor import ChunkSignals, assess_complexity, detect_x_bimodal


def _signals(**overrides) -> ChunkSignals:
    """构建具有合理默认值的 ChunkSignals 的辅助函数。"""
    defaults = dict(
        class_="Text",
        text="Hello world, this is a normal paragraph of text.",
        bbox_area=8000.0,
        font_count=1,
        rect_count_in_bbox=0,
        page_rotation=0,
        has_ocr_fonts=False,
        extractable_chars_on_page=5000,
        bimodal_x=False,
    )
    defaults.update(overrides)
    return ChunkSignals(**defaults)


def test_simple_text():
    """普通文本，单一字体：分数 = min(1/10, 0.2) = 0.1 < 0.25 -> simple。"""
    assert assess_complexity(_signals()) == "simple"


def test_simple_title():
    """单一字体的短标题：分数 = 0.1 < 0.25 -> simple。"""
    assert assess_complexity(_signals(class_="Title", text="Chapter 1")) == "simple"


def test_medium_sparse_density():
    """稀疏文本（密度 < 0.001）：分数 = 0.3 + 0.1 = 0.4 -> medium。"""
    assert assess_complexity(_signals(text="Hi", bbox_area=500000.0)) == "medium"


def test_medium_math_symbols():
    """数学符号加 0.25：分数 = 0.25 + 0.1 = 0.35 -> medium。"""
    assert assess_complexity(_signals(text="Compute the integral f(x) = sqrt(a)")) == "simple"
    # 注意：纯 ASCII 的 "integral"/"sqrt" 不包含数学 Unicode 字符
    assert assess_complexity(_signals(text="The result is x \u2264 y + \u03b1")) == "medium"


def test_medium_rotation():
    """非标准旋转：分数 = 0.3 + 0.1 = 0.4 -> medium。"""
    assert assess_complexity(_signals(page_rotation=45)) == "medium"


def test_complex_scanned_page():
    """短路逻辑：可提取字符 < 20 -> complex。"""
    assert assess_complexity(_signals(extractable_chars_on_page=5)) == "complex"


def test_complex_picture():
    """短路逻辑：Picture 类别 -> 始终为 complex。"""
    assert assess_complexity(_signals(class_="Picture")) == "complex"


def test_complex_math_and_ocr_fonts():
    """数学 (0.25) + OCR 字体 (0.4) + 基础 (0.1) = 0.75 -> complex。"""
    assert assess_complexity(
        _signals(text="\u222b + \u2211", has_ocr_fonts=True)
    ) == "complex"


def test_complex_sparse_and_dense_rects():
    """稀疏 (0.3) + 矩形>20 (0.4) + 基础 (0.1) = 0.8 -> complex。"""
    assert assess_complexity(
        _signals(text=" ", bbox_area=500000.0, rect_count_in_bbox=25, class_="Table")
    ) == "complex"


def test_scanned_page_picture_not_complex_shortcircuit():
    """扫描页上的图片类：短路至 complex（优先检查图片）。"""
    assert assess_complexity(
        _signals(class_="Picture", extractable_chars_on_page=5)
    ) == "complex"


def test_table_with_few_rects_is_simple():
    """矩形 < 5 且密度正常的表格：分数 = 0.1 -> simple。"""
    assert assess_complexity(
        _signals(class_="Table", text="A B C\n1 2 3", rect_count_in_bbox=2)
    ) == "simple"


def test_medium_bimodal_x():
    """双峰分布 (0.15) + 基础 (0.1) = 0.25，恰好等于 medium 阈值 -> medium。
    bimodal_x=False 时仅基础 0.1 -> simple。"""
    assert assess_complexity(_signals(bimodal_x=True)) == "medium"
    assert assess_complexity(_signals(bimodal_x=False)) == "simple"


def test_bimodal_x_false_no_extra_score():
    """bimodal_x=False 时不额外加分：font_count=2 -> 0.2 < 0.25 -> simple。"""
    assert assess_complexity(_signals(bimodal_x=False, font_count=2)) == "simple"


def test_detect_x_bimodal_two_columns():
    """典型的双栏布局：X 中心分两组，中间有明显间隔。"""
    page_width = 1000.0
    # 左栏 x_center ~200，右栏 ~800，gap=600 > 1000*0.15=150
    x_centers = [180, 200, 210, 790, 800, 810]
    assert detect_x_bimodal(x_centers, page_width) is True


def test_detect_x_bimodal_single_column():
    """单栏布局：所有 X 中心聚集在一起。"""
    page_width = 1000.0
    x_centers = [400, 420, 410, 430, 415, 425]
    assert detect_x_bimodal(x_centers, page_width) is False


def test_detect_x_bimodal_too_few_blocks():
    """区块数量不足时不检测。"""
    assert detect_x_bimodal([100, 500], 1000.0) is False
    assert detect_x_bimodal([], 1000.0) is False

import fitz
import pytest
from pathlib import Path

from backend.app.extractors.text_extractor import TextExtractor


@pytest.fixture
def text_pdf(tmp_path):
    """在已知位置创建带有已知文本的 PDF。"""
    pdf_path = tmp_path / "test_text.pdf"
    with fitz.open() as doc:
        page = doc.new_page(width=612, height=792)  # US Letter 标准，单位为 PDF 点
        page.insert_text(fitz.Point(72, 72), "Hello World from text extractor", fontsize=14)
        page.insert_text(fitz.Point(72, 100), "Second line of test content", fontsize=12)
        page.insert_text(fitz.Point(72, 200), "Bottom area text block", fontsize=12)
        doc.save(str(pdf_path))
    return pdf_path


def test_extract_returns_text_from_known_area(text_pdf):
    """测试从已知区域提取文本。"""
    extractor = TextExtractor(dpi=150)
    # 在 150 DPI 下渲染：像素 = 点 * 150/72
    # 位于 Point(72, 72) 的文本 -> 像素坐标约为 (150, 150)
    # 使用覆盖上半部分的宽松像素坐标 bbox
    bbox = (100.0, 40.0, 700.0, 180.0)
    text = extractor.extract(text_pdf, page_num=0, bbox=bbox)
    assert isinstance(text, str)
    assert "Hello World" in text


def test_extract_returns_second_line(text_pdf):
    """测试提取第二行文本。"""
    extractor = TextExtractor(dpi=150)
    # 覆盖放置 "Second line" 文本的区域
    bbox = (100.0, 120.0, 700.0, 250.0)
    text = extractor.extract(text_pdf, page_num=0, bbox=bbox)
    assert "Second line" in text


def test_extract_empty_area(text_pdf):
    """测试从没有文本的区域提取。"""
    extractor = TextExtractor(dpi=150)
    # 右下角没有任何文本的区域
    bbox = (900.0, 1200.0, 1200.0, 1500.0)
    text = extractor.extract(text_pdf, page_num=0, bbox=bbox)
    assert isinstance(text, str)
    assert len(text.strip()) == 0


def test_extract_nonexistent_file():
    """测试文件不存在的情况。"""
    extractor = TextExtractor()
    with pytest.raises(FileNotFoundError):
        extractor.extract("/nonexistent/file.pdf", page_num=0, bbox=(0, 0, 100, 100))


def test_extract_page_out_of_range(text_pdf):
    """测试页码超出范围的情况。"""
    extractor = TextExtractor()
    with pytest.raises(ValueError):
        extractor.extract(text_pdf, page_num=99, bbox=(0, 0, 100, 100))


def test_custom_dpi(text_pdf):
    """测试自定义 DPI 映射。"""
    extractor = TextExtractor(dpi=72)
    # 在 72 DPI 下，像素坐标 == PDF 点
    bbox = (50.0, 50.0, 400.0, 120.0)
    text = extractor.extract(text_pdf, page_num=0, bbox=bbox)
    assert "Hello World" in text

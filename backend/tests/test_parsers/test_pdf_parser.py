import pytest
from conftest import SAMPLES_DIR

from backend.app.parsers.pdf_parser import PDFParser, ParsePageResult


@pytest.fixture
def sample_pdf_path():
    """选取一个确实存在的 sample PDF。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    assert len(pdfs) > 0, f"No PDF files found in {SAMPLES_DIR}"
    return pdfs[0]


def test_parse_returns_list_of_pages(sample_pdf_path):
    parser = PDFParser()
    pages = parser.parse(sample_pdf_path)
    assert isinstance(pages, list)
    assert len(pages) >= 1


def test_each_page_has_required_fields(sample_pdf_path):
    parser = PDFParser()
    pages = parser.parse(sample_pdf_path)
    page = pages[0]
    assert "page_num" in page
    assert "width" in page
    assert "height" in page
    assert "image" in page
    assert isinstance(page["image"], str)  # base64
    assert len(page["image"]) > 100       # 不是空字符串


def test_page_dimensions_positive(sample_pdf_path):
    parser = PDFParser()
    pages = parser.parse(sample_pdf_path)
    page = pages[0]
    assert page["width"] > 0
    assert page["height"] > 0


def test_parse_nonexistent_file():
    parser = PDFParser()
    with pytest.raises(FileNotFoundError):
        parser.parse("/nonexistent/file.pdf")

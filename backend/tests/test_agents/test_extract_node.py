from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from backend.app.agents.extract_node import extract_node
from backend.app.state import Chunk, ExtractedChunk, PipelineState


def _make_state(
    chunks: list[Chunk],
    error_type: str | None = None,
    review_feedback: str = "",
) -> PipelineState:
    """辅助函数：创建管道状态。"""
    return PipelineState(
        task_id="test",
        doc_type="paper",
        file_path="/fake/test.pdf",
        pages=[],
        chunks=chunks,
        extracted_chunks=[],
        reviewed_chunks=[],
        final_content=[],
        export_formats=["markdown"],
        review_round=0,
        max_review_rounds=3,
        review_passed=False,
        error_type=error_type,
        review_feedback=review_feedback,
        last_issues_hash=0,
        errors=[],
    )


def _chunk(
    chunk_id: str = "chunk_0000",
    class_: str = "Text",
    complexity: str = "simple",
    status: str = "pending",
) -> Chunk:
    """辅助函数：创建分块对象。"""
    return Chunk(
        chunk_id=chunk_id,
        page_num=0,
        bbox=(10.0, 10.0, 500.0, 100.0),
        image_crop="fake_base64_crop",
        class_=class_,
        complexity=complexity,
        metadata={},
        status=status,
    )


def test_simple_uses_text_extractor():
    """simple 分块应通过 TextExtractor 提取。"""
    chunks = [_chunk(complexity="simple")]
    state = _make_state(chunks)

    with patch("backend.app.agents.extract_node.TextExtractor") as MockTE:
        MockTE.return_value.extract.return_value = "Hello from PyMuPDF"
        result = extract_node(state)

    assert len(result["extracted_chunks"]) == 1
    assert result["extracted_chunks"][0]["content"] == "Hello from PyMuPDF"
    assert result["extracted_chunks"][0]["extraction_method"] == "pymupdf"


def test_complex_uses_vlm():
    """complex 分块应通过 VLMExtractor 提取。"""
    chunks = [_chunk(complexity="complex")]
    state = _make_state(chunks)

    with patch("backend.app.agents.extract_node.VLMExtractor") as MockVLM:
        MockVLM.return_value.extract.return_value = "VLM extracted text"
        result = extract_node(state)

    assert len(result["extracted_chunks"]) == 1
    assert result["extracted_chunks"][0]["content"] == "VLM extracted text"
    assert result["extracted_chunks"][0]["extraction_method"] == "vlm"


def test_medium_uses_text_extractor():
    """medium 分块应首先尝试 TextExtractor。"""
    chunks = [_chunk(complexity="medium")]
    state = _make_state(chunks)

    with patch("backend.app.agents.extract_node.TextExtractor") as MockTE:
        MockTE.return_value.extract.return_value = "Medium quality text"
        result = extract_node(state)

    assert result["extracted_chunks"][0]["extraction_method"] == "pymupdf"


def test_medium_falls_back_to_ocr_on_garble():
    """带高乱码率的 medium 分块应回退到 OCR。"""
    chunks = [_chunk(complexity="medium")]
    state = _make_state(chunks)

    # 返回乱码以触发 OCR 回退
    garbled = "\ufffd" * 50 + "some text"  # 高乱码率

    with patch("backend.app.agents.extract_node.TextExtractor") as MockTE, \
         patch("backend.app.extractors.ocr_extractor.OCRExtractor") as MockOCR, \
         patch("backend.app.agents.extract_node.decode_base64_to_image") as MockDecode:
        MockTE.return_value.extract.return_value = garbled
        MockOCR.return_value.extract.return_value = "OCR cleaned text"
        MockDecode.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        result = extract_node(state)

    assert result["extracted_chunks"][0]["content"] == "OCR cleaned text"
    assert result["extracted_chunks"][0]["extraction_method"] == "ocr"


def test_reextraction_forces_vlm():
    """当存在审核反馈且分块处于 reprocessing 状态时，强制使用 VLM。"""
    chunks = [_chunk(complexity="simple", status="reprocessing")]
    state = _make_state(
        chunks, error_type="complex", review_feedback="Table structure was broken"
    )

    with patch("backend.app.agents.extract_node.VLMExtractor") as MockVLM:
        MockVLM.return_value.extract.return_value = "Re-extracted via VLM"
        result = extract_node(state)

    assert result["extracted_chunks"][0]["content"] == "Re-extracted via VLM"
    assert result["extracted_chunks"][0]["extraction_method"] == "vlm"
    # 验证审核反馈作为上下文被传递
    call_args = MockVLM.return_value.extract.call_args
    assert "Table structure was broken" in str(call_args)


def test_done_chunks_skipped():
    """状态为 'done' 的分块在正常提取中被跳过。"""
    chunks = [
        _chunk(chunk_id="chunk_0000", complexity="simple", status="done"),
        _chunk(chunk_id="chunk_0001", complexity="simple", status="pending"),
    ]
    state = _make_state(chunks)

    with patch("backend.app.agents.extract_node.TextExtractor") as MockTE:
        MockTE.return_value.extract.return_value = "extracted"
        result = extract_node(state)

    # 只有 pending 状态的分块应被提取
    assert len(result["extracted_chunks"]) == 1
    assert result["extracted_chunks"][0]["chunk_id"] == "chunk_0001"


def test_multiple_chunks_mixed_complexity():
    """混合复杂度的多个分块应被正确路由。"""
    chunks = [
        _chunk(chunk_id="c0", complexity="simple"),
        _chunk(chunk_id="c1", complexity="complex"),
        _chunk(chunk_id="c2", complexity="simple"),
    ]
    state = _make_state(chunks)

    with patch("backend.app.agents.extract_node.TextExtractor") as MockTE, \
         patch("backend.app.agents.extract_node.VLMExtractor") as MockVLM:
        MockTE.return_value.extract.return_value = "text_result"
        MockVLM.return_value.extract.return_value = "vlm_result"
        result = extract_node(state)

    assert len(result["extracted_chunks"]) == 3
    methods = [ec["extraction_method"] for ec in result["extracted_chunks"]]
    assert methods == ["pymupdf", "vlm", "pymupdf"]

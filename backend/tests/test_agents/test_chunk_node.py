from conftest import SAMPLES_DIR

from backend.app.agents.chunk_node import chunk_node
from backend.app.state import PipelineState


def _make_state(file_path: str) -> PipelineState:
    """创建初始状态。"""
    return PipelineState(
        task_id="test_task",
        doc_type="paper",
        file_path=file_path,
        pages=[],
        chunks=[],
        extracted_chunks=[],
        reviewed_chunks=[],
        final_content=[],
        export_formats=["markdown"],
        review_round=0,
        max_review_rounds=3,
        review_passed=False,
        error_type=None,
        review_feedback="",
        last_issues_hash=0,
        errors=[],
    )


def test_chunk_node_produces_chunks():
    """集成测试：YOLO 在示例扫描 PDF 上检测布局区域。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    assert len(pdfs) > 0

    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    assert len(result["chunks"]) > 0
    assert len(result["pages"]) > 0


def test_chunks_have_required_fields():
    """测试分块是否包含所有必需字段。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    for chunk in result["chunks"]:
        assert "chunk_id" in chunk
        assert "page_num" in chunk
        assert "bbox" in chunk
        assert "image_crop" in chunk
        assert "class_" in chunk
        assert "complexity" in chunk
        assert "metadata" in chunk
        assert "status" in chunk


def test_chunks_have_valid_display_types():
    """测试分块类别是否在预定义的显示类型中。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    valid_types = {"Title", "Text", "Table", "Formula", "Picture"}
    for chunk in result["chunks"]:
        assert chunk["class_"] in valid_types, f"无效的类别: {chunk['class_']}"


def test_chunks_have_valid_complexity():
    """测试分块是否具有合法的复杂度标签。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    valid_complexity = {"simple", "medium", "complex"}
    for chunk in result["chunks"]:
        assert chunk["complexity"] in valid_complexity


def test_chunks_status_is_pending():
    """测试初始分块状态是否为 pending。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    for chunk in result["chunks"]:
        assert chunk["status"] == "pending"


def test_scanned_pdf_all_complex():
    """所有示例 PDF 都是扫描件（无提取文本），因此所有分块都应为 complex。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    for chunk in result["chunks"]:
        # 扫描页面的 extractable_chars_on_page < 20
        # 扫描页上的图片和非图片分块都应该是 complex
        assert chunk["complexity"] == "complex"


def test_pages_have_chunk_ids():
    """测试页面对象是否正确引用了分块 ID。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    for page in result["pages"]:
        assert "page_num" in page
        assert "image" in page
        assert "width" in page
        assert "height" in page
        assert "chunks" in page
        assert isinstance(page["chunks"], list)


def test_page_chunk_ids_match_chunks():
    """页面分块 ID 必须引用实际存在的分块。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    chunk_ids = {c["chunk_id"] for c in result["chunks"]}
    for page in result["pages"]:
        for cid in page["chunks"]:
            assert cid in chunk_ids


def test_image_crop_is_base64():
    """测试裁剪的图像是否为 base64 格式。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    result = chunk_node(state)

    for chunk in result["chunks"]:
        assert isinstance(chunk["image_crop"], str)
        assert len(chunk["image_crop"]) > 100  # 确保不是空的 base64

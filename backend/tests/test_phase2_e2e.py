"""第二阶段 E2E 验证：PDF -> chunk_node -> extract_node -> 提取后的分块。"""
from unittest.mock import patch

from conftest import SAMPLES_DIR

from backend.app.agents.chunk_node import chunk_node
from backend.app.agents.extract_node import extract_node
from backend.app.state import PipelineState


def _make_state(file_path: str) -> PipelineState:
    """初始化测试状态。"""
    return PipelineState(
        task_id="e2e_test",
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


def test_e2e_chunk_then_extract():
    """完整流程：YOLO 分块（真实）+ VLM 提取（模拟）。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    assert len(pdfs) > 0, f"在 {SAMPLES_DIR} 中未找到示例 PDF"

    state = _make_state(str(pdfs[0]))

    # 步骤 1：chunk_node (真实 YOLO)
    state = chunk_node(state)

    print(f"\n=== 第二阶段 E2E: {pdfs[0].name} ===")
    print(f"页数: {len(state['pages'])}")
    print(f"分块数: {len(state['chunks'])}")

    assert len(state["chunks"]) > 0, "YOLO 应该至少检测到一个区域"
    assert len(state["pages"]) == 1, "单页 PDF 应该产生 1 个页面结果"

    for chunk in state["chunks"]:
        print(
            f"  {chunk['chunk_id']}: {chunk['class_']}/{chunk['complexity']}, "
            f"bbox={[round(v, 1) for v in chunk['bbox']]}"
        )

    # 步骤 2：extract_node (由于测试环境下没有 API key，模拟 VLM)
    with patch("backend.app.agents.extract_node.VLMExtractor") as MockVLM:
        MockVLM.return_value.extract.return_value = "[VLM 提取内容占位符]"
        state = extract_node(state)

    print(f"\n提取后的分块: {len(state['extracted_chunks'])}")
    for ec in state["extracted_chunks"]:
        print(f"  {ec['chunk_id']}: 方法={ec['extraction_method']}, 长度={len(ec['content'])}")

    assert len(state["extracted_chunks"]) == len(state["chunks"])

    # 扫描 PDF 上的所有分块都应使用 VLM 提取
    for ec in state["extracted_chunks"]:
        assert ec["extraction_method"] == "vlm"
        assert len(ec["content"]) > 0


def test_e2e_chunk_count_matches_page_chunks():
    """页面分块 ID 的总和必须等于总分块数。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    state = _make_state(str(pdfs[0]))
    state = chunk_node(state)

    page_chunk_count = sum(len(p["chunks"]) for p in state["pages"])
    assert page_chunk_count == len(state["chunks"])

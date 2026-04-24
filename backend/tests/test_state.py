from typing import get_type_hints

from backend.app.state import (
    Chunk,
    ExtractedChunk,
    PageResult,
    PipelineState,
    ReviewedChunk,
)


def test_chunk_has_required_fields():
    hints = get_type_hints(Chunk)
    required = {"chunk_id", "page_num", "bbox", "image_crop", "class_", "complexity", "metadata", "status"}
    assert required == set(hints.keys())


def test_extracted_chunk_has_required_fields():
    hints = get_type_hints(ExtractedChunk)
    required = {"chunk_id", "content", "extraction_method"}
    assert required == set(hints.keys())


def test_reviewed_chunk_has_required_fields():
    hints = get_type_hints(ReviewedChunk)
    required = {"chunk_id", "content", "review_passed", "error_type", "review_feedback", "warnings"}
    assert required == set(hints.keys())


def test_page_result_has_required_fields():
    hints = get_type_hints(PageResult)
    required = {"page_num", "image", "width", "height", "chunks"}
    assert required == set(hints.keys())


def test_pipeline_state_has_required_fields():
    hints = get_type_hints(PipelineState)
    required = {
        "task_id", "doc_type", "file_path",
        "pages", "chunks", "extracted_chunks", "reviewed_chunks", "final_content",
        "export_formats",
        "review_round", "max_review_rounds", "review_passed", "error_type",
        "review_feedback", "last_issues_hash",
        "errors",
    }
    assert required == set(hints.keys())


def test_chunk_can_be_constructed():
    chunk = Chunk(
        chunk_id="c1",
        page_num=0,
        bbox=(10.0, 20.0, 100.0, 200.0),
        image_crop="base64str",
        class_="Text",
        complexity="simple",
        metadata={"confidence": 0.95},
        status="pending",
    )
    assert chunk["chunk_id"] == "c1"
    assert chunk["bbox"] == (10.0, 20.0, 100.0, 200.0)
    assert chunk["status"] == "pending"

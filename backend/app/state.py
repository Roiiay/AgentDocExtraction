from typing import Literal, TypedDict


class Chunk(TypedDict):
    chunk_id: str
    page_num: int
    bbox: tuple[float, float, float, float]  # (x1, y1, x2, y2)
    image_crop: str                          # base64；TODO: Phase 3 改为文件路径或对象存储引用，避免内存暴涨
    class_: str                              # Title / Text / Table / Formula / Picture
    complexity: str                          # simple / medium / complex
    metadata: dict                           # YOLO 置信度、字体信息、密度等
    status: str                              # pending / done / reprocessing


class ExtractedChunk(TypedDict):
    chunk_id: str
    content: str                             # 提取出的文本/表格/公式内容
    extraction_method: str                   # pymupdf / ocr / vlm


class ReviewedChunk(TypedDict):
    chunk_id: str
    content: str                             # 审核后的内容（可能已被修正）
    review_passed: bool
    error_type: str | None                   # None / "simple" / "complex"
    review_feedback: str                     # 错误描述
    warnings: list[str]                      # 强制通过时的警告


class PageResult(TypedDict):
    page_num: int
    image: str                               # base64，原始页面图片
    width: int
    height: int
    chunks: list[str]                        # 该页包含的 chunk_id 列表


class PipelineState(TypedDict):
    task_id: str
    doc_type: str                            # contract / invoice / paper / other
    file_path: str
    pages: list[PageResult]
    chunks: list[Chunk]
    extracted_chunks: list[ExtractedChunk]
    reviewed_chunks: list[ReviewedChunk]
    final_content: list[ReviewedChunk]
    export_formats: list[str]                # ["markdown", "word"]
    review_round: int
    max_review_rounds: int
    review_passed: bool
    error_type: str | None                   # None / "simple" / "complex"
    review_feedback: str                     # 退回提取节点时的错误原因
    last_issues_hash: int                    # 上一轮审核问题的哈希（死循环断路）
    errors: list[str]                        # 流水线错误日志

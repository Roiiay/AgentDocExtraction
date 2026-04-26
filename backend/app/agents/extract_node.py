from backend.app.extractors.text_extractor import TextExtractor
from backend.app.extractors.vlm_extractor import VLMExtractor
from backend.app.state import ExtractedChunk, PipelineState
from backend.app.utils.image_utils import decode_base64_to_image
from backend.app.utils.text_utils import garble_ratio


def extract_node(state: PipelineState) -> PipelineState:
    """根据复杂度级别提取每个分块的内容。

    路由规则：
      - simple:  TextExtractor (PyMuPDF)
      - medium:  TextExtractor；如果 garble_ratio > 0.1，则回退到 OCRExtractor
      - complex: VLMExtractor
      - reprocessing (存在审核反馈): 强制使用带上下文的 VLMExtractor
    """
    file_path = state["file_path"]
    chunks = state["chunks"]

    text_extractor = TextExtractor()
    vlm_extractor = VLMExtractor()

    is_reextraction = (
        state.get("error_type") == "complex" and bool(state.get("review_feedback"))
    )

    extracted: list[ExtractedChunk] = []

    for chunk in chunks:
        # 除非正在重新提取，否则跳过已完成的分块
        if chunk["status"] == "done" and not is_reextraction:
            continue

        content = ""
        method = ""

        if is_reextraction and chunk["status"] == "reprocessing":
            # 强制使用 VLM 进行带有审核上下文的重新提取
            content = vlm_extractor.extract(
                chunk["image_crop"],
                class_=chunk["class_"],
                context=state.get("review_feedback", ""),
            )
            method = "vlm"
        elif chunk["complexity"] == "simple":
            content = text_extractor.extract(
                file_path, chunk["page_num"], chunk["bbox"]
            )
            method = "pymupdf"
        elif chunk["complexity"] == "medium":
            content = text_extractor.extract(
                file_path, chunk["page_num"], chunk["bbox"]
            )
            method = "pymupdf"
            # 如果文本出现乱码，回退到 OCR
            if garble_ratio(content) > 0.1:
                from backend.app.extractors.ocr_extractor import OCRExtractor

                ocr = OCRExtractor()
                img = decode_base64_to_image(chunk["image_crop"])
                content = ocr.extract(img)
                method = "ocr"
        else:  # complex
            content = vlm_extractor.extract(
                chunk["image_crop"], class_=chunk["class_"]
            )
            method = "vlm"

        extracted.append(
            ExtractedChunk(
                chunk_id=chunk["chunk_id"],
                content=content,
                extraction_method=method,
            )
        )

    return {**state, "extracted_chunks": extracted}

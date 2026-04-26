from pathlib import Path
from typing import Optional

import fitz
import numpy as np

from backend.app.config import YOLO_MODEL_PATH, YOLO_TO_DISPLAY_TYPE, YOLO_IMGSZ, YOLO_MODEL_BACKEND
from backend.app.complexity.chunk_assessor import ChunkSignals, assess_complexity, detect_x_bimodal
from backend.app.parsers.pdf_parser import PDFParser
from backend.app.state import Chunk, PageResult, PipelineState
from backend.app.utils.bbox_utils import crop_image
from backend.app.utils.image_utils import decode_base64_to_image, encode_image_to_base64


_yolo_model = None


def _get_yolo_model():
    """延迟加载 YOLO 模型单例。"""
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        _yolo_model = YOLO(str(YOLO_MODEL_PATH))
    return _yolo_model


# 当前模型对应的推理图像尺寸
_yolo_imgsz = YOLO_IMGSZ[YOLO_MODEL_BACKEND]


def _rects_overlap(r1: fitz.Rect, r2: fitz.Rect) -> bool:
    """检查两个 fitz.Rect 对象是否重叠。"""
    return not (r1.x1 <= r2.x0 or r1.x0 >= r2.x1 or r1.y1 <= r2.y0 or r1.y0 >= r2.y1)


def chunk_node(state: PipelineState) -> PipelineState:
    """在每个页面上运行 YOLO 布局分析，构建带有复杂度标签的分块。

    步骤：
      1. 解析 PDF -> 页面图像（通过 PDFParser）
      2. 在每个页面图像上运行 YOLO -> 检测区域
      3. 对每个区域：裁剪图像、提取 PyMuPDF 信号、评估复杂度
      4. 构建 Chunk + PageResult 列表
    """
    file_path = state["file_path"]
    pdf_parser = PDFParser()
    dpi = pdf_parser.dpi

    # 1. 解析 PDF -> 页面图像
    page_images = pdf_parser.parse(file_path)

    # 2. 加载 YOLO 模型
    model = _get_yolo_model()

    # 3. 使用 PyMuPDF 打开 PDF 用于提取信号
    chunks: list[Chunk] = []
    pages: list[PageResult] = []
    chunk_counter = 0

    with fitz.open(str(file_path)) as doc:
        for page_idx, page_img_result in enumerate(page_images):
            # 解码页面图像用于 YOLO 检测和裁剪
            page_image = decode_base64_to_image(page_img_result["image"])
            width_px = page_img_result["width"]
            height_px = page_img_result["height"]

            # 运行 YOLO 推理
            yolo_results = model(page_image, imgsz=_yolo_imgsz, verbose=False)

            pdf_page = doc[page_idx]

            # 页面级信号
            page_text = pdf_page.get_text("text").strip()
            extractable_chars = len(page_text)
            page_rotation = pdf_page.rotation
            drawings = pdf_page.get_drawings()

            page_chunk_ids: list[str] = []

            # 收集本页所有 YOLO 检测框的 X 中心坐标，用于双峰分布检测
            all_x_centers: list[float] = []
            for yr in yolo_results:
                for bx in yr.boxes:
                    bx_coords = bx.xyxy[0].tolist()
                    all_x_centers.append((bx_coords[0] + bx_coords[2]) / 2)

            is_bimodal = detect_x_bimodal(all_x_centers, float(width_px))

            for yolo_result in yolo_results:
                for box in yolo_result.boxes:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]

                    # 将 YOLO 类别映射到显示类型
                    display_type = YOLO_TO_DISPLAY_TYPE.get(class_name)
                    if display_type is None:
                        continue

                    # 将 bbox 裁剪到页面边界内
                    x1 = max(0.0, x1)
                    y1 = max(0.0, y1)
                    x2 = min(float(width_px), x2)
                    y2 = min(float(height_px), y2)

                    bbox = (x1, y1, x2, y2)

                    # 从页面中裁剪图像
                    crop = crop_image(page_image, bbox)
                    crop_b64 = encode_image_to_base64(crop)

                    # 提取 PyMuPDF 信号用于复杂度评估
                    scale = 72.0 / dpi
                    pdf_rect = fitz.Rect(
                        x1 * scale, y1 * scale, x2 * scale, y2 * scale
                    )

                    # bbox 内的文本
                    text = pdf_page.get_text("text", clip=pdf_rect).strip()

                    # bbox 内的字体计数
                    blocks = pdf_page.get_text("dict", clip=pdf_rect)["blocks"]
                    fonts: set[str] = set()
                    for block in blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    fonts.add(span["font"])

                    # 与 bbox 重叠的矩形数量
                    rect_count = sum(
                        1 for d in drawings if _rects_overlap(d["rect"], pdf_rect)
                    )

                    # OCR 字体痕迹
                    has_ocr = any(
                        "CIDFont" in f or "GlyphLess" in f or "Unknown" in f
                        for f in fonts
                    )

                    signals = ChunkSignals(
                        class_=display_type,
                        text=text,
                        bbox_area=(x2 - x1) * (y2 - y1),
                        font_count=len(fonts),
                        rect_count_in_bbox=rect_count,
                        page_rotation=page_rotation,
                        has_ocr_fonts=has_ocr,
                        extractable_chars_on_page=extractable_chars,
                        bimodal_x=is_bimodal,
                    )

                    complexity = assess_complexity(signals)

                    chunk_id = f"chunk_{chunk_counter:04d}"
                    chunk_counter += 1

                    chunks.append(
                        Chunk(
                            chunk_id=chunk_id,
                            page_num=page_idx,
                            bbox=bbox,
                            image_crop=crop_b64,
                            class_=display_type,
                            complexity=complexity,
                            metadata={"confidence": confidence, "yolo_class": class_name},
                            status="pending",
                        )
                    )
                    page_chunk_ids.append(chunk_id)

            pages.append(
                PageResult(
                    page_num=page_idx,
                    image=page_img_result["image"],
                    width=width_px,
                    height=height_px,
                    chunks=page_chunk_ids,
                )
            )

    # 返回更新后的状态（PipelineState 是 TypedDict，本质是 dict，直接展开）
    return {**state, "pages": pages, "chunks": chunks}

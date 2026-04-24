from pathlib import Path
from typing import List, TypedDict

import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np

from backend.app.utils.image_utils import encode_image_to_base64


class ParsePageResult(TypedDict):
    page_num: int
    width: int
    height: int
    image: str          # base64 编码的页面 PNG 图像


class PDFParser:
    """使用 PyMuPDF 将 PDF 解析为页面图像 + 元数据。"""

    def __init__(self, dpi: int = 150) -> None:
        self.dpi = dpi

    def parse(self, pdf_path: str | Path) -> List[ParsePageResult]:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        results: List[ParsePageResult] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]

            # 渲染为 PNG 图像
            zoom = self.dpi / 72.0  # 72 DPI 是 PDF 默认
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            # 使用渲染后的实际像素尺寸（而非 PDF points），确保与 YOLO 检测 / bbox 裁剪坐标一致
            width_px = pix.width
            height_px = pix.height

            # 转换为 numpy -> base64
            img_bytes = pix.tobytes("png")
            pil_img = Image.open(io.BytesIO(img_bytes))
            np_img = np.array(pil_img.convert("RGB"))
            b64_image = encode_image_to_base64(np_img)

            results.append(
                ParsePageResult(
                    page_num=page_idx,
                    width=width_px,
                    height=height_px,
                    image=b64_image,
                )
            )

        doc.close()
        return results

from pathlib import Path

import fitz


class TextExtractor:
    """使用 PyMuPDF get_text 从 PDF 页面区域提取文本。

    坐标：bbox 位于像素空间（与渲染的页面图像匹配）。
    内部通过 dpi 缩放转换为 PDF 点。
    """

    def __init__(self, dpi: int = 150) -> None:
        self.dpi = dpi

    def extract(
        self,
        pdf_path: str | Path,
        page_num: int,
        bbox: tuple[float, float, float, float],
    ) -> str:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"未找到 PDF 文件: {pdf_path}")

        with fitz.open(str(pdf_path)) as doc:
            if page_num >= len(doc):
                raise ValueError(f"页码 {page_num} 超出范围 (文档共有 {len(doc)} 页)")

            page = doc[page_num]

            # 将像素坐标（基于 dpi）转换为 PDF 点（72 DPI）
            scale = 72.0 / self.dpi
            pdf_rect = fitz.Rect(
                bbox[0] * scale,
                bbox[1] * scale,
                bbox[2] * scale,
                bbox[3] * scale,
            )

            text = page.get_text("text", clip=pdf_rect).strip()
            return text

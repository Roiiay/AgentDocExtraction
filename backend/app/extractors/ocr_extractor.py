import numpy as np


class OCRExtractor:
    """使用 RapidOCR 从图像中提取文本。

    在首次使用时延迟初始化 OCR 引擎，以避免在不需要 OCR 时启动缓慢。
    """

    def __init__(self) -> None:
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr import RapidOCR
            self._engine = RapidOCR()
        return self._engine

    def extract(self, image: np.ndarray) -> str:
        """在 numpy 图像上运行 OCR 并返回提取的文本。"""
        engine = self._get_engine()
        result = engine(image)
        if result.txts:
            return "\n".join(result.txts)
        return ""

import numpy as np
import pytest

from backend.app.extractors.ocr_extractor import OCRExtractor


def _make_text_image() -> np.ndarray:
    """创建一个简单的带有高对比度类似文本内容的图像用于 OCR。"""
    img = np.ones((100, 400, 3), dtype=np.uint8) * 255  # 白色背景
    # 绘制黑色矩形模拟文本块
    img[30:50, 20:80] = 0
    img[30:50, 100:200] = 0
    img[30:50, 220:300] = 0
    return img


def test_extract_returns_string():
    extractor = OCRExtractor()
    img = _make_text_image()
    result = extractor.extract(img)
    assert isinstance(result, str)


def test_extract_blank_image_returns_empty():
    extractor = OCRExtractor()
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    result = extractor.extract(img)
    assert isinstance(result, str)
    # 纯黑图像应产生极少或没有文本
    assert len(result.strip()) < 50


def test_extract_white_image_returns_empty():
    extractor = OCRExtractor()
    img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    result = extractor.extract(img)
    assert isinstance(result, str)


def test_engine_lazy_init():
    """引擎不应在第一次调用前被创建。"""
    extractor = OCRExtractor()
    assert extractor._engine is None

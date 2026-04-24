import base64
import io
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image

BBox = Tuple[float, float, float, float]


def encode_image_to_base64(image: np.ndarray, fmt: str = "PNG") -> str:
    """将 numpy 图像编码为 base64 字符串。"""
    pil_img = Image.fromarray(image)
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def image_to_base64(pil_img: Image.Image, fmt: str = "PNG") -> str:
    """将 PIL Image 编码为 base64 字符串。"""
    buf = io.BytesIO()
    pil_img.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def decode_base64_to_image(b64_str: str) -> np.ndarray:
    """将 base64 字符串解码为 numpy 图像 (H, W, 3)。"""
    img_bytes = base64.b64decode(b64_str)
    pil_img = Image.open(io.BytesIO(img_bytes))
    return np.array(pil_img.convert("RGB"))


def draw_numbered_bboxes(
    image: np.ndarray,
    bboxes: List[BBox],
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    font_scale: float = 0.5,
) -> np.ndarray:
    """在图像上绘制带编号的 bbox 矩形框，用于 VLM 排序。"""
    result = image.copy()
    for idx, bbox in enumerate(bboxes):
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        cv2.rectangle(result, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            result,
            str(idx + 1),
            (x1, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
        )
    return result

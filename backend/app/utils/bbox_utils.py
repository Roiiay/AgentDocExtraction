from typing import Tuple

import numpy as np

BBox = Tuple[float, float, float, float]  # (x1, y1, x2, y2)


def compute_iou(bbox1: BBox, bbox2: BBox) -> float:
    """计算两个 bbox 的交并比 (Intersection over Union)。"""
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter_area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def horizontal_overlap_ratio(bbox1: BBox, bbox2: BBox) -> float:
    """计算两个 bbox 的水平重叠比例（相对于较窄的那个）。"""
    x_overlap = max(0.0, min(bbox1[2], bbox2[2]) - max(bbox1[0], bbox2[0]))
    min_width = min(bbox1[2] - bbox1[0], bbox2[2] - bbox2[0])
    if min_width <= 0:
        return 0.0
    return x_overlap / min_width


def crop_image(image: np.ndarray, bbox: BBox) -> np.ndarray:
    """从 numpy 图像中裁剪 bbox 指定区域。"""
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    h, w = image.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    return image[y1:y2, x1:x2]

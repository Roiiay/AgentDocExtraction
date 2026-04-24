import base64

import numpy as np
from PIL import Image

from backend.app.utils.image_utils import (
    decode_base64_to_image,
    draw_numbered_bboxes,
    encode_image_to_base64,
    image_to_base64,
)


def _make_image(w: int = 100, h: int = 100) -> np.ndarray:
    return np.zeros((h, w, 3), dtype=np.uint8)


def test_encode_decode_roundtrip_numpy():
    img = _make_image(80, 60)
    b64 = encode_image_to_base64(img)
    assert isinstance(b64, str)
    restored = decode_base64_to_image(b64)
    assert restored.shape == (60, 80, 3)


def test_encode_decode_roundtrip_pil():
    pil_img = Image.fromarray(_make_image(50, 40))
    b64 = image_to_base64(pil_img)
    restored = decode_base64_to_image(b64)
    assert restored.shape == (40, 50, 3)


def test_draw_numbered_bboxes_returns_image():
    img = _make_image(200, 200)
    bboxes = [(10, 10, 50, 50), (60, 60, 100, 100)]
    result = draw_numbered_bboxes(img, bboxes)
    assert result.shape == img.shape
    assert result.max() > 0


def test_draw_numbered_bboxes_empty_list():
    img = _make_image()
    result = draw_numbered_bboxes(img, [])
    assert result.shape == img.shape

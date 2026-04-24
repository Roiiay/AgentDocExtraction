from backend.app.utils.bbox_utils import (
    BBox,
    compute_iou,
    crop_image,
    horizontal_overlap_ratio,
)


def test_compute_iou_identical():
    bbox = (0, 0, 10, 10)
    assert compute_iou(bbox, bbox) == 1.0


def test_compute_iou_no_overlap():
    a = (0, 0, 10, 10)
    b = (20, 20, 30, 30)
    assert compute_iou(a, b) == 0.0


def test_compute_iou_partial_overlap():
    a = (0, 0, 10, 10)
    b = (5, 5, 15, 15)
    expected = 25.0 / 175.0
    assert abs(compute_iou(a, b) - expected) < 1e-9


def test_compute_iou_contained():
    outer = (0, 0, 20, 20)
    inner = (5, 5, 10, 10)
    expected = 25.0 / 400.0
    assert abs(compute_iou(outer, inner) - expected) < 1e-9


def test_compute_iou_zero_area():
    a = (0, 0, 0, 0)
    b = (0, 0, 10, 10)
    assert compute_iou(a, b) == 0.0


def test_horizontal_overlap_ratio_full():
    a = (0, 0, 100, 50)
    b = (0, 60, 100, 110)
    assert horizontal_overlap_ratio(a, b) == 1.0


def test_horizontal_overlap_ratio_none():
    a = (0, 0, 50, 50)
    b = (60, 0, 100, 50)
    assert horizontal_overlap_ratio(a, b) == 0.0


def test_horizontal_overlap_ratio_partial():
    a = (0, 0, 100, 50)
    b = (50, 60, 120, 110)
    expected = 50.0 / 70.0
    assert abs(horizontal_overlap_ratio(a, b) - expected) < 1e-9


def test_crop_image():
    import numpy as np

    img = np.zeros((100, 200, 3), dtype=np.uint8)
    img[20:40, 10:50] = 255
    cropped = crop_image(img, (10.0, 20.0, 50.0, 40.0))
    assert cropped.shape == (20, 40, 3)
    assert cropped.max() == 255

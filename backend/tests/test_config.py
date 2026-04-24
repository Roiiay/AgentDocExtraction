from backend.app.config import (
    CATEGORY_MAP,
    COMPLEXITY_THRESHOLD_COMPLEX,
    COMPLEXITY_THRESHOLD_MEDIUM,
    MAX_REVIEW_ROUNDS,
    MODELS_DIR,
    PROJECT_ROOT,
    TYPE_COLORS,
    VALID_CONVERSION_TYPES,
    YOLO_MODEL_PATH,
)


def test_project_root_is_valid():
    assert PROJECT_ROOT.exists()


def test_models_dir_exists():
    assert MODELS_DIR.exists()


def test_yolo_model_path_points_to_file():
    assert YOLO_MODEL_PATH.name == "yolov11s-doclaynet.pt"


def test_category_map_covers_all_display_types():
    display_types = set(CATEGORY_MAP.values())
    assert "Title" in display_types
    assert "Text" in display_types
    assert "Table" in display_types
    assert "Formula" in display_types
    assert "Picture" in display_types
    assert None in display_types  # abandon


def test_category_map_has_expected_yolo_keys():
    expected_keys = {
        "title", "section_header", "text_block", "caption", "list_group",
        "page_footnote", "page_number", "header", "code_txt",
        "table", "table_caption",
        "equation_isolated", "equation_semantic",
        "figure", "figure_caption", "chart_mask",
        "abandon",
    }
    assert set(CATEGORY_MAP.keys()) == expected_keys


def test_type_colors_has_all_five_types():
    assert set(TYPE_COLORS.keys()) == {"Title", "Text", "Table", "Formula", "Picture"}


def test_valid_conversion_types_excludes_title():
    assert "Title" not in VALID_CONVERSION_TYPES
    assert set(VALID_CONVERSION_TYPES) == {"Text", "Table", "Formula", "Picture"}


def test_complexity_thresholds_ordering():
    assert 0 < COMPLEXITY_THRESHOLD_MEDIUM < COMPLEXITY_THRESHOLD_COMPLEX < 1


def test_max_review_rounds_positive():
    assert MAX_REVIEW_ROUNDS >= 1

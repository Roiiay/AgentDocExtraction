from backend.app.config import (
    CATEGORY_MAP,
    COMPLEXITY_THRESHOLD_COMPLEX,
    COMPLEXITY_THRESHOLD_MEDIUM,
    MAX_REVIEW_ROUNDS,
    MODELS_DIR,
    PROJECT_ROOT,
    TYPE_COLORS,
    VALID_CONVERSION_TYPES,
    YOLO_MODEL_BACKEND,
    YOLO_MODEL_PATH,
    YOLO_MODEL_PATHS,
    YOLO_TO_DISPLAY_TYPE,
    YOLOV11S_TO_DISPLAY_TYPE,
    DOCLAYOUT_TO_DISPLAY_TYPE,
)


def test_project_root_is_valid():
    assert PROJECT_ROOT.exists()


def test_models_dir_exists():
    assert MODELS_DIR.exists()


def test_yolo_model_path_points_to_file():
    assert YOLO_MODEL_PATH.name == YOLO_MODEL_PATHS[YOLO_MODEL_BACKEND].name


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


def test_yolo_to_display_type_covers_all_yolo_classes():
    """根据当前后端验证 YOLO 类别映射的键。"""
    if YOLO_MODEL_BACKEND == "yolov11s":
        yolo_classes = {
            "Title", "Section-header", "Text", "Caption", "List-item",
            "Footnote", "Page-footer", "Page-header", "Table", "Formula", "Picture",
        }
        assert yolo_classes == set(YOLOV11S_TO_DISPLAY_TYPE.keys())
    elif YOLO_MODEL_BACKEND == "doclayout":
        yolo_classes = {
            "title", "plain text", "figure", "figure_caption",
            "table", "table_caption", "table_footnote",
            "isolate_formula", "formula_caption",
        }
        assert yolo_classes == set(DOCLAYOUT_TO_DISPLAY_TYPE.keys())


def test_yolo_to_display_type_maps_to_valid_display_types():
    """确保映射到了有效的显示类型。"""
    display_types = set(YOLO_TO_DISPLAY_TYPE.values())
    assert display_types == {"Title", "Text", "Table", "Formula", "Picture"}

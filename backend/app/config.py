import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

# ── YOLO Model Backend Selection ──────────────────────────────────────
# 可选值: "yolov11s" (默认) 或 "doclayout"
YOLO_MODEL_BACKEND = os.getenv("YOLO_MODEL_BACKEND", "yolov11s")

# ── YOLO Model Paths ──────────────────────────────────────────────────
YOLO_MODEL_PATHS: dict[str, Path] = {
    "yolov11s": MODELS_DIR / "yolov11s-doclaynet.pt",
    "doclayout": MODELS_DIR / "doclayout_yolo_docstructbench_imgsz1024.pt",
}
YOLO_MODEL_PATH = YOLO_MODEL_PATHS[YOLO_MODEL_BACKEND]
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(PROJECT_ROOT / "uploads")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(PROJECT_ROOT / "outputs")))

# ── API Keys ───────────────────────────────────────────────────────────
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
GLM_API_KEY = os.getenv("GLM_API_KEY", "")

# ── Model Endpoints ────────────────────────────────────────────────────
QWEN_API_URL = os.getenv(
    "QWEN_API_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
)
GLM_API_URL = os.getenv(
    "GLM_API_URL",
    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
)

# ── Model Names ────────────────────────────────────────────────────────
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-vl-max")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4-flash")

# ── Complexity Thresholds ──────────────────────────────────────────────
COMPLEXITY_THRESHOLD_MEDIUM = float(os.getenv("COMPLEXITY_THRESHOLD_MEDIUM", "0.25"))
COMPLEXITY_THRESHOLD_COMPLEX = float(os.getenv("COMPLEXITY_THRESHOLD_COMPLEX", "0.55"))

# ── Review Settings ────────────────────────────────────────────────────
MAX_REVIEW_ROUNDS = int(os.getenv("MAX_REVIEW_ROUNDS", "3"))
REVIEW_CONFIDENCE_THRESHOLD = float(os.getenv("REVIEW_CONFIDENCE_THRESHOLD", "0.6"))

# ── YOLO Category -> Display Type ──────────────────────────────────────
CATEGORY_MAP: dict[str, str | None] = {
    "title": "Title",
    "section_header": "Title",
    "text_block": "Text",
    "caption": "Text",
    "list_group": "Text",
    "page_footnote": "Text",
    "page_number": "Text",
    "header": "Text",
    "code_txt": "Text",
    "table": "Table",
    "table_caption": "Table",
    "equation_isolated": "Formula",
    "equation_semantic": "Formula",
    "figure": "Picture",
    "figure_caption": "Picture",
    "chart_mask": "Picture",
    "abandon": None,
}

# ── Type Colors (for frontend) ─────────────────────────────────────────
TYPE_COLORS: dict[str, str] = {
    "Title": "#2ecc71",    # 绿色
    "Text": "#3498db",     # 蓝色
    "Table": "#e67e22",    # 橙色
    "Formula": "#9b59b6",  # 紫色
    "Picture": "#e74c3c",  # 红色
}

# ── Valid types for force conversion ───────────────────────────────────
VALID_CONVERSION_TYPES = ["Text", "Table", "Formula", "Picture"]

# ── YOLO 模型推理输出类别 -> 显示类型 ────────────────────────────────
# 注意：与 CATEGORY_MAP（Ground Truth 评估用，14 类 → 5 类）不同，
# 此映射专用于 YOLOv11s-doclaynet 模型推理输出（11 类 → 5 类）。
YOLOV11S_TO_DISPLAY_TYPE: dict[str, str] = {
    "Title": "Title",
    "Section-header": "Title",
    "Text": "Text",
    "Caption": "Text",
    "List-item": "Text",
    "Footnote": "Text",
    "Page-footer": "Text",
    "Page-header": "Text",
    "Table": "Table",
    "Formula": "Formula",
    "Picture": "Picture",
}

# DocLayout-YOLO 模型推理输出类别 -> 显示类型（10 类 → 5 类）
DOCLAYOUT_TO_DISPLAY_TYPE: dict[str, str] = {
    "title": "Title",
    "plain text": "Text",
    "figure": "Picture",
    "figure_caption": "Picture",
    "table": "Table",
    "table_caption": "Table",
    "table_footnote": "Text",
    "isolate_formula": "Formula",
    "formula_caption": "Text",
    # "abandon" 不映射，跳过
}

# ── YOLO 推理参数 ──────────────────────────────────────────────────────
YOLO_IMGSZ: dict[str, int] = {
    "yolov11s": 640,
    "doclayout": 1024,
}

# 当前活跃的映射（根据 YOLO_MODEL_BACKEND 自动选择）
_yolo_mappings: dict[str, dict[str, str]] = {
    "yolov11s": YOLOV11S_TO_DISPLAY_TYPE,
    "doclayout": DOCLAYOUT_TO_DISPLAY_TYPE,
}
YOLO_TO_DISPLAY_TYPE = _yolo_mappings[YOLO_MODEL_BACKEND]

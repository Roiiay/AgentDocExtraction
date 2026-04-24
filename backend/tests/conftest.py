import sys
from pathlib import Path

# 确保项目根目录（AgentDocExtraction/）在 sys.path 中，使 from backend.app.xxx 能正确导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "samples" / "group_0000-0099"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"

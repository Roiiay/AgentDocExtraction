import sys
from pathlib import Path

# 确保项目根目录（AgentDocExtraction/）在 sys.path 中，使 from backend.app.xxx 能正确导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
# 将 tests/ 目录也加入 sys.path，使子目录中的测试可以通过 from conftest import ... 导入常量
sys.path.insert(0, str(Path(__file__).resolve().parent))

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "samples" / "group_0000-0099"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.app.main import app
    return TestClient(app)

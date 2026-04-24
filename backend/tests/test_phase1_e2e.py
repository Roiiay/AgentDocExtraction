"""Phase 1 端到端验证：上传 PDF -> 成功解析为页面图像列表。"""

from pathlib import Path

from conftest import SAMPLES_DIR

from backend.app.parsers.pdf_parser import PDFParser
from backend.app.services.task_manager import TaskManager
from backend.app.main import app


def test_e2e_parse_sample_pdf():
    """验证：选取一个 sample PDF，解析后能得到页面图像 + 尺寸。"""
    pdfs = sorted(SAMPLES_DIR.glob("*.pdf"))
    assert len(pdfs) > 0, f"No sample PDFs in {SAMPLES_DIR}"

    parser = PDFParser()
    pdf_path = pdfs[0]

    pages = parser.parse(pdf_path)

    # 至少有一页
    assert len(pages) >= 1

    for page in pages:
        # 每页有必需字段
        assert "page_num" in page
        assert "width" in page
        assert "height" in page
        assert "image" in page

        # 尺寸为正
        assert page["width"] > 0
        assert page["height"] > 0

        # image 是非空 base64 字符串
        assert isinstance(page["image"], str)
        assert len(page["image"]) > 100

    # 打印摘要（方便人工确认）
    print(f"\n=== Phase 1 E2E: {pdf_path.name} ===")
    print(f"Pages: {len(pages)}")
    for p in pages:
        print(f"  Page {p['page_num']}: {p['width']}x{p['height']}, image={len(p['image'])} chars")


def test_e2e_task_lifecycle():
    """验证：任务创建 -> 状态流转 -> 完成。"""
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf", doc_type="paper")

    # pending -> chunking -> extracting -> reviewing -> merging -> exporting -> completed
    for status in ["chunking", "extracting", "reviewing", "merging", "exporting", "completed"]:
        mgr.update_task_status(task_id, status)  # type: ignore

    task = mgr.get_task(task_id)
    assert task is not None
    assert task["status"] == "completed"


def test_e2e_fastapi_health():
    """验证：FastAPI 应用可以响应健康检查。"""
    from fastapi.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

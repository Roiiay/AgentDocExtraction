import json
import threading
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

# 加载项目根目录的 .env 文件
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from backend.app.agents.chunk_node import chunk_node
from backend.app.agents.extract_node import extract_node
from backend.app.config import TYPE_COLORS, UPLOAD_DIR
from backend.app.services.task_manager import TaskManager
from backend.app.state import PipelineState

app = FastAPI(
    title="AgentDocExtraction",
    version="0.1.0",
    description="基于智能体的文档内容提取平台",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="backend/app/templates")
task_manager = TaskManager()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _run_pipeline(task_id: str, file_path: str):
    """在后台线程中运行 chunk_node + extract_node 管道。"""
    try:
        task_manager.update_task_status(task_id, "chunking")
        state = PipelineState(
            task_id=task_id,
            doc_type="other",
            file_path=file_path,
            pages=[],
            chunks=[],
            extracted_chunks=[],
            reviewed_chunks=[],
            final_content=[],
            export_formats=["markdown"],
            review_round=0,
            max_review_rounds=3,
            review_passed=False,
            error_type=None,
            review_feedback="",
            last_issues_hash=0,
            errors=[],
        )
        state = chunk_node(state)
        task_manager.update_task_status(task_id, "extracting")
        state = extract_node(state)
        task = task_manager.get_task(task_id)
        if task is not None:
            task["pages"] = list(state["pages"])
            task["chunks"] = list(state["chunks"])
            task["extracted_chunks"] = list(state["extracted_chunks"])
        # 跳过尚未实现的中间步骤（reviewing → merging → exporting）
        task_manager.update_task_status(task_id, "reviewing")
        task_manager.update_task_status(task_id, "merging")
        task_manager.update_task_status(task_id, "exporting")
        task_manager.update_task_status(task_id, "completed")
    except Exception as e:
        task_manager.update_task_status(task_id, "failed", error_message=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/")
async def index(request: Request):
    """渲染主页面。"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "type_colors": TYPE_COLORS,
        "type_colors_json": json.dumps(TYPE_COLORS),
    })


@app.post("/api/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """上传 PDF 并启动后台处理管道。"""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return JSONResponse({"detail": "仅支持 PDF 文件"}, status_code=400)

    task_id = task_manager.create_task("pending", doc_type="other")
    save_path = UPLOAD_DIR / f"{task_id}.pdf"

    content = await file.read()
    save_path.write_bytes(content)

    # 更新 file_path 为实际保存路径
    task = task_manager.get_task(task_id)
    task["file_path"] = str(save_path)

    # 启动后台线程处理
    thread = threading.Thread(
        target=_run_pipeline, args=(task_id, str(save_path)), daemon=True
    )
    thread.start()

    return JSONResponse({"task_id": task_id}, status_code=202)


@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    """获取任务状态和处理结果。"""
    task = task_manager.get_task(task_id)
    if task is None:
        return JSONResponse({"detail": "任务不存在"}, status_code=404)
    return task

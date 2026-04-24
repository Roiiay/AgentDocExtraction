from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AgentDocExtraction",
    version="0.1.0",
    description="基于智能体的文档内容提取平台",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # 开发环境前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由将在后续轮次中挂载
# from backend.app.api import tasks, chunks, evaluate
# app.include_router(tasks.router, prefix="/api")
# app.include_router(chunks.router, prefix="/api")
# app.include_router(evaluate.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}

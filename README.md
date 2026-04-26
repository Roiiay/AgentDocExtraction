# AgentDocExtraction

基于多 Agent 协作的文档内容提取平台。上传 PDF 文件，自动完成版面分析、分块、内容提取，输出结构化 Markdown。

## 技术架构

```
PDF 上传 → YOLO 版面检测 → 复杂度评估 → 智能路由提取 → 审核 → 合并 → 导出
```

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| Web 框架 | FastAPI + Uvicorn | 异步 API 服务 |
| Agent 编排 | LangGraph | 多阶段管道 |
| 版面检测 | YOLO (本地推理) | 支持 YOLOv11s / DocLayout-YOLO 两种后端 |
| 文本提取 | PyMuPDF + RapidOCR | 简单区域直接提取，乱码自动降级 OCR |
| 视觉提取 | Qwen-VL (云端 API) | 复杂区域通过 VLM 提取 |
| 文本审核 | GLM-4 (云端 API) | 提取结果校验 (规划中) |

### 提取策略路由

每个版面区块根据复杂度自动选择最优提取方式：

| 复杂度 | 评分范围 | 提取策略 |
|--------|----------|----------|
| 简单 | < 0.25 | PyMuPDF 直接提取文本 |
| 中等 | 0.25 ~ 0.55 | PyMuPDF 提取 + 乱码检测，乱码率 >10% 时降级 OCR |
| 复杂 | >= 0.55 | Qwen-VL 视觉提取 |

复杂度由 `chunk_assessor.py` 综合评估，信号包括：文本密度、字体多样性、绘图矩形数量、数学符号、OCR 字体痕迹、页面旋转、多栏布局等。

## 项目结构

```
AgentDocExtraction/
├── .env.example                  # 环境变量模板
├── models/                       # YOLO 模型权重 (需手动放置，已 gitignore)
├── uploads/                      # 运行时：上传的 PDF
├── outputs/                      # 运行时：导出文件
├── backend/
│   ├── requirements.txt          # Python 依赖
│   ├── app/
│   │   ├── main.py               # FastAPI 入口 + 路由
│   │   ├── config.py             # 全局配置
│   │   ├── state.py              # PipelineState 类型定义
│   │   ├── agents/
│   │   │   ├── chunk_node.py     # YOLO 版面检测 + 分块
│   │   │   └── extract_node.py   # 复杂度路由提取
│   │   ├── extractors/
│   │   │   ├── text_extractor.py # PyMuPDF 文本提取
│   │   │   ├── ocr_extractor.py  # RapidOCR 提取
│   │   │   └── vlm_extractor.py  # Qwen-VL 视觉提取
│   │   ├── parsers/
│   │   │   ├── pdf_parser.py     # PDF 解析 (PyMuPDF)
│   │   │   └── ofd_parser.py     # OFD 解析 (ZIP+XML)
│   │   ├── complexity/
│   │   │   └── chunk_assessor.py # 复杂度评分
│   │   ├── services/
│   │   │   └── task_manager.py   # 任务状态管理
│   │   ├── utils/                # 工具函数 (bbox, hash, image, text)
│   │   └── templates/
│   │       └── index.html        # 调试用 Web UI
│   └── tests/                    # 测试套件
└── docs/
    └── samples/                  # 测试样本 (已 gitignore)
```

## 快速开始

### 1. 环境要求

- **Python** 3.10+
- **Git**
- 操作系统：Windows / macOS / Linux

### 2. 克隆仓库

```bash
git clone https://github.com/Roiiay/AgentDocExtraction.git
cd AgentDocExtraction
```

### 3. 创建虚拟环境并安装依赖

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r backend/requirements.txt
```

> 注意：`ultralytics` 和 `opencv-python` 依赖较多，安装可能需要几分钟。如果安装 `opencv-python` 遇到问题，可以尝试 `pip install opencv-python-headless`。

### 4. 配置环境变量

复制模板并填入你的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入真实的 API 密钥：

```env
# 必填：模型 API 密钥
QWEN_API_KEY=sk-your-qwen-api-key-here
GLM_API_KEY=your-glm-api-key-here

# 可选配置（有默认值，一般不需要改）
# QWEN_API_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
# GLM_API_URL=https://open.bigmodel.cn/api/paas/v4
# QWEN_MODEL=qwen-vl-max
# GLM_MODEL=glm-4-flash
# YOLO_MODEL_BACKEND=yolov11s
# COMPLEXITY_THRESHOLD_MEDIUM=0.25
# COMPLEXITY_THRESHOLD_COMPLEX=0.55
# MAX_REVIEW_ROUNDS=3
```

**获取 API 密钥：**
- Qwen (通义千问)：[阿里云 DashScope](https://dashscope.console.aliyun.com/) → 开通服务 → 创建 API Key
- GLM (智谱)：[智谱开放平台](https://open.bigmodel.cn/) → 注册 → 获取 API Key

> 如果只想测试版面检测（不使用 VLM 提取），可以暂时不填 API 密钥，复杂区块的提取会失败但不影响简单区块。

### 5. 准备 YOLO 模型权重

模型权重文件体积较大，未包含在 Git 仓库中。需要手动下载并放入 `models/` 目录。

**默认模型 (yolov11s) — 必须准备：**

```bash
mkdir -p models
# 下载 YOLOv11s-doclaynet 权重到 models/ 目录
# 文件名：yolov11s-doclaynet.pt
```

可以从以下途径获取：
- [DocLayNet 数据集](https://huggingface.co/datasets/visheratin/DocLayNet) 页面查找预训练权重
- 或自行使用 Ultralytics 在 DocLayNet 上训练 YOLOv11s

**备选模型 (doclayout) — 可选：**

如需使用 DocLayout-YOLO 后端，还需下载：
- 文件名：`doclayout_yolo_docstructbench_imgsz1024.pt`
- 然后在 `.env` 中设置 `YOLO_MODEL_BACKEND=doclayout`

最终的 `models/` 目录结构：

```
models/
├── yolov11s-doclaynet.pt                              # 必需 (默认后端)
├── doclayout_yolo_docstructbench_imgsz1024.pt          # 可选 (备选后端)
└── aboutYOLO11.md
```

### 6. 启动服务

```bash
# 确保在项目根目录，虚拟环境已激活
uvicorn backend.app.main:app --reload
```

服务启动后：
- Web UI：http://127.0.0.1:8000/
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/health

### 7. 运行测试

```bash
# 运行全部测试
python -m pytest

# 运行指定模块测试
python -m pytest backend/tests/test_parsers/
python -m pytest backend/tests/test_extractors/
python -m pytest backend/tests/test_agents/
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `GET` | `/` | Web UI 调试页面 |
| `POST` | `/api/upload` | 上传 PDF 并启动处理管道 |
| `GET` | `/api/task/{task_id}` | 查询任务状态和提取结果 |

**上传示例：**

```bash
curl -X POST http://127.0.0.1:8000/api/upload \
  -F "file=@your_document.pdf"
# 返回 {"task_id": "xxx-xxx-xxx"}
```

**查询结果：**

```bash
curl http://127.0.0.1:8000/api/task/{task_id}
```

## 开发进度

| 阶段 | 功能 | 状态 |
|------|------|------|
| Phase 1 | 基础设施 + PDF/OFD 解析 | 已完成 |
| Phase 2 | YOLO 版面检测 + 分块提取 | 已完成 |
| Phase 3 | 提取审核 + 多栏合并排序 | 开发中 |
| Phase 4 | Markdown/Word 导出 | 规划中 |
| Phase 5 | Vue 前端 + 生产化 API | 规划中 |

## License

MIT

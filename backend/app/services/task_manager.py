import uuid
from typing import Any, Literal, Optional

from backend.app.state import PageResult

TaskStatus = Literal[
    "pending", "chunking", "extracting", "reviewing",
    "merging", "exporting", "completed", "failed",
]

VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"chunking", "failed"},
    "chunking": {"extracting", "failed"},
    "extracting": {"reviewing", "failed"},
    "reviewing": {"extracting", "merging", "failed"},  # 支持审核循环回退到 extracting
    "merging": {"exporting", "failed"},
    "exporting": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


class TaskManager:
    """MVP: 内存 dict 存储。预留 SQLite 适配器接口。"""

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}

    def create_task(self, file_path: str, doc_type: str = "other") -> str:
        task_id = uuid.uuid4().hex[:12]
        self._tasks[task_id] = {
            "task_id": task_id,
            "file_path": file_path,
            "doc_type": doc_type,
            "status": "pending",
            "error_message": None,
            "pages": {},
            "created_at": None,
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        return self._tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        error_message: Optional[str] = None,
    ) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        current = task["status"]
        if new_status != "failed" and new_status not in VALID_TRANSITIONS.get(current, set()):
            raise ValueError(f"Invalid transition: {current} -> {new_status}")
        task["status"] = new_status
        if error_message:
            task["error_message"] = error_message

    def delete_task(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def set_page_result(self, task_id: str, page_num: int, page: dict) -> None:
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task {task_id} not found")
        task["pages"][page_num] = page

    def get_page_result(self, task_id: str, page_num: int) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return task["pages"].get(page_num)

    def list_tasks(self) -> list[dict[str, Any]]:
        return list(self._tasks.values())

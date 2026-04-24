import pytest

from backend.app.services.task_manager import TaskManager, TaskStatus


def test_create_task():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf", doc_type="paper")
    assert task_id is not None
    task = mgr.get_task(task_id)
    assert task is not None
    assert task["status"] == "pending"
    assert task["file_path"] == "test.pdf"
    assert task["doc_type"] == "paper"


def test_get_task_not_found():
    mgr = TaskManager()
    assert mgr.get_task("nonexistent") is None


def test_update_task_status():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    mgr.update_task_status(task_id, "chunking")
    task = mgr.get_task(task_id)
    assert task["status"] == "chunking"


def test_update_task_status_to_failed():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    mgr.update_task_status(task_id, "failed", error_message="OOM")
    task = mgr.get_task(task_id)
    assert task["status"] == "failed"
    assert task["error_message"] == "OOM"


def test_update_task_status_invalid():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    with pytest.raises(ValueError):
        mgr.update_task_status(task_id, "invalid_status")


def test_review_loop_can_go_back_to_extracting():
    """验证审核循环：reviewing -> extracting 是合法转换。"""
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    mgr.update_task_status(task_id, "chunking")
    mgr.update_task_status(task_id, "extracting")
    mgr.update_task_status(task_id, "reviewing")
    # 审核不通过，重回 extracting
    mgr.update_task_status(task_id, "extracting")
    task = mgr.get_task(task_id)
    assert task["status"] == "extracting"


def test_delete_task():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    assert mgr.delete_task(task_id) is True
    assert mgr.get_task(task_id) is None


def test_delete_task_not_found():
    mgr = TaskManager()
    assert mgr.delete_task("nonexistent") is False


def test_set_and_get_page_result():
    mgr = TaskManager()
    task_id = mgr.create_task("test.pdf")
    page = {"page_num": 0, "image": "base64...", "width": 800, "height": 600, "chunks": []}
    mgr.set_page_result(task_id, 0, page)
    result = mgr.get_page_result(task_id, 0)
    assert result["width"] == 800
    assert result["height"] == 600


def test_list_tasks():
    mgr = TaskManager()
    id1 = mgr.create_task("a.pdf")
    id2 = mgr.create_task("b.pdf")
    tasks = mgr.list_tasks()
    assert len(tasks) == 2
    ids = {t["task_id"] for t in tasks}
    assert id1 in ids
    assert id2 in ids

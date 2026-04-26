from unittest.mock import MagicMock, patch

import httpx
import pytest

from backend.app.extractors.vlm_extractor import VLMExtractor


def _mock_api_response(text: str) -> MagicMock:
    """构建模拟 API 响应。"""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {"choices": [{"message": {"content": text}}]}
    mock.raise_for_status = MagicMock()
    return mock


def _make_extractor() -> VLMExtractor:
    """创建带有测试用 API key 的 VLMExtractor。"""
    ext = VLMExtractor()
    ext.api_key = "test-api-key"
    return ext


def test_build_prompt_default():
    ext = VLMExtractor()
    prompt = ext._build_prompt("", "")
    assert "提取" in prompt or "extract" in prompt.lower()


def test_build_prompt_with_class():
    ext = VLMExtractor()
    prompt = ext._build_prompt("Table", "")
    assert "Table" in prompt


def test_build_prompt_with_context():
    ext = VLMExtractor()
    prompt = ext._build_prompt("", "Previous extraction had table errors")
    assert "table errors" in prompt


def test_extract_calls_api_and_returns_text():
    """测试是否调用了 API 并正确返回文本内容。"""
    ext = _make_extractor()
    mock_resp = _mock_api_response("Extracted table content here")

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        result = ext.extract("fake_base64_data")
        assert result == "Extracted table content here"
        mock_post.assert_called_once()


def test_extract_request_format():
    """测试发送到 API 的请求格式是否正确。"""
    ext = _make_extractor()
    mock_resp = _mock_api_response("ok")

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        ext.extract("fake_base64_data", class_="Formula")

        call_kwargs = mock_post.call_args
        assert "json" in call_kwargs.kwargs
        payload = call_kwargs.kwargs["json"]

        assert payload["model"] == ext.model
        assert len(payload["messages"]) == 1
        content = payload["messages"][0]["content"]
        assert len(content) == 2
        assert content[0]["type"] == "image_url"
        assert "fake_base64_data" in content[0]["image_url"]["url"]
        assert content[1]["type"] == "text"
        assert "Formula" in content[1]["text"]


def test_extract_passes_class_and_context():
    """测试是否传递了类别和上下文信息。"""
    ext = _make_extractor()
    mock_resp = _mock_api_response("table data")

    with patch("httpx.post", return_value=mock_resp) as mock_post:
        ext.extract("img_b64", class_="Table", context="fix missing columns")
        payload = mock_post.call_args.kwargs["json"]
        text_part = payload["messages"][0]["content"][1]["text"]
        assert "Table" in text_part
        assert "fix missing columns" in text_part


def test_extract_api_error_raises():
    """测试 API 错误时是否抛出异常。"""
    ext = _make_extractor()
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_resp
    )

    with patch("httpx.post", return_value=mock_resp):
        with pytest.raises(httpx.HTTPStatusError):
            ext.extract("fake_base64_data")


def test_extract_strips_whitespace():
    """测试提取结果是否去除了首尾空格。"""
    ext = _make_extractor()
    mock_resp = _mock_api_response("  text with spaces  \n")

    with patch("httpx.post", return_value=mock_resp):
        result = ext.extract("fake_base64_data")
        assert result == "text with spaces"


def test_extract_raises_on_empty_api_key():
    """当 API key 为空时应抛出 ValueError。"""
    ext = VLMExtractor()
    ext.api_key = ""
    with pytest.raises(ValueError, match="QWEN_API_KEY"):
        ext.extract("fake_base64_data")

import httpx

from backend.app.config import QWEN_API_KEY, QWEN_API_URL, QWEN_MODEL


class VLMExtractor:
    """使用 Qwen3-VL-Flash VLM API 提取图像中的文本。

    通过阿里云 DashScope 端点使用 OpenAI 兼容的 API 格式。
    """

    def __init__(self) -> None:
        self.api_url = QWEN_API_URL
        self.api_key = QWEN_API_KEY
        self.model = QWEN_MODEL

    def extract(
        self,
        image_base64: str,
        class_: str = "",
        context: str = "",
    ) -> str:
        """调用 VLM API 从 base64 编码的图像中提取文本。

        参数:
            image_base64: 文档区域的 Base64 编码 PNG 图像。
            class_: 区域的显示类型（表格、公式等）。
            context: 额外上下文，例如重新提取的审核反馈。

        返回:
            提取的文本内容。
        """
        if not self.api_key:
            raise ValueError(
                "QWEN_API_KEY 未配置。请设置 QWEN_API_KEY 环境变量。"
            )

        prompt = self._build_prompt(class_, context)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.0,
        }

        response = httpx.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _build_prompt(self, class_: str, context: str) -> str:
        """构建提示词。"""
        parts = ["请精确提取图片中的所有文字内容，保持原始格式。"]
        if class_:
            parts.append(f"区域类型：{class_}。")
        if context:
            parts.append(f"上下文信息：{context}")
        return " ".join(parts)

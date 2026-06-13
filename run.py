"""
MCP 图片理解服务器

作为桥梁，让 Codex CLI (DeepSeek 纯文本模型) 能够通过 Ollama 多模态模型
(minicpm-o4.5) 理解图片内容。

功能：
- analyze_image: 分析单张图片
- analyze_images: 多图对比分析
- ocr_image: 图片文字提取
"""

import base64
import mimetypes
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

# ===== 配置 =====
OLLAMA_BASE_URL = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("VISION_MODEL", "minicpm-o4.5")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "120"))

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}

# ===== MCP 服务器 =====
mcp = FastMCP("image-understanding")


# ===== 辅助函数 =====
def is_url(path: str) -> bool:
    """判断路径是否为 URL。"""
    try:
        result = urlparse(path)
        return result.scheme in ("http", "https")
    except Exception:
        return False


async def image_to_base64(image_path: str) -> str:
    """
    将本地图片或 URL 图片转换为 Base64 编码。
    """
    if is_url(image_path):
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(image_path)
            response.raise_for_status()
            image_data = response.content
    else:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        with open(path, "rb") as f:
            image_data = f.read()

    return base64.b64encode(image_data).decode("utf-8")


async def query_ollama(
    messages: list,
    model: str = DEFAULT_MODEL,
    system_prompt: str | None = None,
) -> str:
    """
    调用 Ollama /api/chat 接口获取多模态模型回复。
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,  # 分析任务用较低温度，结果更稳定
        },
    }
    if system_prompt:
        payload["system"] = system_prompt

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

            if "message" not in result or "content" not in result["message"]:
                raise RuntimeError(f"Ollama 返回格式异常: {result}")

            return result["message"]["content"].strip()

    except httpx.ConnectError:
        return (
            f"错误：无法连接到 Ollama ({OLLAMA_BASE_URL})。\n"
            f"请确保 Ollama 正在运行。"
        )
    except httpx.TimeoutException:
        return (
            f"错误：Ollama 请求超时（{OLLAMA_TIMEOUT}秒）。\n"
            f"大图片或复杂问题可能需要更长时间，可通过 OLLAMA_TIMEOUT 环境变量调整。"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return (
                f"错误：模型 '{model}' 未找到。\n"
                f"请运行: ollama pull {model}"
            )
        return f"错误：Ollama HTTP {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"错误：调用 Ollama 时发生异常: {type(e).__name__}: {e}"


# ===== MCP Tools =====

@mcp.tool()
async def analyze_image(
    image_path: str,
    question: str = "请详细描述这张图片的内容",
) -> str:
    """
    分析单张图片，根据问题返回描述。

    Args:
        image_path: 图片路径，支持本地绝对路径 (如 C:\\photos\\img.jpg) 或 URL (如 https://example.com/img.png)
        question: 针对图片提出的具体问题，默认为"请详细描述这张图片的内容"
    """
    if not image_path or not image_path.strip():
        return "错误：请提供图片路径。"

    base64_image = await image_to_base64(image_path)

    # 检测 MIME 类型（仅用于日志/调试）
    if not is_url(image_path):
        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type = mime_type or "image/jpeg"
    else:
        mime_type = "image/url"

    messages = [
        {
            "role": "user",
            "content": question,
            "images": [base64_image],
        }
    ]

    return await query_ollama(messages)


@mcp.tool()
async def analyze_images(
    image_paths: list[str],
    question: str = "请对比分析这些图片，指出它们的相似点和不同点",
) -> str:
    """
    同时分析多张图片，用于对比或综合分析。

    Args:
        image_paths: 图片路径列表，每项可以是本地路径或 URL
        question: 关于这些图片的问题，默认为对比分析
    """
    if not image_paths:
        return "错误：请至少提供一张图片路径。"

    if len(image_paths) > 5:
        return "警告：一次最多分析5张图片，多余的将被忽略。"

    # 限制最多5张
    image_paths = image_paths[:5]

    base64_images = []
    for path in image_paths:
        b64 = await image_to_base64(path)
        base64_images.append(b64)

    messages = [
        {
            "role": "user",
            "content": question,
            "images": base64_images,
        }
    ]

    # 添加系统提示，引导模型进行对比
    system_prompt = (
        "你正在对比分析多张图片。请分别描述每张图片的内容，"
        "然后指出它们的相似点和不同点。"
    )

    return await query_ollama(messages, system_prompt=system_prompt)


@mcp.tool()
async def ocr_image(image_path: str) -> str:
    """
    从图片中提取文字（OCR 识别），支持中英文。

    Args:
        image_path: 图片路径，支持本地路径或 URL
    """
    if not image_path or not image_path.strip():
        return "错误：请提供图片路径。"

    base64_image = await image_to_base64(image_path)

    # 使用专门的 OCR 提示词
    ocr_prompt = (
        "请完整提取这张图片中的所有文字内容。\n"
        "要求：\n"
        "1. 保留原文的语言（中文、英文等）\n"
        "2. 按图片中的文字布局顺序输出\n"
        "3. 只输出提取的文字，不要添加任何解释或描述\n"
        "4. 如果图片中没有文字，请输出'图片中未检测到文字'"
    )

    messages = [
        {
            "role": "user",
            "content": ocr_prompt,
            "images": [base64_image],
        }
    ]

    return await query_ollama(messages)


# ===== 启动入口 =====

def main():
    """启动 MCP 服务器。"""
    # 启动前检查 Ollama 是否可用（非阻塞提示）
    print(f"启动 MCP 图片理解服务器...", file=sys.stderr)
    print(f"  Ollama: {OLLAMA_BASE_URL}", file=sys.stderr)
    print(f"  模型: {DEFAULT_MODEL}", file=sys.stderr)
    print(f"  超时: {OLLAMA_TIMEOUT}秒", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"准备就绪，等待 Codex CLI 调用...", file=sys.stderr)

    # 以 stdio 模式运行（MCP 标准传输方式）
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

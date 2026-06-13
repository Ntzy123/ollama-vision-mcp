
# 🖼️ MCP 图片理解服务器

基于 [MCP (Model Context Protocol)](https://modelcontextprotocol.io) 的图片理解服务器，让**纯文本模型**（如 Codex CLI / DeepSeek）也能看懂图片内容。

通过调用本地 **Ollama** 多模态模型（如 `minicpm-o4.5`）进行图片分析，无需调用任何云端视觉 API，数据完全本地处理。

---

## ✨ 功能

- **🔍 `analyze_image`** — 分析单张图片，支持自定义提问
- **🆚 `analyze_images`** — 多图（最多 5 张）对比分析
- **📝 `ocr_image`** — 从图片中提取文字（支持中英文）
- **🔄 支持本地图片和 URL 图片**

---

## 📋 前置要求

| 组件 | 说明 |
|------|------|
| Python 3.10+ | 运行环境 |
| [Ollama](https://ollama.com) | 本地多模态模型服务 |
| 多模态模型 | 如 `minicpm-o4.5`、`llava`、`gemma3` 等 |

安装 Ollama 并拉取模型：

```bash
ollama pull minicpm-o4.5
```

---

## 🚀 快速开始

### 1️⃣ 安装依赖

**方式一：运行脚本（推荐）**

```bash
setup.bat
```

**方式二：手动安装**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ 启动 Ollama（如未运行）

```bash
ollama serve
```

### 3️⃣ 配置 MCP JSON

在 MCP 客户端（如 **Codex CLI** / **Claude Desktop** / **Cursor** 等）的配置文件中，添加以下条目：

```json
{
  "mcpServers": {
    "image-understanding": {
      "command": "python",
      "args": ["F:/path/to/my-image-server/run.py"],
      "env": {
        "OLLAMA_HOST": "http://localhost:11434",
        "VISION_MODEL": "minicpm-o4.5",
        "OLLAMA_TIMEOUT": "120"
      }
    }
  }
}
```

> ⚠️ 将 `F:/path/to/my-image-server` 替换为你项目所在的**实际路径**。

#### 📁 不同客户端的配置位置

| 客户端 | 配置文件路径 |
|--------|------------|
| **Codex CLI** | `~/.codex/config.json` |
| **Claude Desktop** | Settings → Developer → Edit Config → `claude_desktop_config.json` |
| **Cursor** | Settings → Features → MCP → Add new MCP server |

---

## ⚙️ 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 服务地址 |
| `VISION_MODEL` | `minicpm-o4.5` | 使用的多模态模型名称 |
| `OLLAMA_TIMEOUT` | `120` | 请求超时时间（秒），大图片可适当调大 |

也可以直接在命令行中临时设置：

```bash
set OLLAMA_HOST=http://localhost:11434
set VISION_MODEL=llava
python run.py
```

---

## 🧩 提供的 MCP Tools

### `analyze_image`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_path` | string | ✅ | 本地路径或 URL |
| `question` | string | ❌ | 针对图片的问题，默认"请详细描述这张图片的内容" |

### `analyze_images`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_paths` | string[] | ✅ | 图片路径列表（最多 5 张） |
| `question` | string | ❌ | 对比分析问题 |

### `ocr_image`

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image_path` | string | ✅ | 本地路径或 URL |

---

## 💡 在对话中使用示例

```text
> 分析这张图片：C:\photos\cat.jpg
> 对比这两张图有什么不同：img1.png 和 img2.png
> 提取这张截图里的所有文字：screenshot.png
> 这个网页截图里的按钮是做什么的？https://example.com/screenshot.png
```

---

## 🏗️ 项目结构

```
my-image-server/
├── run.py              # MCP 服务器主程序
├── requirements.txt    # Python 依赖
├── setup.bat           # Windows 环境初始化脚本
├── venv/               # Python 虚拟环境
└── README.md           # 本文件
```

---

## 📄 License

MIT


@echo off
chcp 65001 >nul 2>&1

REM 检查pip最新版本

set /p choice="是否更换pip清华源？(y/n，默认n): "
if /i "%choice%"=="y" (
    python -m pip install --upgrade pip
    pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
) else if /i "%choice%"=="n" (
    REM
) else (
    REM
)


if not exist venv (
    echo "正在创建虚拟环境"
    python -m venv venv
    echo "venv环境创建成功！"
    timeout /t 2 >nul
)

REM 激活虚拟环境并安装依赖包
call venv\Scripts\activate
echo "正在检查并安装依赖包"
python -m pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "============================"
echo "MCP 图片理解服务器 环境设置完成！"
echo "============================"
echo ""
echo "使用方式："
echo "  直接运行：python run.py"
echo "  或在 Codex CLI 的 mcpServers 中配置："
echo '    "image-understanding": {'
echo '      "command": "python",'
echo '      "args": ["%cd%\\run.py"]'
echo '    }'
echo ""
pause

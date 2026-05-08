#!/bin/bash
# Yang RAG System 启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
source venv/bin/activate
pip install -q -r requirements.txt

# 启动服务器
echo "启动 Yang RAG API..."
echo "API 文档: http://localhost:8000/docs"
echo ""
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

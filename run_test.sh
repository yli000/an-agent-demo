#!/usr/bin/env bash
set -e
# 在仓库根目录加载本地环境配置并运行入口。
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p log
if [ -f config/config.ini ]; then
  source config/config.ini
fi
export PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export ENTRY_URL="${ENTRY_URL:-http://127.0.0.1:8080}"
python test.py

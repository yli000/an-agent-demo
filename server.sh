#!/usr/bin/env bash
set -e
# 使用当前 Python 环境；Redis 需要事先启动。
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p log
if [ -f config/config.ini ]; then
  source config/config.ini
fi
export PYTHONPATH="$PROJECT_DIR${PYTHONPATH:+:$PYTHONPATH}"
export REJECT_URL="${REJECT_URL:-http://127.0.0.1:8007/reject-server/v1}"
export INTENT_URL="${INTENT_URL:-http://127.0.0.1:8008/intent-server/v1}"
export NLU_URL="${NLU_URL:-http://127.0.0.1:8009/chatnlu-server/v1}"
export ENTRY_URL="${ENTRY_URL:-http://127.0.0.1:8080}"

# 分别启动拒识、意图召回、NLU 和对话入口。
(cd train && nohup python reject_infer.py > ../log/reject.log 2>&1 &)
(cd train && nohup python intent_infer.py > ../log/intent.log 2>&1 &)
(cd function_call && nohup python chatnlu_infer.py > ../log/nlu.log 2>&1 &)
nohup python start.py > log/start.log 2>&1 &

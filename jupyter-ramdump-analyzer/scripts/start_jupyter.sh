#!/usr/bin/env bash
# JupyterLab 시작 스크립트
# - venv 활성화
# - configs/jupyter_ai_openrouter.env에서 API 키 로드
# - Jupyternaut(OPENROUTER_API_KEY)과 %%ai 매직(OPENAI_API_KEY+OPENAI_API_BASE) 모두 설정
# - 추가 인자는 jupyter lab으로 전달 (예: --port 8889)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../configs/jupyter_ai_openrouter.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: $ENV_FILE not found."
    echo "  cp configs/jupyter_ai_openrouter.env.example configs/jupyter_ai_openrouter.env"
    echo "  then fill in your OPENROUTER_API_KEY."
    exit 1
fi

# venv 활성화
source ~/jupyter-ai-env/bin/activate

# env 파일 로드 (기존 환경변수를 덮어쓰지 않음)
set -a
source "$ENV_FILE"
set +a

# %%ai 매직용 OpenAI-compatible 변수 설정 (env 파일에 없으면 OpenRouter 키로 채움)
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-${OPENAI_API_KEY:-}}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-$OPENROUTER_API_KEY}"
export OPENAI_API_BASE="${OPENAI_API_BASE:-https://openrouter.ai/api/v1}"

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "ERROR: OPENROUTER_API_KEY is not set in $ENV_FILE"
    exit 1
fi

echo "Starting JupyterLab..."
echo "  OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:12}..."
echo "  OPENAI_API_BASE:    $OPENAI_API_BASE"
exec jupyter lab "$@"

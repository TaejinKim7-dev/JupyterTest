#!/bin/bash
# Simple launcher for the memory dump debugging chatbot

# Source environment variables
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SCRIPT_DIR/configs/jupyter_ai_openrouter.env"

# Launch JupyterLab with the debug chatbot notebook
echo "Starting JupyterLab with Debug Chatbot..."
echo "Environment variables loaded from: $SCRIPT_DIR/configs/jupyter_ai_openrouter.env"
echo "Model: $OPENAI_MODEL"
echo ""

jupyter lab "$SCRIPT_DIR/notebooks/debug_chatbot.ipynb" --no-browser --ip=0.0.0.0 --port=8888
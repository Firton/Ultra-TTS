#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python_bin="python3"
if [ -x ".venv/bin/python" ]; then
  python_bin=".venv/bin/python"
fi

exec "$python_bin" web_app.py --host 127.0.0.1 --port 8765 --open

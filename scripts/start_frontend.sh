#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../frontend"
if command -v node >/dev/null 2>&1; then
  exec node node_modules/vite/bin/vite.js --host 127.0.0.1
fi
runtime="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node"
exec "$runtime" node_modules/vite/bin/vite.js --host 127.0.0.1

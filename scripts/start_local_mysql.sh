#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
base="$PWD/.runtime/mysql-8.4.11-macos15-arm64"
if [[ ! -x "$base/bin/mysqld" ]]; then
  printf '%s\n' 'This helper is for the preinstalled macOS instance. On other computers start your installed MySQL service and follow README.md.'
  exit 1
fi
exec "$base/bin/mysqld" --no-defaults --basedir="$base" --datadir="$PWD/.runtime/mysql84-data" --port=3307 --bind-address=127.0.0.1 --socket=/private/tmp/caretrack-mysql.sock --mysqlx=0 --pid-file="$PWD/.runtime/mysql.pid" --log-error="$PWD/.runtime/mysql.log"

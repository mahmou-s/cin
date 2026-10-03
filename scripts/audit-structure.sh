#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "CIN Engineering Structure Audit"
echo "root=$ROOT"
printf 'files='; find . -type f -not -path './.git/*' -not -path './.pytest_cache/*' | wc -l
printf 'python='; find . -name '*.py' -not -path './.git/*' -not -path './.pytest_cache/*' | wc -l
printf 'js_ts='; find . \( -name '*.js' -o -name '*.ts' -o -name '*.tsx' \) -not -path './.git/*' -not -path './.pytest_cache/*' | wc -l
printf 'migrations='; find apps/api/migrations/versions -name '*.py' | wc -l
printf 'migration_head='; grep -R '^revision' apps/api/migrations/versions/*.py | tail -1
printf 'compose_services='; awk '/^  [a-zA-Z0-9_-]+:$/ {c++} END{print c+0}' docker-compose.yml

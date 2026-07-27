#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
"$project_dir/.venv/bin/pytest" "$@"
"$project_dir/.venv/bin/ruff" check "$project_dir/src" "$project_dir/tests"
"$project_dir/.venv/bin/mypy" "$project_dir/src"

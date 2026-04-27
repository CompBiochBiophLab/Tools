#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "Activate the tcrtools conda environment first: conda activate tcrtools" >&2
  exit 1
fi

unset PYTHONPATH
unset PYTHONHOME
unset PYMOL_PATH
unset PYMOL_DATA
export PYTHONNOUSERSITE=1

exec "$CONDA_PREFIX/bin/pymol" "$@"

#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DATASETS_ROOT="${PROJECT_ROOT}/Datasets"
ENV_PREFIX="${DATASETS_ROOT}/envs/kiise-vlmdb"

mkdir -p \
  "${DATASETS_ROOT}/envs" \
  "${DATASETS_ROOT}/models/huggingface" \
  "${DATASETS_ROOT}/models/manual" \
  "${DATASETS_ROOT}/cache/huggingface" \
  "${DATASETS_ROOT}/cache/torch" \
  "${DATASETS_ROOT}/cache/transformers" \
  "${DATASETS_ROOT}/logs/setup"

export HF_HOME="${DATASETS_ROOT}/cache/huggingface"
export HF_HUB_CACHE="${DATASETS_ROOT}/models/huggingface"
export TRANSFORMERS_CACHE="${DATASETS_ROOT}/cache/transformers"
export TORCH_HOME="${DATASETS_ROOT}/cache/torch"

if [[ ! -d "${ENV_PREFIX}" ]]; then
  conda create -y -p "${ENV_PREFIX}" python=3.10 pip
fi

conda run -p "${ENV_PREFIX}" python -m pip install --upgrade pip
conda run -p "${ENV_PREFIX}" python -m pip install \
  --extra-index-url https://download.pytorch.org/whl/cu121 \
  -r "${PROJECT_ROOT}/2026_KIISE/env/experiment_requirements.txt" \
  2>&1 | tee "${DATASETS_ROOT}/logs/setup/pip_install_$(date +%Y%m%d_%H%M%S).log"

cat <<EOF
Environment ready.

Activate:
  conda activate ${ENV_PREFIX}

Runtime exports:
  export HF_HOME=${HF_HOME}
  export HF_HUB_CACHE=${HF_HUB_CACHE}
  export TRANSFORMERS_CACHE=${TRANSFORMERS_CACHE}
  export TORCH_HOME=${TORCH_HOME}
  export PYTHONPATH=${PROJECT_ROOT}/2026_KIISE/src:\${PYTHONPATH:-}
EOF

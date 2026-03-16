#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-bioinformatics}"
REPO_URL="https://github.com/dauparas/ProteinMPNN.git"

if ! command -v conda >/dev/null 2>&1; then
  echo "conda was not found in PATH." >&2
  exit 1
fi

if ! conda env list | awk '{print $1}' | grep -Fxq "${ENV_NAME}"; then
  echo "Conda environment '${ENV_NAME}' does not exist." >&2
  exit 1
fi

ENV_PREFIX="$(conda run -n "${ENV_NAME}" python -c 'import sys; print(sys.prefix)')"
INSTALL_ROOT="${ENV_PREFIX}/opt/proteinmpnn"
ACTIVATE_DIR="${ENV_PREFIX}/etc/conda/activate.d"
DEACTIVATE_DIR="${ENV_PREFIX}/etc/conda/deactivate.d"
WRAPPER="${ENV_PREFIX}/bin/proteinmpnn_run"

echo "Using conda environment: ${ENV_NAME}"
echo "Environment prefix: ${ENV_PREFIX}"
echo "ProteinMPNN install root: ${INSTALL_ROOT}"

conda install -n "${ENV_NAME}" -y -c conda-forge \
  biopython matplotlib networkx numpy pandas requests jupyterlab git
conda install -n "${ENV_NAME}" -y -c pytorch pytorch

mkdir -p "${INSTALL_ROOT}"
if [ -d "${INSTALL_ROOT}/.git" ]; then
  git -C "${INSTALL_ROOT}" fetch --depth 1 origin main
  git -C "${INSTALL_ROOT}" checkout main
  git -C "${INSTALL_ROOT}" pull --ff-only origin main
else
  rm -rf "${INSTALL_ROOT}"
  git clone --depth 1 "${REPO_URL}" "${INSTALL_ROOT}"
fi

mkdir -p "${ACTIVATE_DIR}" "${DEACTIVATE_DIR}"

cat > "${ACTIVATE_DIR}/proteinmpnn.sh" <<EOF
export PROTEINMPNN_HOME="${INSTALL_ROOT}"
EOF

cat > "${DEACTIVATE_DIR}/proteinmpnn.sh" <<'EOF'
unset PROTEINMPNN_HOME
EOF

cat > "${WRAPPER}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${ENV_PREFIX}/bin/python" "${INSTALL_ROOT}/protein_mpnn_run.py" "\$@"
EOF
chmod +x "${WRAPPER}"

echo
echo "ProteinMPNN is installed outside the repository."
echo "Reactivate the conda environment before running notebooks:"
echo "  conda activate ${ENV_NAME}"
echo
echo "Environment variable configured on activation:"
echo "  PROTEINMPNN_HOME=${INSTALL_ROOT}"
echo
echo "Wrapper command available inside the environment:"
echo "  proteinmpnn_run --help"

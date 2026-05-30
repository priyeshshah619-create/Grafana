#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist/lambdas"

mkdir -p "${OUT_DIR}"

for source_file in "${ROOT_DIR}"/lambda/*.py; do
  name="$(basename "${source_file}" .py)"
  artifact="${OUT_DIR}/${name}.zip"
  staging_dir="$(mktemp -d)"
  cp "${source_file}" "${staging_dir}/handler.py"
  rm -f "${artifact}"
  (cd "${staging_dir}" && zip -qr "${artifact}" handler.py)
  rm -rf "${staging_dir}"
  echo "Packaged ${artifact}"
done

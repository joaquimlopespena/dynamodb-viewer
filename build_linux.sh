#!/bin/bash
# Gera instalável/executável do DynamoDB Viewer para Linux
# Opções: 1) pip install (pacote)  2) PyInstaller (executável standalone)

set -e
cd "$(dirname "$0")"
APP_NAME="dynamodb-viewer"
VERSION="${VERSION:-1.0.0}"
DIST_DIR="dist"
BUILD_DIR="build"

usage() {
    echo "Uso: $0 [pip|pyinstaller|all]"
    echo ""
    echo "  pip         Cria apenas o pacote instalável (wheel) em dist/"
    echo "  pyinstaller Gera executável standalone em dist/ (requer PyInstaller)"
    echo "  all         Faz os dois (padrão)"
    echo ""
    echo "Exemplos:"
    echo "  $0              # gera wheel e executável"
    echo "  $0 pip          # só wheel: pip install dist/dynamodb_viewer-*.whl"
    echo "  $0 pyinstaller  # só executável em dist/"
}

build_wheel() {
    echo ">>> Gerando pacote wheel..."
    mkdir -p "${DIST_DIR}"
    python3 -m pip install --upgrade build 2>/dev/null || true
    python3 -m build --wheel --outdir "${DIST_DIR}"
    echo ">>> Wheel em: ${DIST_DIR}/"
    ls -la "${DIST_DIR}"/*.whl 2>/dev/null || true
}

build_pyinstaller() {
    echo ">>> Gerando executável com PyInstaller..."
    # Usar python -m PyInstaller (funciona sem 'pyinstaller' no PATH)
    if [ -d ".venv" ]; then
        .venv/bin/python -m pip install pyinstaller 2>/dev/null || true
        .venv/bin/python -m PyInstaller --noconfirm dynamodb_viewer.spec
    else
        python3 -m pip install pyinstaller 2>/dev/null || true
        python3 -m PyInstaller --noconfirm dynamodb_viewer.spec
    fi
    mkdir -p "${DIST_DIR}"
    cp -f dist/dynamodb-viewer "${DIST_DIR}/" 2>/dev/null || true
    echo ">>> Executável em: ${DIST_DIR}/dynamodb-viewer"
}

case "${1:-all}" in
    pip)        build_wheel ;;
    pyinstaller) build_pyinstaller ;;
    all)        build_wheel; build_pyinstaller ;;
    -h|--help)  usage; exit 0 ;;
    *)          echo "Opção inválida: $1"; usage; exit 1 ;;
esac

echo ""
echo "Concluído."

#!/usr/bin/env bash
# Hook: TaskCompleted
# Se ejecuta cuando un teammate intenta marcar una tarea como completa.
# Exit code 0 = aceptar completitud
# Exit code 2 = rechazar completitud y enviar feedback al teammate

set -uo pipefail

echo "=== Verificando calidad antes de completar tarea ==="

# Verificar Python con Ruff
if [ -f "ruff.toml" ]; then
  echo "--- Ruff (Python) ---"
  ruff check . --quiet 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "ERROR: Ruff ha encontrado errores. Corrigelos antes de completar."
    exit 2
  fi
  echo "Ruff: OK"
fi

# Verificar TypeScript con ESLint
if [ -f ".eslintrc.js" ]; then
  echo "--- ESLint (TypeScript) ---"
  npx eslint . --quiet 2>/dev/null
  if [ $? -ne 0 ]; then
    echo "ERROR: ESLint ha encontrado errores. Corrigelos antes de completar."
    exit 2
  fi
  echo "ESLint: OK"
fi

# Tests Python
for pkg in packages/pid-converter packages/pid-knowledge-graph packages/pid-rag; do
  if [ -d "$pkg/tests" ] && [ "$(ls -A $pkg/tests 2>/dev/null)" ]; then
    echo "--- Tests: $pkg ---"
    (cd "$pkg" && python -m pytest tests/ --quiet 2>/dev/null)
    if [ $? -ne 0 ]; then
      echo "ERROR: Tests fallando en $pkg. Corrigelos antes de completar."
      exit 2
    fi
    echo "$pkg: OK"
  fi
done

# Tests TypeScript
for pkg in packages/pid-web packages/pid-mcp-server; do
  if [ -f "$pkg/package.json" ] && grep -q '"test"' "$pkg/package.json" 2>/dev/null; then
    echo "--- Tests: $pkg ---"
    (cd "$pkg" && npm run test --silent 2>/dev/null)
    if [ $? -ne 0 ]; then
      echo "ERROR: Tests fallando en $pkg. Corrigelos antes de completar."
      exit 2
    fi
    echo "$pkg: OK"
  fi
done

echo "=== Verificacion completada: OK ==="
exit 0

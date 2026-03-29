#!/usr/bin/env bash
# Hook: TeammateIdle
# Se ejecuta cuando un teammate se queda sin trabajo.
# Exit code 0 = dejar que se quede inactivo
# Exit code 2 = mantener al teammate trabajando con feedback

REMAINING=$(grep -rn "TODO\|FIXME\|HACK" packages/ e2e/ 2>/dev/null | grep -v node_modules | grep -v __pycache__ | wc -l)

if [ "$REMAINING" -gt 0 ]; then
  echo "Hay $REMAINING TODOs/FIXMEs pendientes en el proyecto:"
  echo ""
  grep -rn "TODO\|FIXME\|HACK" packages/ e2e/ 2>/dev/null | grep -v node_modules | grep -v __pycache__ | head -20
  echo ""
  echo "Revisa si puedes resolver alguno dentro de tu scope."
  exit 2
fi

exit 0

# Configuración de Agent Teams

## settings.local.json

Archivo: `.claude/settings.local.json`

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/verify-task.sh",
            "timeout": 30000
          }
        ]
      }
    ],
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/check-remaining.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

## Hook: verify-task.sh

Se ejecuta cuando un teammate intenta marcar una tarea como completa.
Si el linter o los tests fallan, rechaza la completitud (exit code 2).

```bash
#!/usr/bin/env bash
npm run lint --silent 2>/dev/null
if [ $? -ne 0 ]; then
  echo "El linter ha encontrado errores. Corrígelos antes de completar."
  exit 2
fi

npm test --silent 2>/dev/null
if [ $? -ne 0 ]; then
  echo "Hay tests fallando. Corrígelos antes de completar."
  exit 2
fi

exit 0
```

## Hook: check-remaining.sh

Se ejecuta cuando un teammate se queda sin trabajo.
Si hay TODOs pendientes en su scope, le asigna más trabajo.

```bash
#!/usr/bin/env bash
REMAINING=$(grep -r "TODO\|FIXME\|HACK" src/ tests/ 2>/dev/null | wc -l)

if [ "$REMAINING" -gt 0 ]; then
  echo "Hay $REMAINING TODOs/FIXMEs pendientes. Revisa si puedes resolver alguno dentro de tu scope."
  exit 2
fi

exit 0
```

## Hooks Disponibles en Agent Teams

| Hook | Cuándo se ejecuta | Exit code 2 significa |
|------|-------------------|----------------------|
| `TaskCompleted` | Un teammate marca tarea como completa | Rechazar completitud, enviar feedback |
| `TeammateIdle` | Un teammate se queda sin trabajo | Mantener al teammate trabajando |
| `SubagentStart` | Se lanza un nuevo teammate | Inyectar contexto adicional |
| `SubagentStop` | Un teammate se detiene | Ejecutar limpieza |

## Modos de Visualización

- **In-process** (por defecto): Todo en la misma terminal. Shift+Up/Down para cambiar entre teammates.
- **Split-pane (tmux)**: Cada teammate en un panel separado. Requiere tmux instalado.
- **Split-pane (iTerm2)**: Similar pero usando paneles de iTerm2.

Para forzar tmux: `export CLAUDE_CODE_SPAWN_BACKEND=tmux`

## Controles del Lead

| Acción | Cómo |
|--------|------|
| Activar delegate mode | Shift+Tab (el lead solo coordina, no programa) |
| Ver teammate | Shift+Down para seleccionar, Enter para ver sesión |
| Interrumpir teammate | Escape mientras ves su sesión |
| Enviar mensaje directo | Seleccionar teammate y escribir |

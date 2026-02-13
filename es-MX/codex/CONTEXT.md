# Motor Python — Instantánea del Contexto (2025-10-02)

Este archivo captura el contexto actual de tiempo de ejecución/CLI/prueba para que el trabajo pueda continuar sin problemas después de un reinicio en frío. Señala los archivos correctos, resume los comportamientos importantes para la compatibilidad e incluye comandos reproducibles utilizados durante el desarrollo.

## Resumen
- Referencia canónica: scion-core (Node) a través de `tools/scion-runner/scion-trace.cjs`
- Núcleo del tiempo de ejecución de Python: `py/scjson/context.py` (DocumentContext)
- Subsistema de invocación: `py/scjson/invoke.py`
- Eventos/cola: `py/scjson/events.py`
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`)
- Comparación de trazas: `py/exec_compare.py` (solo hojas + normalización step-0)
- Pruebas: `py/tests/*` (núcleo del motor en `py/tests/test_engine.py`)
- Documentos/PENDIENTES: `docs/TODO-ENGINE-PY.md`, diseño detallado: `py/scjson/ENGINE.md`

Restricciones del entorno
- Python está preconfigurado; no ejecutar pip/poetry
- La entrada CLI de JavaScript es `js/dist/index.js`; ejecutar `npm run build` antes de usar Node CLI en pruebas uber

Novedades recientes (implementadas)
- Normalización de comparación de ejecución: elimina `datamodelDelta` y `firedTransitions` de step-0; `--keep-step0-states` opcionalmente mantiene `enteredStates`/`exitedStates` de step-0.
- Semántica de error: alias genérico `error` emitido junto con `error.execution` (no para `error.communication`) para admitir gráficos que escuchan `error.*`.
- Semántica de asignación: la asignación a una ubicación inexistente encola `error.execution` y no crea variables (habilita W3C test401).
- Coincidencia de eventos: las transiciones admiten nombres separados por espacios, comodín `*` y patrones de prefijo como `error.*`.
- Fallo de `Invoke src` (hijo scxml/scjson): emite `error.communication`.
- Ciclo de vida de Invoke: inicio al final del macrostep; envíos padre↔hijo a través de `#_parent`, `#_child`/`#_invokedChild`, explícito `#_<invokeId>`; `finalize` se ejecuta en el estado de invocación y establece `_event`.
- Temporizadores: `<send>` retrasado determinista a través de `DocumentContext.advance_time`, con soporte para tokens de control de avance de tiempo a mitad de secuencia.

Semántica estable (implementada previamente)
- Macrostep/microstep, conjuntos de entrada/salida a través de LCA
- Orden de finalización paralela + finalización de región
- Historial: superficial + profundo (profundo restaura hojas descendientes exactas)
- Contenido ejecutable: assign, log, raise, if/elseif/else, foreach, send, cancel, script (advertencia de no-op)
- Eventos de error: `error.execution` push-front; envíos externos producen `error.communication`

Dónde buscar (punteros de archivo)
- Núcleo del motor: `py/scjson/context.py`
  - Selección de transición con multi-evento + comodín: `_select_transition`
  - Ejecutar transiciones: `_fire_transition`, `_run_actions`, `_iter_actions`
  - Historial, entrada/salida: `_enter_state`, `_exit_state`, `_enter_history`, `_handle_entered_final`
  - Ayudante de error: `_emit_error`
  - Asignar/enviar/cancelar: `_do_assign`, `_do_send`, `_do_cancel`
  - Ciclo de vida de Invoke: `_start_invocations_for_state`, `_start_invocations_for_active_states`, `_on_invoke_done`, `_cancel_invocations_for_state`
  - Expresiones: `_scope_env`, `_evaluate_expr` (evaluación segura por defecto; `allow_unsafe_eval` opcional)
  - Temporizadores: `_schedule_event`, `_release_delayed_events`, `advance_time`
- Invocadores: `py/scjson/invoke.py`
  - Manejadores: mock:immediate, mock:record, mock:deferred, scxml/scjson child
  - Eventos de burbujeo hijo con metadatos de E/S de eventos SCXML (`origintype`, `invokeid`)
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`) con `--xml`, `--lax/--strict`, `--unsafe-eval`, `--max-steps`, `--advance-time`
- Comparar: `py/exec_compare.py` (normalización de solo hojas, eliminación de ruido de step-0, eliminación opcional de estados de step-0)
- Eventos: `py/scjson/events.py` (Event lleva `origin`, `origintype`, `invokeid`)
 - Envoltorio para pruebas que esperan ruta: `py/py/exec_compare.py`

## Comandos de Reproducción
Pruebas unitarias (Python)
- `PYTHONPATH=py pytest -q py/tests`
- Prueba única: `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_name`
 - Smoke parametrizado sobre gráficos tutoriales (una prueba por gráfico):
   - Todos: `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
   - Filtrar por nombre: `PYTHONPATH=py pytest -q -k "executes_chart and history_shallow.scxml"`

Resultado del motor (gráficos W3C)
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- Lo mismo para: 338, 422, 554 → resultado actual: pasa
- 401 (precedencia de error genérico) ahora pasa debido a la semántica de asignación inválida + alias:
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Comparación de trazas con referencia
- Primario: `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Valores predeterminados: el ejecutor de referencia `node tools/scion-runner/scion-trace.cjs` cuando esté disponible
- Opcional: `--keep-step0-states` para preservar `enteredStates`/`exitedStates` de step-0
- Anulación de entorno: `SCJSON_REF_ENGINE_CMD` para proporcionar un comando de referencia

Configuración del ejecutor de Node (si es necesario)
- El repositorio incluye `tools/scion-runner/scion-trace.cjs` y `node_modules`.
- Usar directamente: `node tools/scion-runner/scion-trace.cjs --help`

## Estado Actual y Verificaciones
Suite de unidades del motor
- Estado: verde (las pruebas de Python pasan)
- Las verificaciones enfocadas incluyen: historial profundo, orden de finalización paralela, normalización de contenido de envío, prioridad de eventos de error, alcance de finalización de invocación, direccionamiento explícito `#_<invokeId>`, coincidencia de patrones de eventos, manejo de tokens de control CLI e inyección de avance de tiempo de vector.

Aspectos destacados de W3C/Tutorial
- W3C obligatorio: 253/338/422/554 pasan con `--advance-time 3`
- W3C obligatorio: 401 ahora pasa (asignación inválida → `error.execution` + alias `error` asegura la precedencia de error genérico)
- Gráficos tutoriales del modelo de datos de Python descubiertos: 208
- Muestra ad-hoc de 50 gráficos python-datamodel: no hay fallos en la construcción de trazas (`DocumentContext.from_xml_file(...).trace_step()`)

Mantenimiento de la lista de omisión
- `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED` ya no incluye W3C test401
- Las entradas restantes son pruebas opcionales no relacionadas con el alcance actual (procesadores HTTP, etc.)

## Notas de Comportamiento
Normalización de trazas de Step-0
- Los motores difieren en la visibilidad de la transición inicial; la normalización elimina `datamodelDelta` y `firedTransitions` de step-0 por defecto
- Opcionalmente, elimine también las listas de entrada/salida de step-0 para reducir el ruido de la diferencia

Coincidencia de eventos
- Acepta nombres de eventos separados por espacios, comodín `*` y prefijo `error.*`

Orden de eventos de error
- `error.execution` es push-front; también emite un `error` genérico (no push-front por defecto a menos que sea explícitamente necesario para preservar la semántica de ordenación de entrada)
- `error.communication` no emite alias para evitar la intercalación con eventos explícitos

Invocar
- `Finalize` se ejecuta en el estado de invocación con el diccionario `_event` (`name`, `data`, `invokeid` y cualquier origen/origintype)
- El orden de `Done` por defecto es específico por ID y luego genérico; la preferencia se ajusta cuando los hijos emiten eventos durante la inicialización para preservar el orden observado
- Inicio al final del macrostep: solo para estados que aún están activos al final del step

## Lo que cambió en esta sesión
- engine-trace: acepta tokens de control `{"advance_time": N}` en eventos JSONL; avanza el reloj simulado sin emitir un paso.
- vector_gen: inyecta tokens de control `advance_time` entre estímulos cuando hay temporizadores pendientes después de un paso.
- Pruebas: se agregó una prueba de token de control CLI; se agregaron gráficos de `sweep_corpus` curados y pruebas `exec_compare` avanzadas.
- Envoltorio: se agregó `py/py/exec_compare.py` para pruebas que invocan esa ruta.
- uber_test: pruebas por gráfico parametrizadas para una retroalimentación más rápida; `python py/uber_test.py --python-smoke` imprime el progreso y el estado por gráfico.
- Documentos: `docs/ENGINE-PY.md` actualizado con tokens de control, inyección de avance de tiempo de vector y semántica de invocación/finalización.
- Orden del motor: se agregó una política de `ordenamiento` explícita con el modo `scion`. En el modo `scion`, las emisiones hijo→padre se encolan normalmente, mientras que `done.invoke` se empuja al frente (genérico antes que específico por ID) para alinearse con el comportamiento de microstep de [SCION](https://www.npmjs.com/package/scion).

## Próximos pasos (sugeridos)
- Opcional: marcar las pruebas `uber` parametrizadas `@pytest.mark.slow` para excluirlas de las ejecuciones predeterminadas; preferir filtros `-k` específicos para la iteración.
- Ampliar el corpus curado; desarrollar heurísticas de vectores para una cobertura más profunda.

## Lista de verificación de reanudación rápida
- Ejecutar suite de unidades: `PYTHONPATH=py pytest -q py/tests`
- Verificar conjunto rápido de W3C: 253/338/422/554/401 con `engine-verify`
- Para diferencias con la referencia, usar `py/exec_compare.py` con o sin `--keep-step0-states`
- Al editar el comportamiento de invocación/hijo, volver a probar:
  - `py/tests/test_engine.py::test_invoke_*`
  - pruebas de burbujeo hijo y orden de finalización
 - Smoke de Python con progreso:
   - `python py/uber_test.py --python-smoke`
   - `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`

Grep rápido
- `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py` para ir al código relevante
 - `rg -n "advance_time|control token|advance-time" py`

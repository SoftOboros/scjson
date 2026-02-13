# Convergencia del Motor Python — Instantánea de Contexto Expandido (2025-10-02)

Esta instantánea expandida está diseñada para acelerar la reanudación después de un reinicio en frío. Captura lo que importa en este momento: dónde viven las cosas, qué cambió, cómo reproducir y qué hacer a continuación.

## Reanudación Rápida
- Ejecutar pruebas unitarias: `PYTHONPATH=py pytest -q py/tests`
- Habilitar el "smoke test" lento explícitamente: `PYTHONPATH=py pytest -q -m slow -k "uber_test and executes_chart"`
- "Smoke test" parametrizado (una prueba por cada tutorial):
  - Todos: `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
  - Filtrar por nombre: `PYTHONPATH=py pytest -q -k "executes_chart and parallel_invoke_complete.scxml"`
- "Smoke test" CLI con salida de progreso:
  - Todos: `python py/uber_test.py --python-smoke`
  - Un solo gráfico: `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`
- Verificar resultados W3C (avanzar temporizadores):
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
  - Repetir para 338, 422, 554 → esperado: aprobado
  - 401 (precedencia de error genérico): `--xml` (sin avance) → esperado: aprobado
- Comparar rastros con la referencia (solo hojas + normalización de paso 0):
  - `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
  - Opcional: `--keep-step0-states` para preservar los estados de entrada/salida del paso 0

## Puntos de Referencia del Repositorio (Qué/Dónde)
- Núcleo del motor: `py/scjson/context.py`
  - Macro/Microstep, selección de transición: `_select_transition`
  - Entrada/Salida e Historial: `_enter_state`, `_exit_state`, `_enter_history`, `_handle_entered_final`
  - Contenido ejecutable: `_run_actions`, `_iter_actions`, `_build_action_sequence`
  - Enviar/Cancelar: `_do_send`, `_do_cancel`, temporizadores: `_schedule_event`, `_release_delayed_events`, `advance_time`
  - Expresiones y alcance: `_scope_env`, `_evaluate_expr` (evaluación segura por defecto)
  - Ciclo de vida de la invocación: `_start_invocations_for_state`, `_start_invocations_for_active_states`, `_on_invoke_done`, `_cancel_invocations_for_state`
  - Ayudante de errores: `_emit_error` (alias específico + genérico para `error.execution`)
- Subsistema de invocación: `py/scjson/invoke.py` (mock:immediate, mock:record, mock:deferred, scxml/scjson child)
- Eventos/cola: `py/scjson/events.py` (`Event` incluye `origin`, `origintype`, `invokeid`)
- CLI: `py/scjson/cli.py` (`engine-trace`, `engine-verify`)
- Herramienta de comparación de rastros: `py/exec_compare.py`
- Envoltorio de comparación de ejecución para pruebas: `py/py/exec_compare.py`
- Diseño/Documentos: `py/scjson/ENGINE.md`, `docs/TODO-ENGINE-PY.md`
- Tutorial/Corpus: `tutorial/` (W3C + ejemplos), lista de exclusión: `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED`

## Instantánea de Comportamiento (Implementado)
- Ejecución + Estructura
  - Bucle de macrostep con transiciones sin eventos hasta la quiescencia
  - Selección de transición determinista (orden del documento)
  - Conjuntos de entrada/salida vía LCA; paralelo emite "done" de región y "done" padre
  - Historial superficial y profundo (el profundo restaura hojas descendientes exactas)
  - Contenido ejecutable: assign, log, raise, if/elseif/else, foreach, send (inmediato + retrasado), cancel, script (sin operación)
- Expresiones y Errores
  - Evaluación segura por defecto; `--unsafe-eval` opcional
  - `error.execution` cuando las expresiones cond/foreach/assign fallan o cond no es booleano (empujar al frente)
  - Alias genérico `error` emitido para `error.execution` (no para `error.communication`) para soportar gráficos que escuchan `error.*`
  - Asignar a ubicación inválida: encola `error.execution` (sin creación de variable); alias priorizado para el orden de entrada
- Envíos y Temporizadores
  - Interno: `#_internal`/`_internal` encola en la cola del motor
  - Externo: los destinos no soportados provocan `error.communication` y se omiten
  - Envíos retrasados deterministas: `advance_time(seconds)` libera en orden
  - Tokens de control: `engine-trace` acepta líneas de flujo de eventos como `{"advance_time": N}` para avanzar el tiempo sin emitir un paso (utilizado por la generación de vectores)
- Invocación
  - Inicio al final del macrostep para los estados ingresados y no salidos durante el paso
  - Padre↔Hijo: burbujeo `#_parent`; padre `#_child`/`#_invokedChild` y `#_<invokeId>` explícito
  - Autoforward de eventos externos a invocaciones activas (omite las canceladas)
  - La finalización se ejecuta en el estado de invocación; los mapas `_event` incluyen `name`, `data`, `invokeid`, `origin`/`origintype` opcionales
  - Orden de "Done": específico por ID y luego genérico por defecto, con preferencias para preservar el orden cuando el hijo emite durante la inicialización
  - El fallo de inicio de scxml/scjson hijo provoca `error.communication`
- Coincidencia de Eventos
  - Listas de eventos separadas por espacios
  - Comodín `*` y patrones de prefijo como `error.*`

## Normalización de Rastros
- Comparación solo de hojas (configuración/entrada/salida limitada a estados hoja)
- Eliminación de ruido del paso 0 por defecto: `datamodelDelta` y `firedTransitions`
- Opcional: eliminar `enteredStates`/`exitedStates` del paso 0 a menos que se proporcione `--keep-step0-states`

## Estado Actual
- Conjunto de unidades (Python): verde → `PYTHONPATH=py pytest -q py/tests`
- Resultados del conjunto rápido obligatorio de W3C (con `--advance-time 3` donde sea aplicable):
  - 253: aprobado; 338: aprobado; 422: aprobado; 554: aprobado
  - 401: aprobado (precedencia de error genérico vía asignación inválida + alias)
- Gráficos de tutorial python-datamodel descubiertos: 208
- Muestra ad-hoc de 50 gráficos: no hay fallos en la construcción de un paso vía `trace_step()`

## Diferencia (Desde la Instantánea Anterior)
- engine-trace: soporta tokens de control `{"advance_time": N}` dentro de eventos JSONL
- vector_gen: inyecta tokens `advance_time` a mitad de secuencia cuando los temporizadores están pendientes después de un paso
- Se agregaron `tests/sweep_corpus/*` curados y pruebas `exec_compare` avanzadas
- Se agregó el shim `py/py/exec_compare.py` para la estabilidad de la ruta de prueba
- uber_test: pruebas parametrizadas por gráfico; modo "smoke test" CLI con progreso por gráfico
- Documentos actualizados: tokens de control, inyección de vectores, semántica de invocación/finalización
- Ordenamiento del motor: nuevo modo `--ordering scion`. Las emisiones hijo→padre se encolan normalmente; `done.invoke` se empuja al frente con genérico antes de específico por ID para que coincida mejor con [SCION](https://www.npmjs.com/package/scion).

## Recetas de Reproducción
Pruebas unitarias
- Todas las pruebas de Python: `PYTHONPATH=py pytest -q py/tests`
- Prueba única: `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_invoke_generic_done_event`

Resultado del motor
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- 401: `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Comparación de rastros
- Principal: `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Opcional: `--keep-step0-states` para retener `enteredStates`/`exitedStates` del paso 0
- La referencia de respaldo se resuelve automáticamente a `node tools/scion-runner/scion-trace.cjs`; anular vía `SCJSON_REF_ENGINE_CMD`

"Uber harness" (conversión entre idiomas)
- Ruta: `py/uber_test.py`
- "Smoke test" del motor Python (parametrizado): `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
- "Smoke test" CLI con progreso: `python py/uber_test.py --python-smoke [--chart <ruta>]`

## Diferencias y Notas Conocidas
- La visibilidad de la inicialización varía entre motores; la normalización del paso 0 mitiga las diferencias
- Los ID de invocación difieren; no son relevantes para el comportamiento
- Los procesadores externos (HTTP) siguen sin ser compatibles; las pruebas que dependen de ellos se dejan en `ENGINE_KNOWN_UNSUPPORTED`

## Próximos Pasos
- Barrido de tutorial más amplio y reducciones incrementales de la lista de exclusión
- Validar más gráficos con exec_compare y ajustar la normalización solo si es necesario
- Considerar marcar el "smoke test" parametrizado como `@pytest.mark.slow` y usar filtros `-k` por defecto

## Greps Útiles
- Ir a puntos clave:
  - `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py`
  - `rg -n "engine-verify|engine-trace" py/scjson/cli.py`
  - `rg -n "InvokeRegistry|SCXMLChildHandler|send\(\)" py/scjson/invoke.py`
  - `rg -n "advance_time|control token|advance-time" py`

```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: python-engine-reference

Parte del proyecto scjson.
Desarrollado por Softoboros Technology Inc.
Licenciado bajo la Licencia BSD 1-Clause.

# Paquete Python — Arquitectura y Referencia

Este documento proporciona una referencia práctica y detallada para el paquete `scjson` de Python: sus módulos, comportamientos en tiempo de ejecución, herramientas CLI y cómo encajan. Si solo desea un uso rápido, consulte el resumen a continuación; para una inmersión más profunda, salte a las secciones enlazadas.

Resumen de inicio rápido
- Resumen de la CLI: la CLI de scjson admite la conversión SCXML↔SCJSON, la exportación de esquemas, el rastreo y la verificación del motor. Consulte: [CLI](#cli)
- Motor de ejecución: tiempo de ejecución de un solo archivo con evaluación de expresiones seguras, semántica de historial/paralelo, temporizadores e invocación. Consulte: [Motor de ejecución](#execution-engine)
- Rastreo y comparación: rastreos JSONL deterministas, normalización y comparación de referencias [SCION](https://www.npmjs.com/package/scion). Consulte: [Comparación de rastreos](#trace-compare)
- Generación y barrido de vectores: genera vectores de eventos, mide la cobertura y barre los corpus. Consulte: [Vectores y barrido](#vectors--sweep)
- Empaquetado: scripts de consola y módulos instalados por el paquete de Python. Consulte: [Empaquetado y scripts](#packaging--scripts)

Documentos relacionados
- docs/ENGINE-PY.md — guía del motor y uso de la CLI orientados al usuario
- docs/COMPATIBILITY.md — compatibilidad entre lenguajes y notas de paridad con [SCION](https://www.npmjs.com/package/scion)
- codex/CONTEXT.md — contexto de sesión actual y comandos de reproducción
- codex/CONTEXT-EXPANDED.md — instantánea de contexto expandido

## Navegación

- Esta página: Arquitectura y Referencia
  - [Diseño del paquete](#package-layout)
  - [Motor de ejecución](#execution-engine)
  - [Evaluación de expresiones seguras](#safe-expression-evaluation)
  - [Convertidor](#converter-scxml--scjson)
  - [CLI](#cli)
  - [Subsistema de invocación](#invoke-subsystem)
  - [Temporizadores](#timers)
  - [Comparación de rastreos](#trace-compare)
  - [Vectores y barrido](#vectors--sweep)
  - [Empaquetado y scripts](#packaging--scripts)
  - [Pruebas y comandos de reproducción](#testing--repro-commands)
- Guía de usuario: `docs/ENGINE-PY.md`
- Matriz de compatibilidad: `docs/COMPATIBILITY.md`

---

## Diseño del paquete

Módulos centrales del paquete (directorio: `py/scjson`):
- `cli.py` — interfaz de línea de comandos (conversión; engine-trace/verify; codegen).
- `context.py` — motor de ejecución (macro/microstep, transiciones, historial, invocación, temporizadores, semántica de errores, rastreo).
- `events.py` — primitivas `Event` y `EventQueue`.
- `activation.py` — registros de activación y especificaciones de transición utilizadas por el motor.
- `safe_eval.py` — evaluación de expresiones en sandbox (predeterminado) con anulación `--unsafe-eval`.
- `invoke.py` — registro de invocador ligero y manejador SCXML/SCJSON secundario.
- `SCXMLDocumentHandler.py` — convertidor XML↔JSON usando xsdata/xmlschema.
- `json_stream.py` — decodifica flujos JSONL sin depender del enmarcado de nueva línea.
- `jinja_gen.py` + templates — ayudantes de generación de código/esquema para CLI.

Herramientas de alto nivel (directorio: `py/`):
- `exec_compare.py` — ejecuta un gráfico con el motor de Python y compara con una referencia ([SCION](https://www.npmjs.com/package/scion) por defecto); diff JSONL con normalización.
- `exec_sweep.py` — barre un directorio de gráficos; generación de vectores opcional; resultados agregados.
- `vector_gen.py` — genera vectores de eventos y sidecars de cobertura.
- `vector_lib/` — ayudantes de analizador/búsqueda/cobertura para la generación de vectores.

---

## Motor de ejecución

Archivo: `py/scjson/context.py`

Conceptos clave
- Activaciones y configuración: Un `ActivationRecord` representa un nodo activo (estado/paralelo/final/historial). `configuration` es el conjunto de ID de activación activos; se actualiza durante los microsteps de transición.
- Macro/microstep: `microstep()` procesa como máximo un evento externo (más cualquier procesamiento `done.invoke*` inmediatamente relevante); las transiciones sin eventos se ejecutan hasta la quiescencia. `run()` ejecuta `microstep()` en bucle hasta que la cola se vacía o se alcanza un presupuesto de pasos.
- Selección de transición: `_select_transition(evt)` itera el orden del documento, admite eventos de múltiples tokens (separados por espacios), comodines `*` y patrones de prefijo `error.*`. `_eval_condition` se ejecuta en un sandbox; los resultados no booleanos producen `error.execution` y se evalúan como falsos.
- Entrada/Salida/Historial: `_enter_state`, `_exit_state`, `_enter_history` manejan el orden de entrada/salida basado en LCA, la restauración del historial superficial y profundo, y la propagación `done.state.*`.
- Contenido ejecutable: `assign`, `log`, `raise`, `if/elseif/else`, `foreach`, `send`, `cancel` y `script` (advertencia/sin operación). El orden de ejecución de las acciones se conserva mediante el orden de los hijos XML o la síntesis de orden JSON.
- Temporizadores: `_schedule_event` y `advance_time(seconds)` implementan temporizadores deterministas; el rastreo/CLI admite la inyección de tokens de control `{ "advance_time": N }` para liberar envíos retrasados entre estímulos.
- Errores: `_emit_error` encola `error.execution` (push-front) para fallos de evaluación y `error.communication` para envíos externos no compatibles o fallos de carga de invocación. También se emite un alias genérico `error` para `error.execution` para admitir gráficos que escuchan `error.*`.
- Invocación: `_start_invocations_for_state`, `_on_invoke_done`, `_cancel_invocations_for_state` gestionan el ciclo de vida de la invocación; la finalización se ejecuta en el estado de invocación con `_event` mapeado; interacción padre↔hijo a través de `#_parent`, `#_child`/`#_invokedChild` y `#_<invokeId>`.
- Modos de ordenación: `ctx.ordering_mode` controla la prioridad de emisión hijo→padre y la puesta en cola de `done.invoke`.
  - tolerant (predeterminado): las emisiones secundarias se colocan al principio; `done.invoke` se coloca al principio solo cuando no hay salidas secundarias que lo precedan.
  - strict: las emisiones secundarias y `done.invoke` se encolan al final.
  - scion: las emisiones secundarias se encolan al final; `done.invoke` se coloca al principio con un genérico antes de un id-específico, coincidiendo con el orden microstep observable de [SCION](https://www.npmjs.com/package/scion).

Ayudantes notables
- Expresiones seguras: `_evaluate_expr()` delega en `safe_eval` a menos que `allow_unsafe_eval=True`.
- Entrada de rastreo: `trace_step(evt: Event|None)` devuelve un diccionario normalizado con claves: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`.

---

## Evaluación de expresiones seguras

Archivo: `py/scjson/safe_eval.py`

- Sandbox predeterminado: el motor evalúa expresiones a través de un sandbox de lista blanca (`py-sandboxed`) que bloquea importaciones, acceso dunder y builtins inseguros. Se expone un conjunto curado de builtins puros (y opcionalmente `math.*`).
- Controles CLI: `engine-trace` acepta `--unsafe-eval` para omitir el sandbox (solo gráficos de confianza); los patrones de permitir/denegar y los presets pueden refinar la exposición cuando están en sandbox.
- Superficie de importación: prefiere `py_sandboxed` (su paquete administrado); recurre a `py_sandboxer` para entornos que exponen la misma API bajo un nombre diferente.
- Semántica de errores: las violaciones del sandbox o las excepciones en tiempo de ejecución generan `SafeEvaluationError`; el motor encola `error.execution` y trata la condición como falsa o el valor de la expresión como un literal cuando corresponda.

---

## Convertidor (SCXML ↔ SCJSON)

Archivo: `py/scjson/SCXMLDocumentHandler.py`

- Análisis/serialización: utiliza `XmlParser`/`XmlSerializer` de xsdata y validación `xmlschema` opcional.
- Estricto vs laxo: `fail_on_unknown_properties=True` impone un análisis XML estricto; establezca `False` para tolerar elementos desconocidos en gráficos no canónicos.
- Normalización JSON: decimales/enumeraciones normalizadas; contenedores vacíos eliminados por defecto; marcado de texto/anidado en `<content>` preservado en una estructura JSON compatible con [SCION](https://www.npmjs.com/package/scion).

---

## CLI

Archivo: `py/scjson/cli.py`

Comandos
- Conversión
  - `scjson json PATH [--output/-o OUT] [--recursive/-r] [--verify/-v] [--keep-empty] [--fail-unknown/--skip-unknown]`
  - `scjson xml PATH [--output/-o OUT] [--recursive/-r] [--verify/-v] [--keep-empty]`
- Validación
  - `scjson validate PATH [--recursive/-r]` (ida y vuelta en memoria)
- Motor
  - `scjson engine-trace -I CHART [--xml] [-e EVENTS] [--out OUT] [--lax/--strict] [--advance-time N] [--leaf-only] [--omit-actions] [--omit-delta] [--omit-transitions] [--ordering MODE] [--unsafe-eval|--expr-*]`
  - `scjson engine-verify -I CHART [--xml] [--advance-time N] [--max-steps N] [--lax/--strict]`
- Generación de código y esquema
  - `scjson typescript -o OUT` / `scjson rust -o OUT` / `scjson swift -o OUT` / `scjson ruby -o OUT`
  - `scjson schema -o OUT` (escribe `scjson.schema.json`)

Opciones de rastreo
- Modo solo hoja, omitir acciones/delta/transiciones y `--advance-time` para vaciar los temporizadores de forma determinista antes de procesar los eventos.

---

## Subsistema de invocación

Archivo: `py/scjson/invoke.py`

- Registro y manejadores: `InvokeRegistry` con manejadores simulados (`mock:immediate`, `mock:record`, `mock:deferred`) y manejadores de máquinas secundarias para `scxml`/`scjson`.
- Máquinas secundarias: construidas a través de `DocumentContext._from_model` con entrada inicial diferida para que los envíos de entrada puedan burbujear antes de que el padre vea `done.invoke`.
- E/S padre↔hijo: el hijo emite con metadatos de E/S de evento SCXML (`origintype`, `invokeid`) y admite envíos `#_parent`; el padre puede dirigirse al hijo por `#_child`/`#_invokedChild` o `#_<invokeId>`.
- Semántica de finalización: `<finalize>` se ejecuta en el estado de invocación; `_event` contiene `{name, data, invokeid}`.

---

## Temporizadores

- Programación: `<send delay|delayexpr>` se programa en relación con el reloj simulado del motor (`_timer_now`).
- Control: `advance_time(seconds)` libera los temporizadores listos; la CLI acepta `--advance-time N` y tokens de control `{ "advance_time": N }` dentro de los flujos de eventos.

---

## Comparación de rastreos

Archivo: `py/exec_compare.py`

- Propósito: ejecuta el motor de Python frente a la referencia ([SCION](https://www.npmjs.com/package/scion) Node por defecto) y compara rastreos JSONL.
- Normalización: filtrado solo de hojas; eliminación de ruido en el paso 0 (`datamodelDelta`, `firedTransitions`), eliminación opcional de estados de entrada/salida en el paso 0; claves `datamodelDelta` ordenadas.
- Referencia: se resuelve automáticamente a `tools/scion-runner/scion-trace.cjs` cuando está disponible (o anula `SCJSON_REF_ENGINE_CMD`).
- Vectores: puede generar vectores sobre la marcha (`--generate-vectors`) y adoptar el `advanceTime` recomendado de los metadatos del vector.

---

## Vectores y barrido

Archivo: `py/vector_gen.py`, ayudantes en `py/vector_lib/`

- Analizador: extrae un alfabeto de eventos de transiciones y sugerencias de invocación simples; heurísticas de carga útil de expresiones `cond`.
- Búsqueda: BFS guiada por cobertura sobre el alfabeto (`vector_lib.search.generate_sequences`); admite estímulos con datos.
- Generación: escribe `.events.jsonl`, `.coverage.json` y `.vector.json` (metadatos con `advanceTime`). Agrega `{ "advance_time": N }` entre estímulos cuando los temporizadores están pendientes.
- Barrido: `py/exec_sweep.py` descubre gráficos, genera vectores cuando faltan, compara rastreos y agrega la cobertura.

---

## Empaquetado y scripts

Archivo: `py/pyproject.toml`

- Versión: `0.3.5`
- Dependencias: `pydantic`, `lxml`, `jsonschema`, `click`, `py-sandboxed` (sandbox), `jinja2`, `xmlschema`, `xsdata`.
- Scripts de consola:
  - `scjson` — CLI principal
  - `scjson-exec-compare` — compara rastreos con la referencia
  - `scjson-exec-sweep` — barre directorios con generación de vectores opcional
  - `scjson-vector-gen` — generador de vectores independiente
- Módulos instalados: `exec_compare`, `exec_sweep`, `vector_gen`

---

## Pruebas y comandos de reproducción

- Pruebas unitarias: `PYTHONPATH=py pytest -q py/tests`
- Comprobaciones rápidas del motor (SCXML):
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/.../test253.scxml --xml --advance-time 3`
  - Repetir para: 338, 422, 554 → pase esperado
  - `test401.scxml` (precedencia de errores) pasa sin `--advance-time`
- Comparación de rastreos: `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Generación de vectores: `python py/vector_gen.py <chart.scxml> --xml --out vectors/`

---

## Limitaciones conocidas y notas de compatibilidad

- Procesadores externos: los destinos `<send>` externos (que no sean `#_parent`, `_internal`) no se ejecutan; el motor emite `error.communication` y omite la entrega.
- Visibilidad del paso 0: los motores difieren en las transiciones iniciales; la normalización mitiga las diferencias.
- Orden de invocación: el modo `scion` alinea la puesta en cola de `done.invoke` con [SCION](https://www.npmjs.com/package/scion); los modos `tolerant/strict` proporcionan alternativas flexibles.

---

## Apéndice: Esquema de rastreo (Pasos del motor)

Cada paso producido por `trace_step` o `engine-trace` incluye:
- `event`: `{name, data}` del evento externo consumido (o `null` para el paso 0)
- `firedTransitions`: `[{source, targets[], event, cond}]` filtrado a estados de usuario
- `enteredStates` / `exitedStates`: listas de ID de estado (filtradas por hoja cuando se solicita)
- `configuration`: ID de estado activo actual (filtradas por hoja cuando se solicita)
- `actionLog`: entradas de `log`, opcionalmente omitidas
- `datamodelDelta`: claves cambiadas desde el paso anterior, con claves ordenadas (opcionalmente omitidas)

---

## Apéndice: Glosario

- Activación: un registro en tiempo de ejecución de un nodo SCXML introducido (estado/paralelo/final/historial).
- Configuración: el conjunto de ID de activación actualmente activos.
- Macrostep: un `microstep()` más el drenaje de transiciones sin eventos hasta la quiescencia.
- [SCION](https://www.npmjs.com/package/scion): motor SCXML de referencia utilizado para la comparación de comportamiento.

---

Volver a
- Guía de usuario: `docs/ENGINE-PY.md`
- Matriz de compatibilidad: `docs/COMPATIBILITY.md`
```

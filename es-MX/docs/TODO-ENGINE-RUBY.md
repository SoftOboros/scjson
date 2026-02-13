<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Nombre del Agente: ruby-engine-todo

Parte del proyecto scjson.
Desarrollado por Softoboros Technology Inc.
Licenciado bajo la Licencia BSD 1-Cláusula.

# Motor de Ejecución Ruby — Plan de Checklist

Este checklist rastrea el trabajo para entregar un motor de ejecución Ruby con comportamiento completo compatible con [SCION](https://www.npmjs.com/package/scion) y paridad entre lenguajes con el motor Python. El plan también cubre el empaquetado, la documentación y la integración en el arnés de validación existente.

## Alcance y Metas
- [ ] Implementar el algoritmo de ejecución SCXML (macro/microstep), procesamiento de eventos, selección de transiciones, resolución de conflictos, gestión de configuración.
- [ ] Lograr semántica totalmente compatible con SCION para Ruby, haciendo coincidir las trazas en un corpus compartido (normalización permitida cuando sea apropiado).
- [ ] Reflejar primero las capacidades del motor Python (documento único), luego extender al comportamiento completo equivalente a SCION para múltiples documentos (invocar/finalizar, máquinas hijas, eventos de finalización).
- [ ] Mantener el pipeline de validación igual que en Python: usar el arnés de Python para evaluar la ejecución del motor Ruby versus SCION y/o Python.
- [ ] Convertir los documentos de prueba actualmente adaptados para JS y Python en extensiones de vectores de prueba de Ruby (solo en el repositorio; no editar el contenido del tutorial).
- [ ] Proporcionar una guía de usuario dedicada para el motor Ruby (como la de Python), con detalles más profundos y ejemplos ejecutables.
- [ ] Destacar el motor Ruby en la parte superior del README y mencionar la ejecución de SCXML/SCML en la descripción, metadatos del paquete y términos de búsqueda.
- [ ] Mejorar el soporte de documentación de RubyGems y agregar detalles del paquete RubyGems a la sección inferior del README.
- [ ] Aumentar la versión del proyecto a 0.3.5 como parte del lanzamiento que incluye el motor Ruby.

## Semántica de Referencia
- [ ] Usar [SCION](https://www.npmjs.com/package/scion) (Node) como referencia de comportamiento.
- [ ] Comparar las trazas del motor Ruby con las de SCION y Python a través de las herramientas del arnés de Python.
- [ ] Documentar cualquier ordenamiento definido por la implementación o deltas conocidos y proporcionar banderas de normalización consistentes con Python.

## Hoja de Ruta (Iteraciones)

1) Inicio y Paridad con Python (documento único)
- [x] Definir el núcleo de tiempo de ejecución de Ruby (contexto del documento, configuración, cola de eventos, reglas de selección/conflicto — básicas, de una sola transición).
- [x] Implementar transiciones sin eventos hasta la quiescencia (macrostep básico; acotado).
- [x] Implementar ordenamiento de entrada/salida basado en LCA para microsteps de una sola transición (básico; configuración solo de hojas).
- [x] Evaluación de condiciones de transición (básico: literales, variables, ==/!=, comparaciones numéricas).
- [ ] Implementar bucle macrostep completo y resolución completa de conflictos para que coincida con Python.
- [x] Contenido ejecutable Fase 1 (subconjunto): log, assign (literales e incrementos +N), raise, if/elseif/else, foreach.
- [x] E/S de eventos: cola interna, eventos de error; temporizadores a través de reloj simulado (token de control advance_time aceptado en flujos de eventos para que coincida con las trazas deterministas de Python).
- [x] CLI: `scjson engine-trace` en Ruby, emitiendo trazas JSONL deterministas (mismo esquema que Python).
- [x] Integrar con `py/exec_compare.py` como un motor "secundario" bajo prueba (usar `--secondary "ruby/bin/scjson engine-trace"`).

2) Multi-documento e Invocar/Finalizar
- [x] Implementar el ciclo de vida de `<invoke>`, `<finalize>`, eventos `done.invoke`/`done.invoke.<id>` (detección básica inmediata y de finalización de hijos); ordenamiento con búfer con `--ordering scion`.
- [x] Soporte para máquinas hijas (SCXML/SCJSON en línea y URIs de archivo); `#_parent`, `#_child`/`#_invokedChild`, y `#_<id>` objetivos; `autoforward`.
- [x] Soporte para máquinas hijas (en línea y archivos `src`); `#_parent`, `#_child`/`#_invokedChild`, y `#_<id>` objetivos; `autoforward`.
- [x] Finalización paralela (básica), objetivos de historial (superficial/profundo) y semántica de estados finales; encolar eventos `done.state.<id>`.
- [ ] Manejo de errores y ordenamiento consistente con SCION; adoptar los controles de normalización de Python cuando sea útil.
  - [x] `<cancel>` implementado con gestión de temporizadores basada en ID; emite `error.execution` cuando falta/no se encuentra el ID.
  - [x] Evaluador: `in(stateId)`, recorrido de `_event.data` seguro contra nulos, e igualdad de tipos mixtos (cadena numérica vs número).
  - [x] Invocar: propagar `<donedata>` hijo a la carga útil `done.invoke`; ordenamiento con búfer respetado (`--ordering scion`).
  - [x] Agregar opción `--defer-done` (predeterminado ON) para aplazar el procesamiento de `done.invoke*` al siguiente paso para que coincida con los límites de paso de SCION.
  - [ ] Ajustar aún más la resolución de conflictos de transición para casos extremos anidados/paralelos; agregar pruebas enfocadas.

3) Integración del Arnés de Validación
- [ ] Conectar el CLI de Ruby en `py/exec_compare.py` y `py/exec_sweep.py` (cadena de comando + suposiciones de cwd documentadas).
- [x] Normalizar trazas con controles de solo hoja/omitir-delta/paso-0 reflejando las banderas de Python (`--strip-step0-noise`, `--strip-step0-states`, `--keep-cond`).
- [ ] Objetivo CI para ejecutar un subconjunto de gráficos en cada PR contra SCION y Python.

4) Documentación y Ejemplos
- [x] Crear `docs/ENGINE-RB.md` (guía de usuario) reflejando la estructura de `docs/ENGINE-PY.md`.
- [x] Agregar `ruby/ENGINE-RB-DETAILS.md` (arquitectura y referencia en profundidad) análogo a `py/ENGINE-PY-DETAILS.md`.
- [x] Portar los flujos de eventos de ejemplo de JS/Python a ejemplos enfocados en Ruby (sin cambiar `tutorial/`): membership, invoke_inline, invoke_timer, parallel_invoke.
- [x] Agregar guía de resolución de problemas y normalización (paso-0, temporizadores, limitaciones de expresión) en `docs/ENGINE-RB.md`.

5) Empaquetado y Lanzamiento
- [x] Mejorar el soporte de documentación de RubyGems: secciones README, ganchos YARD/RDoc, enlaces de página de inicio y fuente, resumen/descripción extendida.
- [ ] Actualizar palabras clave de metadatos de gemas (términos de búsqueda): "scxml", "statecharts", "state-machine", "scjson", "scml", "execution".
- [x] Actualizaciones del README: destacar el motor Ruby en la parte superior; agregar detalles del paquete RubyGems en la parte inferior.
- [x] Aumento de versión a 0.3.5 en todo el repositorio (paquetes Python, Ruby y JS actualizados).

## Vectores de Prueba y Corpus
- [ ] Convertir los documentos de prueba de JS/Python en extensiones de vectores de Ruby alojadas en el repositorio (por ejemplo, variantes `tests/exec/*.events.jsonl` si Ruby requiere tokens de tiempo). No modificar el contenido de `tutorial/`.
- [ ] Asegurarse de que el arnés de Python pueda seleccionar Ruby como objetivo a través de `-l ruby` y agregar la cobertura en `uber_out/`.
- [ ] Agregar un pequeño corpus específico de Ruby para ejercitar la semántica de múltiples documentos (invocar/finalizar).

## Criterios de Aceptación
- [ ] Las trazas del motor Ruby coinciden con SCION en el corpus canónico (después de la normalización) y coinciden con Python en subconjuntos compartidos.
- [ ] El trabajo de CI ejecuta `exec_compare` para Ruby vs SCION y no reporta discrepancias en el paquete de aceptación.
- [ ] `docs/ENGINE-RB.md` y `ruby/ENGINE-RB-DETAILS.md` se publican con ejemplos ejecutables.
- [ ] El README destaca el motor Ruby; los enlaces y metadatos de RubyGems se actualizan.
- [ ] La versión del repositorio se ha incrementado a 0.3.5 y los artefactos liberados están etiquetados.

## Próximos Pasos Inmediatos
- [x] Borrador del documento de paridad del esquema de traza para Ruby (reutilizar el esquema y las banderas de Python).
- [x] Agregar un comando stub de CLI de Ruby `engine-trace` que imprime una línea de traza estática para validar el cableado del arnés, luego iterar.
- [x] Agregar integración del arnés a `py/exec_compare.py` para invocar el CLI de Ruby y analizar la salida de la traza (a través de `--secondary`).
- [ ] Preparar ejemplos iniciales de Ruby y los flujos `.events.jsonl` correspondientes (con `advance_time` si se usan temporizadores).
 - [x] Implementar temporizadores: `<send delay>` con token de control `advance_time` para vaciar eventos programados de forma determinista.

## Riesgos y Mitigaciones
- [ ] Diferencias en la evaluación de expresiones entre lenguajes: restringir a un subconjunto entre motores; proporcionar un modo opcional solo para Ruby marcado en los documentos.
- [ ] Matices de ordenación de temporizadores y eventos: mantener los interruptores de normalización de Python; probar con controles advance_time.
- [ ] Diferencias de ordenación de finalización de múltiples documentos: documentar la política y, si es necesario, adoptar estrictamente el ordenamiento de SCION en un "modo scion".

## Instantánea de Estado — 2025-10-03
- `El CLI del Convertidor y los tipos de esquema existen en ruby/lib/scjson.` - Sin cambios.
- `Se agregó el stub del CLI de traza del motor (scjson engine-trace); el arnés puede llamar a Ruby a través de --secondary.` - Sin cambios.
- `Se agregaron esqueletos de documentación (docs/ENGINE-RB.md, ruby/ENGINE-RB-DETAILS.md).` - Sin cambios.
 - `Temporizadores soportados (send retrasado + advance_time), eventos internos, pruebas de membresía y literales JSON.` - Sin cambios.
 - `Invocar: contextos hijos (en línea + src), enrutamiento padre↔hijo, autoforward, mapeo de parámetros y ordenación de done.invoke con búfer con --ordering.` - Sin cambios.
 - `Entrada inicial paralela corregida para múltiples regiones.` - Sin cambios.

Volver a
- Guía del Usuario del Motor Python: `docs/ENGINE-PY.md`
- Matriz de Compatibilidad: `docs/COMPATIBILITY.md`
- Descripción general del proyecto: `README.md`

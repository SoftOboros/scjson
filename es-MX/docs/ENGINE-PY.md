<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Motor Python — Guía de Usuario

Esta guía explica cómo usar el motor de ejecución de Python y las herramientas complementarias para rastrear diagramas, comparar con un motor de referencia, generar vectores de prueba y barrer corpus. Es un compañero de cara al usuario de la lista de verificación de desarrollo en `docs/TODO-ENGINE-PY.md`.

¿Busca detalles de implementación más profundos? Consulte la referencia de arquitectura en `py/ENGINE-PY-DETAILS.md`.

Para la paridad entre idiomas y los detalles de comparación con [SCION](https://www.npmjs.com/package/scion), consulte `docs/COMPATIBILITY.md`.

## Navegación

- Esta página: Guía de Usuario
  - [Descripción General](#descripción-general)
  - [Inicio Rápido](#inicio-rápido)
  - [Flujos de Eventos](#flujos-de-eventos-eventsjsonl)
- [Generación de Vectores](#generación-de-vectores)
  - [Control de Tiempo](#control-de-tiempo)
- Arquitectura y referencia en profundidad: `py/ENGINE-PY-DETAILS.md`
- Matriz de Compatibilidad: `docs/COMPATIBILITY.md`

## Descripción General

El motor de Python ejecuta diagramas de estado SCXML/SCJSON y puede emitir trazas JSONL determinísticas de la ejecución. Un conjunto de utilidades CLI le ayuda a:

- Ejecutar el motor de Python y recolectar trazas
- Comparar trazas de Python con un motor de referencia ([SCION](https://www.npmjs.com/package/scion)/Node)
- Generar vectores de eventos de entrada para mejorar la cobertura
- Barrer carpetas de diagramas, auto-generar vectores y agregar cobertura

Componentes clave (rutas relativas a la raíz del repositorio):

- `py/scjson/cli.py` – CLI principal, incluyendo `engine-trace`
- `py/exec_compare.py` – compara Python vs referencia (y secundario opcional)
- `py/exec_sweep.py` – barre un directorio y compara todos los diagramas
- `py/vector_gen.py` – generador de vectores de eventos con heurística de cobertura

Las trazas son objetos JSONL delimitados por líneas con los campos: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`.

## Inicio Rápido

1) Traza del motor (solo Python)

```bash
python -m scjson.cli engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.python.trace.jsonl --xml \
  --leaf-only --omit-delta
```

Notas:
- `-I` apunta al diagrama de entrada; agregue `--xml` para entrada SCXML, omítalo para SCJSON.
- `-e` proporciona un archivo de eventos JSONL (vea "Flujos de Eventos").
- Los indicadores de normalización reducen el ruido y mantienen las trazas determinísticas.

2) Comparar con el motor de referencia

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --leaf-only --omit-delta
```

Si omite `--events`, puede pedirle a la herramienta que genere vectores:

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3
```

3) Barrer un directorio de diagramas

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep
```

Cuando se proporciona `--workdir` y se generan vectores, se escribe un `coverage-summary.json` con la cobertura agregada en todos los diagramas.

---

Volver a
- Arquitectura y referencia: `py/ENGINE-PY-DETAILS.md`
- Matriz de Compatibilidad: `docs/COMPATIBILITY.md`

## Flujos de Eventos (.events.jsonl)

Los flujos de eventos son objetos JSON delimitados por saltos de línea, uno por evento:

```json
{"event": "start"}
{"event": "go", "data": {"flag": true}}
```

Claves aceptadas:
- `event` (o `name`) – nombre del evento en cadena
- `data` – carga útil opcional (objeto, número, cadena, etc.)

Tokens de control:
- `advance_time` – número de segundos para adelantar el reloj simulado del motor de Python
  antes de que se procese el siguiente evento externo. Esto es ignorado por los motores de referencia
  que solo consumen `event`/`name`, pero permite al motor de Python vaciar
  temporizadores `<send>` retrasados entre estímulos para que coincida mejor con los motores que no
  modelan el tiempo explícitamente.

## Control de Tiempo

Por defecto, la CLI emite un paso sintético cada vez que un token de control `{"advance_time": N}`
es procesado, de modo que los temporizadores vencidos son visibles incluso cuando no
ocurren eventos externos subsiguientes. Deshabilite este comportamiento con
`--no-emit-time-steps` cuando se desee una paridad estricta con herramientas que no emiten
dichos pasos.

Ejemplo:

```bash
python -m scjson.cli engine-trace -I chart.scxml --xml \
  -e stream.events.jsonl --leaf-only --omit-delta
```

Notas:
- El paso sintético establece `event` en `null` y, por lo demás, sigue las mismas
  reglas de normalización (`--leaf-only`, `--omit-*`).
- Use `--no-emit-time-steps` para suprimir estos pasos si compara con herramientas
  que no los emiten.

## Generación de Vectores

`py/vector_gen.py` genera secuencias de eventos compactas para explorar el comportamiento de un diagrama. Extrae un alfabeto de eventos y utiliza una búsqueda guiada por cobertura con heurística de carga útil.

Características principales:
- Extracción del alfabeto de los tokens de `event` de transición (omite comodines/patrones de prefijo)
- Heurística de carga útil de las expresiones `cond` en `_event.data.*`:
  - Veracidad / negación (Verdadero/Falso)
  - Igualdad/desigualdad y umbrales numéricos
  - Pruebas de membresía (incluidas formas invertidas y contenedores de modelo de datos)
  - Rangos numéricos encadenados/divididos
- Fusión de carga útil:
  - Fusionar sugerencias por condición no conflictivas para cargas útiles más ricas
  - Variantes "cambio de rama" de una sola vez (positivas para una condición, negativas para otras)
- Detección de avance automático: si el diagrama programa envíos retrasados durante la inicialización, el generador recomienda y aplica un pequeño avance de tiempo inicial

Uso de CLI:

```bash
python py/vector_gen.py path/to/chart.scxml --xml \
  --out ./vectors --max-depth 2 --limit 1 \
  --variants-per-event 3 --advance-time 0 \
  # use --no-auto-advance to disable delayed-send detection
```

Salidas escritas junto al nombre base del diagrama:
- `<name>.events.jsonl` – secuencia de eventos generada
- `<name>.coverage.json` – resumen de cobertura para la secuencia
- `<name>.vector.json` – metadatos que incluyen `advanceTime`, `sequenceLength` y recuentos de sugerencias

`exec_compare` y `exec_sweep` adoptan el `advanceTime` recomendado de `.vector.json` cuando usa `--generate-vectors` y no pasa un `--advance-time` explícito.

El número de variantes de carga útil candidatas por evento está limitado por `--variants-per-event`.

Inyección de avance de tiempo a mitad de secuencia
- Cuando el diagrama programa eventos `<send>` retrasados después de la inicialización, el
  generador ahora inyecta tokens de control (`{"advance_time": N}`) entre
  estímulos externos en `<name>.events.jsonl` para que esos temporizadores se liberen antes
  del siguiente evento. La CLI `engine-trace` entiende estos tokens y avanza el
  reloj simulado del intérprete sin emitir un paso de traza; el [SCION](https://www.npmjs.com/package/scion) de referencia
  lo ignora (solo busca `event`/`name`).

Este comportamiento mejora la paridad entre motores cuando la referencia no modela
el tiempo, al tiempo que mantiene el formato del flujo de eventos compatible con versiones anteriores.

## Normalización e Indicadores

Estos indicadores aparecen en `engine-trace`, `exec_compare` y `exec_sweep` para mantener la salida reproducible y enfocar las comparaciones:

- `--leaf-only` – restringe `configuration`, `enteredStates` y `exitedStates` a estados hoja
- `--omit-delta` – borra `datamodelDelta` (el paso 0 aún se normaliza)
- `--omit-actions` – borra `actionLog`
- `--omit-transitions` – borra `firedTransitions`
- `--advance-time <seconds>` – avanza el tiempo simulado antes del procesamiento de eventos (y se propaga a las invocaciones secundarias)

Normalización del paso 0: tanto las trazas de Python como las de referencia tienen `datamodelDelta` y `firedTransitions` borrados en el paso 0. El filtrado de estado de solo hoja reduce aún más la varianza del paso 0.

## Motor de Referencia ([SCION](https://www.npmjs.com/package/scion))

La referencia predeterminada es la implementación de [SCION](https://www.npmjs.com/package/scion) Node; se incluye un script auxiliar. `exec_compare` y `exec_sweep` lo usan automáticamente cuando está presente.

Configurar una vez:

```bash
cd tools/scion-runner
npm install
```

Apunte `exec_compare`/`exec_sweep` a él explícitamente con:

```bash
--reference "node tools/scion-runner/scion-trace.cjs"
```

Alternativamente, establezca `SCJSON_REF_ENGINE_CMD` en su entorno. Cuando se agreguen otros motores, estos deberían volver a compararse con [SCION](https://www.npmjs.com/package/scion) como referencia.

## Ejemplos

Rastrear y comparar con vectores generados:

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 2 \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Barrer una carpeta y escribir el resumen de cobertura:

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" --generate-vectors \
  --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Generar solo vectores (sin comparar):

```bash
python py/vector_gen.py examples/demo.scxml --xml \
  --out ./vectors --max-depth 2 --variants-per-event 3
```

## Cobertura

La cobertura es un simple agregado de únicos:
- IDs de estado introducidos
- Transiciones disparadas (por origen y destino)
- Eventos `done.*`
- Eventos `error*`

`exec_sweep` agrega la cobertura para los vectores generados y escribe un `coverage-summary.json` cuando se proporciona `--workdir`. Los archivos complementarios de cobertura por diagrama son escritos por `vector_gen.py`.

## Solución de Problemas

- Si `engine-trace` no está disponible, `exec_compare` recurre a un ejecutor de Python en línea.
- Para entradas SCXML que programan envíos retrasados durante la inicialización, use `--advance-time` (o confíe en la autodetección del generador) para que esos temporizadores se vacíen antes del primer evento externo.
- Si Node no está disponible, aún puede ejecutar `exec_sweep` usando el motor de Python como referencia: `--reference "$(python -c 'import sys;print(sys.executable)') -m scjson.cli engine-trace"`.

## Más Detalles

Para notas de diseño, estado de implementación y limitaciones conocidas, consulte: `py/scjson/ENGINE.md` y `docs/TODO-ENGINE-PY.md`.

Esta guía explica cómo usar la interfaz del motor de ejecución de Ruby para emitir rastros JSONL deterministas y cómo comparar el comportamiento con el motor de referencia ([SCION](https://www.npmjs.com/package/scion)) y el motor de Python. Refleja la guía de Python cuando es apropiado, siguiendo las convenciones de Ruby.

¿Busca detalles de implementación más profundos? Consulte la referencia de arquitectura en `ruby/ENGINE-RB-DETAILS.md`.

Para obtener detalles sobre la paridad entre lenguajes y la comparación con SCION, consulte `docs/COMPATIBILITY.md`.

## Navegación

- Esta página: Guía del usuario
  - Resumen
  - Inicio rápido
  - Flujos de eventos (.events.jsonl)
- Arquitectura y referencia detallada: `ruby/ENGINE-RB-DETAILS.md`
- Matriz de compatibilidad: `docs/COMPATIBILITY.md`

## Resumen

La interfaz del motor de Ruby se está desarrollando para ejecutar diagramas de estado SCXML/SCJSON y emitir rastros JSONL deterministas de la ejecución. Un conjunto de utilidades CLI y el arnés de Python existente le ayudan a:

- Ejecutar el motor de Ruby y recopilar rastros
- Comparar rastros de Ruby con un motor de referencia (SCION/Node) y Python
- Reutilizar vectores de eventos existentes y tokens de control para ejecuciones deterministas

Componentes clave (rutas relativas a la raíz del repositorio):

- `ruby/lib/scjson/cli.rb` – CLI de Ruby, incluyendo `engine-trace`
- `ruby/lib/scjson/engine.rb` – interfaz de rastreo del motor (stub; se expande con el tiempo)
  - Banderas de normalización: `--leaf-only`, `--omit-actions`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`, `--keep-cond`
  - Ordenación: `--ordering tolerant|strict|scion` (afecta la ordenación de eventos done.invoke)
- `py/exec_compare.py` – compara rastros con la referencia y una secundaria opcional (usar para Ruby)

Los rastros son objetos JSON delimitados por líneas con los campos: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`, `step`.

## Inicio rápido

1) Rastro del motor (Ruby; entrada SCXML)

```bash
ruby/bin/scjson engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.ruby.trace.jsonl --xml \
  --leaf-only --omit-delta --strip-step0-noise --strip-step0-states
```

Notas:
- `-I` apunta al diagrama de entrada; agregue `--xml` para entrada SCXML, omítalo para SCJSON.
- `-e` proporciona un archivo de eventos JSONL (consulte "Flujos de eventos").
- Las banderas de normalización reducen el ruido y mantienen los rastros deterministas.

2) Comparar con el motor de referencia con Ruby como secundario

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --secondary "ruby/bin/scjson engine-trace" \
  --leaf-only --omit-delta
```

3) Barrido de un directorio de diagramas (Ruby como secundario)

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --workdir uber_out/sweep \
  --secondary "ruby/bin/scjson engine-trace"
```

Al usar vectores generados, el arnés de Python escribe un `coverage-summary.json` con la cobertura agregada en los diagramas.

## Flujos de eventos (.events.jsonl)

Los flujos de eventos son objetos JSON delimitados por líneas, uno por evento:

```json
{"event": "start"}
{"event": "go", "data": {"flag": true}}
```

Claves aceptadas:
- `event` (o `name`) – nombre del evento en cadena
- `data` – carga útil opcional (objeto, número, cadena, etc.)

Tokens de control:
- `advance_time` – número de segundos para avanzar el reloj del motor antes de que se procese el siguiente evento externo. No se emite un paso de rastro para este token de control. Esto refleja el comportamiento de Python para mantener los rastros comparables.
  - La CLI de Ruby también admite `--advance-time N` para aplicar un avance de tiempo inicial antes del primer evento.

## Notas de CI — Retorno de conversor

- El conversor SCXML↔scjson de Ruby utiliza Nokogiri cuando está disponible. Algunos entornos de CI no instalan gemas de Ruby (Nokogiri requiere extensiones nativas). Para mantener el arnés del motor utilizable en esos entornos, el conversor de Ruby recurre de forma transparente a la CLI de Python para la conversión:
  - SCXML→scjson: `python -m scjson.cli json <in.scxml> -o <out.scjson>`
  - scjson→SCXML: `python -m scjson.cli xml <in.scjson> -o <out.scxml>`
- Este retorno es solo para la conversión de formato de archivo; la ejecución/rastreo todavía la realiza el motor de Ruby. Usar el conversor de Python mantiene el JSON canónico idéntico en todos los lenguajes y evita la varianza solo de CI.
- Si se prefiere, pre-convierta los diagramas por adelantado y ejecute el motor de Ruby en entradas scjson para omitir completamente el análisis de XML:
  - `python -m scjson.cli json chart.scxml -o chart.scjson`
  - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

Cobertura de la documentación
- Las comprobaciones de conversión y compilación de la documentación se ejecutan antes en la tubería de CI; cuando se ejecuta el arnés del motor de Ruby, la documentación y los conversores ya han sido validados. El retorno de Nokogiri simplemente elimina la necesidad de una pila XML nativa de Ruby en etapas posteriores.

## Solución de problemas

- Diferencias conocidas en las ejecuciones de CI
  - Algunos diagramas tienen diferencias intencionales y documentadas entre motores (por ejemplo, semántica `in` de ECMA, matices de reentrada del historial). Use la lista de diferencias conocidas para mantener la CI en verde mientras informa estos casos:
    - Archivo: `scripts/ci_ruby_known_diffs.txt`
    - Arnés: `bash scripts/ci_ruby_harness.sh --list scripts/ci_ruby_charts.txt --known scripts/ci_ruby_known_diffs.txt`

- Perfil de normalización para comparaciones
  - Use el perfil SCION para alinear los campos de salida y la ordenación entre motores:
    - `python py/exec_compare.py <chart> --events <events> --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
  - `--norm scion` establece: leaf-only, omit-delta, omit-transitions, strip-step0-states, y ordering=scion.

- Pre-convertir SCXML a scjson para la ejecución de Ruby
  - Para evitar diferencias en el analizador XML o la configuración de Nokogiri en su máquina, pre-convierta una vez y ejecute Ruby en scjson:
    - `python -m scjson.cli json chart.scxml -o chart.scjson`
    - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

- Dependencia de Nokogiri (desarrollo local)
  - El conversor SCXML↔scjson de Ruby utiliza la gema Nokogiri para el análisis de XML cuando se ejecuta desde la fuente. Si la gema no está instalada, la CLI de Ruby recurre de forma transparente al conversor de Python (consulte "Notas de CI").
  - Para obtener el mejor rendimiento local y mantener todo en Ruby, instale Nokogiri (y las dependencias de compilación del sistema) en su entorno. De lo contrario, se utilizará el retorno de Python para la conversión, mientras que la ejecución permanecerá en Ruby.

---

Volver a
- Arquitectura y referencia: `ruby/ENGINE-RB-DETAILS.md`
- Matriz de compatibilidad: `docs/COMPATIBILITY.md`
- Descripción general del proyecto: `README.md`

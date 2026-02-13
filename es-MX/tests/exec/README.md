Agent Name: exec-tests

Parte del proyecto scjson.
Desarrollado por Softoboros Technology Inc.
Licenciado bajo la Licencia BSD 1-Clause.

# Accesorios del Arnés de Ejecución

Este directorio contiene documentos SCXML de muestra y flujos de eventos coincidentes utilizados por
`exec_compare.py`. Cada archivo `.scxml` debe tener un archivo hermano `.events.jsonl`
que proporcione un objeto JSON por línea con el nombre del evento y datos opcionales.

## Archivos

- `toggle.scxml` – máquina de dos estados (`idle` ↔ `active`) que incrementa
  `count` al entrar en `active`.
- `toggle.events.jsonl` – script de eventos que ejercita `start`, `go`, y `reset`.

Siéntase libre de agregar accesorios adicionales a medida que el arnés de comparación crezca.

## Ejecutor de Referencia ([Scion](https://www.npmjs.com/package/scion))

El motor de referencia predeterminado utilizado por `py/exec_compare.py` es un envoltorio delgado
alrededor de la implementación de Node de [SCION](https://www.npmjs.com/package/scion).

1. Instale las dependencias una vez:

   ```bash
   cd tools/scion-runner
   npm install
   ```

2. Genere un rastreo directamente:

   ```bash
   node scion-trace.cjs -I ../../tests/exec/toggle.scxml \
       -e ../../tests/exec/toggle.events.jsonl \
       -o toggle.scion.trace.jsonl
   ```

3. Compare Python vs [Scion](https://www.npmjs.com/package/scion) (y opcionalmente un motor secundario) usando:

   ```bash
   cd ../../py
   python exec_compare.py ../tests/exec/toggle.scxml \
       --events ../tests/exec/toggle.events.jsonl
   ```

Establezca `SCJSON_SECONDARY_ENGINE_CMD` o `--secondary` para proporcionar un motor adicional
(por ejemplo, Apache Commons SCXML) para comparaciones de tres vías.

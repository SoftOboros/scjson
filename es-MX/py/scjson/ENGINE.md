```markdown
# Motor de ejecución estilo SCXML con nombres:

### Capas
Lo que se crea cuando el intérprete inicia	Tiempo de vida	Contenido típico

Documento (global)	Contexto del Documento (a veces "Modelo de Datos")	Toda la ejecución	• todos los elementos <data> de nivel superior
• constantes inmutables
• un puntero a la Activación Raíz actual (ver la siguiente fila)
• cola de eventos / manejador de programador

Máquina de estados raíz	Registro de Activación Raíz	Toda la ejecución	• ID del elemento <scxml> raíz
• configuración actual (conjunto de estados activos)
• instantáneas de historial, temporizadores globales, etc.
Cada estado / paralelo que se activa	Estado

Registro de Activación ("contexto local", "marco", etc.)	Desde la entrada hasta la finalización de la salida	• referencia a la activación padre
• indicadores de tiempo de ejecución: isFinal, isParallel, hasHistory …
• cualquier <data> con ámbito en el estado
• variables temporales creadas por acciones assign/var
• temporizadores en ejecución activados por este estado

## Por qué funciona esta estratificación

### Aislamiento de datos transitorios

Un Registro de Activación de Estado desaparece cuando el estado sale, por lo que cualquier variable temporal o temporizador no se filtra hacia arriba. Esto coincide con la expectativa de SCXML de que los <data> locales se recrean en cada reentrada.

### La jerarquía refleja el flujo de control

Debido a que las activaciones se anidan exactamente como el anidamiento de <state> / <parallel>, los algoritmos como "¿el ancestro está activo?", la restauración del historial y la detección de estados finales se convierten en simples recorridos de árbol.
Contabilidad del estado final

Marca una activación como final cuando su hijo <final> entra; propaga esto hacia arriba para que un <parallel> se complete solo cuando todas las activaciones de sus hijos estén en el estado final.

### Eficiencia de bajo nivel
Si implementas las activaciones como objetos ligeros (o manejadores de estructuras de un grupo de objetos), crearlas/destruirlas en cada entrada/salida es económico y mantiene la memoria por instancia proporcional a la configuración activa, no a todo el gráfico.

### Un par de pistas de implementación
Mantén un conjunto de "configuración actual" junto con el árbol de activación; la mayoría de los algoritmos (microstep, transiciones legales, resolución de conflictos) son operaciones de conjunto sobre la configuración.

Las colas de eventos viven a nivel de documento o raíz. Entrega eventos hacia abajo recorriendo el árbol de activación hasta que alguien los consume.

Historial: almacena, al salir, los ID (o punteros) de las activaciones secundarias que estaban activas. Al restaurar el historial, recrea las activaciones para esos ID en lugar de evaluar <initial>.

Datos globales vs. locales: deja que los <data> a nivel de estado oculten las entradas a nivel de documento; las búsquedas ascienden por la cadena de activación.

## Sandbox de Expresiones y Modelo de Confianza

Las expresiones de Python dentro de los atributos `<assign>`, `<log>` y `cond` de transición
se evalúan con un sandbox impulsado por [`py-sandboxed`](https://pypi.org/project/py-sandboxed/).
Solo un subconjunto curado de funciones incorporadas puras (ej., `abs`, `len`, `sum`, `sorted`) y
el módulo `math` se exponen por defecto; los intentos de importar módulos, acceder
a atributos con doble guion bajo, o llamar a `eval`/`exec` generan un
``SafeEvaluationError`` y recurren a la cadena de expresión literal cuando
es posible. La función auxiliar `In(stateId)` se inyecta automáticamente para que los gráficos
puedan consultar estados activos sin abrir el sandbox.

Para entornos que confían plenamente en el gráfico de entrada, puedes optar por no usar el
sandbox pasando `--unsafe-eval` a `scjson engine-trace` (o construyendo
`DocumentContext` con `allow_unsafe_eval=True`). Esto vuelve a habilitar
`eval` nativo de CPython, coincidiendo con el comportamiento anterior del motor.

Preajustes y anulaciones del Sandbox
- `--expr-preset` controla la superficie del sandbox: `standard` (por defecto) o `minimal`.
  El preajuste `minimal` deniega `math.*` para aproximar mejor un subconjunto entre motores.
- Ajusta con `--expr-allow PATTERN` y/o `--expr-deny PATTERN` (repetible).
- `--unsafe-eval` omite el sandbox por completo (solo entornos de confianza).

## Filtros de Traza y Determinismo

El comando `engine-trace` ahora soporta filtros opcionales de tamaño/visibilidad:
- `--leaf-only` limita `configuration`/`enteredStates`/`exitedStates` a estados hoja.
- `--omit-actions` omite `actionLog` de las entradas de traza.
- `--omit-delta` omite `datamodelDelta` (el paso 0 aún imprime un objeto vacío).
- `--omit-transitions` omite `firedTransitions` de las entradas.
- `--advance-time N` avanza el reloj simulado antes del procesamiento de eventos para liberar
  eventos `<send>` retrasados de forma determinista en las trazas.

Para mejorar la reproducibilidad, las claves `datamodelDelta` se emiten en orden alfabético cuando están presentes.

## Ingesta Canónica de JSON

Incluso cuando la CLI recibe SCXML, el tiempo de ejecución primero lo convierte a su
forma SCJSON canónica y se ejecuta contra el árbol JSON. Esto garantiza que se apliquen
las mismas reglas de inferencia independientemente del formato de origen y permite que el motor
preserve el orden de autoría para el contenido ejecutable leyendo directamente de la
estructura JSON normalizada.

## Guía de Compatibilidad de Referencia

El tiempo de ejecución de Python trata a [`scion-core`](https://github.com/ReactiveSystems/scion-core)
como la referencia de comportamiento para la ejecución de SCXML:

- **Activo aguas arriba** – scion-core sigue la última especificación del W3C y aplica
  correcciones de errores más rápido que el antiguo motor Apache Commons.
- **Semántica canónica** – resuelve ambigüedades de larga data sobre
  el orden del documento, la finalización paralela y el ámbito del modelo de datos de una
  manera ampliamente adoptada. Coincidir con scion-core nos da un comportamiento predecible en
  todas las plataformas.
- **Ejecutor programable** – el repositorio incluye `tools/scion-runner/scion-trace.cjs`
  que es un envoltorio delgado que expone el mismo formato de traza JSONL que el motor de Python.
  El arnés de comparación puede, por lo tanto, diferenciar trazas sin
  adaptadores a medida.

### Usando el ejecutor de referencia

1. Instala Node.js 18+ y ejecuta `npm ci` dentro de `tools/scion-runner/`.
2. Invoca el ejecutor directamente o vía `SCJSON_REF_ENGINE_CMD`, ej.:

   ```bash
   export SCJSON_REF_ENGINE_CMD="node tools/scion-runner/scion-trace.cjs"
   python py/exec_compare.py examples/toggle.scxml --events tests/exec/toggle.events.jsonl
   ```

3. El arnés de comparación normaliza las trazas antes de compararlas; las divergencias aparecen
   en el primer paso que no coincide y conservan los artefactos en bruto para su inspección.

### Manejo de diferencias conocidas

scion-core implementa el modelo de datos ECMA por defecto. Nuestro motor actualmente
solo soporta el modelo de datos de Python; los gráficos que dependen de ayudantes específicos de ECMA
deben convertirse a expresiones de Python equivalentes antes de la comparación. Para
pruebas que aún dependen de `ecmascript`, establece `--unsafe-eval` temporalmente o protégelas
detrás de banderas de características.

La ejecución de referencia debe preceder al nuevo trabajo de características. Al extender el
tiempo de ejecución de Python, agrega gráficos de regresión a `tests/exec/` y actualiza el arnés para que
el nuevo escenario se ejercite contra scion-core.

### Estado del Contenido Ejecutable

- `<assign>`, `<log>` y `<raise>` se ejecutan en orden de autoría y alimentan la
  traza JSON.
- `<if>`/`<elseif>`/`<else>` y `<foreach>` respetan el orden del documento consultando
  la estructura JSON canónica en lugar de clases de datos regeneradas.
- `<send>` encola eventos internos (incluyendo `<param>` y cargas `namelist`);
  los envíos retrasados se encolan a través del planificador incorporado y pueden ser
  activados en pruebas con `DocumentContext.advance_time(seconds)`. `<cancel>`
  elimina los envíos internos pendientes por ID. Los bloques de `<content>` textuales se
  normalizan en objetos JSON antes de la validación para que los consumidores posteriores
  vean una estructura consistente, y el marcado anidado se serializa en diccionarios
  con claves `qname`/`text`/`children` para compatibilidad con las cargas de scion-core.
- Los cuerpos de transición se ejecutan entre la salida y la entrada:
  el contenido ejecutable adjunto a una `<transition>` se ejecuta después de que se procesa el conjunto de salida
  y antes de que se tome el conjunto de entrada, coincidiendo con el orden compatible con la especificación.
- Las transiciones sin objetivo se tratan como internas: no salen de ningún estado.
  Esto es necesario para manejadores como `done.state.region` que actualizan el
  modelo de datos pero mantienen la configuración intacta hasta una transición posterior.
- Los destinos externos de `<send>` no se ejecutan; el tiempo de ejecución encola
  `error.communication` y omite la entrega.
- Los bloques `<script>` no se ejecutan (no-op con una advertencia).

### Invocar y Finalizar (Andamiaje)

- El motor soporta una semántica básica de `<invoke>` suficiente para pruebas:
  - Al entrar en un estado (después de `onentry` y el procesamiento inicial), las invocaciones listadas
    bajo el estado se inician a través de un `InvokeRegistry` conectable.
  - Al salir de un estado (antes de `onexit`), cualquier invocación activa para el estado se
    cancela; sus bloques `<finalize>` se ejecutan en el ámbito del estado invocador.
  - Un registro simulado se envía con tres tipos de manejadores:
    - `mock:immediate`: se completa inmediatamente al iniciar y llama a la devolución de llamada `done`
      con la carga inicial; el motor ejecuta `<finalize>` y encola
      `done.invoke.<id>` con la carga.
    - `mock:record`: un manejador sin operación que registra los eventos reenviados a través de `send`.
    - `mock:deferred`: se completa cuando recibe un evento llamado `complete`.
  - La materialización de la carga útil refleja `<send>`: recopila `<param>`, `namelist` y
    `<content>` en un diccionario disponible para el manejador y como `_event.data`
    durante `<finalize>`.
  - Se respeta `idlocation`; cuando no se proporciona `id` se genera un UUID.
  - `typeexpr` y `srcexpr` se evalúan en el ámbito del estado cuando están presentes.
- `autoforward="true"` reenvía eventos externos (excluyendo `__*`, `error.*`,
  `done.state.*`, `done.invoke.*`) al manejador activo a través de `handler.send(name, data)`.
- Las máquinas SCXML/SCJSON hijas propagan sus eventos generados a la cola principal del padre;
  la finalización se detecta a través de `done.state.<childRootId>`.
  - El motor hijo reconoce `<send target="#_parent">` y emite directamente
    a la cola de eventos del padre cuando un emisor es adjuntado por el invocador.

Política de ordenación
- El motor expone un control de ordenación para emisiones de hijo a padre y entrega de `done.invoke`.
  Configúralo a través de la CLI `--ordering` o configurando `ctx.ordering_mode`.
  - `tolerant` (por defecto): las emisiones de hijo a padre se insertan al principio; `done.invoke`
    usa la inserción al principio solo cuando el hijo no emitió al padre antes en el paso.
  - `strict`: las emisiones de hijo a padre usan la cola normal (al final); `done.invoke` usa la cola normal
    (específica por ID y luego genérica).
  - `scion`: emula la ordenación de SCION: las emisiones de hijo a padre usan la cola normal, mientras
    que `done.invoke` se empuja al principio con genérico antes que específico por ID, lo que permite
    transiciones en el mismo microstep en un orden compatible con SCION.

Limitaciones:
- La semántica completa de invocación de SCXML (acoplamiento del procesador, máquinas anidadas, paridad de manejo de errores)
  no está implementada. El comportamiento actual está diseñado para
  desbloquear las pruebas del motor y puede extenderse detrás del `InvokeRegistry`.

### Invocadores Personalizados

Puedes extender el registro con tus propios tipos de invocación. Al iniciar, el
motor construye un `InvokeRegistry` por defecto que puedes aumentar:

```python
from scjson.invoke import InvokeHandler

class MyService(InvokeHandler):
    def start(self) -> None:
        # perform setup, and optionally complete immediately
        pass

    def send(self, name: str, data=None) -> None:
        # receive autoforwarded parent events or explicit #_child sends
        if name == 'complete':
            self._on_done({'result': 'ok'})

# during context creation or before run
ctx.invoke_registry.register('my:service', lambda t, src, payload, on_done=None: MyService(t, src, payload, on_done))
```

Una vez registrado, una entrada `<invoke type="my:service"/>` utilizará tu manejador.
Los manejadores pueden propagar eventos al padre a través del emisor del motor; el tiempo de ejecución
adjunta automáticamente un emisor para máquinas hijas, por lo que los envíos `#_parent` funcionan
de inmediato. Para servicios externos, prefiere emitir eventos padre con
`self._emit` cuando sea apropiado.

### Finalización y Eventos Done

- Entrar en un hijo `<final>` de un estado compuesto encola inmediatamente
  `done.state.<parentId>` después de ejecutar las acciones `onentry` del `<final>`.
- Si el elemento `<final>` contiene `<donedata>`:
  - `<content>` establece el valor completo de `_event.data` para el evento `done`.
  - De lo contrario, los pares `<param>` se convierten en un diccionario asignado a `_event.data`.
- Para `<parallel>`, el padre se considera completo solo una vez que todas las regiones están
  finalizadas; en ese momento, el motor encola `done.state.<parallelId>`.

### Historial (Superficial y Profundo)

- El historial superficial almacena el conjunto de hijos inmediatos activos al salir; al
  restaurar, esos hijos se reintroducen utilizando el procesamiento inicial normal.
- El historial profundo almacena el conjunto de hojas descendientes activas bajo el padre; al
  restaurar, el motor entra la ruta exacta desde el padre del historial hasta cada hoja guardada,
  sin seguir el `<initial>` de los nodos intermedios.
  Esto produce un retorno a la configuración anidada precisa previa a la salida.

### Errores

- Las condiciones que fallan al evaluarse, o que producen resultados no booleanos, encolan
  `error.execution` y se evalúan como falso.
- Los fallos de evaluación de `<foreach>` también encolan `error.execution` e iteran
  sobre una secuencia vacía.
- `<assign>`
  - Los fallos de expresión encolan `error.execution` y almacenan la cadena de expresión
    sin procesar como valor.
  - Las ubicaciones no válidas (sin variable coincidente en el ámbito) encolan
    `error.execution` y no crean una nueva variable.
- Los destinos externos de `<send>` encolan `error.communication` y se omiten.

### Coincidencia de Eventos de Transición

- Los atributos de evento admiten:
  - Listas de nombres separadas por espacios (cualquier coincidencia habilita la transición)
  - Comodín `*` (coincide con cualquier evento externo)
  - Patrones de prefijo como `error.*` (coincide, por ejemplo, con `error.execution`)

### Tutorial Sweep y Lista de Omisión

El arnés de regresión `py/uber_test.py::test_python_engine_executes_python_charts`
detecta el motor de Python en tiempo de ejecución, carga cada gráfico tutorial con
`datamodel="python"` y agrega las fallas con sus diferencias de traza.
Los gráficos que dependen de características no soportadas se capturan en
`ENGINE_KNOWN_UNSUPPORTED` (ver `py/uber_test.py:44-58`); actualiza esa lista
cada vez que se implementan nuevas capacidades para que las regresiones genuinas sigan siendo visibles.
Las advertencias emitidas durante la ejecución se conservan en el resumen de fallas para
resaltar las deficiencias, como los destinos externos o los cuerpos `<script>`.

Al agregar cobertura para nuevos comportamientos (por ejemplo, cancelación de `<send>` retrasada),
prefiera pruebas unitarias enfocadas junto con el barrido y elimine las entradas de omisión una vez que
el escenario pase de principio a fin.
```

```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquete JavaScript scjson

Este directorio contiene la implementación en JavaScript de **scjson**, un formato para representar máquinas de estado SCXML en JSON. El paquete proporciona una interfaz de línea de comandos para convertir entre archivos `.scxml` y `.scjson` y para validar documentos contra el esquema del proyecto.

Para detalles sobre cómo se infieren los elementos SCXML durante la conversión, consulte [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).

El paquete incluye tipos de TypeScript para las funciones y funciones predeterminadas para devolver cada uno.

## Instalación

```bash
npm install scjson
```

También puede instalarlo desde un checkout de este repositorio:

```bash
cd js && npm install
```

## Código Fuente - Soporte Multi-idioma
[https://github.com/SoftOboros/scjson/]
- csharp
- go
- java
- javascript / typescript
- lua
- python
- ruby
- rust
- swift

## Uso de Línea de Comandos

Después de la instalación, el comando `scjson` está disponible:

```bash
# Convertir un solo archivo
scjson json path/to/machine.scxml

# Convertir de nuevo a SCXML
scjson xml path/to/machine.scjson

# Validar recursivamente
scjson validate path/to/dir -r
```

## CLI del Harness (SCION)

El paquete también incluye un CLI de harness que ejecuta SCXML usando el motor SCION
y emite trazas JSONL compatibles con las herramientas de comparación.

Instale la dependencia de pares:
```bash
npm i scion-core
```

Uso:
```bash
npx scjson-scion-trace -I path/to/chart.(scxml|scjson) -e path/to/events.jsonl [--xml]
```

Verificación rápida (desde este repositorio):
```bash
cd js
npm ci
npm run harness:sample
```

Banderas:
- `--leaf-only` – emite configuraciones solo de hoja (SCION ya reporta estados atómicos)
- `--omit-delta` – borra `datamodelDelta`
- `--omit-transitions` – borra `firedTransitions`
- `--strip-step0-noise` – en el paso 0, borra `datamodelDelta` y `firedTransitions`
- `--strip-step0-states` – en el paso 0, borra `enteredStates` y `exitedStates`

Notas:
- La entrada `.scjson` se convierte a SCXML internamente antes de la ejecución.
- SCION no modela el tiempo; los tokens de control `{"advance_time": N}` emiten un
  paso sintético para mantener el progreso de los flujos.

## Funciones de Conversión
```js
/**
 * xmlToJson
 * Convierte una cadena SCXML a scjson.
 *
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {string} xmlStr - Entrada XML.
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {boolean} [omitEmpty=true] - Elimina valores vacíos cuando es verdadero.
 * @returns {string} Representación JSON.
 */

/**
 * jsonToXml
 * Convierte una cadena scjson a SCXML.
 *
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {string} jsonStr - Entrada JSON.
 * @returns {string} Salida XML.
 */
```

## Uso Común de Traducción JS
```js
const { xmlToJson, jsonToXml } = require('scjson');

```

## Uso de Traducción ESR
```js
import { xmlToJson, jsonToXml }from "scjson/browser"
```

## Conversores Compartidos
Tanto las compilaciones de Node como las de navegador usan la misma lógica de conversión expuesta en
`scjson/converters`. Puede importar estos ayudantes directamente si necesita acceso a
las funciones de utilidad usadas por el CLI y los módulos del navegador.
```js
import { xmlToJson, jsonToXml } from 'scjson/converters';
```

## Ejemplo de Endpoint de Axios
```typescript
import axios from "axios"
import * as scjson from "scjson/props"

// Una función para crear un nuevo documento con tres estados y transiciones.
const newScxml = (): scjson.ScxmlProps => {
  const doc: scjson.ScxmlProps = scjson.defaultScxml();
  let state: scjson.StateProps = scjson.defaultState();
  let transition: scjson.TransitionProps = scjson.defaultTransition();
  doc.name = 'New State Machine';
  doc.exmode = scjson.ExmodeDatatypeProps.Lax;
  doc.binding = scjson.BindingDatatypeProps.Early;
  doc.initial.push('Start');
  state.id = 'Start';
  transition.target.push('Process');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'Process';
  transition = scjson.defaultTransition();
  transition.target.push('End');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'End';
  transition = scjson.defaultTransition();
  transition.target.push('Start');
  state.transition.push(transition);
  doc.state.push(state);
  return doc;
}

// Crear instancia de Axios
const ax = axios.create({
  baseURL: "https://api.example.com/scxml",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Exportar una función para enviar el documento
export const sendNewScxml = () => {
  const doc = newScxml();
  ax.post('/newDoc', doc);
}

```

## Problemas Conocidos
Ninguno en este momento.

Las pruebas de conformidad operativa se realizan a través de [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Nota: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) aplica todos los archivos scxml en [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) que proporciona un conjunto robusto de vectores de prueba scxml útiles para la verificación de cumplimiento estándar. Este es el único archivo en el conjunto de pruebas que no logra verificar el viaje de ida y vuelta.


### `scjson/props`

### Enumeraciones

Cada enumeración representa un conjunto de cadenas restringidas utilizadas por SCXML. Los valores
que se muestran a continuación reflejan los definidos en el esquema SCJSON.

Las enumeraciones utilizan este patrón para permitir que todas las partes estáticas y dinámicas se traten por separado,
pero se asignan al mismo nombre.
```typescript
export const BooleanDatatypeProps = {
    False: "false",
    True: "true",
} as const;

export type BooleanDatatypeProps = typeof BooleanDatatypeProps[keyof typeof BooleanDatatypeProps];
```

- `AssignTypeDatatypeProps` – cómo el elemento `<assign>` manipula el modelo de datos.
  Valores: `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatypeProps` – determina si las variables del modelo de datos se enlazan `early` o
  `late` durante la ejecución.
- `BooleanDatatypeProps` – valores de atributo booleano `true` o `false`.
- `ExmodeDatatypeProps` – modo de ejecución del procesador, ya sea `lax` o `strict`.
- `HistoryTypeDatatypeProps` – tipo de estado `<history>`: `shallow` o `deep`.
- `TransitionTypeDatatypeProps` – si una `<transition>` es `internal` o
  `external`.

### Tipos Comunes

Varias clases generadas comparten campos de ayuda genéricos:

- `other_attributes`: `Record<str, str>` que captura atributos XML adicionales de
  espacios de nombres externos.
- `other_element`: `list[object]` que permite preservar nodos hijos sin tipo de otros
  espacios de nombres.
- `content`: `list[object]` utilizado cuando los elementos permiten contenido mixto o comodín.


### Tipos de Documentos / Objetos
Tipos Plain TypeScript sin validación en tiempo de ejecución.
- `AssignProps` `AssignArray`         – actualiza una ubicación del modelo de datos con una expresión o valor.
- `CancelProps` `CancelArray`         – cancela una operación `<send>` pendiente.
- `ContentProps` `ContentArray`       – carga útil en línea utilizada por `<send>` e `<invoke>`.
- `DataProps` `DataArray`             – representa una sola variable del modelo de datos.
- `DatamodelProps` `DatamodelArray`   – contenedor para uno o más elementos `<data>`.
- `DonedataProps` `DonedataArray`     – carga útil devuelta cuando se alcanza un estado `<final>`.
- `ElseProps`                         – rama de respaldo para condiciones `<if>`.
- `ElseifProps`                       – rama condicional que sigue a un `<if>`.
- `FinalProps` `FinalArray`           – marca un estado terminal en la máquina.
- `FinalizeProps` `FinalizeArray`     – ejecutado después de que un `<invoke>` se complete.
- `ForeachProps` `ForeachArray`       – itera sobre elementos dentro del contenido ejecutable.
- `HistoryProps` `HistoryArray`       – pseudoestado que recuerda los hijos activos anteriores.
- `IfProps` `IfArray`                 – bloque de ejecución condicional.
- `InitialProps` `InitialArray`       – estado inicial dentro de un estado compuesto.
- `InvokeProps` `InvokeArray`         – ejecuta un proceso o máquina externa.
- `LogProps` `LogArray`               – declaración de salida de diagnóstico.
- `OnentryProps` `OnentryArray`       – acciones realizadas al entrar en un estado.
- `OnexitProps` `OnexitArray`         – acciones realizadas al salir de un estado.
- `ParallelProps` `ParallelArray`     – coordina regiones concurrentes.
- `ParamProps` `ParamArray`           – parámetro pasado a `<invoke>` o `<send>`.
- `RaiseProps` `RaiseArray`           – genera un evento interno.
- `ScriptProps` `ScriptArray`         – script ejecutable en línea.
- `ScxmlProps`                        – elemento raíz de un documento SCJSON.
- `SendProps` `SendArray`             – despacha un evento externo.
- `StateProps` `StateArray`           – nodo de estado básico.
- `TransitionProps` `TransitionArray` – arista entre estados activada por eventos.

### Gestión de Objetos
- Tipo - marcador único para cada uno de los tipos.
```typescript
export type Kind = "number" | "string" | "record<string, object>" | "number[]" | "string[]"
                   | "record<string, object>[]" | "assign" | "assigntypedatatype" | "bindingdatatype" | "booleandatatype"
                   | "cancel" | "content" | "data" | "datamodel" | "donedata" | "else" | "elseif"
                   | "exmodedatatype" | "final" | "finalize" | "foreach" | "history" | "historytypedatatype" | "if"
                   | "initial" | "invoke" | "log" | "onentry" | "onexit" | "parallel" | "param" | "raise"
                   | "script" | "scxml" | "send" | "state" | "transition" | "transitiontypedatatype"
                   | "assignarray" | "cancelarray" | "contentarray" | "dataarray" | "datamodelarray"
                   | "donedataarray" | "finalarray" | "finalizearray" | "foreacharray" | "historyarray" | "ifarray"
                   | "initialarray" | "invokearray" | "logarray" | "onentryarray" | "onexitarray" | "parallelarray"
                   | "paramarray" | "raisearray" | "scriptarray" | "sendarray" | "statearray" | "transitionarray";
```
- PropsUnion - una unión de los tipos utilizados en el modelo de datos scxml
```typescript
export type PropsUnion = null | string | number | Record<string, object> | string[] | number[]
                         | Record<string, object>[] | AssignProps | AssignTypeDatatypeProps | BindingDatatypeProps
                         | BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | ExmodeDatatypeProps | FinalProps | FinalizeProps | ForeachProps
                         | HistoryProps | HistoryTypeDatatypeProps | IfProps | InitialProps | InvokeProps | LogProps
                         | OnentryProps | OnentryArray | OnexitProps | OnexitArray | ParallelProps | ParamProps
                         | RaiseProps | ScriptProps | ScxmlProps | SendProps | StateProps | TransitionProps | TransitionTypeDatatypeProps
                         | AssignArray | CancelArray | ContentArray | DataArray | DatamodelArray | DonedataArray
                         | FinalArray | FinalizeArray | ForeachArray | HistoryArray | IfArray | InitialArray
                         | InvokeArray | LogArray | OnentryArray | OnexitArray | ParallelArray | ParamArray
                         | RaiseArray | ScriptArray | SendArray | StateArray | TransitionArray;
```
- KindMap - mapea el nombre de cadena a tipo para los objetos utilizados en el modelo de datos scxml
```typescript
export type KindMap = {
    assign: AssignProps
    assignarray: AssignArray
    assigntypedatatype: AssignTypeDatatypeProps
    bindingdatatype: BindingDatatypeProps
    booleandatatype: BooleanDatatypeProps
    cancel: CancelProps
    cancelarray: CancelArray
    content: ContentProps
    contentarray: ContentArray
    data: DataProps
    dataarray: DataArray
    datamodel: DatamodelProps
    datamodelarray: DatamodelArray
    donedata: DonedataProps
    donedataarray: DonedataArray
    else: ElseProps
    elseif: ElseifProps
    exmodedatatype: ExmodeDatatypeProps
    final: FinalProps
    finalarray: FinalArray
    finalize: FinalizeProps
    finalizearray: FinalizeArray
    foreach: ForeachProps
    foreacharray: ForeachArray
    history: HistoryProps
    historyarray: HistoryArray
    historytypedatatype: HistoryTypeDatatypeProps
    if: IfProps
    ifarray: IfArray
    initial: InitialProps
    initialarray: InitialArray
    invoke: InvokeProps
    invokearray: InvokeArray
    log: LogProps
    logarray: LogArray
    onentry: OnentryProps
    onentryarray: OnentryArray
    onexit: OnexitProps
    onexitarray: OnexitArray
    parallel: ParallelProps
    parallelarray: ParallelArray
    param: ParamProps
    paramarray: ParamArray
    raise: RaiseProps
    raisearray: RaiseArray
    script: ScriptProps
    scriptarray: ScriptArray
    scxml: ScxmlProps
    send: SendProps
    sendarray: SendArray
    state: StateProps
    statearray: StateArray
    transition: TransitionProps
    transitionarray: TransitionArray
    transitiontypedatatype: TransitionTypeDatatypeProps
}
```


### Otros Recursos
GitHub: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git @github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

PyPI: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

Cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

DockerHub: [https://hub.docker.com/r/iraa/scjson]
(Entorno de desarrollo completo para todos los lenguajes soportados)
```bash
docker pull iraa/scjson:latest
```


Todo el código fuente en este directorio se publica bajo la Licencia BSD de 1 Cláusula. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para más detalles.
```

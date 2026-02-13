```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquete Python scjson

Este directorio contiene la implementación en Python de **scjson**, un formato para representar máquinas de estado SCXML en JSON. El paquete proporciona una interfaz de línea de comandos y funciones de utilidad para convertir entre archivos `.scxml` y `.scjson`, y para validar documentos contra el esquema del proyecto.

El paquete incluye tipos pydantic y dataclasses para los objetos/enums asociados en formas estándar y estrictas.

Para obtener detalles sobre cómo se infieren los elementos SCXML durante la conversión, consulte [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md). En Python, la inferencia para la conversión es manejada por los modelos de dataclasses. Véase más abajo.

## Instalación

```bash
pip install scjson
```

También puede instalar desde una copia de este repositorio:

```bash
cd py && pip install -e .
```

## Código Fuente - Soporte Multi-Lenguaje
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

## Motor Python — Guía de Usuario

Para el uso completo del motor de ejecución de Python (rastreo, comparación con una referencia, generación de vectores, barrido de corpus), consulte:

- docs/ENGINE-PY.md (en este repositorio)

En línea: https://github.com/SoftOboros/scjson/blob/main/docs/ENGINE-PY.md

## Dependencia de Referencia SCION

Varias pruebas de comparación (`py/tests/test_exec_compare_advanced.py`) y la herramienta `exec_compare` invocan el ejecutor [SCION](https://www.npmjs.com/package/scion) basado en Node incluido en `tools/scion-runner`. Node.js debe poder resolver los paquetes [SCION](https://www.npmjs.com/package/scion) (`scxml`, `jsdom` y `regenerator-runtime`) a través de su cargador de módulos. Instálelos una vez antes de ejecutar las comparaciones:

```bash
cd tools/scion-runner
npm ci  # or npm install
```

Al ejecutar las pruebas de Python o las comparaciones de CLI, asegúrese de que `node` pueda cargar estos módulos (por ejemplo, manteniendo la instalación anterior o agregando su ubicación a `NODE_PATH`). Sin los paquetes [SCION](https://www.npmjs.com/package/scion), las comparaciones recurrirán al motor de Python.

## Uso en Línea de Comandos

Después de la instalación, el comando `scjson` está disponible:

```bash
# Convertir un solo archivo
scjson json path/to/machine.scxml

# Convertir de nuevo a SCXML
scjson xml path/to/machine.scjson - o path/to/output.scxml

# Validar recursivamente
scjson validate path/to/dir -r

# Generar tipos TypeScript
scjson  typescript -o dir/of/output

# Generar scjson.schema.json
scjson  schema -o dir/of/output
```

## Ejemplo de Uso con FastAPI
Este es un endpoint mínimo de FastAPI como ejemplo de uso de la clase SCXMLDocumentHandler.

```python
import json
from fastapi import FastAPI, Request, HTTPException, Response
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

app = FastAPI()
handler = SCXMLDocumentHandler(schema_path=None)

# Almacén en memoria para demostración
store = {}

 @app.get("/xml/{slug}")
async def get_xml(slug: str):
    """Return the SCXML document as XML."""
    data = store.get(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Document not found")
    xml_str = handler.json_to_xml(json.dumps(data))
    return Response(content=xml_str, media_type="application/xml")

 @app.post("/xml/{slug}")
async def post_xml(slug: str, request: Request):
    """Accept an SCXML document and convert it to scjson."""
    xml_bytes = await request.body()
    xml_str = xml_bytes.decode("utf-8")
    json_str = handler.xml_to_json(xml_str)
    data = json.loads(json_str)
    data.setdefault("name", slug)
    store[slug] = data
    return data
```

## Importación de Objetos
Esto importa las definiciones de tipos individuales. Véase a continuación para variantes de librerías.
Variantes de clase disponibles para pydantic y dataclasses que implementan tanto las variantes XSD estándar como estrictas.

```python
from scjson.pydantic import Scxml, State, Transition, Onentry # etc.

```

## Advertencias de SCJSON

Los ayudantes de conversión de SCXML normalizan los datos para que puedan almacenarse como JSON.
Durante la serialización `asdict()`, los dataclasses generados pueden contener valores `Decimal` e instancias de enumeración (por ejemplo, `AssignTypeDatatype`).

- Los valores `Decimal` se convierten en números de punto flotante.
- Los valores Enum se almacenan usando su cadena `.value`.

Estas conversiones permiten que la representación JSON sea serializada por
`json.dumps` y luego convertida de nuevo a través del ayudante `_to_dataclass`.

## Problemas Conocidos
Ninguno en este momento.

Las pruebas de conformidad operativa se realizan a través de [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l python 2>&1 | tee test.log
```
Nota: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) aplica todos los archivos scxml en [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/), que proporciona un conjunto robusto de vectores de prueba scxml útiles para la verificación de cumplimiento estándar. Este es el único archivo en el conjunto de pruebas que no logra verificar el viaje de ida y vuelta.

### Arnés de Prueba Uber

Ejecutar en todos los lenguajes o en un solo lenguaje con soporte de alias:

```bash
# Todos los lenguajes detectados en PATH
python py/uber_test.py

# Un solo lenguaje (se permiten alias): py, python, js, ts, javascript, rs, rust, swift, java, csharp
python py/uber_test.py -l js
python py/uber_test.py -l swift   # se tolera el error tipográfico → swift

# Limitar el corpus y tratar el consenso solo como advertencias
python py/uber_test.py -l swift -s "Examples/Qt/StopWatch/*.scxml" --consensus-warn
```

- `-s/--subset` filtra archivos SCXML por un patrón glob relativo a `tutorial/`.
- `--consensus-warn` degrada las inconsistencias a advertencias cuando los lenguajes de referencia (Python/JavaScript/Rust) coinciden con la estructura canónica.
- El arnés normaliza las diferencias estructurales (véase INFERENCE.md) para producir diferencias accionables e imprime una línea de clasificación con una recomendación.

## Variantes de Modelo

El paquete Python expone cuatro conjuntos de modelos generados que reflejan el
esquema SCJSON. Todos comparten los mismos nombres de campo y enumeraciones, pero
ofrecen diferentes características en tiempo de ejecución.

### Enums

Cada enumeración representa un conjunto de cadenas restringidas utilizadas por SCXML. Los valores
que se muestran a continuación reflejan los definidos en el esquema SCJSON.

- `AssignTypeDatatype` – cómo el elemento `<assign>` manipula el modelo de datos.
  Valores: `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatype` – determina si las variables del modelo de datos se enlazan `early` o
  `late` durante la ejecución.
- `BooleanDatatype` – valores de atributo booleano `true` o `false`.
- `ExmodeDatatype` – modo de ejecución del procesador, ya sea `lax` o `strict`.
- `HistoryTypeDatatype` – tipo de estado `<history>`: `shallow` o `deep`.
- `TransitionTypeDatatype` – si una `<transition>` es `internal` o
  `external`.

## Tipos Comunes

Varias clases generadas comparten campos auxiliares genéricos:

- `other_attributes`: `dict[str, str]` que captura atributos XML adicionales de
  espacios de nombres externos.
- `other_element`: `list[object]` que permite preservar nodos hijos no tipados de otros
  espacios de nombres.
- `content`: `list[object]` utilizado cuando los elementos permiten contenido mixto o comodín.

### `scjson.dataclasses`

Dataclasses de Python simple sin validación en tiempo de ejecución.

- `Assign` – actualiza una ubicación del modelo de datos con una expresión o valor.
- `Cancel` – cancela una operación `<send>` pendiente.
- `Content` – carga útil en línea utilizada por `<send>` y `<invoke>`.
- `Data` – representa una única variable del modelo de datos.
- `Datamodel` – contenedor para uno o más elementos `<data>`.
- `Donedata` – carga útil devuelta cuando se alcanza un estado `<final>`.
- `Else` – rama de respaldo para condiciones `<if>`.
- `Elseif` – rama condicional que sigue a un `<if>`.
- `Final` – marca un estado terminal en la máquina.
- `Finalize` – ejecutado después de que un `<invoke>` se complete.
- `Foreach` – itera sobre elementos dentro de contenido ejecutable.
- `History` – pseudoestado que recuerda hijos activos anteriores.
- `If` – bloque de ejecución condicional.
- `Initial` – estado inicial dentro de un estado compuesto.
- `Invoke` – ejecuta un proceso o máquina externa.
- `Log` – sentencia de salida de diagnóstico.
- `Onentry` – acciones realizadas al entrar en un estado.
- `Onexit` – acciones realizadas al salir de un estado.
- `Parallel` – coordina regiones concurrentes.
- `Param` – parámetro pasado a `<invoke>` o `<send>`.
- `Raise` – genera un evento interno.
- `Script` – script ejecutable en línea.
- `Scxml` – elemento raíz de un documento SCJSON.
- `Send` – despacha un evento externo.
- `State` – nodo de estado básico.
- `Transition` – borde entre estados activado por eventos.

### `scjson.dataclasses_strict`

Las mismas dataclasses que las anteriores pero configuradas para una verificación de tipos más estricta.

### `scjson.pydantic`

Clases `BaseModel` de Pydantic generadas a partir del esquema SCJSON. Proporcionan
validación de datos y ayudantes `.model_dump()` convenientes.

### `scjson.pydantic_strict`

Modelos Pydantic con configuraciones de validación estrictas.

### Otros Recursos
github: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git @github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

npm: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
```

cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Entorno de desarrollo completo para todos los lenguajes soportados)
```bash
docker pull iraa/scjson:latest
```

## Licencia

Todo el código fuente en este directorio se publica bajo la Licencia BSD de 1 Cláusula. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles.
```

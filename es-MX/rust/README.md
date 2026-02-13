```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Crate Rust de scjson

Este directorio contiene la implementación en Rust de **scjson**. Ofrece una herramienta de línea de comandos y una biblioteca de soporte para convertir entre archivos `.scxml` y `.scjson`, y para validar documentos.

Para obtener detalles sobre cómo se infieren los elementos SCXML durante la conversión, consulte [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).

## Instalación

```bash
cargo install scjson
```

También puede construir desde este repositorio:

```bash
cd rust && cargo build --release
```

# Código Fuente - Soporte Multi-Lenguaje
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

## Uso de la Línea de Comandos

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

## Problemas Conocidos
Ninguno en este momento.

Las pruebas de conformidad operativa se realizan a través de [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Nota: [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) aplica todos los archivos scxml en [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/), que proporciona un sólido conjunto de vectores de prueba scxml útiles para la verificación de cumplimiento estándar. Este es el único archivo en el conjunto de pruebas que no verifica el viaje de ida y vuelta.

### Enumeraciones
Cada enumeración representa un conjunto de cadenas restringido utilizado por SCXML. Los valores que se muestran a continuación reflejan los definidos en el esquema SCJSON.
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
- `AssignProps` `AssignArray` – actualiza una ubicación del modelo de datos con una expresión o valor.
- `CancelProps` `CancelArray` – cancela una operación `<send>` pendiente.
- `ContentProps` `ContentArray` – carga útil en línea utilizada por `<send>` y `<invoke>`.
- `DataProps` `DataArray` – representa una única variable del modelo de datos.
- `DatamodelProps` `DatamodelArray` – contenedor para uno o más elementos `<data>`.
- `DonedataProps` `DonedataArray` – carga útil devuelta cuando se alcanza un estado `<final>`.
- `ElseProps` – rama de respaldo para las condiciones `<if>`.
- `ElseifProps` – rama condicional que sigue a un `<if>`.
- `FinalProps` `FinalArray` – marca un estado terminal en la máquina.
- `FinalizeProps` `FinalizeArray` – ejecutado después de que un `<invoke>` se completa.
- `ForeachProps` `ForeachArray` – itera sobre elementos dentro del contenido ejecutable.
- `HistoryProps` `HistoryArray` – pseudoestado que recuerda los hijos activos anteriores.
- `IfProps` `IfArray` – bloque de ejecución condicional.
- `InitialProps` `InitialArray` – estado inicial dentro de un estado compuesto.
- `InvokeProps` `InvokeArray` – ejecuta un proceso o máquina externa.
- `LogProps` `LogArray` – declaración de salida de diagnóstico.
- `OnentryProps` `OnentryArray` – acciones realizadas al entrar en un estado.
- `OnexitProps` `OnexitArray` – acciones realizadas al salir de un estado.
- `ParallelProps` `ParallelArray` – coordina regiones concurrentes.
- `ParamProps` `ParamArray` – parámetro pasado a `<invoke>` o `<send>`.
- `RaiseProps` `RaiseArray` – levanta un evento interno.
- `ScriptProps` `ScriptArray` – script ejecutable en línea.
- `ScxmlProps` – elemento raíz de un documento SCJSON.
- `SendProps` `SendArray` – despacha un evento externo.
- `StateProps` `StateArray` – nodo de estado básico.
- `TransitionProps` `TransitionArray` – borde entre estados activado por eventos.

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

pypi: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Entorno de desarrollo completo para todos los lenguajes soportados)
```bash
docker pull iraa/scjson:latest
```

Todo el código fuente en este directorio se publica bajo la licencia BSD 1-Clause. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles.
```

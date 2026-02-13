```markdown
<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# scjson

> Una serialización basada en JSON de SCXML (State Chart XML) para herramientas modernas, interoperabilidad y educación.

**Motores de Ejecución**
- Motor Python: Emisor de trazas determinista, generación de vectores y herramientas de comparación. Consulte `docs/ENGINE-PY.md` y `py/ENGINE-PY-DETAILS.md`.
- Motor Ruby: Interfaz de traza en desarrollo activo con creciente paridad de características. Consulte `docs/ENGINE-RB.md`.

**Arnés JS/TS (a través de SCION)**
- El paquete JS incluye una CLI de arnés `scjson-scion-trace` que requiere directamente `scion-core` para ejecutar SCXML y emitir trazas JSONL. Instale `scion-core` en su proyecto para habilitarlo.
- Soporta entrada `.scxml` y `.scjson` (este último se convierte a SCXML internamente).
- Banderas de normalización: `--leaf-only`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`.
- Uso (paquete): `npx scjson-scion-trace -I chart.(scxml|scjson) -e events.jsonl [--xml] [--leaf-only] [--omit-delta] [...]`
- Alternativa de desarrollo (en este repositorio): `node tools/scion-runner/scion-trace.cjs -I chart.scxml -e events.jsonl --xml`

---

## Resumen

`scjson` es una representación estructurada y basada en esquemas de [SCXML](https://www.w3.org/TR/scxml/), el estándar W3C para el modelado de máquinas de estado. Este formato conserva la semántica y la jerarquía de SCXML al tiempo que lo hace más accesible para herramientas, lenguajes e interfaces modernas.

¿Por qué JSON?

- Más fácil de analizar en JavaScript, Python, Rust, etc.
- Se adapta naturalmente a las API REST, editores y validación estática
- Puede ser convertido de ida y vuelta a SCXML estándar
- Funciona con formatos compactos como MessagePack o Protobuf cuando es necesario

---

## Objetivos

- 💡 **Interoperabilidad**: Servir como puente entre SCXML y los ecosistemas de aplicaciones modernas
- 📦 **Portabilidad**: Permitir la traducción a formatos binarios (MessagePack, Protobuf, etc.)
- 📚 **Pedagogía**: Facilitar la enseñanza y el aprendizaje de máquinas de estado con una sintaxis más limpia y herramientas visuales
- 🔁 **Fidelidad de ida y vuelta**: Admitir la conversión de nuevo a SCXML válido sin pérdida semántica

---

## Esquema

El archivo canónico `scjson.schema.json` se encuentra en [`/scjson.schema.json`](./scjson.schema.json).
Se genera a partir de modelos Pydantic y se utiliza para validar todos los documentos `*.scjson`.
Las reglas de inferencia detalladas utilizadas por los convertidores se describen en [INFERENCE.md](./INFERENCE.md).

---

## Estructura de Directorios

Cada implementación de lenguaje reside en su propio directorio, como un módulo o raíz de biblioteca independiente:

/schema/ → Definición del esquema JSON de scjson
/examples/ → Pares de ejemplos SCXML y scjson
/tutorial/ → Submódulo de Git: Tutorial de Zhornyak SCXML
/python/ → Implementación de referencia de Python (CLI + biblioteca)
/js/ → CLI y biblioteca de JavaScript
/ruby/ → CLI y gema de Ruby
/go/ → Utilidad de línea de comandos de Go
/rust/ → Utilidad de línea de comandos de Rust
/swift/ → Herramienta de línea de comandos de Swift
/java/ → Herramienta de línea de comandos de Java
/lua/ → Scripts de Lua
/csharp/ → Herramienta de línea de comandos de C#


Cada directorio está diseñado para ser utilizable de forma independiente como una biblioteca o herramienta CLI.

---

## Convertidores y Motores

| Lenguaje | Estado | Ruta | Notas |
|----------|--------|------|-------|
| Python | ✅ Canónico | [py](./py/README.md) | Implementación de referencia y línea base de compatibilidad |
| JavaScript| ✅ Paridad | [js](./js/README.md) | Coincide con la salida de Python en el corpus del tutorial; arnés disponible a través de SCION |
| Ruby | ✅ Paridad | [ruby](./ruby/README.md) | Paridad de convertidor; interfaz de traza del motor en desarrollo activo |
| Rust | ✅ Paridad | [rust](./rust/README.md) | Coincide con la salida de Python en el corpus del tutorial |
| Java | ✅ Paridad | [java](./java/README.md) | Utiliza el ejecutor respaldado por [SCION](https://www.npmjs.com/package/scion); coincide con la salida de Python |
| Go | ✅ Paridad | [go](./go/README.md) | Coincide con la salida de Python en el corpus del tutorial |
| Swift | ✅ Paridad | [swift](./swift/README.md) | Coincide con la salida de Python en el corpus del tutorial |
| C# | ⚠️ Beta | [csharp](./csharp/README.md) | CLI funcional; trabajo de paridad en progreso |
| Lua | ✅ Paridad | [lua](./lua/README.md) | Coincide con la salida de Python en el corpus del tutorial |

Consulte [docs/COMPATIBILITY.md](./docs/COMPATIBILITY.md) para obtener los últimos detalles de paridad entre lenguajes y notas de prueba.

---

## Ejemplos y Suite de Pruebas

Este repositorio incluye un conjunto curado de ejemplos canónicos de SCXML y sus formas `scjson` equivalentes en [`/examples`](./examples). Estos se utilizan para:

- Validación funcional (SCXML ↔ scjson ↔ SCXML)
- Enseñar conceptos de máquinas de estado a través de herramientas visuales
- Demostrar el uso en editores, bibliotecas de UI y plataformas de bajo código

Estos ejemplos se derivan y/o adaptan de:

### 📚 Tutorial Incluido (como Submódulo de Git)

Incluimos el **Tutorial del Editor SCXML de Alex Zhornyak** como un submódulo de Git en [`/tutorial`](./tutorial).
Esto proporciona un amplio conjunto de casos de prueba y diagramas SCXML canónicos.

> La atribución se proporciona con fines educativos. No se implica ningún respaldo.
> Fuente: [https://alexzhornyak.github.io/ScxmlEditor-Tutorial/](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/)

---

### 🛠️ Configuración del Submódulo

Si clonó este repositorio y `/tutorial` está vacío, ejecute:

```bash
git submodule init
git submodule update
O clone con submódulos en un solo paso:

git clone --recurse-submodules https://github.com/your-org/scjson.git
```

Esto asegura que obtenga el contenido completo del tutorial junto con los ejemplos y convertidores.

---

## Convertidores
Todos los convertidores comparten el mismo esquema y suite de pruebas para garantizar la compatibilidad.

---

## Primeros Pasos

```bash
# Convertir de SCXML a scjson
scjson convert --from scxml path/to/file.scxml --to scjson path/to/file.scjson

# Validar un archivo scjson
scjson validate path/to/file.scjson
```

### Disponibilidad del Repositorio de Paquetes
pypi: [https://pypi.org/project/scjson/]
```bash
pip install scjson
```
npm: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
# el arnés requiere scion-core
npm install scion-core
```

Arnés (Node):
```bash
npx scjson-scion-trace -I path/to/chart.scxml -e events.jsonl --xml
```

rubygems: [https://rubygems.org/gems/scjson]
```bash
gem install scjson
```
Notas de RubyGems:
- La CLI de Ruby incluye convertidores y una interfaz de traza. Consulte `docs/ENGINE-RB.md` para el uso y la madurez del motor. La gema se publica en el enlace anterior.

cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Entorno de desarrollo completo para todos los lenguajes soportados)
```bash
docker pull iraa/scjson:latest
```

Para un ejemplo completo de instalación de cadenas de herramientas y dependencias entre lenguajes, consulte [`codex/startup.sh`](codex/startup.sh).


## Documentación

- Guía de usuario (motor Python): `docs/ENGINE-PY.md`
- Arquitectura y referencia en profundidad (Python): `py/ENGINE-PY-DETAILS.md`
- Matriz de compatibilidad: `docs/COMPATIBILITY.md`
- Guía de pruebas: `TESTING.md`
- Resumen de agentes: `AGENTS.md`


## Divergencias y Problemas Conocidos

Las comparaciones entre motores a veces revelan diferencias intencionales y documentadas (por ejemplo, matices de ordenación, semántica ECMA `in`, reentrada de historial). Utilice estos recursos para comprender, normalizar y clasificar el comportamiento en SCION (Node), Python y Ruby:

- Visión general completa: docs/COMPATIBILITY.MD
- Perfil de normalización: `--norm scion` en exec_compare establece leaf-only, omit-delta, omit-transitions, strip-step0-states y ordering=scion.
  - Ejemplo: `python py/exec_compare.py tests/exec/toggle.scxml --events tests/exec/toggle.events.jsonl --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
- Lista de diferencias conocidas de CI: scripts/ci_ruby_known_diffs.txt (utilizado por `scripts/ci_ruby_harness.sh --known` para mantener CI en verde mientras se informan los desajustes esperados).
- Convertidor Ruby en CI: cuando Nokogiri no está disponible, la CLI de Ruby recurre al convertidor de Python solo para SCXML↔scjson; la ejecución sigue siendo Ruby. Consulte docs/ENGINE-RB.md (Notas de CI).


## Instalaciones Rápidas.

### Módulo Python
```bash
cd py
pip install -r requirements.txt
pytest -q
```

### Módulo JavaScript
```bash
cd js
npm ci
npm test --silent
```

### Módulo Ruby
```bash
cd ruby
gem install bundler
bundle install
bundle exec rspec
```

### Módulo Go
```bash
cd go
go test ./...
go build
```

### Módulo Rust
```bash
cd rust
cargo test
```

### Módulo Swift
```bash
cd swift
swift test
```

### Módulo C#
```bash
cd csharp
dotnet test -v minimal
```

### Módulo Lua
```bash
cd lua
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
busted tests
```

## Legal y Documentación

Todo el código fuente en este directorio se publica bajo la licencia BSD de 1 cláusula. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles. Hay documentación adicional disponible en [AGENTS.md](./AGENTS.md) y [TESTING.md](./TESTING.md).
```

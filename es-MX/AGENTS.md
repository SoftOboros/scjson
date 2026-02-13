```markdown
<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# AGENTES

Este archivo define los agentes y sus respectivos roles para el proyecto `scjson`. Cada agente es responsable de una tarea específica de transformación, validación o extracción.

---
## Configuración de Python
Python está configurado con todos los módulos especificados. No ejecute pip ni poetry.

## Configuración de JavaScript
El archivo package.json para el directorio js especifica dist/index.js como el punto de entrada. Por lo tanto, el paquete debe compilarse con 'npm run build' antes de la ejecución a través de node o de las pruebas después de los cambios con uber_test.py.


## Requisitos de Documentación y Atribución

Todos los agentes **deben** incluir:

- Un **docstring completo a nivel de módulo** en la parte superior de cada archivo
- Docstrings para clases y funciones, incluyendo parámetros/retornos al estilo doxygen.
- Atribución a nivel de archivo en el siguiente formato:

```python
"""
Agent Name: <identificador descriptivo>

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
```

### Política de Mantenimiento de Listas de Verificación

- Todos los archivos `docs/TODO-*.md` son listas de verificación vivas.
- Manténgalas actualizadas: los elementos marcados reflejan las características que se han implementado; los no marcados están pendientes.
- Al implementar o cambiar características que afectan a una lista de verificación, actualice el `docs/TODO-*.md` correspondiente en el mismo cambio.

---

## Agente: scxml-to-scjson

- **Entrada**: Documento SCXML (`*.scxml`, formato XML)
- **Salida**: Objeto SCJSON (`*.scjson`, formato JSON)
- **Modo**: Transformación estructural unidireccional
- **Validación**: Contra `scjson.schema.json`
- **Notas**:
  - Convierte la estructura de etiquetas, atributos y anidamiento de XML a JSON
  - Elimina comentarios y extensiones SCXML no compatibles
  - Conserva la jerarquía y la semántica de ejecución

---

## Agente: scjson-to-scxml

- **Entrada**: Objeto SCJSON (`*.scjson`, formato JSON)
- **Salida**: Documento SCXML (`*.scxml`, formato XML)
- **Modo**: Transformación reversible
- **Validación**: Contra SCXML XSD (`scxml.xsd`)
- **Notas**:
  - Genera SCXML válido que cumple con el esquema W3C
  - La salida es funcionalmente equivalente a la entrada, primero la estructura

---

## Agente: validate-scjson

- **Entrada**: Objeto SCJSON (`*.scjson`)
- **Salida**: Aprobado/Fallido + lista de errores de validación
- **Modo**: Sin estado
- **Validador**: `scjson.schema.json`
- **Notas**:
  - Se puede usar de forma independiente o como un paso previo
  - Compatible con las bibliotecas validadoras `jsonschema`

---

## Agente: validate-scxml

- **Entrada**: Documento SCXML (`*.scxml`)
- **Salida**: Aprobado/Fallido + lista de errores de validación
- **Modo**: Sin estado
- **Validador**: `scxml.xsd` (W3C)
- **Notas**:
  - Requiere un validador de esquemas XML (por ejemplo, lxml, xmllint)
  - Asume una entrada XML codificada en UTF-8

---

## Agente: generate-jsonschema

- **Entrada**: Definiciones internas del modelo Pydantic
- **Salida**: Esquema JSON (`scjson.schema.json`)
- **Modo**: En tiempo de construcción
- **Notas**:
  - Esquema canónico utilizado para toda la validación SCJSON
  - Debe regenerarse si los modelos cambian

---

## Agente: roundtrip-test

- **Entrada**: SCXML → SCJSON → SCXML
- **Salida**: Aprobado/Fallido + diferencias
- **Modo**: Utilidad de prueba
- **Notas**:
  - Detecta pérdida de fidelidad o deriva semántica
  - Útil para la integración CI y las comprobaciones de regresión

---

## Agente: schema-dump

- **Entrada**: Archivo SCJSON
- **Salida**: Bloque de metadatos o resumen de la estructura
- **Modo**: Introspectivo
- **Notas**:
  - Imprime la etiqueta raíz, el recuento de estados y la cobertura de características
  - Opcional: hash de la estructura para la coincidencia de pruebas
```

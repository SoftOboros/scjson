```markdown
<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# Guía de Inferencia de SCXML a SCJSON

Este documento describe cómo el convertidor de JavaScript transforma SCXML al formato `scjson`. Captura la *lógica de inferencia* codificada en [`js/src/converters.js`](js/src/converters.js) para que otras implementaciones de lenguaje puedan reproducir un comportamiento idéntico.

## 1. Resumen

- **SCJSON** es una representación JSON estructurada de SCXML.
- El convertidor hace más que copiar nombres de elementos. Ciertas estructuras SCXML se **infieren** y se adjuntan directamente a sus objetos padre.
- La comprensión de estas reglas permite a los desarrolladores implementar convertidores compatibles en Rust, Python o cualquier otro lenguaje.

## 2. Punto de Entrada de Conversión

- El elemento raíz es `<scxml>`.
- Cada elemento se convierte en un objeto con un campo `"tag"` que contiene el nombre de la etiqueta.
- Todos los atributos XML se copian como propiedades de cadena al mismo nivel que `tag`.
- Los hijos se procesan recursivamente.

## 3. Extracción de Campos Estructurales

El convertidor extrae elementos hijos específicos de `content[]` para que residan directamente en el objeto padre. Cada una de las siguientes etiquetas se convierte en una propiedad de array en su padre:

- `state`
- `parallel`
- `final`
- `history`
- `transition`
- `onentry`
- `onexit`
- `invoke`
- `datamodel`
- `data`
- `initial`
- `script`
- `log`
- `assign`
- `send`
- `cancel`

Cuando alguno de estos elementos está presente:

1. Inicialice un array para la propiedad coincidente (por ejemplo, `state: []`).
2. Coloque los objetos hijos convertidos en este array.
3. No deje el elemento crudo en `content[]` a menos que su etiqueta sea desconocida.

## 4. Manejo del Array de Contenido

- Los hijos que **no** coinciden con un campo estructural permanecen dentro de `content[]`.
- El orden se conserva y cada hijo se convierte recursivamente.
- Los atributos se aplanan en cada objeto.
- Una etiqueta vacía se convierte en `{ "tag": "..." }` sin campos adicionales.

## 5. Otros Atributos y Alternativas

- Todos los atributos XML se conservan exactamente como cadenas.
- El uso de espacios de nombres no se aplica a menos que se agregue explícitamente en futuras versiones.
- Los elementos y atributos desconocidos se conservan sin generar errores.
- Estos puntos son ganchos de extensión para futuras actualizaciones de esquemas.

## 6. Ejemplos

### Entrada SCXML
```xml
<state id="parent">
  <transition event="go" target="child"/>
  <state id="child"/>
  <onentry>
    <log label="start" expr="enter"/>
    <foo/>
  </onentry>
</state>
```

### SCJSON Convertido
```json
{
  "tag": "state",
  "id": "parent",
  "transition": [{
    "tag": "transition",
    "event": "go",
    "target": ["child"]
  }],
  "state": [{ "tag": "state", "id": "child" }],
  "onentry": [{
    "tag": "onentry",
    "log": [{ "tag": "log", "label": "start", "expr": "enter" }],
    "content": [{ "tag": "foo" }]
  }]
}
```

El elemento `<foo/>` desconocido permanece dentro de `content[]` del bloque `onentry`.

## 7. Notas sobre el Determinismo

- Las conversiones son deterministas: el mismo SCXML produce SCJSON idéntico.
- Los espacios en blanco no tienen ningún efecto estructural.
- El orden de los atributos no influye en la salida.

## 8. Sugerencias de Implementación

- Se utiliza un enfoque de descenso recursivo.
- Use `element.tagName`, `element.attributes` y `element.children` al recorrer el DOM.
- `STRUCTURAL_FIELDS` es un `Set` que controla si un hijo se extrae de `content[]`.
```

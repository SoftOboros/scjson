```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Matriz de Compatibilidad del Convertidor

Nombre del Agente: documentation-compatibility
Parte del proyecto scjson.
Desarrollado por Softoboros Technology Inc.
Licenciado bajo la Licencia BSD 1-Clause.

Esta página resume el estado actual de compatibilidad entre lenguajes para los
convertidores `scjson`. La CLI de Python sigue siendo la implementación canónica; todos
los demás agentes se validan comparando su salida con la de Python usando
`py/uber_test.py`.

Niveles de estado:

- **Canónico** – sirve como implementación de referencia.
- **Paridad** – pasa el corpus tutorial a través de `uber_test.py` y coincide con la
  salida de Python después de la normalización.
- **Beta** – completo en características para el uso diario, pero pendiente de
  validación de paridad total; espere discrepancias ocasionales en la cola larga
  de vectores de prueba.
- **Experimental** – soporte mínimo, principalmente para exploración o trabajo futuro.

| Idioma | Estado | Notas |
|----------|--------|-------|
| Python | Canonical | Línea base para todas las diferencias. |
| JavaScript | Parity | Pasa el corpus tutorial después de la normalización. |
| Ruby | Parity | Pasa el corpus tutorial después de la normalización. |
| Rust | Parity | Pasa el corpus tutorial después de la normalización. |
| Java | Parity | Utiliza el ejecutor de referencia [SCION](https://www.npmjs.com/package/scion); pasa el corpus tutorial después de la normalización. |
| Go | Beta | CLI estabilizada; auditoría de paridad en progreso. |
| Swift | Beta | CLI estabilizada; auditoría de paridad en progreso. |
| C# | Beta | CLI estabilizada; auditoría de paridad en progreso. |
| Lua | Experimental | Convertidor de subconjunto mínimo. |

## Conjunto de Pruebas

Ejecute la barrida de compatibilidad localmente con:

```bash
cd py
python uber_test.py
```

Puede apuntar a una sola implementación con `-l` (por ejemplo, `-l java`). El
conjunto de pruebas imprime un resumen de los archivos que no coinciden y escribe la salida
detallada en `uber_out/` para su inspección.

## Referencia de Comportamiento

El comportamiento operativo (rastros de ejecución de eventos) se valida contra [SCION](https://www.npmjs.com/package/scion).
El motor de documentación de Python y el proxy del ejecutor de Java a la CLI de
[SCION](https://www.npmjs.com/package/scion), asegurando una semántica consistente para los
ejemplos canónicos. Consulte `docs/TODO-ENGINE-PY.md` para ver el trabajo
de integración pendiente.

Ver también
- Guía del usuario (motor Python): `docs/ENGINE-PY.md`
- Arquitectura y referencia en profundidad (Python): `py/ENGINE-PY-DETAILS.md`

## Motor Python vs [SCION](https://www.npmjs.com/package/scion) — Soporte de Características

La siguiente tabla resume la cobertura actual de características del motor Python en relación con la referencia [SCION](https://www.npmjs.com/package/scion) (Node) y destaca cualquier diferencia matizada que sea importante para la compatibilidad.

| Área | Motor Python | [SCION](https://www.npmjs.com/package/scion) (Node) | Notas / Compatibilidad |
|------|---------------|--------------|-----------------------|
| Algoritmo de ejecución | Macro/microstep con quiescencia | Igual | Semántica equivalente |
| Selección de transición | Orden del documento; multi-token, `*`, `error.*` | Igual | Equivalente |
| Evaluación de condición | Datamodel Python en sandbox (`safe_eval`) | Datamodel JS | Equivalente para pruebas; cond no booleana → `error.execution` en Python |
| Contenido ejecutable | assign, log, raise, if/elseif/else, foreach, send, cancel | Igual | Equivalente; `script` es una advertencia/no-op en Python ([SCION](https://www.npmjs.com/package/scion) ejecuta JS) |
| Bloques `script` | No-op (advertencia) | Ejecuta JS | Diferencia esperada; las pruebas evitan requerir efectos secundarios de `script` |
| Historial | Shallow + deep | Igual | Equivalente; deep restaura las hojas descendientes exactas |
| Finalización paralela | Región finalizada → padre finalizado | Igual | Ordenamiento equivalente |
| Eventos de finalización | `done.state.*`, `done.invoke*` | Igual | Equivalente; ver notas de ordenamiento de invocación |
| Eventos de error | `error.execution` (al frente de la cola) + alias genérico `error`; `error.communication` (al final) | Emite tipos de error | Python añade alias genérico `error` para gráficos que escuchan `error.*` |
| Coincidencia de eventos | Exacta, `*`, prefijo `error.*` | Igual | Equivalente |
| Temporizadores | Determinístico vía `advance_time` | Temporizadores de tiempo de ejecución | Python soporta tokens de control `{ "advance_time": N }` en flujos de eventos |
| Destinos de envío externos | No soportado (emite `error.communication`) | Soporta procesadores de E/S SCXML | Diferencia esperada; procesadores externos fuera de alcance |
| Tipos de invocación | `mock:immediate`, `mock:record`, `mock:deferred`, hijo `scxml`/`scjson` | Hijo SCXML, procesadores externos | Equivalente para máquinas hijas; procesadores externos fuera de alcance |
| E/S Padre↔Hijo | `#_parent`, `#_child`/`#_invokedChild`, `#_<id>` | Igual | Equivalente |
| Semántica de finalización | Se ejecuta en el estado invocador; `_event` = `{name,data,invokeid}` | Igual | Equivalente |
| Ordenamiento de invocación | Modos: `tolerant` (predeterminado), `strict`, `scion` | N/A | El modo `scion` alinea el ordenamiento de `done.invoke` con [SCION](https://www.npmjs.com/package/scion) (genérico antes que específico por id, al frente de la cola) |
| Normalización de Step-0 | Las herramientas de comparación eliminan el ruido de step-0 | N/A | Reduce las diferencias debido a la visibilidad de las transiciones iniciales |

---

Nota sobre la emisión de pasos de tiempo
- El motor Python emite un paso de rastreo sintético por defecto cuando se procesa un token de control `{"advance_time": N}` para que los cambios impulsados por el temporizador sean visibles incluso sin un evento externo posterior. Use `--no-emit-time-steps` para suprimir estos pasos cuando se desee una paridad estricta con herramientas que no los emiten.

---

Volver a
- Guía del usuario: `docs/ENGINE-PY.md`
- Arquitectura y referencia: `py/ENGINE-PY-DETAILS.md`
- Resumen del proyecto: `README.md`
## Navegación

- Esta página: Matriz de Compatibilidad
  - [Niveles de estado](#niveles-de-estado)
  - [Conjunto de Pruebas](#conjunto-de-pruebas)
  - [Referencia de Comportamiento](#referencia-de-comportamiento)
  - [Motor Python vs SCION — Soporte de Características](#motor-python-vs-scion--soporte-de-características) ([SCION](https://www.npmjs.com/package/scion))
- Guía del Usuario del Motor Python: `docs/ENGINE-PY.md`
- Arquitectura y Referencia de Python: `py/ENGINE-PY-DETAILS.md`
- Resumen del Proyecto: `README.md`
```

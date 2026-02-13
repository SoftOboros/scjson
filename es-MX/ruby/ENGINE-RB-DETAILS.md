```
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: ruby-engine-details

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.

# Motor Ruby — Arquitectura y Detalles

Este documento describe la arquitectura, los objetivos de diseño y las notas de implementación para el motor de ejecución Ruby. Rastrea la paridad con la referencia de Python cuando es apropiado, siguiendo los modismos de Ruby.

## Objetivos

- Ejecutar SCXML/SCJSON con semántica compatible con SCION
- Salida de traza JSONL determinista (esquema que coincide con Python)
- Modos laxos/estrictos análogos a Python
- Soporte para el ciclo de vida de invocación/finalización de múltiples documentos

## Componentes

- `Scjson::Engine` – punto de entrada público para la ejecución de trazas (`engine.rb`)
- CLI: `scjson engine-trace` – envoltorio alrededor de `Scjson::Engine.trace`
- Futuro: tiempo de ejecución central (contexto del documento, activación/configuración, cola de eventos)

## Esquema de Traza

Cada línea de traza es un objeto JSON con los campos:

- `step` – número entero de paso (0 es inicialización)
- `event` – `{ "name": string, "data": any } | null`
- `configuration` – `[string]` configuración activa actual
- `enteredStates` / `exitedStates` – `[string]` deltas para el paso
- `firedTransitions` – `[object]` transiciones tomadas en este paso
- `actionLog` – `[object]` acciones ejecutadas (orden conservado)
- `datamodelDelta` – `{string: any}` cambios en el modelo de datos (claves normalizadas)

## Algoritmo de Ejecución (previsualización)

1. Inicialización (paso 0): calcula la configuración inicial
2. Procesar eventos: bucle de macrostep hasta el reposo, microsteps por conjunto de transiciones (selección básica de una sola transición implementada; resolución de conflictos pendiente)
3. Temporizadores: admite la programación de `<send delay>` y tokens de control `advance_time` en flujos de eventos para vaciar los temporizadores de forma determinista

## Paridad con Python

- Banderas: `--leaf-only`, `--omit-delta`, `--omit-actions`, `--omit-transitions`, `--advance-time`, `--ordering`
- Normalización: la eliminación de ruido del paso 0 se maneja en las herramientas de comparación
- Cobertura y vectores: reutiliza el generador y el arnés de Python

## Estado

La implementación inicial proporciona una CLI (`engine-trace`) funcional con:
- Traza del paso 0, configuración ingresada
- Eventos externos + internos, reposo sin eventos
- Ordenación de salida/entrada basada en LCA (microsteps de una sola transición)
- Contenido ejecutable: log, assign, raise, if/elseif/else, foreach
- Temporizadores: `<send delay>` con vaciado `advance_time`

El trabajo pendiente incluye la resolución de conflictos y la semántica completa de paralelo/historial para alcanzar un comportamiento compatible con SCION.

Ver también
- Guía de usuario: `docs/ENGINE-RB.md`
- Plan de lista de verificación: `docs/TODO-ENGINE-RUBY.md`
```

<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Lua SCJSON

Este directorio proporciona una implementación de la utilidad SCXML ↔ scjson basada en Lua.

## Configuración de Desarrollo

1. Instale Lua y Luarocks usando apt:

```bash
sudo apt-get update
sudo apt-get install -y lua5.4 luarocks
```

2. Instale los módulos de Lua requeridos:

```bash
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
```

> Si está detrás de un proxy, configure Luarocks con los ajustes de proxy apropiados.

3. Ejecute las pruebas:

```bash
busted -v tests
```

El módulo `scjson.lua` proporcionado ofrece utilidades de conversión mínimas. Está pensado como un punto de partida para una portabilidad completa a Lua de la implementación de referencia en Python.

Todo el código fuente en este directorio se publica bajo la licencia BSD 1-Clause. Consulte [LICENSE](./LICENSE) y [LEGAL.md](./LEGAL.md) para obtener más detalles.

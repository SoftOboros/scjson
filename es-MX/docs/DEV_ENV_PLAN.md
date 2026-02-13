```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>
"""
Agent Name: dev-env-plan

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""

# Plan de Entorno de Desarrollo Unificado

Esta nota captura los requisitos de paquetes y la estrategia de conflicto para construir una
sola imagen Docker que soporte cada implementación de lenguaje en el proyecto.
El objetivo es una instalación determinista que tenga éxito con un conjunto de
paquetes mínimo y compatible, y que falle con una explicación clara siempre que
se soliciten opciones mutuamente excluyentes.

## Paquetes Base (Ubuntu 24.04)

Estos paquetes no tienen conflictos mutuos y cubren todas las cadenas de herramientas requeridas.

| Propósito | Paquetes |
|---|---|
| Herramientas Core | `build-essential`, `curl`, `wget`, `git`, `nano`, `zstd`, `pkg-config` |
| Python | `python3`, `python3-venv`, `python3-pip` |
| Ruby | `ruby-full` |
| Java | `openjdk-21-jdk`, `maven` |
| .NET | `dotnet-sdk-8.0` |
| Go | `golang-go` |
| Rust (bootstrap) | `clang`, `cmake`, `llvm-dev`, `libssl-dev`, `libgtk-3-dev`, `libx11-dev`, `libxext-dev`, `libxrender1`, más el instalador curl de Rustup |
| Swift (dependencias de tiempo de ejecución)| `libicu-dev`, `libxml2`, `libcurl4`, `libsqlite3-0`, `libpthread-stubs0-dev`, `libedit-dev` |
| Lua | `lua5.4`, `luarocks` |

Pasos de construcción adicionales del proyecto instalan Node.js, Swift y Rust a través de
tarballs/instaladores oficiales para evitar conflictos con los paquetes de la distribución.

## Flujo de Instalación de Referencia

1. `apt-get update`
2. Instalar los paquetes base listados arriba con `--no-install-recommends`.
3. Instalar AWS CLI v2 usando el instalador zip oficial de AWS (no hay paquete apt
disponible en 24.04).
4. Instalar Node.js, Swift y Rust desde sus tarballs oficiales como ya se hace
en el Dockerfile del proyecto.

## Familias de Conflictos Conocidos y Resoluciones

| Familia | Conflicto | Resolución |
|---|---|---|
| Lua JIT | `luajit` vs `luajit2` | Ninguno es requerido; mantener `lua5.4` + `luarocks`. |
| Bases de datos | `mysql-*` vs `mariadb-*` | Ningún componente de lenguaje depende de ninguno; omitir ambos. |
| Controladores NVIDIA | múltiples variantes `nvidia-*` | No son necesarios para la construcción/pruebas; omitir por completo. |
| Servidores de correo/impresión | paquetes como `postfix`, `sendmail`, `magicfilter` | Fuera de alcance; omitir. |
| `rustup` vs `cargo` de distribución | `rustup` entra en conflicto con el meta-paquete `cargo` | Instalar Rust vía rustup; **no** instalar el `cargo` de la distribución. |

Al eliminar estos paquetes opcionales/irrelevantes, el resolvedor de dependencias ya
no encuentra conflictos.

## Flags de Características Opcionales

Si un futuro contribuidor necesita una pila opcional que entra en conflicto con la
línea base, proteja la instalación detrás de una variable de entorno y falle con
un mensaje claro cuando se hagan selecciones incompatibles. Ejemplo de pseudo-lógica:

```bash
if [ "$INSTALL_DATABASE" = "mysql" ] && [ "$INSTALL_DATABASE" = "mariadb" ]; then
  echo "Selecciones de base de datos en conflicto (mysql vs mariadb). Elija una." >&2
  exit 1
fi
```

Documente cualquier opción de este tipo en este archivo para que la matriz se mantenga
actualizada.

## Próximos Pasos

1. Actualizar el Dockerfile para usar la lista de paquetes base y el instalador de AWS CLI.
2. Eliminar las instalaciones `apt` heredadas para paquetes en conflicto.
3. Agregar flags de características opcionales solo cuando tengamos una necesidad concreta,
siguiendo el patrón de fallo descrito anteriormente.
```

# Lua SCJSON

This directory provides a Lua-based implementation of the SCXML ↔ scjson utility.

## Development Setup

1. Install Lua and Luarocks using apt:

```bash
sudo apt-get update
sudo apt-get install -y lua5.4 luarocks
```

2. Install required Lua modules:

```bash
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
```

> If you are behind a proxy, configure Luarocks with the appropriate proxy settings.

3. Run tests:

```bash
busted -v tests
```

The provided `scjson.lua` module offers minimal conversion utilities. It is intended as a starting point for a complete Lua port of the reference Python implementation.

All source code in this directory is released under the BSD 1-Clause license. See [LICENSE](./LICENSE) and [LEGAL.md](./LEGAL.md) for details.

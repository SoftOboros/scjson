<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Lua SCJSON

Ce répertoire fournit une implémentation basée sur Lua de l'utilitaire SCXML ↔ scjson.

## Configuration de développement

1. Installez Lua et Luarocks en utilisant apt :

```bash
sudo apt-get update
sudo apt-get install -y lua5.4 luarocks
```

2. Installez les modules Lua requis :

```bash
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
```

> Si vous êtes derrière un proxy, configurez Luarocks avec les paramètres de proxy appropriés.

3. Exécutez les tests :

```bash
busted -v tests
```

Le module `scjson.lua` fourni offre des utilitaires de conversion minimaux. Il est destiné à servir de point de départ pour un portage Lua complet de l'implémentation Python de référence.

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Consultez [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.

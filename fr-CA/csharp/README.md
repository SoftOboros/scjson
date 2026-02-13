<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquet scjson C#

Ce répertoire contient l'implémentation .NET de **scjson**, offrant un outil en ligne de commande et une bibliothèque pour convertir entre les fichiers `.scxml` et `.scjson`.

## Installation

```bash
dotnet build csharp/ScjsonCli
```

Après la compilation, vous pouvez exécuter la CLI avec :

```bash
dotnet run --project csharp/ScjsonCli -- json path/to/machine.scxml
```

## Utilisation en ligne de commande

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.

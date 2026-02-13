<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquet Go scjson

Ce répertoire contient l'implémentation Go de **scjson**, un format pour représenter les machines d'état SCXML en JSON. L'outil en ligne de commande peut convertir entre les fichiers `.scxml` et `.scjson` et valider les documents en utilisant le schéma partagé.

## Installation

```bash
go install github.com/softoboros/scjson/go @scripts/aws/update_web_latest.sh
```

Vous pouvez également compiler à partir de ce dépôt :

```bash
cd go && go build
```

## Utilisation en ligne de commande

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.

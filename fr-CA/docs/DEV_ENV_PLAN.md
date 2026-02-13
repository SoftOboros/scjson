```
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>
"""
Agent Name: dev-env-plan

Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause License.
"""

# Plan d'environnement de développement unifié

Cette note décrit les exigences de paquets et la stratégie de résolution des conflits pour construire une
image Docker unique qui prend en charge chaque implémentation linguistique du projet.
L'objectif est une installation déterministe qui réussit avec un ensemble de paquets minimal et compatible
et échoue avec une explication claire lorsque des options mutuellement exclusives
sont demandées.

## Paquets de base (Ubuntu 24.04)

Ces paquets n'ont pas de conflits mutuels et couvrent toutes les chaînes d'outils requises.

| Objectif | Paquets |
|---|---|
| Outils de base | `build-essential`, `curl`, `wget`, `git`, `nano`, `zstd`, `pkg-config` |
| Python | `python3`, `python3-venv`, `python3-pip` |
| Ruby | `ruby-full` |
| Java | `openjdk-21-jdk`, `maven` |
| .NET | `dotnet-sdk-8.0` |
| Go | `golang-go` |
| Rust (bootstrap) | `clang`, `cmake`, `llvm-dev`, `libssl-dev`, `libgtk-3-dev`, `libx11-dev`, `libxext-dev`, `libxrender1`, plus installeur curl Rustup |
| Swift (dépendances runtime)| `libicu-dev`, `libxml2`, `libcurl4`, `libsqlite3-0`, `libpthread-stubs0-dev`, `libedit-dev` |
| Lua | `lua5.4`, `luarocks` |

Des étapes de construction de projet supplémentaires installent Node.js, Swift et Rust via des
archives/installateurs officiels pour éviter les paquets de distribution conflictuels.

## Flux d'installation de référence

1. `apt-get update`
2. Installer les paquets de base listés ci-dessus avec `--no-install-recommends`.
3. Installer AWS CLI v2 en utilisant l'installeur zip officiel d'AWS (aucun paquet apt n'est
disponible sur 24.04).
4. Installer Node.js, Swift et Rust à partir de leurs archives officielles comme déjà fait
dans le Dockerfile du projet.

## Familles de conflits connues et résolutions

| Famille | Conflit | Résolution |
|---|---|---|
| Lua JIT | `luajit` vs `luajit2` | Aucun n'est requis ; s'en tenir à `lua5.4` + `luarocks`. |
| Bases de données | `mysql-*` vs `mariadb-*` | Aucun composant linguistique ne dépend de l'un ou l'autre ; omettre les deux. |
| Pilotes NVIDIA | plusieurs variantes `nvidia-*` | Non nécessaires pour la construction/le test ; omettre entièrement. |
| Serveurs de messagerie/impression | paquets tels que `postfix`, `sendmail`, `magicfilter` | Hors de portée ; omettre. |
| `rustup` vs `cargo` de distribution | `rustup` entre en conflit avec le méta-paquet `cargo` | Installer Rust via rustup ; ne **pas** installer le `cargo` de distribution. |

En supprimant ces paquets optionnels/non pertinents, le résolveur de dépendances ne
rencontre plus de conflits.

## Indicateurs de fonctionnalités optionnels

Si un futur contributeur a besoin d'une pile optionnelle qui entre en conflit avec la
base de référence, protéger l'installation derrière une variable d'environnement et échouer avec un message clair
lorsque des sélections incompatibles sont faites. Exemple de pseudo-logique :

```bash
if [ "$INSTALL_DATABASE" = "mysql" ] && [ "$INSTALL_DATABASE" = "mariadb" ]; then
  echo "Sélections de bases de données conflictuelles (mysql vs mariadb). Choisissez-en une." >&2
  exit 1
fi
```

Documenter toutes ces options dans ce fichier afin que la matrice reste à jour.

## Prochaines étapes

1. Mettre à jour le Dockerfile pour utiliser la liste des paquets de base et l'installeur AWS CLI.
2. Supprimer les installations `apt` héritées pour les paquets conflictuels.
3. Ajouter des indicateurs de fonctionnalités optionnels uniquement lorsque nous avons un besoin concret, en suivant le
modèle d'échec décrit ci-dessus.
```

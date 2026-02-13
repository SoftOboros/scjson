<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Gemme Ruby scjson

Ce répertoire contient l'implémentation Ruby de **scjson**. La gemme fournit un outil en ligne de commande et des fonctions de bibliothèque pour convertir entre les fichiers `.scxml` et `.scjson`.

## Installation

```bash
gem install scjson
```

Vous pouvez également installer à partir d'un dépôt local :

```bash
cd ruby && gem build scjson.gemspec && gem install scjson-*.gem
```

## Utilisation en ligne de commande

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

## Utilisation de la bibliothèque

```ruby
require 'scjson'

document = Scjson::Types::ScxmlProps.new
json = document.to_json
round_trip = Scjson::Types::ScxmlProps.from_json(json)
```

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.

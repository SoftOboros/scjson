```markdown
<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# scjson

> Une sérialisation basée sur JSON de SCXML (State Chart XML) pour les outils modernes, l'interopérabilité et l'éducation.

**Moteurs d'exécution**
- Moteur Python : Émetteur de trace déterministe, génération de vecteurs et outils de comparaison. Voir `docs/ENGINE-PY.md` et `py/ENGINE-PY-DETAILS.md`.
- Moteur Ruby : Interface de trace en développement actif avec une parité de fonctionnalités croissante. Voir `docs/ENGINE-RB.md`.

**Harnais JS/TS (via SCION)**
- Le package JS fournit un CLI de harnais `scjson-scion-trace` qui nécessite directement `scion-core` pour exécuter SCXML et émettre des traces JSONL. Installez `scion-core` dans votre projet pour l'activer.
- Prend en charge les entrées `.scxml` et `.scjson` (ce dernier est converti en SCXML en interne).
- Drapeaux de normalisation : `--leaf-only`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`.
- Utilisation (package) : `npx scjson-scion-trace -I chart.(scxml|scjson) -e events.jsonl [--xml] [--leaf-only] [--omit-delta] [...]`
- Alternative de développement (dans ce dépôt) : `node tools/scion-runner/scion-trace.cjs -I chart.scxml -e events.jsonl --xml`

---

## Vue d'ensemble

`scjson` est une représentation structurée et basée sur un schéma de [SCXML](https://www.w3.org/TR/scxml/), la norme W3C pour la modélisation de machines à états. Ce format préserve la sémantique et la hiérarchie de SCXML tout en le rendant plus accessible aux outils, langages et interfaces modernes.

Pourquoi JSON ?

- Plus facile à analyser en JavaScript, Python, Rust, etc.
- S'intègre naturellement avec les API REST, les éditeurs et la validation statique
- Peut être converti vers et depuis le SCXML standard
- Fonctionne avec des formats compacts comme MessagePack ou Protobuf lorsque nécessaire

---

## Objectifs

- 💡 **Interopérabilité** : Servir de pont entre SCXML et les écosystèmes d'applications modernes
- 📦 **Portabilité** : Permettre la traduction vers des formats binaires (MessagePack, Protobuf, etc.)
- 📚 **Pédagogie** : Faciliter l'enseignement et l'apprentissage des machines à états avec une syntaxe plus claire et des outils visuels
- 🔁 **Fidélité de l'aller-retour** : Soutenir la conversion vers un SCXML valide sans perte sémantique

---

## Schéma

Le fichier canonique `scjson.schema.json` se trouve dans [`/scjson.schema.json`](./scjson.schema.json).
Il est généré à partir de modèles Pydantic et utilisé pour valider tous les documents `*.scjson`.
Les règles d'inférence détaillées utilisées par les convertisseurs sont décrites dans [INFERENCE.md](./INFERENCE.md).

---

## Structure des répertoires

Chaque implémentation linguistique se trouve dans son propre répertoire, en tant que module ou racine de bibliothèque autonome :

/schema/ → Définition du schéma JSON de scjson
/examples/ → Paires d'exemples SCXML et scjson
/tutorial/ → Sous-module Git : tutoriel Zhornyak SCXML
/python/ → Implémentation de référence Python (CLI + bibliothèque)
/js/ → CLI et bibliothèque JavaScript
/ruby/ → CLI et gem Ruby
/go/ → Utilitaire de ligne de commande Go
/rust/ → Utilitaire de ligne de commande Rust
/swift/ → Outil de ligne de commande Swift
/java/ → Outil de ligne de commande Java
/lua/ → Scripts Lua
/csharp/ → Outil de ligne de commande C#


Chaque répertoire est conçu pour être utilisable indépendamment en tant que bibliothèque ou outil CLI.

---

## Convertisseurs et moteurs

| Langage | Statut | Chemin | Notes |
|-----------|--------|------|-------|
| Python | ✅ Canonique | [py](./py/README.md) | Implémentation de référence et base de compatibilité |
| JavaScript| ✅ Parité | [js](./js/README.md) | Correspond à la sortie Python sur le corpus du tutoriel ; harnais disponible via SCION |
| Ruby | ✅ Parité | [ruby](./ruby/README.md) | Parité du convertisseur ; interface de trace du moteur en développement actif |
| Rust | ✅ Parité | [rust](./rust/README.md) | Correspond à la sortie Python sur le corpus du tutoriel |
| Java | ✅ Parité | [java](./java/README.md) | Utilise le pilote basé sur [SCION](https://www.npmjs.com/package/scion) ; correspond à la sortie Python |
| Go | ✅ Parité | [go](./go/README.md) | Correspond à la sortie Python sur le corpus du tutoriel |
| Swift | ✅ Parité | [swift](./swift/README.md) | Correspond à la sortie Python sur le corpus du tutoriel |
| C# | ⚠️ Bêta | [csharp](./csharp/README.md) | CLI fonctionnel ; travail de parité en cours |
| Lua | ✅ Parité | [lua](./lua/README.md) | Correspond à la sortie Python sur le corpus du tutoriel |

Voir [docs/COMPATIBILITY.md](./docs/COMPATIBILITY.md) pour les derniers détails de parité inter-langages
et les notes de test.

---

## Exemples et suite de tests

Ce dépôt inclut un ensemble organisé d'exemples SCXML canoniques et leurs formes `scjson` équivalentes dans [`/examples`](./examples). Ceux-ci sont utilisés pour :

- La validation fonctionnelle (SCXML ↔ scjson ↔ SCXML)
- L'enseignement des concepts de machines à états via des outils visuels
- La démonstration de l'utilisation dans les éditeurs, les bibliothèques d'interface utilisateur et les plateformes à code bas

Ces exemples sont dérivés et/ou adaptés de :

### 📚 Tutoriel inclus (en tant que sous-module Git)

Nous incluons le **Tutoriel de l'éditeur SCXML d'Alex Zhornyak** en tant que sous-module Git sous [`/tutorial`](./tutorial).
Ceci fournit un ensemble riche de cas de test et de diagrammes SCXML canoniques.

> L'attribution est fournie à des fins éducatives. Aucun endossement n'est implicite.
> Source : [https://alexzhornyak.github.io/ScxmlEditor-Tutorial/](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/)

---

### 🛠️ Configuration du sous-module

Si vous avez cloné ce dépôt et que `/tutorial` est vide, exécutez :

```bash
git submodule init
git submodule update
Ou clonez avec les sous-modules en une seule étape :

git clone --recurse-submodules https://github.com/your-org/scjson.git
```

Ceci garantit que vous obtenez le contenu complet du tutoriel ainsi que les exemples et les convertisseurs.

---

## Convertisseurs
Tous les convertisseurs partagent le même schéma et la même suite de tests pour assurer la compatibilité.

---

## Démarrage rapide

```bash
# Convertir de SCXML en scjson
scjson convert --from scxml path/to/file.scxml --to scjson path/to/file.scjson

# Valider un fichier scjson
scjson validate path/to/file.scjson
```

### Disponibilité du dépôt de packages
pypi : [https://pypi.org/project/scjson/]
```bash
pip install scjson
```
npm : [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
# harnais nécessite scion-core
npm install scion-core
```

Harnais (Node) :
```bash
npx scjson-scion-trace -I path/to/chart.scxml -e events.jsonl --xml
```

rubygems : [https://rubygems.org/gems/scjson]
```bash
gem install scjson
```
Notes sur RubyGems :
- Le CLI Ruby inclut les convertisseurs et une interface de trace. Voir `docs/ENGINE-RB.md` pour l'utilisation et la maturité du moteur. La gem est publiée au lien ci-dessus.

cargo : [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub : [https://hub.docker.com/r/iraa/scjson]
(Environnement de développement complet pour toutes les langues prises en charge)
```bash
docker pull iraa/scjson:latest
```

Pour un exemple complet d'installation des toolchains et des dépendances entre les langues, voir [`codex/startup.sh`](codex/startup.sh).


## Documentation

- Guide de l'utilisateur (moteur Python) : `docs/ENGINE-PY.md`
- Architecture et référence approfondie (Python) : `py/ENGINE-PY-DETAILS.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`
- Guide de test : `TESTING.md`
- Vue d'ensemble des agents : `AGENTS.md`


## Divergences et problèmes connus

Les comparaisons entre moteurs révèlent parfois des différences intentionnelles et documentées (par exemple, des nuances d'ordonnancement, la sémantique de `in` ECMA, la ré-entrée de l'historique). Utilisez ces ressources pour comprendre, normaliser et trier le comportement entre SCION (Node), Python et Ruby :

- Vue d'ensemble complète : docs/COMPATIBILITY.md
- Profil de normalisation : `--norm scion` dans exec_compare définit leaf-only, omit-delta, omit-transitions, strip-step0-states et ordering=scion.
  - Exemple : `python py/exec_compare.py tests/exec/toggle.scxml --events tests/exec/toggle.events.jsonl --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
- Liste des différences connues CI : scripts/ci_ruby_known_diffs.txt (utilisé par `scripts/ci_ruby_harness.sh --known` pour maintenir la CI verte tout en signalant les incohérences attendues).
- Convertisseur Ruby en CI : lorsque Nokogiri n'est pas disponible, le CLI Ruby utilise le convertisseur Python pour SCXML↔scjson uniquement ; l'exécution reste Ruby. Voir docs/ENGINE-RB.md (Notes CI).


## Installations rapides.

### Module Python
```bash
cd py
pip install -r requirements.txt
pytest -q
```

### Module JavaScript
```bash
cd js
npm ci
npm test --silent
```

### Module Ruby
```bash
cd ruby
gem install bundler
bundle install
bundle exec rspec
```

### Module Go
```bash
cd go
go test ./...
go build
```

### Module Rust
```bash
cd rust
cargo test
```

### Module Swift
```bash
cd swift
swift test
```

### Module C#
```bash
cd csharp
dotnet test -v minimal
```

### Module Lua
```bash
cd lua
luarocks install luaexpat --deps-mode=one
luarocks install dkjson --deps-mode=one
luarocks install busted --deps-mode=one
busted tests
```

## Mentions légales et documentation

Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails. Une documentation supplémentaire est disponible dans [AGENTS.md](./AGENTS.md) et [TESTING.md](./TESTING.md).
```

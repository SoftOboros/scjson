<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Crate Rust scjson

Ce répertoire contient l'implémentation Rust de **scjson**. Il offre un outil en ligne de commande et une bibliothèque de support pour convertir des fichiers `.scxml` en `.scjson` et vice versa, ainsi que pour valider des documents.

Pour plus de détails sur la façon dont les éléments SCXML sont inférés pendant la conversion, voir [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).


## Installation

```bash
cargo install scjson
```

Vous pouvez également compiler à partir de ce dépôt :

```bash
cd rust && cargo build --release
```

# Code Source - Support Multi-Langage
[https://github.com/SoftOboros/scjson/]
- csharp
- go
- java
- javascript / typescript
- lua
- python
- ruby
- rust
- swift

## Utilisation en ligne de commande

```bash
scjson json path/to/machine.scxml
scjson xml path/to/machine.scjson
scjson validate path/to/dir -r
```

## Problèmes connus
Aucun pour le moment.

Les tests de conformité opérationnelle sont effectués via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Note : [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applique tous les fichiers scxml de [Zhornyak's ScxmlEditor-Tutorial](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/), qui fournit un ensemble robuste de vecteurs de test scxml utiles pour la vérification de la conformité aux normes. C'est le seul fichier de la suite de tests qui échoue à la vérification aller-retour.


### Énumérations
Chaque énumération représente un ensemble de chaînes restreintes utilisées par SCXML. Les valeurs
indiquées ci-dessous reflètent celles définies dans le schéma SCJSON.
- `AssignTypeDatatypeProps` – comment l'élément `<assign>` manipule le modèle de données.
  Valeurs : `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatypeProps` – détermine si les variables du modèle de données sont liées `early` ou
  `late` pendant l'exécution.
- `BooleanDatatypeProps` – valeurs d'attribut booléennes `true` ou `false`.
- `ExmodeDatatypeProps` – mode d'exécution du processeur, `lax` ou `strict`.
- `HistoryTypeDatatypeProps` – type d'état `<history>` : `shallow` ou `deep`.
- `TransitionTypeDatatypeProps` – indique si une `<transition>` est `internal` ou
  `external`.

### Types Communs
Plusieurs classes générées partagent des champs d'aide génériques :
- `other_attributes` : `Record<str, str>` capturant des attributs XML additionnels provenant
  d'espaces de noms étrangers.
- `other_element` : `list[object]` permettant de conserver des nœuds enfants non typés provenant d'autres
  espaces de noms.
- `content` : `list[object]` utilisé lorsque des éléments permettent un contenu mixte ou générique
  (wildcard).


### Types de Documents / Objets
- `AssignProps` `AssignArray` – met à jour un emplacement du modèle de données avec une expression ou une valeur.
- `CancelProps` `CancelArray` – annule une opération `<send>` en attente.
- `ContentProps` `ContentArray` – charge utile en ligne utilisée par `<send>` et `<invoke>`.
- `DataProps` `DataArray` – représente une seule variable du modèle de données.
- `DatamodelProps` `DatamodelArray` – conteneur pour un ou plusieurs éléments `<data>`.
- `DonedataProps` `DonedataArray` – charge utile retournée lorsqu'un état `<final>` est atteint.
- `ElseProps` – branche de repli pour les conditions `<if>`.
- `ElseifProps` – branche conditionnelle suivant un `<if>`.
- `FinalProps` `FinalArray` – marque un état terminal dans la machine.
- `FinalizeProps` `FinalizeArray` – exécuté après la complétion d'un `<invoke>`.
- `ForeachProps` `ForeachArray` – itère sur des éléments au sein d'un contenu exécutable.
- `HistoryProps` `HistoryArray` – pseudo-état mémorisant les enfants actifs précédents.
- `IfProps` `IfArray` – bloc d'exécution conditionnelle.
- `InitialProps` `InitialArray` – état de départ au sein d'un état composé.
- `InvokeProps` `InvokeArray` – exécute un processus ou une machine externe.
- `LogProps` `LogArray` – instruction de sortie de diagnostic.
- `OnentryProps` `OnentryArray` – actions effectuées lors de l'entrée dans un état.
- `OnexitProps` `OnexitArray` – actions effectuées lors de la sortie d'un état.
- `ParallelProps` `ParallelArray` – coordonne des régions concurrentes.
- `ParamProps` `ParamArray` – paramètre passé à `<invoke>` ou `<send>`.
- `RaiseProps` `RaiseArray` – déclenche un événement interne.
- `ScriptProps` `ScriptArray` – script exécutable en ligne.
- `ScxmlProps` – élément racine d'un document SCJSON.
- `SendProps` `SendArray` – distribue un événement externe.
- `StateProps` `StateArray` – nœud d'état de base.
- `TransitionProps` `TransitionArray` – arête entre les états déclenchée par des événements.


### Autres Ressources
github : [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git @github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

npm : [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
```

pypi : [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

dockerhub : [https://hub.docker.com/r/iraa/scjson]
(Environnement de développement complet pour toutes les langues supportées)
```bash
docker pull iraa/scjson:latest
```


Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.

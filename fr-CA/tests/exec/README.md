Agent Name: exec-tests

Partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause License.

# Fixtures du Harnais d'Exécution

Ce répertoire contient des exemples de documents SCXML et les flux d'événements correspondants utilisés par
`exec_compare.py`. Chaque fichier `.scxml` devrait avoir un fichier `.events.jsonl` correspondant
fournissant un objet JSON par ligne avec le nom de l'événement et les données optionnelles.

## Fichiers

- `toggle.scxml` – une machine à deux états (`idle` ↔ `active`) qui incrémente
  `count` à l'entrée de `active`.
- `toggle.events.jsonl` – script d'événements exerçant `start`, `go` et `reset`.

N'hésitez pas à ajouter des fixtures supplémentaires au fur et à mesure que le harnais de comparaison se développe.

## Exécuteur de Référence ([Scion](https://www.npmjs.com/package/scion))

Le moteur de référence par défaut utilisé par `py/exec_compare.py` est un mince wrapper
autour de l'implémentation Node [SCION](https://www.npmjs.com/package/scion).

1. Installez les dépendances une seule fois :

   ```bash
   cd tools/scion-runner
   npm install
   ```

2. Générez une trace directement :

   ```bash
   node scion-trace.cjs -I ../../tests/exec/toggle.scxml \
       -e ../../tests/exec/toggle.events.jsonl \
       -o toggle.scion.trace.jsonl
   ```

3. Comparez Python vs [Scion](https://www.npmjs.com/package/scion) (et éventuellement un moteur secondaire) en utilisant :

   ```bash
   cd ../../py
   python exec_compare.py ../tests/exec/toggle.scxml \
       --events ../tests/exec/toggle.events.jsonl
   ```

Définissez `SCJSON_SECONDARY_ENGINE_CMD` ou `--secondary` pour fournir un moteur additionnel
(par exemple, Apache Commons SCXML) pour des comparaisons à trois voies.

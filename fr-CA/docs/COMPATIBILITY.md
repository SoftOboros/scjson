<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Matrice de compatibilité des convertisseurs

Nom de l'agent : documentation-compatibility
Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Licence BSD 1-Clause.

Cette page résume l'état actuel de la compatibilité inter-langues pour les
convertisseurs `scjson`. L'interface de ligne de commande Python reste l'implémentation canonique ; tous
les autres agents sont validés en comparant leur sortie avec Python à l'aide de
`py/uber_test.py`.

Niveaux de statut :

-   **Canonique** – sert d'implémentation de référence.
-   **Parité** – passe le corpus tutoriel via `uber_test.py` et correspond à la sortie Python
    après normalisation.
-   **Bêta** – fonctionnalités complètes pour une utilisation quotidienne mais en attente d'une validation de parité complète ;
    attendez-vous à des incohérences occasionnelles dans la longue traîne des vecteurs de test.
-   **Expérimental** – support minimal, principalement pour l'exploration ou les travaux futurs.

| Langage | Statut | Notes |
|---|---|---|
| Python | Canonique | Base pour tous les diffs. |
| JavaScript | Parité | Passe le corpus tutoriel après normalisation. |
| Ruby | Parité | Passe le corpus tutoriel après normalisation. |
| Rust | Parité | Passe le corpus tutoriel après normalisation. |
| Java | Parité | Utilise le moteur de référence [SCION](https://www.npmjs.com/package/scion) ; passe le corpus tutoriel après normalisation. |
| Go | Bêta | CLI stabilisé ; audit de parité en cours. |
| Swift | Bêta | CLI stabilisé ; audit de parité en cours. |
| C# | Bêta | CLI stabilisé ; audit de parité en cours. |
| Lua | Expérimental | Convertisseur de sous-ensemble minimal. |

## Harnais de test

Exécutez la vérification de compatibilité localement avec :

```bash
cd py
python uber_test.py
```

Vous pouvez cibler une seule implémentation avec `-l` (par exemple `-l java`). Le
harnais affiche un résumé des fichiers non concordants et écrit des résultats détaillés sous
`uber_out/` pour inspection.

## Référence comportementale

Le comportement opérationnel (traces d'exécution d'événements) est validé par rapport à [SCION](https://www.npmjs.com/package/scion). Le
moteur de documentation Python et le proxy d'exécution Java vers l'interface de ligne de commande de [SCION](https://www.npmjs.com/package/scion), garantissant
une sémantique cohérente pour les exemples canoniques. Voir `docs/TODO-ENGINE-PY.md`
pour les travaux d'intégration en suspens.

Voir aussi
- Guide de l'utilisateur (moteur Python) : `docs/ENGINE-PY.md`
- Architecture et référence approfondie (Python) : `py/ENGINE-PY-DETAILS.md`

## Moteur Python vs [SCION](https://www.npmjs.com/package/scion) — Support des fonctionnalités

Le tableau ci-dessous résume la couverture actuelle des fonctionnalités du moteur Python par rapport à la référence [SCION](https://www.npmjs.com/package/scion) (Node) et met en évidence les différences nuancées qui importent pour la compatibilité.

| Zone | Moteur Python | [SCION](https://www.npmjs.com/package/scion) (Node) | Notes / Compatibilité |
|---|---|---|---|
| Algorithme d'exécution | Macro/microstep avec quiescence | Idem | Sémantique équivalente |
| Sélection de transition | Ordre des documents ; multi-jetons, `*`, `error.*` | Idem | Équivalent |
| Évaluation de condition | Datamodel Python en sandbox (`safe_eval`) | Datamodel JS | Équivalent pour les tests ; cond non booléenne → `error.execution` en Python |
| Contenu exécutable | assign, log, raise, if/elseif/else, foreach, send, cancel | Idem | Équivalent ; `script` est un avertissement/no-op en Python ([SCION](https://www.npmjs.com/package/scion) exécute JS) |
| Blocs `script` | No-op (avertissement) | Exécute JS | Différence attendue ; les tests évitent d'exiger des effets secondaires de `script` |
| Historique | Shallow + deep | Idem | Équivalent ; deep restaure les feuilles descendantes exactes |
| Complétion parallèle | Région terminée → parent terminé | Idem | Ordre équivalent |
| Événements "done" | `done.state.*`, `done.invoke*` | Idem | Équivalent ; voir les notes sur l'ordre d'invocation |
| Événements d'erreur | `error.execution` (pushed en avant) + alias générique `error` ; `error.communication` (queue) | Émet des types d'erreur | Python ajoute l'alias générique `error` pour les graphiques écoutant `error.*` |
| Correspondance d'événements | Exacte, `*`, préfixe `error.*` | Idem | Équivalent |
| Minuteurs | Déterministe via `advance_time` | Minuteurs d'exécution | Python prend en charge les jetons de contrôle `{ "advance_time": N }` dans les flux d'événements |
| Cibles d'envoi externes | Non pris en charge (émet `error.communication`) | Prend en charge les processeurs d'E/S SCXML | Différence attendue ; les processeurs externes hors de portée |
| Types d'invocation | `mock:immediate`, `mock:record`, `mock:deferred`, `scxml`/`scjson` enfant | Enfant SCXML, processeurs externes | Équivalent pour les machines enfants ; les processeurs externes hors de portée |
| E/S parent↔enfant | `#_parent`, `#_child`/`#_invokedChild`, `#_<id>` | Idem | Équivalent |
| Sémantique de finalisation | S'exécute dans l'état d'invocation ; `_event` = `{name,data,invokeid}` | Idem | Équivalent |
| Ordre d'invocation | Modes : `tolerant` (par défaut), `strict`, `scion` | N/A | Le mode `scion` aligne l'ordre `done.invoke` avec [SCION](https://www.npmjs.com/package/scion) (générique avant id-spécifique, poussé en avant) |
| Normalisation à l'étape 0 | L'outil de comparaison supprime le bruit de l'étape 0 | N/A | Réduit les différences dues à la visibilité des transitions initiales |

---

Note sur l'émission des pas de temps
- Le moteur Python émet par défaut une étape de trace synthétique lorsqu'un jeton de contrôle `{"advance_time": N}` est traité, de sorte que les changements pilotés par minuterie soient visibles même sans événement externe ultérieur. Utilisez `--no-emit-time-steps` pour supprimer ces étapes lorsque la parité stricte avec des outils qui ne les émettent pas est souhaitée.

---

Retour à
- Guide de l'utilisateur : `docs/ENGINE-PY.md`
- Architecture et référence : `py/ENGINE-PY-DETAILS.md`
- Vue d'ensemble du projet : `README.md`
## Navigation

- Cette page : Matrice de compatibilité
  - [Niveaux de statut](#niveaux-de-statut)
  - [Harnais de test](#harnais-de-test)
  - [Référence comportementale](#référence-comportementale)
  - [Moteur Python vs SCION — Support des fonctionnalités](#moteur-python-vs-scion--support-des-fonctionnalités) ([SCION](https://www.npmjs.com/package/scion))
- Guide de l'utilisateur du moteur Python : `docs/ENGINE-PY.md`
- Architecture et référence Python : `py/ENGINE-PY-DETAILS.md`
- Vue d'ensemble du projet : `README.md`

```markdown
# Moteur d'exécution de style SCXML avec noms:

### Couches
Ce que vous créez au démarrage de l'interprète	Durée de vie	Contenu typique

Document (global)	Contexte du document (parfois « Modèle de données »)	Exécution entière	• tous les éléments <data> de niveau supérieur
• constantes immuables
• un pointeur vers l'activation racine actuelle (voir ligne suivante)
• file d'attente d'événements / gestionnaire de planification

Machine à états racine	Enregistrement d'activation racine	Exécution entière	• ID de l'élément <scxml> racine
• configuration actuelle (ensemble d'états actifs)
• instantanés d'historique, minuteries globales, etc.
Chaque état / parallèle qui devient actif	État

Enregistrement d'activation (« contexte local », « cadre », etc.)	De onentry à la fin de onexit	• référence à l'activation parent
• indicateurs d'exécution: isFinal, isParallel, hasHistory …
• toute <data> scopée à l'état
• variables temporaires créées par des actions d'affectation/variable
• minuteries en cours déclenchées par cet état

## Pourquoi cette architecture fonctionne

### Isolation des données transitoires

Un enregistrement d'activation d'état disparaît lorsque l'état se termine, de sorte que les variables temporaires ou les minuteries ne remontent pas. Cela correspond à l'attente de SCXML selon laquelle les <data> locales sont recréées à chaque ré-entrée.

### La hiérarchie reflète le flux de contrôle

Étant donné que les activations s'imbriquent exactement comme l'imbrication <state> / <parallel>, les algorithmes comme « l'ancêtre est-il actif ? », la restauration de l'historique et la détection d'état final deviennent de simples parcours d'arbre.
Tenue de livres d'état final

Marquez une activation comme finale lorsque son enfant <final> entre; propagez ceci vers le haut afin qu'un <parallel> ne se termine que lorsque les activations de tous ses enfants sont dans l'état final.

### Efficacité de bas niveau
Si vous implémentez les activations comme des objets légers (ou des descripteurs de structure d'un pool d'objets), leur création/destruction à chaque entrée/sortie est peu coûteuse et maintient la mémoire par instance proportionnelle à la configuration active, et non à l'ensemble du graphique.

### Quelques astuces d'implémentation
Conservez un ensemble de « configuration actuelle » à côté de l'arbre d'activation; la plupart des algorithmes (microstep, transitions légales, résolution de conflits) sont des opérations d'ensemble sur la configuration.

Les files d'attente d'événements vivent au niveau du document ou de la racine. Livrez les événements vers le bas en parcourant l'arbre d'activation jusqu'à ce que quelqu'un les consomme.

Historique: stockez, à la sortie, les ID (ou pointeurs) des activations enfants qui étaient actives. Lors de la restauration de l'historique, recréez les activations pour ces ID au lieu d'évaluer <initial>.

Données globales vs locales: laissez les <data> au niveau de l'état masquer les entrées au niveau du document; les recherches remontent la chaîne d'activation.

## Sandbox d'expressions et modèle de confiance

Les expressions Python à l'intérieur des attributs `cond` de `<assign>`, `<log>` et des transitions
sont évaluées avec un sandbox alimenté par [`py-sandboxed`](https://pypi.org/project/py-sandboxed/).
Seul un sous-ensemble sélectionné de fonctions intrinsèques pures (par exemple, `abs`, `len`, `sum`, `sorted`) et
le module `math` sont exposés par défaut; les tentatives d'importer des modules, d'accéder
aux attributs à double tiret bas, ou d'appeler `eval`/`exec` déclenchent une
``SafeEvaluationError`` et reviennent à la chaîne d'expression littérale lorsque
cela est possible. La fonction d'aide `In(stateId)` est injectée automatiquement afin que les graphiques
puissent interroger les états actifs sans ouvrir le sandbox.

Pour les environnements qui font entièrement confiance au graphique d'entrée, vous pouvez désactiver le
sandbox en passant `--unsafe-eval` à `scjson engine-trace` (ou en construisant
`DocumentContext` avec `allow_unsafe_eval=True`). Cela réactive l'`eval` natif de CPython,
correspondant au comportement précédent du moteur.

Préréglages et remplacements du sandbox
- `--expr-preset` contrôle la surface du sandbox: `standard` (par défaut) ou `minimal`.
  Le préréglage `minimal` refuse `math.*` pour mieux se rapprocher d'un sous-ensemble inter-moteur.
- Affinez avec `--expr-allow PATTERN` et/ou `--expr-deny PATTERN` (répétable).
- `--unsafe-eval` contourne entièrement le sandbox (environnements de confiance uniquement).

## Filtres de trace et déterminisme

La commande `engine-trace` prend désormais en charge des filtres de taille/visibilité optionnels:
- `--leaf-only` limite `configuration`/`enteredStates`/`exitedStates` aux états feuilles.
- `--omit-actions` omet `actionLog` des entrées de trace.
- `--omit-delta` omet `datamodelDelta` (l'étape 0 imprime toujours un objet vide).
- `--omit-transitions` omet `firedTransitions` des entrées.
- `--advance-time N` avance l'horloge simulée avant le traitement des événements pour libérer
  les événements `<send>` retardés de manière déterministe dans les traces.

Pour améliorer la reproductibilité, les clés `datamodelDelta` sont émises dans l'ordre trié lorsqu'elles sont présentes.

## Ingestion JSON canonique

Même lorsque le CLI reçoit du SCXML, le runtime le convertit d'abord dans sa
forme SCJSON canonique et s'exécute par rapport à l'arbre JSON. Cela garantit que
les mêmes règles d'inférence s'appliquent quel que soit le format source et permet au moteur
de préserver l'ordre d'écriture pour le contenu exécutable en lisant directement de la
structure JSON normalisée.

## Guide de compatibilité de référence

Le runtime Python considère [`scion-core`](https://github.com/ReactiveSystems/scion-core)
comme la référence comportementale pour l'exécution SCXML:

- **Mise à jour active** – scion-core suit la dernière spécification W3C et applique
  les corrections de bogues plus rapidement que l'ancien moteur Apache Commons.
- **Sémantique canonique** – il résout les ambiguïtés de longue date concernant
  l'ordre des documents, l'achèvement parallèle et la portée du modèle de données de manière
  largement adoptée. La correspondance avec scion-core nous donne un comportement prévisible sur
  toutes les plateformes.
- **Exécuteur scriptable** – le dépôt contient `tools/scion-runner/scion-trace.cjs`
  qui est un mince wrapper exposant le même format de trace JSONL que le moteur Python.
  Le harnais de comparaison peut donc différencier les traces sans adaptateurs sur mesure.

### Utilisation de l'exécuteur de référence

1. Installez Node.js 18+ et exécutez `npm ci` dans `tools/scion-runner/`.
2. Appelez l'exécuteur directement ou via `SCJSON_REF_ENGINE_CMD`, par exemple:

   ```bash
   export SCJSON_REF_ENGINE_CMD="node tools/scion-runner/scion-trace.cjs"
   python py/exec_compare.py examples/toggle.scxml --events tests/exec/toggle.events.jsonl
   ```

3. Le harnais de comparaison normalise les traces avant de les différencier; les divergences apparaissent
   à la première étape non concordante et conservent les artefacts bruts pour inspection.

### Gestion des différences connues

scion-core implémente le modèle de données ECMA par défaut. Notre moteur ne prend actuellement en charge
que le modèle de données Python; les graphiques qui reposent sur des aides spécifiques à l'ECMA
doivent être convertis en expressions Python équivalentes avant comparaison. Pour
les tests qui dépendent encore de `ecmascript`, définissez `--unsafe-eval` temporairement ou protégez-les
derrière des indicateurs de fonctionnalité.

L'exécution de référence doit précéder les nouveaux travaux de fonctionnalité. Lors de l'extension du runtime Python,
ajoutez des graphiques de régression à `tests/exec/` et mettez à jour le harnais afin que le
nouveau scénario soit exercé par rapport à scion-core.

### État du contenu exécutable

- `<assign>`, `<log>` et `<raise>` s'exécutent dans l'ordre d'écriture et alimentent la
  trace JSON.
- `<if>`/`<elseif>`/`<else>` et `<foreach>` respectent l'ordre du document en consultant
  la structure JSON canonique plutôt que les dataclasses régénérées.
- `<send>` met en file d'attente des événements internes (y compris les charges utiles `<param>` et `namelist`);
  les envois retardés sont mis en file d'attente via le planificateur intégré et peuvent être
  déclenchés dans les tests avec `DocumentContext.advance_time(seconds)`. `<cancel>`
  supprime les envois internes en attente par ID. Les blocs de `<content>` textuels sont
  normalisés en objets JSON avant validation afin que les consommateurs en aval
  voient une structure cohérente, et le balisage imbriqué est sérialisé en dictionnaires
  avec les clés `qname`/`text`/`children` pour la compatibilité avec les charges utiles de scion-core.
- Les corps de transition s'exécutent entre la sortie et l'entrée:
  le contenu exécutable attaché à une `<transition>` est exécuté après le traitement
  de l'ensemble de sortie et avant que l'ensemble d'entrée ne soit pris, correspondant à
  un ordre respectueux des spécifications.
- Les transitions sans cible sont traitées comme internes: elles ne sortent d'aucun état.
  Ceci est requis pour les gestionnaires tels que `done.state.region` qui mettent à jour le
  modèle de données mais maintiennent la configuration intacte jusqu'à une transition ultérieure.
- Les cibles `<send>` externes ne sont pas exécutées; le runtime met en file d'attente
  `error.communication` et ignore la livraison.
- Les blocs `<script>` ne sont pas exécutés (aucune opération avec un avertissement).

### Invoke & Finalize (Échafaudage)

- Le moteur prend en charge la sémantique de base de `<invoke>` suffisante pour les tests:
  - À l'entrée d'état (après `onentry` et le traitement initial), les invocations listées
    sous l'état sont démarrées via un `InvokeRegistry` enfichable.
  - À la sortie d'état (avant `onexit`), toutes les invocations actives pour l'état sont
    annulées; leurs blocs `<finalize>` s'exécutent dans la portée de l'état d'invocation.
  - Un registre simulé est fourni avec trois types de gestionnaires:
    - `mock:immediate`: se termine immédiatement au démarrage et appelle la fonction de rappel `done`
      avec la charge utile initiale; le moteur exécute `<finalize>` et met en file d'attente
      `done.invoke.<id>` avec la charge utile.
    - `mock:record`: un gestionnaire sans opération qui enregistre les événements transmis via `send`.
    - `mock:deferred`: se termine lorsqu'il reçoit un événement nommé `complete`.
  - La matérialisation de la charge utile reflète `<send>`: collecte `<param>`, `namelist` et
    `<content>` dans un dictionnaire disponible pour le gestionnaire et comme `_event.data`
    pendant `<finalize>`.
  - `idlocation` est respecté; lorsque `id` n'est pas fourni, un UUID est généré.
  - `typeexpr` et `srcexpr` sont évalués dans la portée de l'état lorsqu'ils sont présents.
- `autoforward="true"` transmet les événements externes (à l'exclusion de `__*`, `error.*`,
  `done.state.*`, `done.invoke.*`) au gestionnaire actif via `handler.send(name, data)`.
- Les machines SCXML/SCJSON enfants transmettent leurs événements déclenchés à la file d'attente parente;
  l'achèvement est détecté via `done.state.<childRootId>`.
  - Le moteur enfant reconnaît `<send target="#_parent">` et émet directement
    dans la file d'attente d'événements du parent lorsqu'un émetteur est attaché par l'invocateur.

Politique d'ordonnancement
- Le moteur expose un bouton d'ordonnancement pour les émissions enfant→parent et la livraison de done.invoke.
  Configurez via le CLI `--ordering` ou en définissant `ctx.ordering_mode`.
  - `tolerant` (par défaut): les émissions enfant→parent sont insérées au début; done.invoke
    n'utilise l'insertion au début que si l'enfant n'a pas émis vers le parent plus tôt dans l'étape.
  - `strict`: les émissions enfant→parent utilisent une file d'attente normale (queue); done.invoke utilise une file d'attente normale
    (spécifique à l'ID puis générique).
  - `scion`: émule l'ordonnancement de SCION: les émissions enfant→parent utilisent une file d'attente normale, tandis que
    `done.invoke` est poussé au début avec générique avant spécifique à l'ID, permettant des transitions
    dans le même microstep dans un ordre compatible avec SCION.

Limitations:
- La sémantique complète de l'invocation SCXML (couplage de processeur, machines imbriquées, parité de gestion des erreurs)
  n'est pas implémentée. Le comportement actuel est conçu pour débloquer les tests du moteur et peut être étendu
  derrière l'`InvokeRegistry`.

### Invocateurs personnalisés

Vous pouvez étendre le registre avec vos propres types d'invocation. Au démarrage, le
moteur construit un `InvokeRegistry` par défaut que vous pouvez augmenter:

```python
from scjson.invoke import InvokeHandler

class MyService(InvokeHandler):
    def start(self) -> None:
        # perform setup, and optionally complete immediately
        pass

    def send(self, name: str, data=None) -> None:
        # receive autoforwarded parent events or explicit #_child sends
        if name == 'complete':
            self._on_done({'result': 'ok'})

# during context creation or before run
ctx.invoke_registry.register('my:service', lambda t, src, payload, on_done=None: MyService(t, src, payload, on_done))
```

Une fois enregistré, une entrée `<invoke type="my:service"/>` utilisera votre gestionnaire.
Les gestionnaires peuvent transmettre des événements au parent via l'émetteur du moteur; le runtime
attache automatiquement un émetteur pour les machines enfants afin que les envois `#_parent` fonctionnent
immédiatement. Pour les services externes, préférez émettre des événements parent avec
`self._emit` si nécessaire.

### Finalisation et événements de fin

- L'entrée dans un enfant `<final>` d'un état composé met immédiatement en file d'attente
  `done.state.<parentId>` après l'exécution des actions `onentry` du `<final>`.
- Si l'élément `<final>` contient `<donedata>`:
  - `<content>` définit la valeur complète de `_event.data` pour l'événement de fin.
  - Sinon, les paires `<param>` deviennent un dictionnaire attribué à `_event.data`.
- Pour `<parallel>`, le parent est considéré comme complet seulement lorsque toutes les régions sont
  finales; à ce moment-là, le moteur met en file d'attente `done.state.<parallelId>`.

### Historique (superficiel et profond)

- L'historique superficiel stocke l'ensemble des enfants immédiats actifs à la sortie; à la
  restauration, ces enfants sont ré-entrés en utilisant le traitement initial normal.
- L'historique profond stocke l'ensemble des feuilles descendantes actives sous le parent; à la
  restauration, le moteur entre le chemin exact du parent de l'historique jusqu'à chaque feuille enregistrée,
  sans suivre `<initial>` des nœuds intermédiaires.
  Ceci permet un retour à la configuration imbriquée précise d'avant la sortie.

### Erreurs

- Les conditions qui échouent à être évaluées, ou qui produisent des résultats non booléens, mettent en file d'attente
  `error.execution` et sont évaluées à faux.
- Les échecs d'évaluation de `<foreach>` mettent également en file d'attente `error.execution` et itèrent
  sur une séquence vide.
- `<assign>`
  - Les échecs d'expression mettent en file d'attente `error.execution` et stockent l'expression brute
    sous forme de chaîne comme valeur.
  - Les emplacements invalides (pas de variable correspondante dans la portée) mettent en file d'attente
    `error.execution` et ne créent pas de nouvelle variable.
- Les cibles `<send>` externes mettent en file d'attente `error.communication` et sont ignorées.

### Correspondance d'événements de transition

- Les attributs d'événement prennent en charge:
  - Des listes de noms séparées par des espaces (toute correspondance active la transition)
  - Le caractère générique `*` (correspond à tout événement externe)
  - Des motifs de préfixe comme `error.*` (correspond par exemple à `error.execution`)

### Balayage de tutoriel et liste d'ignorés

Le harnais de régression `py/uber_test.py::test_python_engine_executes_python_charts`
détecte le moteur Python au moment de l'exécution, charge chaque graphique de tutoriel avec
`datamodel="python"` et agrège les échecs avec leurs différences de trace.
Les graphiques qui dépendent de fonctionnalités non prises en charge sont capturés dans
`ENGINE_KNOWN_UNSUPPORTED` (voir `py/uber_test.py:44-58`); mettez à jour cette liste
chaque fois que de nouvelles capacités sont ajoutées afin que les régressions réelles restent visibles.
Les avertissements émis pendant l'exécution sont conservés dans le résumé des échecs pour
mettre en évidence les lacunes telles que les cibles externes ou les corps de `<script>`.

Lorsque vous ajoutez une couverture pour de nouveaux comportements (par exemple, l'annulation de `<send>` retardé),
préférez des tests unitaires ciblés parallèlement au balayage et supprimez les entrées d'ignorés une fois que
le scénario passe de bout en bout.
```

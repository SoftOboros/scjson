<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# MENTION LÉGALE

Ce dépôt contient du travail original développé pour le format `scjson` et ses outils, schémas et convertisseurs associés. Le projet intègre également des matériaux tiers sous leurs licences respectives, comme indiqué ci-dessous.

---

## Licence Principale

Tout le code original, le schéma, les exemples et la documentation rédigés dans ce dépôt sont sous licence :

**Licence BSD 1 Clause ("Licence BSD Zéro Clause")**
Identifiant SPDX : `BSD-1-Clause`

> La permission d'utiliser, de copier, de modifier et/ou de distribuer ce logiciel à quelque fin que ce soit, avec ou sans frais, est par la présente accordée.
> Le logiciel est fourni "tel quel" sans aucune garantie.

Voir [LICENSE](./LICENSE) pour les termes complets.

---

## Sous-module de Tutoriel Inclus

Ce dépôt inclut le sous-module Git suivant :

**Tutoriel de l'éditeur SCXML d'Alex Zhornyak**
Emplacement : [`/tutorial`](./tutorial)
Source : [https://github.com/Alexzhornyak/SCXML-Tutorial](https://github.com/Alexzhornyak/SCXML-Tutorial)
Licence : **BSD 3 Clauses**

Ce matériel est inclus pour fournir des exemples SCXML canoniques et des cas de test à des fins éducatives et de test de compatibilité.

> Tout le contenu original du sous-module reste la propriété de son auteur.
> Aucune approbation ou affiliation n'est implicite.

---

## Matériaux W3C

Ce dépôt référence et utilise du contenu dérivé de la Recommandation officielle SCXML du W3C :

- **Spécification SCXML** : [https://www.w3.org/TR/scxml/](https://www.w3.org/TR/scxml/)
- **Schéma XML SCXML (`scxml.xsd`)** : Inclus dans [`/schema`](./schema)

Ces matériaux sont utilisés selon les termes de la :

**Licence de Document W3C (2015)**
[https://www.w3.org/Consortium/Legal/2015/doc-license](https://www.w3.org/Consortium/Legal/2015/doc-license)

Selon la licence :
- La spécification SCXML peut être citée ou référencée à des fins d'implémentation.
- Les fichiers de schéma XML peuvent être utilisés ou redistribués sous forme non modifiée.
- Les versions modifiées ne doivent pas être présentées comme des artefacts officiels du W3C.

Ce projet inclut `scxml.xsd` sous forme non modifiée à des fins d'implémentation et de validation, et toute variante dérivée est clairement distinguée.

---

## Résumé des Composantes de Licence

| Composante                         | Licence              | Emplacement           |
|------------------------------------|----------------------|-----------------------|
| Ce dépôt (`scjson`)                | BSD-1-Clause         | Racine                |
| Sous-module tutoriel Zhornyak      | BSD-3-Clause         | `/tutorial`           |
| Spécification et XSD SCXML du W3C  | Licence de Document W3C | `/schema/scxml.xsd` |

---

Si vous avez des questions concernant les licences, l'attribution ou la réutilisation, veuillez ouvrir une issue ou contacter les mainteneurs.

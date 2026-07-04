# bim-query

Couche **requête / sélection read-only** sur un modèle BIM, extraite de
[`audit-bim-i3f`](https://github.com/Slimouzi/audit-bim-i3f). Elle travaille sur
un `ModelSnapshot` **normalisé** (contrat défini dans
[`bim-core`](https://github.com/Slimouzi/bim-core)) et **n'écrit jamais** dans
BIMData : ni appel réseau, ni mutation.

## Ce que le package fournit

| Module | Rôle |
|---|---|
| `bim_query.filtering` | prédicats + pagination sur objets / findings / suggestions (`apply_object_filter`, `apply_finding_filter`, `apply_suggestion_filter`, prédicats `*_matches`) |
| `bim_query.views` | adaptateur `ModelSnapshot` → `BimObject` (itérateur lazy, résolution spatiale) |
| `bim_query.property_aliases` | résolution sémantique de champs métier (alias multi-langue FR/EN : acoustique, feu, dimensions, fabricant, GMAO…) |
| `bim_query.table_query` | requêtes tabulaires (`BimQuery` → `BimQueryResult`) avec warnings qualité |
| `bim_query.presets` | presets métier (`doors_acoustic_dimensions`, `walls_fire_acoustic`, `equipment_maintenance`) |

## Frontière (read-only, source-agnostique)

- **Dépend de `bim-core` uniquement.** Le `ModelSnapshot` peut être produit en
  amont par `bimdata-read`, mais `bim-query` n'en dépend pas — il consomme un
  snapshot déjà normalisé, quelle qu'en soit la source.
- **Aucune écriture BIMData, aucun appel réseau.** BCF/Smart Views apply,
  transport BIMData et mutations relèvent d'autres couches.
- La **source** des suggestions (store de classification) reste côté
  `audit-bim-i3f` : `apply_suggestion_filter` accepte tout objet exposant
  `.all()` ou un simple itérable d'entrées (duck-typing structurel), sans
  importer la classe concrète.

## Installation

```bash
git clone https://github.com/Slimouzi/bim-query.git
cd bim-query
python -m venv .venv && source .venv/bin/activate
# bim-core n'est pas publié sur PyPI : on l'installe d'abord depuis son tag Git,
# sinon la résolution de la dépendance ``bim-core>=0.1.0,<0.2`` échoue.
pip install "git+https://github.com/Slimouzi/bim-core.git@bim-core-v0.1.0"
pip install -e ".[dev]"
```

## Exemple

```python
from bim_core.filters import ObjectFilter
from bim_query import BimQuery, iter_bim_objects, apply_object_filter, query_bim_table

# snapshot : ModelSnapshot (produit p.ex. par bimdata-read, ou une fixture)
doors, total, next_offset = apply_object_filter(
    iter_bim_objects(snapshot), ObjectFilter(ifc_types=["IfcDoor"])
)

result = query_bim_table(
    snapshot,
    BimQuery(
        object_filter=ObjectFilter(ifc_types=["IfcDoor"]),
        fields=["name", "acoustic_performance", "width", "fire_rating"],
    ),
)
print(result.columns, result.total, result.warnings)
```

## Tests

```bash
pytest -q
```

Couvre le filtrage (objets / findings / suggestions), la résolution d'alias,
les requêtes tabulaires et l'intégrité des presets — sur des fixtures
`ModelSnapshot` déterministes, **offline**.

## Licence

Apache-2.0 — © Stanislas Limouzi / BIMData.

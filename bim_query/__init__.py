"""bim-query — couche **requête / sélection read-only** sur un modèle BIM.

Travaille sur un ``ModelSnapshot`` **normalisé** (contrat ``bim-core``) : filtrage
déclaratif d'objets / findings / suggestions, adaptateur snapshot → ``BimObject``,
requêtes tabulaires sémantiques (alias multi-langue) et presets métier.

**Source-agnostique** : ne dépend que de ``bim-core``. Le snapshot peut être
produit en amont par ``bimdata-read``, mais ``bim-query`` n'en dépend pas et
n'effectue **aucune écriture BIMData, aucun appel réseau**. La *source* des
suggestions (store de classification) reste côté ``audit-bim-i3f`` ; le filtre
correspondant est structurel (duck-typing).
"""

from __future__ import annotations

from .filtering import (
    apply_finding_filter,
    apply_object_filter,
    apply_suggestion_filter,
    finding_matches,
    object_matches,
    suggestion_matches,
)
from .presets import QUERY_PRESETS, get_preset, list_presets
from .property_aliases import (
    MatchedValue,
    find_attribute_value,
    find_material_value,
    find_property_value,
    find_quantity_value,
    normalize_key,
    resolve_requested_field,
)
from .table_query import (
    KNOWN_FIELDS,
    BimQuery,
    BimQueryResult,
    BimQueryRow,
    query_bim_table,
)
from .views import bim_object_from_element, iter_bim_objects

__all__ = [
    # filtering
    "apply_object_filter",
    "apply_finding_filter",
    "apply_suggestion_filter",
    "object_matches",
    "finding_matches",
    "suggestion_matches",
    # views
    "iter_bim_objects",
    "bim_object_from_element",
    # table query
    "BimQuery",
    "BimQueryRow",
    "BimQueryResult",
    "query_bim_table",
    "KNOWN_FIELDS",
    # property aliases
    "resolve_requested_field",
    "normalize_key",
    "find_property_value",
    "find_quantity_value",
    "find_attribute_value",
    "find_material_value",
    "MatchedValue",
    # presets
    "QUERY_PRESETS",
    "list_presets",
    "get_preset",
]

__version__ = "0.1.1"

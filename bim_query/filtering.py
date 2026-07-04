"""Application des filtres déclaratifs sur les collections domaine.

Ces fonctions sont **pures** (pas d'I/O, pas d'état global). Elles
acceptent un itérable et un filtre, retournent une liste finie après
application de la pagination.

Convention pagination
---------------------

- ``offset`` et ``limit`` sont appliqués **après** le filtrage ; pas de
  short-circuit sur l'itération.
- Le `total` (nombre d'items qui matchent avant pagination) est calculé
  en parallèle pour que les tools MCP puissent renvoyer ``{items, total,
  next_offset}``.
- Pas de tri imposé : les caller passent leur propre clé via
  ``sort_key`` si besoin.

Note extraction
---------------

Ce module vit désormais dans le package **``bim-query``** et ne dépend que
de ``bim-core`` (``ModelSnapshot``/``BimObject``/filtres). La **source** des
suggestions (le store de classification) reste côté ``audit-bim-i3f`` :
:func:`apply_suggestion_filter` accepte donc n'importe quel objet exposant
``.all()`` (le store réel) **ou** un simple itérable d'entrées — via
duck-typing structurel (:class:`SuggestionEntry` / :class:`SuggestionStore`),
sans importer la classe concrète.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Protocol, TypeVar

from bim_core.bim_object import BimObject
from bim_core.filters import (
    ConfidenceBand,
    FindingFilter,
    ObjectFilter,
    SuggestionFilter,
    SuggestionStatus,
)
from bim_core.findings import Finding, Severity

if TYPE_CHECKING:  # pragma: no cover — typing only
    pass

T = TypeVar("T")


# ── Contrats structurels (suggestions) ───────────────────────────────────
#
# La source concrète (ClassificationSuggestionStore / ...Entry) reste dans
# audit-bim-i3f. Ici on ne dépend que de la *forme* attendue, via Protocol.


class SuggestionEntry(Protocol):
    """Forme attendue d'une entrée de suggestion (duck-typing)."""

    element_uuid: str
    ifc_type: str | None
    proposed_classification: str
    proposed_level_3: str
    confidence: float
    confidence_band: ConfidenceBand
    status: SuggestionStatus
    source: str

    @property
    def is_mismatch(self) -> bool: ...

    @property
    def is_missing_current(self) -> bool: ...


class SuggestionStore(Protocol):
    """Forme attendue d'un store de suggestions (expose ``.all()``)."""

    def all(self) -> Iterable[SuggestionEntry]: ...


# ── Helpers génériques ───────────────────────────────────────────────────


def _paginate(items: list[T], offset: int, limit: int) -> tuple[list[T], int, int | None]:
    """Applique offset/limit et calcule le ``next_offset``.

    Returns:
        ``(slice, total, next_offset)`` où ``next_offset`` est ``None``
        s'il n'y a plus de pages.
    """
    total = len(items)
    end = offset + limit
    next_offset = end if end < total else None
    return items[offset:end], total, next_offset


def _in_or_all(values: list[str] | None, candidate: str | None) -> bool:
    """``True`` si ``candidate`` ∈ ``values`` (ou si ``values`` est None)."""
    if values is None:
        return True
    if candidate is None:
        return False
    return candidate in values


def _in_ci(values: list[str] | None, candidate: str | None) -> bool:
    """Insensible à la casse."""
    if values is None:
        return True
    if candidate is None:
        return False
    cl = candidate.lower()
    return any(v.lower() == cl for v in values)


# ── ObjectFilter ─────────────────────────────────────────────────────────


def _object_matches(obj: BimObject, f: ObjectFilter) -> bool:
    if f.uuids is not None and obj.uuid not in f.uuids:
        return False
    if not _in_or_all(f.ifc_types, obj.ifc_type):
        return False

    if not _in_ci(f.storey_names, obj.storey_name):
        return False
    if not _in_or_all(f.storey_uuids, obj.storey_uuid):
        return False
    if not _in_ci(f.zone_names, obj.zone_name):
        return False
    if not _in_or_all(f.zone_uuids, obj.zone_uuid):
        return False
    if not _in_ci(f.space_names, obj.space_name):
        return False
    if not _in_or_all(f.space_uuids, obj.space_uuid):
        return False

    if f.is_external is not None and obj.is_external is not f.is_external:
        return False
    if f.load_bearing is not None and obj.load_bearing is not f.load_bearing:
        return False

    if f.has_any_classification is not None:
        has = obj.has_classification(system=f.classification_system)
        if has is not f.has_any_classification:
            return False

    if f.current_classification_codes is not None:
        codes = {c.upper() for c in obj.classification_codes(system=f.classification_system)}
        if not any(c.upper() in codes for c in f.current_classification_codes):
            return False

    if f.current_level_3 is not None:
        l3s = {c.level_3 for c in obj.classifications}
        if f.classification_system is not None:
            l3s = {
                c.level_3
                for c in obj.classifications
                if (c.system or "").lower() == f.classification_system.lower()
            }
        if not any(target.upper() in l3s for target in f.current_level_3):
            return False

    if f.has_property is not None and not obj.has_property(f.has_property):
        return False
    if f.missing_property is not None and obj.has_property(f.missing_property):
        return False

    if f.has_base_quantities is not None and obj.has_base_quantities() is not f.has_base_quantities:
        return False
    if f.has_quantity is not None and obj.get_quantity(f.has_quantity) is None:
        return False
    if f.missing_quantity is not None and obj.get_quantity(f.missing_quantity) is not None:
        return False

    if f.name_contains is not None or f.name_regex is not None:
        blob = f"{obj.name or ''} {obj.long_name or ''}"
        if f.name_contains is not None and f.name_contains.lower() not in blob.lower():
            return False
        if f.name_regex is not None and not re.search(f.name_regex, blob, re.IGNORECASE):
            return False

    if f.layer_contains is not None:
        needle = f.layer_contains.lower()
        if not any(needle in (layer or "").lower() for layer in obj.layers):
            return False
    if f.material_contains is not None:
        needle = f.material_contains.lower()
        if not any(needle in (mat or "").lower() for mat in obj.materials):
            return False

    if f.source is not None and obj.source.lower() != f.source.lower():
        return False

    return True


def apply_object_filter(
    objects: Iterable[BimObject],
    f: ObjectFilter,
    *,
    sort_key: Callable[[BimObject], object] | None = None,
) -> tuple[list[BimObject], int, int | None]:
    """Filtre + tri + pagination sur :class:`BimObject`.

    Returns:
        ``(items, total, next_offset)``.
    """
    matched = [o for o in objects if _object_matches(o, f)]
    if sort_key is not None:
        matched.sort(key=sort_key)
    return _paginate(matched, f.offset, f.limit)


# ── FindingFilter ────────────────────────────────────────────────────────


_SEV_ORDER = {s: i for i, s in enumerate(Severity.ordered())}


def _finding_matches(finding: Finding, f: FindingFilter) -> bool:
    if f.themes is not None and finding.theme.value not in f.themes:
        return False
    if f.severities is not None and finding.severity.value not in f.severities:
        return False
    if f.severity_min is not None:
        try:
            min_idx = _SEV_ORDER[Severity(f.severity_min)]
        except (KeyError, ValueError) as exc:
            raise ValueError(f"severity_min invalide : {f.severity_min!r}") from exc
        if _SEV_ORDER.get(finding.severity, 99) > min_idx:
            return False
    if f.error_types is not None and finding.error_type.value not in f.error_types:
        return False
    if not _in_or_all(f.ifc_types, finding.ifc_type):
        return False
    if f.element_uuids is not None:
        if finding.element_uuid is None or finding.element_uuid not in f.element_uuids:
            return False
    if f.require_element_uuid is True and finding.element_uuid is None:
        return False
    if f.require_element_uuid is False and finding.element_uuid is not None:
        return False
    return True


def apply_finding_filter(
    findings: Iterable[Finding],
    f: FindingFilter,
) -> tuple[list[Finding], int, int | None]:
    matched = [x for x in findings if _finding_matches(x, f)]
    return _paginate(matched, f.offset, f.limit)


# ── SuggestionFilter ─────────────────────────────────────────────────────


def _suggestion_matches(entry: SuggestionEntry, f: SuggestionFilter) -> bool:
    if f.element_uuids is not None and entry.element_uuid not in f.element_uuids:
        return False
    if not _in_or_all(f.ifc_types, entry.ifc_type):
        return False

    if f.proposed_codes is not None:
        if entry.proposed_classification.upper() not in {c.upper() for c in f.proposed_codes}:
            return False
    if f.proposed_level_3 is not None:
        if entry.proposed_level_3.upper() not in {c.upper() for c in f.proposed_level_3}:
            return False

    if f.min_confidence is not None and entry.confidence < f.min_confidence:
        return False
    if f.max_confidence is not None and entry.confidence > f.max_confidence:
        return False
    if f.confidence_bands is not None:
        if entry.confidence_band not in f.confidence_bands:
            return False

    if f.statuses is not None and entry.status not in f.statuses:
        return False

    if f.only_mismatches is True and not entry.is_mismatch:
        return False
    if f.only_mismatches is False and entry.is_mismatch:
        return False

    if f.only_missing_current is True and not entry.is_missing_current:
        return False
    if f.only_missing_current is False and entry.is_missing_current:
        return False

    if f.sources is not None and entry.source not in f.sources:
        return False

    return True


def apply_suggestion_filter(
    store: SuggestionStore | Iterable[SuggestionEntry],
    f: SuggestionFilter,
) -> tuple[list[SuggestionEntry], int, int | None]:
    """Filtre + pagination sur les entrées du store.

    Args:
        store: Soit un store complet (objet exposant ``.all()``), soit un
            itérable d'entrées. Détection **structurelle** (duck-typing) —
            aucun import de la classe concrète, qui reste côté audit-bim-i3f.
        f: Filtre déclaratif.
    """
    all_method = getattr(store, "all", None)
    if callable(all_method):
        iterable: Iterable[SuggestionEntry] = all_method()
    else:
        iterable = store  # type: ignore[assignment]
    matched = [e for e in iterable if _suggestion_matches(e, f)]
    # Tri par confiance décroissante par défaut — comportement attendu
    # par les tools MCP de revue.
    matched.sort(key=lambda e: (-e.confidence, e.element_uuid))
    return _paginate(matched, f.offset, f.limit)


# ── Prédicats publics (sans pagination, hors limite MAX_LIMIT) ───────────

# Alias publics utilisés par les planners de la couche actions/ pour
# parcourir l'intégralité d'une collection sans contrainte de pagination
# (l'API MCP utilise apply_*_filter qui borne à MAX_LIMIT=500 ; un
# planner peut légitimement traiter plus d'éléments).

object_matches = _object_matches
finding_matches = _finding_matches
suggestion_matches = _suggestion_matches


# Re-exports pour confort de test
__all__ = [
    "apply_object_filter",
    "apply_finding_filter",
    "apply_suggestion_filter",
    "object_matches",
    "finding_matches",
    "suggestion_matches",
    "SuggestionEntry",
    "SuggestionStore",
    "ConfidenceBand",
    "SuggestionStatus",
]

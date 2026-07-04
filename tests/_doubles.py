"""Doubles de test pour la *source* des suggestions.

La classe concrète ``ClassificationSuggestionStore`` / ``...Entry`` vit dans
``audit-bim-i3f`` (couche audit/classifier) — **hors** du package ``bim-query``,
conformément à la frontière : le filtrage est pur (dans le package), mais la
source des suggestions reste côté audit.

Ces doubles reproduisent **fidèlement** la forme structurelle attendue par
:func:`bim_query.filtering.apply_suggestion_filter` (attributs + propriétés
calculées ``is_mismatch`` / ``is_missing_current`` + ``store.all()``), en ne
dépendant que des enums ``bim-core``. Ils servent à prouver que le filtre
fonctionne en autonomie, sans importer audit-bim.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from bim_core.filters import ConfidenceBand, SuggestionStatus
from pydantic import BaseModel, ConfigDict, Field


class ClassificationSuggestionEntry(BaseModel):
    """Double structurel d'une entrée de suggestion (cf. audit-bim-i3f)."""

    model_config = ConfigDict(extra="ignore")

    element_uuid: str
    ifc_type: str | None = None

    current_classification: str | None = None
    current_classification_system: str | None = None

    proposed_classification: str
    proposed_label: str | None = None
    proposed_system: str = "uniformat"
    proposed_level_3: str

    confidence: float = Field(..., ge=0.0, le=1.0)
    confidence_band: ConfidenceBand

    reason_codes: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)

    status: SuggestionStatus = SuggestionStatus.PROPOSED
    source: str = "audit"

    alternatives: list[dict[str, Any]] = Field(default_factory=list)

    @property
    def is_mismatch(self) -> bool:
        if not self.current_classification:
            return False
        cur = (self.current_classification or "").strip().upper()
        cur_l3 = cur[:5] if len(cur) >= 5 and cur[0].isalpha() else cur
        return cur_l3 != self.proposed_level_3.upper()

    @property
    def is_missing_current(self) -> bool:
        return self.current_classification is None or self.current_classification.strip() == ""


class ClassificationSuggestionStore:
    """Double structurel du store (indexé par ``element_uuid``, expose ``all()``)."""

    def __init__(self) -> None:
        self._by_uuid: dict[str, ClassificationSuggestionEntry] = {}

    def add(self, entry: ClassificationSuggestionEntry, *, replace: bool = False) -> None:
        if entry.element_uuid in self._by_uuid and not replace:
            return
        self._by_uuid[entry.element_uuid] = entry

    def get(self, element_uuid: str) -> ClassificationSuggestionEntry | None:
        return self._by_uuid.get(element_uuid)

    def all(self) -> list[ClassificationSuggestionEntry]:
        return list(self._by_uuid.values())

    def __len__(self) -> int:
        return len(self._by_uuid)

    def __iter__(self) -> Iterator[ClassificationSuggestionEntry]:
        return iter(self._by_uuid.values())

"""Intégrité des presets métier (données pures)."""

from __future__ import annotations

import pytest
from bim_core.filters import ObjectFilter

from bim_query import get_preset, list_presets
from bim_query.presets import QUERY_PRESETS
from bim_query.table_query import KNOWN_FIELDS

_EXPECTED = {
    "doors_acoustic_dimensions",
    "walls_fire_acoustic",
    "equipment_maintenance",
}


def test_expected_presets_present():
    assert set(list_presets()) == _EXPECTED
    assert set(QUERY_PRESETS) == _EXPECTED


@pytest.mark.parametrize("name", sorted(_EXPECTED))
def test_preset_shape(name):
    preset = get_preset(name)
    assert set(preset) >= {"description", "filter", "fields"}
    assert isinstance(preset["description"], str) and preset["description"]
    assert isinstance(preset["fields"], list) and preset["fields"]


@pytest.mark.parametrize("name", sorted(_EXPECTED))
def test_preset_filter_is_valid_object_filter(name):
    # Le dict ``filter`` doit être accepté tel quel par ObjectFilter (bim-core).
    ObjectFilter(**get_preset(name)["filter"])


@pytest.mark.parametrize("name", sorted(_EXPECTED))
def test_preset_fields_are_known_or_dotted(name):
    # Chaque champ est soit un champ connu du moteur tabulaire, soit un
    # nom pointé (Pset.Prop) traité en fallback dynamique.
    known = {k.lower() for k in KNOWN_FIELDS}
    for f in get_preset(name)["fields"]:
        assert f.lower() in known or "." in f, f"champ preset non résolvable : {f!r}"


def test_get_preset_unknown_raises():
    with pytest.raises(KeyError):
        get_preset("does_not_exist")

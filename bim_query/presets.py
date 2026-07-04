"""Presets métier pour les requêtes tabulaires (``query_bim_preset``).

Requêtes préconfigurées pour les cas d'usage fréquents — portes
(acoustique / dimensions), murs (feu / acoustique), équipements techniques
(maintenance). Chaque preset = ``{description, filter, fields}`` où
``filter`` est un dict compatible :class:`bim_core.filters.ObjectFilter` et
``fields`` la liste de champs à projeter (résolus via
:mod:`bim_query.property_aliases`).

Volontairement en données pures (module-level), listables / testables
indépendamment de la couche MCP. La surface MCP (``query_bim_preset`` /
``list_query_presets``) reste côté ``audit-bim-i3f`` et consomme ce registre.
"""

from __future__ import annotations

# ── Presets métier ───────────────────────────────────────────────────────

QUERY_PRESETS: dict[str, dict] = {
    "doors_acoustic_dimensions": {
        "description": (
            "Portes — matériaux, performance acoustique, dimensions, "
            "résistance au feu, localisation."
        ),
        "filter": {"ifc_types": ["IfcDoor", "IfcDoorStandardCase"]},
        "fields": [
            "uuid",
            "name",
            "object_type",
            "materials",
            "acoustic_performance",
            "height",
            "width",
            "thickness",
            "fire_rating",
            "storey",
            "space",
        ],
    },
    "walls_fire_acoustic": {
        "description": (
            "Murs — matériaux, résistance au feu, performance acoustique, "
            "épaisseur, IsExternal, LoadBearing."
        ),
        "filter": {
            "ifc_types": [
                "IfcWall",
                "IfcWallStandardCase",
                "IfcWallElementedCase",
                "IfcCurtainWall",
            ]
        },
        "fields": [
            "uuid",
            "name",
            "materials",
            "fire_rating",
            "acoustic_performance",
            "thickness",
            "is_external",
            "load_bearing",
            "storey",
        ],
    },
    "equipment_maintenance": {
        "description": (
            "Équipements techniques — fabricant, référence, ID maintenance, "
            "numéro de série, tag, localisation."
        ),
        "filter": {
            # ``ObjectFilter`` matche les types IFC en exact. On liste donc
            # explicitement les classes "parent" abstraites ET les classes
            # concrètes les plus fréquentes en CVC / Plomberie / Électricité.
            # (Limitation connue : un IfcXxxStandardCase non listé sera
            # raté ; à terme, ajouter ``include_ifc_subclasses=True`` à
            # ``ObjectFilter`` pour résoudre via une table IFC4 supertypes.)
            "ifc_types": [
                # Classes parent abstraites
                "IfcDistributionElement",
                "IfcDistributionFlowElement",
                "IfcDistributionControlElement",
                "IfcEnergyConversionDevice",
                "IfcFlowTerminal",
                "IfcFlowController",
                "IfcFlowSegment",
                "IfcFlowFitting",
                "IfcFlowStorageDevice",
                "IfcFlowMovingDevice",
                "IfcFlowTreatmentDevice",
                # CVC — Énergie / chaud / froid
                "IfcBoiler",
                "IfcChiller",
                "IfcCoil",
                "IfcCoolingTower",
                "IfcHeatExchanger",
                "IfcSpaceHeater",
                "IfcUnitaryEquipment",
                "IfcEvaporator",
                "IfcCondenser",
                # CVC — Air
                "IfcAirTerminal",
                "IfcAirTerminalBox",
                "IfcDuctFitting",
                "IfcDuctSegment",
                "IfcDuctSilencer",
                "IfcDamper",
                "IfcFan",
                "IfcFilter",
                # Plomberie / fluide
                "IfcPump",
                "IfcValve",
                "IfcPipeFitting",
                "IfcPipeSegment",
                "IfcSanitaryTerminal",
                "IfcWasteTerminal",
                "IfcStackTerminal",
                "IfcTank",
                # Électricité / éclairage / signal
                "IfcElectricAppliance",
                "IfcElectricDistributionBoard",
                "IfcElectricFlowStorageDevice",
                "IfcElectricGenerator",
                "IfcElectricMotor",
                "IfcLightFixture",
                "IfcLamp",
                "IfcOutlet",
                "IfcSwitchingDevice",
                "IfcCableSegment",
                "IfcCableFitting",
                "IfcCableCarrierSegment",
                "IfcCableCarrierFitting",
                "IfcJunctionBox",
                "IfcProtectiveDevice",
                # Sécurité / détection
                "IfcAlarm",
                "IfcSensor",
                "IfcController",
                "IfcActuator",
                "IfcFireSuppressionTerminal",
                # Transport
                "IfcTransportElement",
            ]
        },
        "fields": [
            "uuid",
            "name",
            "ifc_type",
            "manufacturer",
            "reference",
            "maintenance_id",
            "serial_number",
            "tag",
            "space",
            "zone",
        ],
    },
}


def list_presets() -> list[str]:
    """Noms des presets disponibles (ordre d'insertion)."""
    return list(QUERY_PRESETS.keys())


def get_preset(name: str) -> dict:
    """Retourne le preset ``name``.

    Raises:
        KeyError: si le preset n'existe pas.
    """
    return QUERY_PRESETS[name]


__all__ = ["QUERY_PRESETS", "list_presets", "get_preset"]

from __future__ import annotations
from typing import Literal
import uuid

POWERS = [
    "England", "France", "Germany", "Italy", "Austria", "Russia", "Turkey"
]

INITIAL_UNITS = {
    "England": [
        {"type": "F", "loc": "London"},
        {"type": "F", "loc": "Edinburgh"},
        {"type": "A", "loc": "Liverpool"},
    ],
    "France": [
        {"type": "A", "loc": "Paris"},
        {"type": "A", "loc": "Marseilles"},
        {"type": "F", "loc": "Brest"},
    ],
    "Germany": [
        {"type": "A", "loc": "Berlin"},
        {"type": "A", "loc": "Munich"},
        {"type": "F", "loc": "Kiel"},
    ],
    "Italy": [
        {"type": "A", "loc": "Rome"},
        {"type": "A", "loc": "Venice"},
        {"type": "F", "loc": "Naples"},
    ],
    "Austria": [
        {"type": "A", "loc": "Vienna"},
        {"type": "A", "loc": "Budapest"},
        {"type": "F", "loc": "Trieste"},
    ],
    "Russia": [
        {"type": "A", "loc": "Moscow"},
        {"type": "A", "loc": "Warsaw"},
        {"type": "F", "loc": "Sevastopol"},
        {"type": "F", "loc": "StPetersburg(sc)"},
    ],
    "Turkey": [
        {"type": "A", "loc": "Constantinople"},
        {"type": "A", "loc": "Smyrna"},
        {"type": "F", "loc": "Ankara"},
    ],
}

PhaseType = Literal["Movement", "Retreat", "Adjustment"]


def initial_board_state() -> dict:
    units = []
    for power, ulist in INITIAL_UNITS.items():
        for u in ulist:
            units.append({
                "id": str(uuid.uuid4()),
                "power": power,
                "type": u["type"],
                "loc": u["loc"],
            })
    return {
        "season": "Spring",
        "year": 1901,
        "phase_type": "Movement",
        "units": units,
        "supply_centers": {},
    }


def next_phase(season: str, year: int, phase_type: PhaseType):
    if phase_type == "Movement":
        return season, year, "Retreat"
    if phase_type == "Retreat":
        if season == "Spring":
            return "Fall", year, "Movement"
        else:
            return "Fall", year, "Adjustment"
    if phase_type == "Adjustment":
        return "Spring", year + 1, "Movement"
    raise ValueError("invalid phase")

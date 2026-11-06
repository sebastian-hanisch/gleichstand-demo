"""Gemeinsame Fixtures: das Handbeispiel (n = 3), an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gst_scenario import Instance  # noqa: E402

HAND_A = ((1, 3, 2), (2, 4, 2), (1, 3, 3))
HAND_B = ((2, 1, 3), (1, 3, 2), (3, 2, 1))
HAND_C = ((4, 4, 1), (3, 1, 2), (2, 3, 2))


def make_hand() -> Instance:
    return Instance((HAND_A, HAND_B, HAND_C), True)


@pytest.fixture
def hand():
    """Handbeispiel n = 3 (A Kosten, B Zeit, C Wünsche; Zeile Person, Spalte Aufgabe). Sechs Pläne mit (Maximum, Summe, Quadratsumme, C-Summe) von A:
    (0,1,2): (4, 8, 26, 7); (0,2,1): (3, 6, 14, 9); (1,0,2): (3, 8, 22, 9); (1,2,0): (3, 6, 14, 8); (2,0,1): (3, 7, 17, 7); (2,1,0): (4, 7, 21, 4).
    Kette ab Maximum: 4 Pläne, dann 2 (Summe 6), 2 (Quadratsumme 14), 1 (C-Summe 8: Plan (1,2,0)), 1."""
    return make_hand()


@pytest.fixture
def hand_arrays(hand) -> list[np.ndarray]:
    return hand.arrays()

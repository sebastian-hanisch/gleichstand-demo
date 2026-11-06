"""Szenario: n Personen, n Aufgaben, drei Belastungen je Paar: A (Kosten), B (Zeit), C (Wünsche), drei unabhängige Matrizen. Alles simuliert.

Ganze Zahlen 1 bis K (K = 3, 9, 99, 999: je gröber, desto mehr Gleichstände) oder reell gleichverteilt 0 bis 100 (Gleichstände entstehen dort nur beim
Maximum, weil nur ein einziger Eintrag zählt)."""

from dataclasses import dataclass

import numpy as np

import gst_constants as C


@dataclass(frozen=True)
class Instance:
    mats: tuple               # drei Matrizen (A, B, C) als Tupel von Tupeln (ganze Zahlen oder Gleitkommazahlen)
    exact: bool               # ganze Zahlen (exakter Vergleich)?

    @property
    def n(self) -> int:
        return len(self.mats[0])

    def arrays(self) -> list[np.ndarray]:
        return [np.array(m, dtype=np.int64 if self.exact else float) for m in self.mats]


def _tup(m) -> tuple:
    return tuple(tuple(x.item() for x in row) for row in m)


def make_instance(n: int, family: int, seed: int) -> Instance:
    """Deterministisch aus (n, Familie, Seed): gleiche Eingabe, gleiche Instanz."""
    rng = np.random.default_rng(seed)
    k = C.GRANULARITIES[family]
    if k == 0:
        return Instance(tuple(_tup(rng.uniform(0.0, 100.0, (n, n))) for _ in range(3)), False)
    return Instance(tuple(_tup(rng.integers(1, k + 1, (n, n)).astype(np.int64)) for _ in range(3)), True)


def relabel_arrays(mats: list[np.ndarray], rng: np.random.Generator) -> tuple[list[np.ndarray], np.ndarray, np.ndarray]:
    """Personen (Zeilen) und Aufgaben (Spalten) aller Matrizen zufällig umnummerieren; derselbe Sachverhalt, andere Nummern.

    Rückgabe: die umnummerierten Matrizen und die beiden Permutationen (neue Zeile i ist alte Zeile r[i], neue Spalte j ist alte Spalte c[j])."""
    n = mats[0].shape[0]
    r, c = rng.permutation(n), rng.permutation(n)
    return [m[r][:, c] for m in mats], r, c

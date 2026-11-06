"""Kern der Demo (numpy, scipy): Gleichstände im Optimum einer Zuordnung und was danach entscheidet.

Drei Matrizen A (Kosten), B (Zeit), C (Wünsche), Summenkriterien. Zielarten auf A: Summe, Quadratsumme, Maximum der Belastungen.
  * `objectives`: je Plan Summe, Quadratsumme, Maximum, absteigend sortierter Belastungsvektor (Leximax) von A sowie die Summen von B und C (n <= 9).
  * `opt_set`: Indizes aller Pläne mit kleinstem Wert (die Optimalmenge); exakt bei ganzen Zahlen.
  * `chain_sets`: Optimalmenge nach jeder Ebene der Kette (Ziel, dann Maximum, Summe, Quadratsumme, C-Summe, Leximax, ohne Wiederholung).
  * `pick`: der gewählte Plan nach einer Regel: erster Plan der Aufzählung, letzter, Zufall mit Seed, kleinste Nebenkennzahl, volle Kette.
  * `values`: die Kennzahlen (Summe A, Maximum A, Summe B, Summe C) eines Plans; sie ändern sich nicht, wenn man Personen und Aufgaben umnummeriert.
  * `lap_plan`, `highs_plan`: die Summe über die Ungarische Methode und über HiGHS (scipy.optimize.milp, Voreinstellungen).
Quelle: Aufzählung (`all_plans`, `burdens`, `check_feasible`), Ungarische Methode und HiGHS-Aufruf stammen aus Stück 1 bis 4 der Linie (zielvergleich-demo,
preis-der-fairness-demo, zwei-kriterien-demo, lexikographisch-demo); neu sind Optimalmengen, Kette, Regeln, Spanne und der Vergleich unter Umnummerieren.
Gleichstandsregeln (sichtbar, siehe README): „erster Plan“ heißt der kleinste Index in der Reihenfolge von `itertools.permutations`; das ist eine Folge der
Nummerierung und kein Merkmal des Problems.
"""

import itertools
from functools import lru_cache

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linear_sum_assignment, milp

import gst_constants as C


@lru_cache(maxsize=None)
def all_plans(n: int) -> np.ndarray:
    """Alle n! Pläne als Zeilen (Reihenfolge von itertools.permutations); nur bis n = 9."""
    if not 1 <= n <= 9:
        raise ValueError(f"n = {n}: Aufzählung nur für 1 bis 9 Personen")
    return np.array(list(itertools.permutations(range(n))), dtype=np.int16)


def check_feasible(plan, n: int) -> bool:
    """Unabhängiger Prüfer: der Plan ist eine Zuordnung, jede Aufgabe genau einmal."""
    plan = [int(j) for j in plan]
    return len(plan) == n and sorted(plan) == list(range(n))


def burdens(m: np.ndarray, n: int) -> np.ndarray:
    """Belastungsvektoren aller Pläne für eine Matrix, Form (n!, n)."""
    return m[np.arange(n)[None, :], all_plans(n)]


def objectives(mats: list[np.ndarray], n: int) -> dict:
    """Je Plan: sum, sq, max, sorted (Belastungen von A absteigend sortiert), sumB, sumC."""
    b = burdens(mats[0], n)
    return {"sum": b.sum(axis=1), "sq": (b * b).sum(axis=1), "max": b.max(axis=1), "sorted": -np.sort(-b, axis=1),
            "sumB": burdens(mats[1], n).sum(axis=1), "sumC": burdens(mats[2], n).sum(axis=1)}


def opt_set(values: np.ndarray) -> np.ndarray:
    """Indizes aller Pläne mit kleinstem Wert; bei Gleitkommazahlen gilt Gleichheit der Zahl (praktisch nur beim Maximum)."""
    return np.flatnonzero(values == values.min())


def chain_order(objective: str) -> list[str]:
    """Reihenfolge der Kette: das gewählte Ziel zuerst, dann Maximum, Summe, Quadratsumme, C-Summe, Leximax ohne Wiederholung."""
    return [objective] + [k for k in C.CHAIN_KEYS if k != objective]


def _filter(o: dict, idx: np.ndarray, key: str) -> np.ndarray:
    if key == "sorted":
        vecs = o["sorted"][idx]
        best = min(map(tuple, vecs))
        return idx[[tuple(v) == best for v in vecs]]
    col = o[key][idx]
    return idx[col == col.min()]


def chain_sets(o: dict, objective: str) -> list[np.ndarray]:
    """Optimalmenge nach jeder Ebene der Kette (Länge 5: das Ziel und die vier weiteren)."""
    keys = chain_order(objective)
    idx = opt_set(o[keys[0]])
    out = [idx]
    for key in keys[1:]:
        idx = _filter(o, idx, key)
        out.append(idx)
    return out


def pick(o: dict, objective: str, rule: str, seed: int = 0) -> int:
    """Index des gewählten Plans nach der Regel (siehe Modulkopf); bei vollem Gleichstand der erste Plan der Aufzählung."""
    base = opt_set(o[objective])
    if rule == "first":
        return int(base[0])
    if rule == "last":
        return int(base[-1])
    if rule == "random":
        return int(np.random.default_rng(seed).choice(base))
    if rule == "secondary":
        return int(_filter(o, base, C.SECONDARY[objective])[0])
    if rule == "chain":
        return int(chain_sets(o, objective)[-1][0])
    raise ValueError(f"unbekannte Regel: {rule}")


def values(o: dict, idx: int) -> tuple:
    """Kennzahlen eines Plans: (Summe A, Maximum A, Summe B, Summe C); unabhängig von der Nummerierung."""
    return tuple(o[k][idx].item() for k in ("sum", "max", "sumB", "sumC"))


def same_values(v0: tuple, v1: tuple, exact: bool) -> bool:
    """Gleiche Kennzahlen? Ganze Zahlen exakt; Gleitkommazahlen mit relativer Toleranz 1e-9 (die Summationsreihenfolge ändert die letzten Bits)."""
    if exact:
        return v0 == v1
    return all(abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b)) for a, b in zip(v0, v1))


def spread(o: dict, objective: str, idx: np.ndarray) -> tuple[float, float, float]:
    """Spanne der Nebenkennzahl über die Optimalmenge: (kleinster Wert, größter Wert, relative Spanne (max - min) / min)."""
    col = o[C.SECONDARY[objective]][idx].astype(float)
    lo, hi = float(col.min()), float(col.max())
    return lo, hi, (hi - lo) / lo if lo else 0.0


def lap_plan(cost: np.ndarray) -> np.ndarray:
    """Ungarische Methode (scipy.optimize.linear_sum_assignment) auf der Kostenmatrix."""
    rows, cols = linear_sum_assignment(cost)
    plan = np.empty(cost.shape[0], dtype=int)
    plan[rows] = cols
    return plan


def highs_plan(cost: np.ndarray) -> np.ndarray:
    """Zuordnung als ganzzahlige Optimierung (HiGHS über scipy.optimize.milp, Voreinstellungen)."""
    n = cost.shape[0]
    rows, cols = np.zeros((n, n * n)), np.zeros((n, n * n))
    for i in range(n):
        rows[i, i * n:(i + 1) * n] = 1
        cols[i, i::n] = 1
    res = milp(cost.ravel().astype(float), constraints=[LinearConstraint(np.vstack([rows, cols]), 1, 1)], integrality=np.ones(n * n), bounds=Bounds(0, 1))
    return np.round(res.x).reshape(n, n).argmax(axis=1)


def plan_sum(m: np.ndarray, plan) -> float:
    return m[np.arange(m.shape[0]), np.asarray(plan, dtype=int)].sum().item()

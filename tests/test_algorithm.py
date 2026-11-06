"""Handwerte: jede Einheit des Kerns an einem Beispiel, das von Hand nachgerechnet ist (DEMO-PLAYBOOK §1b)."""

import itertools

import numpy as np
import pytest

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev
from gst_scenario import make_instance, relabel_arrays

PLANS = list(itertools.permutations(range(3)))
# (Maximum, Summe, Quadratsumme, C-Summe) je Plan, von Hand
HAND = {(0, 1, 2): (4, 8, 26, 7), (0, 2, 1): (3, 6, 14, 9), (1, 0, 2): (3, 8, 22, 9), (1, 2, 0): (3, 6, 14, 8), (2, 0, 1): (3, 7, 17, 7), (2, 1, 0): (4, 7, 21, 4)}


def _o(hand_arrays):
    return A.objectives(hand_arrays, 3)


def _plan(idx):
    return tuple(int(x) for x in A.all_plans(3)[idx])


def test_hand_example_objectives_of_all_six_plans(hand_arrays):
    o = _o(hand_arrays)
    for k, plan in enumerate(PLANS):
        assert (int(o["max"][k]), int(o["sum"][k]), int(o["sq"][k]), int(o["sumC"][k])) == HAND[plan]


def test_hand_example_optimal_sets_and_chain(hand_arrays):
    o = _o(hand_arrays)
    assert [_plan(k) for k in A.opt_set(o["max"])] == [(0, 2, 1), (1, 0, 2), (1, 2, 0), (2, 0, 1)]
    sets = A.chain_sets(o, "max")
    assert [len(s) for s in sets] == [4, 2, 2, 1, 1]
    assert [_plan(k) for k in sets[1]] == [(0, 2, 1), (1, 2, 0)] and [_plan(k) for k in sets[3]] == [(1, 2, 0)]
    assert [len(A.opt_set(o["sum"]))] == [2] and [len(A.opt_set(o["sq"]))] == [2]


def test_hand_example_rules_pick_the_documented_plans(hand_arrays):
    o = _o(hand_arrays)
    got = {rule: _plan(A.pick(o, "max", rule)) for rule in ("first", "last", "secondary", "chain")}
    assert got == {"first": (0, 2, 1), "last": (2, 0, 1), "secondary": (0, 2, 1), "chain": (1, 2, 0)}
    assert A.values(o, A.pick(o, "max", "first"))[0] == 6 and A.values(o, A.pick(o, "max", "last"))[0] == 7
    assert A.pick(o, "max", "random", 5) in set(A.opt_set(o["max"])) and A.pick(o, "max", "random", 5) == A.pick(o, "max", "random", 5)
    with pytest.raises(ValueError):
        A.pick(o, "max", "unbekannt")


def test_hand_example_spread_of_the_sum_among_the_maximum_optimal_plans(hand_arrays):
    o = _o(hand_arrays)
    lo, hi, rel = A.spread(o, "max", A.opt_set(o["max"]))
    assert (lo, hi) == (6.0, 8.0) and rel == pytest.approx(1 / 3)
    c_vals = sorted(int(o["sumC"][k]) for k in A.opt_set(o["max"]))
    assert c_vals == [7, 8, 9, 9]


def test_hand_example_chain_order_moves_the_objective_to_the_front():
    assert A.chain_order("max") == ["max", "sum", "sq", "sumC", "sorted"]
    assert A.chain_order("sum") == ["sum", "max", "sq", "sumC", "sorted"]
    assert A.chain_order("sq") == ["sq", "max", "sum", "sumC", "sorted"]


def test_hand_example_leximax_and_summary(hand):
    a = ev.analyse(ev.Settings(3, 0, 0))
    a = ev.Analysis(hand, "enum", hand.arrays(), A.objectives(hand.arrays(), 3), 0)
    c = ev.chain_summary(a, "max")
    assert c["sizes"] == [4, 2, 2, 1, 1] and c["unique_at"] == 3 and c["residual"] == 1 and c["residual_equivalent"]
    t = ev.tie_summary(a, "max")
    assert t["size"] == 4 and t["total"] == 6 and t["secondary"] == "sum" and t["rel"] == pytest.approx(1 / 3)
    rows = {r["rule"]: r for r in ev.rule_rows(a, "max", 0)}
    assert rows["first"]["vals"][0] == 6 and rows["chain"]["vals"][3] == 8 and rows["last"]["vals"][3] == 7


def test_hand_example_labels_change_the_first_plan_but_never_the_chain_result(hand):
    """Alle sechs Zeilenpermutationen: die Kennzahlen des Kettenplans bleiben, die des „ersten Plans“ ändern sich für mindestens eine Nummerierung."""
    mats = hand.arrays()
    base_chain = A.values(A.objectives(mats, 3), A.pick(A.objectives(mats, 3), "max", "chain"))
    first_values = set()
    for r in itertools.permutations(range(3)):
        m2 = [m[list(r)] for m in mats]
        o2 = A.objectives(m2, 3)
        assert A.values(o2, A.pick(o2, "max", "chain")) == base_chain
        first_values.add(A.values(o2, A.pick(o2, "max", "first")))
    assert len(first_values) > 1


def test_relabeling_is_a_permutation_of_rows_and_columns():
    mats = make_instance(5, 1, 3).arrays()
    m2, r, c = relabel_arrays(mats, np.random.default_rng(4))
    assert sorted(r) == list(range(5)) and sorted(c) == list(range(5))
    assert all((m2[k] == mats[k][r][:, c]).all() for k in range(3))


def test_solver_rows_for_the_hand_example_choose_a_plan_in_the_sum_optimal_set(hand):
    rows = ev.solver_rows(hand, 0)
    o = A.objectives(hand.arrays(), 3)
    opt = {tuple(int(x) for x in A.all_plans(3)[k]) for k in A.opt_set(o["sum"])}
    assert [r["method"] for r in rows][:3] == ["Aufzählung (erster Plan)", "Ungarische Methode", "HiGHS"] and len(rows) == 5
    for r in rows:
        assert tuple(int(x) for x in r["plan"]) in opt and r["sum_a"] == 6 and A.check_feasible(r["plan"], 3)


def test_check_feasible_and_enumeration_limits():
    assert A.check_feasible((2, 0, 1), 3) and not A.check_feasible((0, 0, 1), 3) and not A.check_feasible((0, 1), 3)
    with pytest.raises(ValueError):
        A.all_plans(10)
    assert len(A.all_plans(5)) == 120 and C.GRANULARITIES.index(9) == 1


def test_same_values_is_exact_for_integers_and_tolerant_for_floats():
    assert A.same_values((1, 2), (1, 2), True) and not A.same_values((1, 2), (1, 3), True)
    assert A.same_values((0.1 + 0.2, 5.0), (0.3, 5.0), False) and not A.same_values((0.1, 5.0), (0.2, 5.0), False)

"""Randfälle: kleinste und größte Instanz, vollständiger Gleichstand, Nullspanne, nicht aufgezählte Größen, Determinismus der Erzeugung."""

import numpy as np
import pytest

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev
from gst_scenario import Instance, make_instance


def _flat(n: int, value: int = 2) -> Instance:
    m = tuple(tuple(value for _ in range(n)) for _ in range(n))
    return Instance((m, m, m), True)


def test_constant_matrix_makes_every_plan_optimal_and_the_chain_never_unique():
    inst = _flat(4)
    a = ev.Analysis(inst, "enum", inst.arrays(), A.objectives(inst.arrays(), 4), 0)
    assert all(len(A.opt_set(a.o[k])) == 24 for k in C.OBJECTIVES)
    c = ev.chain_summary(a, "max")
    assert c["sizes"] == [24] * 5 and c["unique_at"] is None and c["residual"] == 24 and c["residual_equivalent"]
    kind, text = ev.verdict_chain(c)
    assert kind == "warning" and "bleiben 24 Pläne" in text and "folgenlos" in text
    assert ev.verdict_rules(ev.rule_rows(a, "max", 0)) == ("info", "Alle Regeln wählen Pläne mit denselben Kennzahlen: hier ist die Regel folgenlos.")
    lo, hi, rel = A.spread(a.o, "max", A.opt_set(a.o["max"]))
    assert (lo, hi, rel) == (8.0, 8.0, 0.0)
    assert ev.verdict_spread(ev.tie_summary(a, "max"))[0] == "info"


def test_spread_with_zero_minimum_does_not_divide_by_zero():
    m = ((0, 0), (0, 0))
    inst = Instance((m, m, m), True)
    o = A.objectives(inst.arrays(), 2)
    assert A.spread(o, "max", A.opt_set(o["max"])) == (0.0, 0.0, 0.0)


def test_smallest_instance_n_equals_three_has_six_plans_and_runs_every_experiment():
    for family in range(len(C.FAMILIES)):
        a = ev.analyse(ev.Settings(3, family, 0))
        assert a.mode == "enum" and len(a.o["sum"]) == 6
        for obj in C.OBJECTIVES:
            ev.verdict_ties(ev.tie_summary(a, obj)), ev.verdict_spread(ev.tie_summary(a, obj))
            ev.verdict_rules(ev.rule_rows(a, obj, 1)), ev.verdict_chain(ev.chain_summary(a, obj)), ev.verdict_relabel(ev.relabel_check(a, obj, 2, 1))
        ev.verdict_solvers(ev.solver_rows(a.inst, 0))


def test_n_above_the_enumeration_limit_is_not_enumerated_but_still_compares_solvers():
    for n in (C.ENUM_MAX + 1, C.N_MAX):
        a = ev.analyse(ev.Settings(n, 1, 2))
        assert a.mode == "large" and a.o is None
        rows = ev.solver_rows(a.inst, 2)
        assert [r["method"] for r in rows][0] == "Ungarische Methode" and len(rows) == 4
        assert all(A.check_feasible(r["plan"], n) for r in rows) and len({r["sum_a"] for r in rows}) == 1


def test_enumeration_refuses_ten_persons():
    with pytest.raises(ValueError):
        A.all_plans(10)
    with pytest.raises(ValueError):
        A.all_plans(0)


def test_ordinary_instances_are_deterministic_and_seed_sensitive():
    for family in range(len(C.FAMILIES)):
        assert make_instance(6, family, 4) == make_instance(6, family, 4)
        assert make_instance(6, family, 4) != make_instance(6, family, 5)
    inst = make_instance(5, 4, 3)
    assert not inst.exact and inst.arrays()[0].dtype == float
    assert make_instance(5, 1, 3).arrays()[0].dtype == np.int64


def test_value_ranges_follow_the_granularity():
    for family, k in enumerate(C.GRANULARITIES):
        m = make_instance(8, family, 1).arrays()
        for x in m:
            if k:
                assert x.min() >= 1 and x.max() <= k
            else:
                assert x.min() >= 0 and x.max() <= 100


def test_text_helpers_format_numbers_with_a_decimal_comma():
    assert ev.de(3.14159, 2) == "3,14" and ev.de(-0.0001) == "0,0" and ev.pct(0.5909, 1) == "59,1 %"
    assert ev.value_text(5.0) == "5" and ev.value_text(5.3) == "5,3"
    assert ev.plan_text((2, 0, 1), 3) == "P1→A3, P2→A1, P3→A2" and ev.plan_text(range(13), 13) == "siehe Rechnung"


def test_pick_with_unknown_rule_raises_and_random_stays_in_the_optimal_set():
    a = ev.analyse(ev.Settings(5, 0, 1))
    with pytest.raises(ValueError):
        A.pick(a.o, "max", "wuerfeln")
    opt = set(A.opt_set(a.o["max"]))
    assert {A.pick(a.o, "max", "random", s) for s in range(30)} <= opt

"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für jede Instanz gelten müssen, an festen Seeds und allen Granularitäten."""

import numpy as np
import pytest

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev
from gst_scenario import make_instance, relabel_arrays

CASES = [(n, family, seed) for n in (3, 5, 7, 8) for family in range(5) for seed in range(3)]


def _analysis(n, family, seed):
    return ev.analyse(ev.Settings(n, family, seed))


@pytest.mark.parametrize("n,family,seed", CASES)
def test_optimal_sets_are_never_empty_and_hold_exactly_the_minimum(n, family, seed):
    a = _analysis(n, family, seed)
    for obj in C.OBJECTIVES:
        idx = A.opt_set(a.o[obj])
        assert len(idx) >= 1 and (a.o[obj][idx] == a.o[obj].min()).all() and (a.o[obj][np.setdiff1d(np.arange(len(a.o[obj])), idx)] > a.o[obj].min()).all()


@pytest.mark.parametrize("n,family,seed", CASES)
def test_each_chain_level_is_a_subset_of_the_previous_and_minimal(n, family, seed):
    a = _analysis(n, family, seed)
    for obj in C.OBJECTIVES:
        sets = A.chain_sets(a.o, obj)
        keys = A.chain_order(obj)
        assert all(len(s) >= 1 for s in sets) and all(set(sets[i + 1]) <= set(sets[i]) for i in range(len(sets) - 1))
        for key, s, prev in zip(keys[1:], sets[1:], sets):
            if key != "sorted":
                assert (a.o[key][s] == a.o[key][prev].min()).all()
        assert [len(s) for s in sets] == sorted((len(s) for s in sets), reverse=True)


@pytest.mark.parametrize("n,family,seed", CASES)
def test_first_and_last_agree_exactly_when_the_optimal_set_has_one_plan(n, family, seed):
    a = _analysis(n, family, seed)
    for obj in C.OBJECTIVES:
        size = len(A.opt_set(a.o[obj]))
        assert (A.pick(a.o, obj, "first") == A.pick(a.o, obj, "last")) == (size == 1)
        assert A.pick(a.o, obj, "first") == A.pick(a.o, obj, "chain") or size > 1


@pytest.mark.parametrize("n,family,seed", CASES)
def test_every_rule_picks_a_plan_of_the_optimal_set_and_the_secondary_rule_minimizes_the_secondary(n, family, seed):
    a = _analysis(n, family, seed)
    for obj in C.OBJECTIVES:
        opt = set(A.opt_set(a.o[obj]))
        picks = {rule: A.pick(a.o, obj, rule, 7) for rule in C.RULES}
        assert all(p in opt for p in picks.values())
        sec = C.SECONDARY[obj]
        assert a.o[sec][picks["secondary"]] == min(a.o[sec][k] for k in opt)
        assert A.pick(a.o, obj, "random", 7) == A.pick(a.o, obj, "random", 7)


@pytest.mark.parametrize("n,family,seed", [(5, 0, 1), (6, 1, 2), (7, 2, 3), (8, 4, 4), (8, 1, 5)])
def test_relabeling_keeps_the_sizes_of_every_optimal_set_and_the_multiset_of_plan_kennzahlen(n, family, seed):
    a = _analysis(n, family, seed)
    mats2, _, _ = relabel_arrays(a.mats, np.random.default_rng(seed + 100))
    o2 = A.objectives(mats2, n)
    for obj in C.OBJECTIVES:
        assert len(A.opt_set(a.o[obj])) == len(A.opt_set(o2[obj]))
        assert [len(s) for s in A.chain_sets(a.o, obj)] == [len(s) for s in A.chain_sets(o2, obj)]
    for key in ("sum", "sq", "max", "sumB", "sumC"):
        assert np.allclose(np.sort(a.o[key].astype(float)), np.sort(o2[key].astype(float)))


@pytest.mark.parametrize("n,family,seed", [(5, 1, 1), (6, 1, 2), (7, 0, 3), (8, 1, 4), (8, 2, 5)])
def test_the_full_chain_is_label_invariant_whenever_its_end_is_unique_in_all_kennzahlen(n, family, seed):
    a = _analysis(n, family, seed)
    c = ev.chain_summary(a, "max")
    if not c["residual_equivalent"]:
        pytest.skip("die Kette endet mit verschiedenen Kennzahlen: dann darf die Nummerierung entscheiden")
    base = A.values(a.o, A.pick(a.o, "max", "chain"))
    for k in range(6):
        mats2, _, _ = relabel_arrays(a.mats, np.random.default_rng(seed * 10 + k))
        o2 = A.objectives(mats2, n)
        assert A.values(o2, A.pick(o2, "max", "chain")) == base


@pytest.mark.parametrize("n,family,seed", CASES)
def test_the_spread_is_never_negative_and_zero_exactly_when_the_secondary_is_constant(n, family, seed):
    a = _analysis(n, family, seed)
    for obj in C.OBJECTIVES:
        idx = A.opt_set(a.o[obj])
        lo, hi, rel = A.spread(a.o, obj, idx)
        assert rel >= 0 and hi >= lo and (rel == 0) == (hi == lo)


def test_everything_is_deterministic():
    s = ev.Settings(8, 1, 11)
    a1, a2 = ev.analyse(s), ev.analyse(s)
    assert (a1.o["max"] == a2.o["max"]).all() and ev.chain_summary(a1, "max")["sizes"] == ev.chain_summary(a2, "max")["sizes"]
    assert make_instance(5, 1, 3) == make_instance(5, 1, 3) and make_instance(5, 1, 3) != make_instance(5, 1, 4)
    assert [r["vals"] for r in ev.rule_rows(a1, "max", 3)] == [r["vals"] for r in ev.rule_rows(a2, "max", 3)]

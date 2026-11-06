"""Orakel-Test gleichstand-demo: der Kern gegen einen ANDEREN Rechenweg (ORACLE-PLAYBOOK §2, DEMO-PLAYBOOK §12).

Reines Python (itertools, Tupelvergleich, keine numpy-Zeile im Referenzweg) gegen die int64-Aufzählung, die Regeln, die Kette und die Löser.
Mini-Instanzen n = 3 bis 6, feste Seeds, alle Granularitäten."""

import itertools

import pytest

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev
from gst_scenario import make_instance

scipy_opt = pytest.importorskip("scipy.optimize")


def _all(inst):
    """Alle Pläne mit ihren Kennzahlen (Maximum, Summe, Quadratsumme, C-Summe, absteigend sortierter Vektor) in reinem Python."""
    n = inst.n
    out = []
    for plan in itertools.permutations(range(n)):
        b = [inst.mats[0][i][plan[i]] for i in range(n)]
        out.append((plan, {"max": max(b), "sum": sum(b), "sq": sum(x * x for x in b), "sumC": sum(inst.mats[2][i][plan[i]] for i in range(n)), "sorted": tuple(sorted(b, reverse=True)),
                           "sumB": sum(inst.mats[1][i][plan[i]] for i in range(n))}))
    return out


def _cases(sizes=(3, 4, 5, 6), families=(0, 1, 2, 3), seeds=range(5)):
    for n in sizes:
        for family in families:
            for seed in seeds:
                yield n, family, seed


def _ref_chain(plans, objective):
    keys = [objective] + [k for k in C.CHAIN_KEYS if k != objective]
    cur = plans
    out = []
    for key in keys:
        best = min(v[key] for _, v in cur)
        cur = [(p, v) for p, v in cur if v[key] == best]
        out.append(cur)
    return out


def test_optimal_sets_match_the_definition():
    for n, family, seed in _cases():
        inst = make_instance(n, family, seed)
        plans = _all(inst)
        a = ev.analyse(ev.Settings(n, family, seed))
        for obj in C.OBJECTIVES:
            best = min(v[obj] for _, v in plans)
            expected = sorted(p for p, v in plans if v[obj] == best)
            got = sorted(tuple(int(x) for x in A.all_plans(n)[k]) for k in A.opt_set(a.o[obj]))
            assert got == expected, (n, family, seed, obj)


def test_the_chain_matches_repeated_filtering_in_pure_python():
    for n, family, seed in _cases(sizes=(3, 4, 5)):
        inst = make_instance(n, family, seed)
        plans = _all(inst)
        a = ev.analyse(ev.Settings(n, family, seed))
        for obj in C.OBJECTIVES:
            ref = _ref_chain(plans, obj)
            got = A.chain_sets(a.o, obj)
            assert [len(s) for s in got] == [len(r) for r in ref], (n, family, seed, obj)
            assert sorted(tuple(int(x) for x in A.all_plans(n)[k]) for k in got[-1]) == sorted(p for p, _ in ref[-1])


def test_every_rule_picks_what_its_definition_says():
    for n, family, seed in _cases(sizes=(3, 4, 5), seeds=range(4)):
        inst = make_instance(n, family, seed)
        plans = _all(inst)                                                              # in der Reihenfolge von itertools.permutations
        a = ev.analyse(ev.Settings(n, family, seed))
        for obj in C.OBJECTIVES:
            best = min(v[obj] for _, v in plans)
            opt = [(p, v) for p, v in plans if v[obj] == best]
            sec = C.SECONDARY[obj]
            sec_best = min(v[sec] for _, v in opt)
            expected = {"first": opt[0][0], "last": opt[-1][0], "secondary": next(p for p, v in opt if v[sec] == sec_best), "chain": _ref_chain(plans, obj)[-1][0][0]}
            for rule, plan in expected.items():
                assert tuple(int(x) for x in A.all_plans(n)[A.pick(a.o, obj, rule)]) == plan, (n, family, seed, obj, rule)


def test_spread_matches_pure_python():
    for n, family, seed in _cases(sizes=(4, 5), seeds=range(4)):
        inst = make_instance(n, family, seed)
        plans = _all(inst)
        a = ev.analyse(ev.Settings(n, family, seed))
        for obj in C.OBJECTIVES:
            best = min(v[obj] for _, v in plans)
            vals = [v[C.SECONDARY[obj]] for _, v in plans if v[obj] == best]
            lo, hi, rel = A.spread(a.o, obj, A.opt_set(a.o[obj]))
            assert (lo, hi) == (min(vals), max(vals)) and rel == pytest.approx((max(vals) - min(vals)) / min(vals))


def test_relabeling_with_explicit_index_maps_gives_the_same_kennzahlen_for_the_corresponding_plan():
    """Zweite Implementierung der Umnummerierung in reinem Python: der Plan p der Instanz gehört zum Plan q der umnummerierten Instanz, Kennzahlen gleich."""
    import numpy as np
    for n, family, seed in _cases(sizes=(4, 5), families=(0, 1), seeds=range(3)):
        inst = make_instance(n, family, seed)
        rng = np.random.default_rng(seed + 31)
        r, c = [int(x) for x in rng.permutation(n)], [int(x) for x in rng.permutation(n)]
        mats2 = tuple(tuple(tuple(m[r[i]][c[j]] for j in range(n)) for i in range(n)) for m in inst.mats)
        from gst_scenario import Instance
        inst2 = Instance(mats2, True)
        ref, ref2 = dict(_all(inst)), dict(_all(inst2))
        # neuer Plan q (Person i -> Aufgabe q[i]) entspricht dem alten Plan p mit p[r[i]] = c[q[i]]
        for q, v2 in ref2.items():
            p = [0] * n
            for i in range(n):
                p[r[i]] = c[q[i]]
            v1 = ref[tuple(p)]
            assert (v1["max"], v1["sum"], v1["sumB"], v1["sumC"]) == (v2["max"], v2["sum"], v2["sumB"], v2["sumC"])


def test_solver_choices_are_optimal_and_in_the_optimal_set_of_the_sum():
    for n, family, seed in _cases(sizes=(4, 5, 6), families=(0, 1), seeds=range(4)):
        inst = make_instance(n, family, seed)
        plans = _all(inst)
        best = min(v["sum"] for _, v in plans)
        opt = {p for p, v in plans if v["sum"] == best}
        for row in ev.solver_rows(inst, seed):
            assert tuple(int(x) for x in row["plan"]) in opt and row["sum_a"] == best, (n, family, seed, row["method"])
        cost = inst.arrays()[0].astype(float)
        rows, cols = scipy_opt.linear_sum_assignment(cost)
        assert cost[rows, cols].sum() == best


def test_the_row_permuted_solver_runs_map_back_to_the_original_numbering():
    """Der zurückgemappte Plan der vertauschten Zeilen ist ein zulässiger Plan der ursprünglichen Instanz und optimal."""
    for n in (6, 9, 12):
        inst = make_instance(n, 1, 3)
        base = {r["method"]: r for r in ev.solver_rows(inst, 3)}
        for name in ("Ungarische Methode, Zeilen vertauscht", "HiGHS, Zeilen vertauscht"):
            r = base[name]
            assert A.check_feasible(r["plan"], n) and r["sum_a"] == base["Ungarische Methode"]["sum_a"]

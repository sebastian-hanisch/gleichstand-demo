"""Jede Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4). Aufzählung, Ungarische Methode und feste Instanzerzeugung sind deterministisch;
die HiGHS-Zeilen sind Messwerte der benutzten Version (Voreinstellungen)."""

from pathlib import Path

import pytest

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")
(MANY, SMALL, REAL_SUM, REAL_MAX, UNCLEAR, RELABEL, SOLVERS, BIG) = list(C.PRESETS)


def _claim(text):
    assert text in README, text


def _slash(values, digits=0):
    return " / ".join(ev.de(v, digits) for v in values)


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


@pytest.fixture(scope="module")
def ties():
    return ev.ties_sweep()


@pytest.fixture(scope="module")
def spread():
    return ev.spread_sweep()


@pytest.fixture(scope="module")
def chain():
    return ev.chain_sweep()


@pytest.fixture(scope="module")
def relabel():
    return ev.relabel_sweep()


@pytest.fixture(scope="module")
def solvers():
    return ev.solver_sweep()


def test_sweep_instances_are_the_documented_ones():
    assert C.SWEEP_SEEDS == tuple(range(100000, 100020)) and C.SWEEP_N == 8 and C.GRANULARITIES == (3, 9, 99, 999, 0) and C.RELABEL_COUNT == 8
    _claim("Seeds 100000 bis 100019")
    _claim("je acht Umnummerierungen")


def test_tie_counts(ties):
    assert [ties[("sum", k)]["ties"] for k in C.SWEEP_KS] == [19, 13, 2, 0, 0] and [ties[("sq", k)]["ties"] for k in C.SWEEP_KS] == [19, 7, 0, 0, 0]
    assert [ties[("max", k)]["ties"] for k in C.SWEEP_KS] == [20, 19, 16, 15, 17]
    assert _slash([ties[("sum", k)]["median"] for k in C.SWEEP_KS], 1) == "10,0 / 2,5 / 1,0 / 1,0 / 1,0"
    assert [ties[("max", k)]["median"] for k in C.SWEEP_KS] == [26, 13, 2, 2, 4] and [ties[("max", k)]["max"] for k in C.SWEEP_KS] == [3640, 69, 61, 28, 45]
    for text in ("**19 / 13 / 2 / 0 / 0** von 20", "**10,0 / 2,5 / 1,0 / 1,0 / 1,0**", "**19 / 7 / 0 / 0 / 0** von 20", "**20 / 19 / 16 / 15 / 17** von 20",
                 "**26 / 13 / 2 / 2 / 4** (Maximum **3640 / 69 / 61 / 28 / 45**)", "auch bei reellen Werten"):
        _claim(text)


def test_spread_claims(spread):
    k9, k99, k3 = spread[("max", 9)], spread[("max", 99)], spread[("max", 3)]
    assert (k9["ties"], k9["positive"], ev.pct(k9["median"]), ev.pct(k9["max"])) == (19, 19, "38,5 %", "57,1 %")
    assert (k99["ties"], k99["positive"], ev.pct(k99["median"]), ev.pct(k99["max"])) == (16, 16, "19,7 %", "80,7 %")
    assert (k3["ties"], k3["positive"], ev.pct(k3["max"])) == (20, 9, "77,8 %")
    for text in ("K = 9: Spanne über null in **19** von 19, Median **38,5 %**, Maximum **57,1 %**", "K = 99: **16** von 16, Median **19,7 %**, Maximum **80,7 %**",
                 "K = 3 nur in **9** von 20 (Maximum **77,8 %**)"):
        _claim(text)


def test_chain_claims(chain):
    assert [chain[k]["unique"] for k in (3, 9, 99, 999)] == [[0, 1, 1, 12, 12], [1, 10, 13, 20, 20], [4, 18, 20, 20, 20], [5, 20, 20, 20, 20]]
    assert [ev.de(chain[k]["mean"][0]) for k in (3, 9, 99, 999)] == ["533,5", "17,9", "8,1", "5,7"]
    for text in ("K = 3: **0 / 1 / 1 / 12 / 12**", "K = 9: **1 / 10 / 13 / 20 / 20**", "K = 99: **4 / 18 / 20 / 20 / 20**", "K = 999: **5 / 20 / 20 / 20 / 20**",
                 "mittlere Optimalmenge nach dem Maximum **533,5 / 17,9 / 8,1 / 5,7**", "nur in **10** von 20 Instanzen eindeutig, und erst mit der C-Summe in der Kette in allen **20** (der Leximax ändert hier nichts)"):
        _claim(text)


def test_relabel_claims(relabel):
    cases = {c: [relabel[k][c] for k in (3, 9, 99)] for c in ev.RELABEL_CASES}
    assert cases[("sum", "first")] == [19, 13, 2] and cases[("max", "first")] == [20, 19, 16] and cases[("max", "secondary")] == [19, 10, 2] and cases[("max", "chain")] == [7, 0, 0]
    for text in ("Summe, erster Plan: **19 / 13 / 2**", "Maximum, erster Plan: **20 / 19 / 16**", "Maximum, kleinste Nebenkennzahl: **19 / 10 / 2**", "Maximum, volle Kette: **7 / 0 / 0**"):
        _claim(text)


def test_solver_claims(solvers):
    g = lambda name, case: solvers[name][case]
    k9 = [g(n, (8, 9)) for n in ev.SOLVER_COMPARISONS]
    assert [x["plans"] for x in k9] == [7, 7, 8, 7, 7] and [x["sum_b"] for x in k9] == [7, 7, 8, 7, 7]
    assert [g("Ungarisch|HiGHS", (n, 9))["plans"] for n in (10, 12)] == [9, 11]
    assert [g("Ungarisch|Ungarisch, Zeilen vertauscht", (n, 9))["plans"] for n in (10, 12)] == [7, 13]
    assert [g("HiGHS|HiGHS, Zeilen vertauscht", (n, 9))["plans"] for n in (10, 12)] == [7, 9]
    assert (g("Ungarisch|HiGHS", (8, 3))["plans"], g("Ungarisch|HiGHS", (8, 99))["plans"]) == (17, 1)
    assert (g("Ungarisch|Ungarisch, Zeilen vertauscht", (8, 3))["plans"], g("Ungarisch|Ungarisch, Zeilen vertauscht", (8, 99))["plans"]) == (16, 0)
    for text in ("Aufzählung gegen Ungarisch **7**, Aufzählung gegen HiGHS **7**, Ungarisch gegen HiGHS **8**, Ungarisch mit vertauschten Zeilen **7**, HiGHS mit vertauschten Zeilen **7**",
                 "Ungarisch gegen HiGHS **9 / 11**, Ungarisch mit vertauschten Zeilen **7 / 13**, HiGHS mit vertauschten Zeilen **7 / 9**",
                 "Ungarisch gegen HiGHS **17** und **1**; Ungarisch mit vertauschten Zeilen **16** und **0**"):
        _claim(text)


def test_preset_claims():
    a = _a(MANY)
    t, c = ev.tie_summary(a, "max"), ev.chain_summary(a, "max")
    rules = ev.rule_rows(a, "max", 0)
    assert (t["size"], t["total"], t["lo"], t["hi"], ev.pct(t["rel"])) == (37, 40320, 22.0, 35.0, "59,1 %") and c["sizes"] == [37, 1, 1, 1, 1]
    assert len({r["vals"] for r in rules}) == 4 and {r["rule"]: r["vals"][0] for r in rules}["first"] == 30 and {r["rule"]: r["vals"][0] for r in rules}["chain"] == 22
    assert sum(r["changed"] for r in ev.relabel_check(a, "max", 1, 0)["rows"] if r["rule"] != "random") == 2
    _claim("**37** Pläne von 40 320, die Summe reicht von **22** bis **35** (**59,1 %**); Kette **37 / 1 / 1 / 1 / 1**; die fünf Regeln liefern **4** Kennzahlensätze: der erste Plan hat Summe A **30**, die volle Kette **22**; **2** von 4 festen Regeln ändern sich beim Umnummerieren")

    b = _a(SMALL)
    t, c = ev.tie_summary(b, "max"), ev.chain_summary(b, "max")
    assert (t["size"], t["total"], t["lo"], t["hi"], ev.pct(t["rel"]), c["sizes"], c["unique_at"]) == (3, 6, 4.0, 5.0, "25,0 %", [3, 2, 2, 1, 1], 3)
    _claim("**3** gleich gute Pläne von 6, Summe **4** bis **5** (**25,0 %**), Kette **3 / 2 / 2 / 1 / 1**, eindeutig erst nach der C-Summe")

    r = _a(REAL_SUM)
    t = ev.tie_summary(r, "max")
    assert ev.tie_summary(r, "sum")["size"] == 1 and (t["size"], ev.de(t["lo"]), ev.de(t["hi"]), ev.pct(t["rel"])) == (2, "89,3", "101,0", "13,1 %")
    assert len({tuple(int(x) for x in row["plan"]) for row in ev.solver_rows(r.inst, 5)}) == 1
    _claim("Summe: **ein** bester Plan; Maximum: **2**, Summe **89,3** bis **101,0** (**13,1 %**); alle Löser wählen denselben Plan")

    m = _a(REAL_MAX)
    t = ev.tie_summary(m, "max")
    assert (t["size"], ev.de(t["lo"]), ev.de(t["hi"]), ev.pct(t["rel"])) == (7, "179,2", "231,6", "29,2 %")
    _claim("**7** Pläne, Summe **179,2** bis **231,6** (**29,2 %**)")

    u = _a(UNCLEAR)
    cu = ev.chain_summary(u, "max")
    sums_b = sorted({row["sum_b"] for row in ev.solver_rows(u.inst, 3)})
    assert cu["sizes"] == [18, 18, 18, 3, 3] and not cu["residual_equivalent"] and ev.tie_summary(u, "sum")["size"] == 18 and sums_b == [14, 15, 16]
    assert len({tuple(int(x) for x in row["plan"]) for row in ev.solver_rows(u.inst, 3)}) == 4
    _claim("Kette **18 / 18 / 18 / 3 / 3**: es bleiben **3** Pläne mit verschiedenen Kennzahlen; bei der Summe als Ziel **18** Pläne, die Löser wählen **4** verschiedene mit Summe B **14**, **15**, **16**")

    rl = _a(RELABEL)
    rc = ev.relabel_check(rl, "max", 1, 0)
    assert ev.chain_summary(rl, "max")["sizes"] == [11, 3, 3, 1, 1] and sum(row["changed"] for row in rc["rows"] if row["rule"] != "random") == 3
    assert not next(row for row in rc["rows"] if row["rule"] == "chain")["changed"]
    _claim("Kette **11 / 3 / 3 / 1 / 1**; **3** von 4 festen Regeln ändern sich, die volle Kette nicht")

    s = _a(SOLVERS)
    rows = {row["method"]: row for row in ev.solver_rows(s.inst, 2)}
    assert {row["sum_a"] for row in rows.values()} == {17} and len({tuple(int(x) for x in row["plan"]) for row in rows.values()}) == 4
    assert (rows["Aufzählung (erster Plan)"]["sum_b"], rows["Ungarische Methode"]["sum_b"], rows["HiGHS"]["sum_b"]) == (41, 42, 31)
    _claim("Summe A **17**, vier verschiedene Pläne mit Summe B **41** (Aufzählung), **42** (Ungarisch), **31** (HiGHS) und einem vierten bei vertauschten Zeilen")

    g = _a(BIG)
    rows = {row["method"]: row for row in ev.solver_rows(g.inst, 2)}
    assert {row["sum_a"] for row in rows.values()} == {23} and len({tuple(int(x) for x in row["plan"]) for row in rows.values()}) == 3
    assert (rows["HiGHS"]["sum_b"], rows["Ungarische Methode"]["sum_b"], rows["HiGHS, Zeilen vertauscht"]["sum_b"]) == (47, 57, 64) and A.check_feasible(rows["HiGHS"]["plan"], 12)
    _claim("Summe A **23**, drei Pläne mit Summe B **47** (HiGHS), **57** (Ungarisch) und **64** (HiGHS, Zeilen vertauscht)")

"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und was jedes Preset zeigen soll."""

import gst_algorithm as A
import gst_constants as C
import gst_evaluation as ev
import gst_presets as P

(MANY, SMALL, REAL_SUM, REAL_MAX, UNCLEAR, RELABEL, SOLVERS, BIG) = list(C.PRESETS)


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["family"] < len(C.FAMILIES) and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS[MANY]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_no_non_default_preset_uses_the_default_seed_with_default_other_settings():
    """Lehre aus Stück 4: ein Preset, das den Voreinstellungen gleicht, wäre nicht von „nichts geklickt“ zu unterscheiden."""
    for name, preset in C.PRESETS.items():
        if name != MANY:
            assert ev.Settings(**preset) != ev.Settings(), name


def _a(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_many_preset_has_thirty_seven_best_plans_and_a_spread_of_fifty_nine_percent():
    a = _a(MANY)
    t = ev.tie_summary(a, "max")
    assert t["size"] == 37 and t["total"] == 40320 and (t["lo"], t["hi"]) == (22.0, 35.0) and ev.pct(t["rel"]) == "59,1 %"
    assert ev.chain_summary(a, "max")["sizes"] == [37, 1, 1, 1, 1]


def test_small_preset_has_the_three_two_one_chain():
    a = _a(SMALL)
    assert a.inst.n == 3 and ev.chain_summary(a, "max")["sizes"] == [3, 2, 2, 1, 1] and ev.chain_summary(a, "max")["unique_at"] == 3


def test_real_sum_preset_has_a_unique_sum_optimum_but_a_maximum_tie():
    a = _a(REAL_SUM)
    assert not a.inst.exact and ev.tie_summary(a, "sum")["size"] == 1 and ev.tie_summary(a, "sq")["size"] == 1 and ev.tie_summary(a, "max")["size"] == 2


def test_real_max_preset_has_seven_maximum_optimal_plans():
    a = _a(REAL_MAX)
    assert ev.tie_summary(a, "max")["size"] == 7 and ev.tie_summary(a, "sum")["size"] == 1


def test_unclear_preset_leaves_three_plans_with_different_kennzahlen():
    c = ev.chain_summary(_a(UNCLEAR), "max")
    assert c["sizes"] == [18, 18, 18, 3, 3] and c["unique_at"] is None and not c["residual_equivalent"]


def test_relabel_preset_changes_first_but_not_the_chain():
    a = _a(RELABEL)
    rc = {r["rule"]: r["changed"] for r in ev.relabel_check(a, "max", 1, 0)["rows"]}
    assert rc["first"] and rc["last"] and rc["secondary"] and not rc["chain"]


def test_solver_preset_shows_four_different_plans_and_the_documented_sums_of_b():
    a = _a(SOLVERS)
    rows = {r["method"]: r for r in ev.solver_rows(a.inst, 2)}
    assert [rows[m]["sum_b"] for m in ("Aufzählung (erster Plan)", "Ungarische Methode", "HiGHS")] == [41, 42, 31]
    assert {r["sum_a"] for r in rows.values()} == {17} and len({tuple(int(x) for x in r["plan"]) for r in rows.values()}) == 4


def test_big_preset_is_not_enumerated_and_three_methods_choose_three_plans():
    a = _a(BIG)
    rows = {r["method"]: r for r in ev.solver_rows(a.inst, 2)}
    assert a.mode == "large" and rows["Ungarische Methode"]["sum_b"] == 57 and rows["HiGHS"]["sum_b"] == 47 and rows["HiGHS, Zeilen vertauscht"]["sum_b"] == 64
    assert {r["sum_a"] for r in rows.values()} == {23}
    assert A.check_feasible(rows["HiGHS"]["plan"], 12)

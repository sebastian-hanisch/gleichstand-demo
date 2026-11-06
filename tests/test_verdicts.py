"""Verdikte: Art und Wortlaut in den Fällen, die sie unterscheiden (DEMO-PLAYBOOK §6): jede Zahl im Text kommt aus der Rechnung."""

import gst_constants as C
import gst_evaluation as ev


def _a(n, family, seed):
    return ev.analyse(ev.Settings(n, family, seed))


def test_ties_verdict_distinguishes_one_best_plan_from_many_and_uses_the_right_article():
    a = _a(8, 4, 5)
    kind, text = ev.verdict_ties(ev.tie_summary(a, "sum"))
    assert kind == "info" and text.startswith("Die Summe hat hier **genau einen** besten Plan")
    kind, text = ev.verdict_ties(ev.tie_summary(a, "max"))
    assert kind == "warning" and text.startswith("Das Maximum hat **2** gleich gute Pläne (von 40320)") and "nur ein einziger Eintrag" in text
    kind, text = ev.verdict_ties(ev.tie_summary(_a(8, 0, 3), "sum"))
    assert kind == "warning" and text.startswith("Die Summe hat **18** gleich gute Pläne") and "nur ein einziger Eintrag" not in text


def test_spread_verdict_has_three_cases():
    assert ev.verdict_spread(ev.tie_summary(_a(8, 4, 5), "sum")) == ("info", "Ohne Gleichstand gibt es keine Streuung.")
    kind, text = ev.verdict_spread(ev.tie_summary(_a(8, 0, 3), "max"))
    assert kind == "info" and "Alle 18 gleich guten Pläne haben dieselbe Summe (8)" in text
    kind, text = ev.verdict_spread(ev.tie_summary(_a(8, 1, 0), "max"))
    assert kind == "warning" and "reicht die Summe von **22 bis 35** (Spanne 59,1 %)" in text


def test_rules_verdict_names_the_chain_and_the_first_plan():
    kind, text = ev.verdict_rules(ev.rule_rows(_a(8, 1, 0), "max", 0))
    assert kind == "warning" and "**4 verschiedene** Kennzahlensätze" in text
    assert "Die volle Kette wählt Summe A 22, Maximum A 5, Summe B 45, Summe C 47" in text and "der erste Plan wählt Summe A 30, Maximum A 5, Summe B 52, Summe C 55" in text


def test_chain_verdict_cases():
    kind, text = ev.verdict_chain(ev.chain_summary(_a(8, 1, 0), "max"))
    assert kind == "info" and "Maximum 37, Summe 1" in text and "erst nach „Summe“" in text and "Ebene 2 von 5" in text
    kind, text = ev.verdict_chain(ev.chain_summary(_a(3, 0, 22), "max"))
    assert kind == "warning" and "Maximum 3, Summe 2, Quadratsumme 2, C-Summe 1, Leximax 1" in text and "erst nach „C-Summe“" in text
    kind, text = ev.verdict_chain(ev.chain_summary(_a(8, 0, 3), "max"))
    assert kind == "warning" and "Auch nach der letzten Ebene bleiben 3 Pläne" in text and "unterscheiden sich in mindestens einer Kennzahl" in text
    kind, text = ev.verdict_chain(ev.chain_summary(_a(8, 4, 5), "sum"))
    assert kind == "info" and "Schon das Ziel allein ist eindeutig" in text


def test_relabel_verdict_lists_changed_and_unchanged_rules():
    kind, text = ev.verdict_relabel(ev.relabel_check(_a(8, 1, 10), "max", 1, 0))
    assert kind == "warning" and "**3 von 4 festen Regeln ändern die Kennzahlen**" in text and "Unverändert bleiben: volle Kette, dann erster." in text
    kind, text = ev.verdict_relabel(ev.relabel_check(_a(8, 4, 2), "max", 1, 0))
    assert kind == "warning" and "**1 von 4 festen Regeln ändert die Kennzahlen**" in text
    kind, text = ev.verdict_relabel(ev.relabel_check(_a(8, 4, 5), "max", 1, 0))
    assert kind == "info" and "ändert **keine** der festen Regeln" in text


def test_the_chain_rule_never_changes_under_relabeling_in_the_verdict_examples():
    for n, family, seed in ((8, 1, 0), (3, 0, 22), (8, 1, 10), (8, 4, 2)):
        rc = ev.relabel_check(_a(n, family, seed), "max", 1, 0)
        assert not next(r for r in rc["rows"] if r["rule"] == "chain")["changed"]


def test_solver_verdict_counts_plans_and_sums_of_b():
    a = _a(8, 1, 2)
    kind, text = ev.verdict_solvers(ev.solver_rows(a.inst, 2))
    assert kind == "warning" and "**4 verschiedene Pläne**" in text and "Summe A (17)" in text and "4 verschiedenen Summen B (31, 41, 42, 44)" in text
    kind, text = ev.verdict_solvers(ev.solver_rows(_a(8, 4, 5).inst, 5))
    assert kind == "info" and "**denselben Plan**" in text
    kind, text = ev.verdict_solvers(ev.solver_rows(_a(12, 1, 2).inst, 2))
    assert kind == "warning" and "**3 verschiedene Pläne**" in text and "(47, 57, 64)" in text


def test_sweep_verdicts_carry_the_phase_zero_numbers():
    ties = ev.ties_sweep()
    assert [ties[("sum", k)]["ties"] for k in C.SWEEP_KS] == [19, 13, 2, 0, 0] and [ties[("sq", k)]["ties"] for k in C.SWEEP_KS] == [19, 7, 0, 0, 0]
    assert [ties[("max", k)]["ties"] for k in (3, 9, 0)] == [20, 19, 17]
    kind, text = ev.verdict_ties_sweep(ties, C.SWEEP_N)
    assert kind == "info" and "Summe: K = 3: 19 von 20" in text and "Maximum: K = 3: 20 von 20" in text and "K = reell: 17 von 20" in text
    chain = ev.chain_sweep()
    assert chain[9]["unique"] == [1, 10, 13, 20, 20] and chain[3]["unique"] == [0, 1, 1, 12, 12] and chain[999]["unique"] == [5, 20, 20, 20, 20]
    assert "K = 9: eindeutig nach Maximum / + Summe / + Quadratsumme / + C / + Leximax in 1 / 10 / 13 / 20 / 20 von 20" in ev.verdict_chain_sweep(chain, 8)[1]

"""Kennzahlen, Verdikt-Logik und Sweeps. Verdikte sind reine Funktionen (Art, Text); jede Zahl im Text kommt aus der Rechnung.

Ein Gleichstand ist hier: mehr als ein Plan hat den kleinsten Wert des Ziels (die Optimalmenge). Gefragt wird, wie oft das vorkommt, wie stark das Ergebnis darin
streut, wie viele Regeln es bis zu einem eindeutigen Plan braucht und was passiert, wenn man es nicht regelt (Umnummerieren, Löser)."""

from dataclasses import dataclass

import numpy as np

import gst_algorithm as A
import gst_constants as C
from gst_scenario import Instance, make_instance, relabel_arrays


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma; kein „-0,0“."""
    text = f"{x:.{digits}f}"
    if float(text) == 0.0:
        text = f"{0.0:.{digits}f}"
    return text.replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    """Anteil als Prozent: 0,05 -> „5,0 %“."""
    return de(x * 100.0, digits) + " %"


def plan_text(plan, n: int) -> str:
    return ", ".join(f"P{i + 1}→A{int(j) + 1}" for i, j in enumerate(plan)) if n <= 12 else "siehe Rechnung"


DEFINITE = {"max": "das", "sum": "die", "sq": "die", "sumC": "die", "sorted": "der"}
SAME = {"max": "dasselbe", "sum": "dieselbe", "sq": "dieselbe", "sumC": "dieselbe", "sorted": "derselbe"}


def value_text(v) -> str:
    """Kennzahl: ganze Zahlen ohne Nachkommastelle, sonst mit einer."""
    return str(int(v)) if float(v).is_integer() else de(float(v), 1)


def values_text(vals: tuple) -> str:
    return ", ".join(f"{name} {value_text(v)}" for name, v in zip(C.VALUE_NAMES, vals))


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    seed: int = C.DEFAULT_SEED


@dataclass
class Analysis:
    inst: Instance
    mode: str                  # "enum" (alle Pläne aufgezählt) oder "large" (nur Löservergleich)
    mats: list                 # die drei Matrizen als Arrays
    o: dict | None             # Kennzahlen aller Pläne (nur bei Aufzählung)
    seed: int


def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.family, settings.seed)
    mats = inst.arrays()
    if inst.n > C.ENUM_MAX:
        return Analysis(inst, "large", mats, None, settings.seed)
    return Analysis(inst, "enum", mats, A.objectives(mats, inst.n), settings.seed)


# --- Experimente auf einer Instanz ---------------------------------------------------------------------------------------------------------

def tie_summary(a: Analysis, objective: str) -> dict:
    """Optimalmenge des Ziels: Größe, Indizes, Nebenkennzahl und deren Spanne."""
    idx = A.opt_set(a.o[objective])
    lo, hi, rel = A.spread(a.o, objective, idx)
    return {"objective": objective, "size": len(idx), "idx": idx, "secondary": C.SECONDARY[objective], "lo": lo, "hi": hi, "rel": rel, "total": len(a.o["sum"])}


def rule_rows(a: Analysis, objective: str, rule_seed: int = 0) -> list[dict]:
    """Alle Regeln: gewählter Plan und seine Kennzahlen."""
    rows = []
    for rule in C.RULES:
        idx = A.pick(a.o, objective, rule, rule_seed)
        rows.append({"rule": rule, "idx": idx, "plan": A.all_plans(a.inst.n)[idx].astype(int), "vals": A.values(a.o, idx)})
    return rows


def chain_summary(a: Analysis, objective: str) -> dict:
    """Optimalmenge nach jeder Ebene; ob der Plan eindeutig ist; ob die übrigen Pläne wenigstens alle Kennzahlen gemeinsam haben."""
    sets = A.chain_sets(a.o, objective)
    keys = A.chain_order(objective)
    sizes = [len(s) for s in sets]
    unique_at = next((i for i, s in enumerate(sizes) if s == 1), None)
    last = sets[-1]
    same_vals = len({A.values(a.o, int(i)) for i in last}) == 1
    return {"objective": objective, "keys": keys, "sizes": sizes, "sets": sets, "unique_at": unique_at, "residual": len(last), "residual_equivalent": same_vals}


def relabel_check(a: Analysis, objective: str, relabel_seed: int, rule_seed: int = 0) -> dict:
    """Dieselbe Instanz mit anderen Nummern: ändern sich die Kennzahlen des gewählten Plans je Regel?"""
    mats2, r, c = relabel_arrays(a.mats, np.random.default_rng(relabel_seed))
    o2 = A.objectives(mats2, a.inst.n)
    rows = []
    for rule in C.RULES:
        i0, i1 = A.pick(a.o, objective, rule, rule_seed), A.pick(o2, objective, rule, rule_seed)
        v0, v1 = A.values(a.o, i0), A.values(o2, i1)
        rows.append({"rule": rule, "before": v0, "after": v1, "changed": not A.same_values(v0, v1, a.inst.exact)})
    return {"rows": rows, "r": r, "c": c, "objective": objective}


def solver_rows(inst: Instance, perm_seed: int) -> list[dict]:
    """Die Summe von A mit Aufzählung (n <= 8, erster Plan), Ungarischer Methode und HiGHS, und mit vertauschter Zeilenreihenfolge; dazu die Summe von B."""
    n = inst.n
    A_, B_ = inst.arrays()[0], inst.arrays()[1]
    cost = A_.astype(float)
    r = np.random.default_rng(perm_seed + 11).permutation(n)

    def back(plan_r):
        plan = np.empty(n, dtype=int)
        plan[r] = plan_r
        return plan

    methods = []
    if n <= C.ENUM_MAX:
        o = A.objectives([A_, B_, B_], n)
        methods.append(("Aufzählung (erster Plan)", A.all_plans(n)[int(A.opt_set(o["sum"])[0])].astype(int)))
    methods += [("Ungarische Methode", A.lap_plan(cost)), ("HiGHS", A.highs_plan(cost)),
                ("Ungarische Methode, Zeilen vertauscht", back(A.lap_plan(cost[r]))), ("HiGHS, Zeilen vertauscht", back(A.highs_plan(cost[r])))]
    return [{"method": name, "plan": plan, "sum_a": A.plan_sum(A_, plan), "sum_b": A.plan_sum(B_, plan)} for name, plan in methods]


# --- Sweeps über feste Instanzen -----------------------------------------------------------------------------------------------------------

def _o(n: int, k: int, seed: int) -> dict:
    return A.objectives(make_instance(n, C.GRANULARITIES.index(k), seed).arrays(), n)


def ties_sweep(n: int = C.SWEEP_N, ks=C.SWEEP_KS, seeds=C.SWEEP_SEEDS) -> dict:
    """Je Zielart und Granularität: Instanzen mit Optimalmenge >= 2, Optimalmenge Median und Maximum."""
    out = {}
    for obj in C.OBJECTIVES:
        for k in ks:
            sizes = [len(A.opt_set(_o(n, k, s)[obj])) for s in seeds]
            out[(obj, k)] = {"ties": int(sum(x > 1 for x in sizes)), "median": float(np.median(sizes)), "max": int(max(sizes)), "seeds": len(seeds)}
    return out


def spread_sweep(n: int = C.SWEEP_N, ks=(3, 9, 99), seeds=C.SWEEP_SEEDS) -> dict:
    """Streuung der Nebenkennzahl über die Optimalmenge, nur über die Instanzen mit Gleichstand: Zahl, Zahl mit Spanne > 0, Median und Maximum der relativen Spanne."""
    out = {}
    for obj in C.OBJECTIVES:
        for k in ks:
            ties, pos, spans = 0, 0, []
            for s in seeds:
                o = _o(n, k, s)
                idx = A.opt_set(o[obj])
                if len(idx) < 2:
                    continue
                ties += 1
                rel = A.spread(o, obj, idx)[2]
                pos += rel > 0
                spans.append(rel)
            out[(obj, k)] = {"ties": ties, "positive": int(pos), "median": float(np.median(spans)) if spans else None, "max": float(max(spans)) if spans else None}
    return out


def chain_sweep(n: int = C.SWEEP_N, ks=(3, 9, 99, 999), seeds=C.SWEEP_SEEDS) -> dict:
    """Kette ab Maximum: Anteil der Instanzen mit genau einem Plan nach jeder Ebene und mittlere Größe der Optimalmenge."""
    out = {}
    for k in ks:
        uniq, mean = np.zeros(5), np.zeros(5)
        for s in seeds:
            sizes = np.array([len(x) for x in A.chain_sets(_o(n, k, s), "max")])
            uniq += sizes == 1
            mean += sizes
        out[k] = {"unique": [int(u) for u in uniq], "mean": [float(m) / len(seeds) for m in mean], "seeds": len(seeds)}
    return out


RELABEL_CASES = (("sum", "first"), ("max", "first"), ("max", "secondary"), ("max", "chain"))


def relabel_sweep(n: int = C.SWEEP_N, ks=(3, 9, 99), seeds=C.SWEEP_SEEDS, count: int = C.RELABEL_COUNT) -> dict:
    """Je Regel: in wie vielen Instanzen ändern sich die Kennzahlen des gewählten Plans, wenn man Personen und Aufgaben umnummeriert (je `count` Umnummerierungen)."""
    out = {}
    for k in ks:
        res = {case: 0 for case in RELABEL_CASES}
        for s in seeds:
            mats = make_instance(n, C.GRANULARITIES.index(k), s).arrays()
            o0 = A.objectives(mats, n)
            rng = np.random.default_rng(s + 7)
            others = [A.objectives(relabel_arrays(mats, rng)[0], n) for _ in range(count)]
            for obj, rule in RELABEL_CASES:
                base = A.values(o0, A.pick(o0, obj, rule))
                res[(obj, rule)] += any(not A.same_values(A.values(o, A.pick(o, obj, rule)), base, True) for o in others)
        out[k] = {case: int(v) for case, v in res.items()}
    return out


SOLVER_COMPARISONS = ("Aufzählung|Ungarisch", "Aufzählung|HiGHS", "Ungarisch|HiGHS", "Ungarisch|Ungarisch, Zeilen vertauscht", "HiGHS|HiGHS, Zeilen vertauscht")


def solver_sweep(cases=C.SOLVER_CASES, seeds=C.SWEEP_SEEDS) -> dict:
    """Je Vergleich und (n, K): Instanzen, in denen die beiden Wege verschiedene Pläne wählen, und davon die mit verschiedener Summe B."""
    out = {name: {} for name in SOLVER_COMPARISONS}
    for n, k in cases:
        diff = {name: [0, 0] for name in SOLVER_COMPARISONS}
        for s in seeds:
            inst = make_instance(n, C.GRANULARITIES.index(k), s)
            rows = {r["method"]: r for r in solver_rows(inst, s)}
            for name in SOLVER_COMPARISONS:
                a_name, b_name = name.split("|")
                a_key = {"Aufzählung": "Aufzählung (erster Plan)", "Ungarisch": "Ungarische Methode", "HiGHS": "HiGHS"}[a_name]
                b_key = {"Ungarisch": "Ungarische Methode", "HiGHS": "HiGHS", "Ungarisch, Zeilen vertauscht": "Ungarische Methode, Zeilen vertauscht", "HiGHS, Zeilen vertauscht": "HiGHS, Zeilen vertauscht"}[b_name]
                if a_key not in rows:
                    continue
                p1, p2 = rows[a_key], rows[b_key]
                diff[name][0] += not np.array_equal(p1["plan"], p2["plan"])
                diff[name][1] += p1["sum_b"] != p2["sum_b"]
        for name in SOLVER_COMPARISONS:
            out[name][(n, k)] = None if (name.startswith("Aufzählung") and n > C.ENUM_MAX) else {"plans": int(diff[name][0]), "sum_b": int(diff[name][1]), "seeds": len(seeds)}
    return out


# --- Verdikte ------------------------------------------------------------------------------------------------------------------------------

def verdict_ties(t: dict) -> tuple[str, str]:
    """Experiment Optimalmenge: wie viele Pläne sind gleich gut?"""
    name = C.OBJECTIVE_NAMES[t["objective"]]
    art = "Das" if t["objective"] == "max" else "Die"
    if t["size"] == 1:
        return "info", f"{art} {name} hat hier **genau einen** besten Plan: kein Gleichstand, keine Regel nötig."
    extra = " Beim Maximum zählt nur ein einziger Eintrag, deshalb sind Gleichstände dort fast immer da." if t["objective"] == "max" else ""
    return "warning", f"{art} {name} hat **{t['size']}** gleich gute Pläne (von {t['total']}). Welcher gewählt wird, entscheidet nicht das Ziel.{extra}"


def verdict_spread(t: dict) -> tuple[str, str]:
    """Experiment Willkür: wie weit streut die Nebenkennzahl in der Optimalmenge?"""
    sec = C.CHAIN_NAMES[t["secondary"]]
    if t["size"] == 1:
        return "info", "Ohne Gleichstand gibt es keine Streuung."
    if t["hi"] == t["lo"]:
        return "info", f"Alle {t['size']} gleich guten Pläne haben {SAME[t['secondary']]} {sec} ({value_text(t['lo'])}): die Wahl unter ihnen ist hier folgenlos für diese Kennzahl."
    return "warning", (f"Unter den {t['size']} gleich guten Plänen reicht {DEFINITE[t['secondary']]} {sec} von **{value_text(t['lo'])} bis {value_text(t['hi'])}** (Spanne {pct(t['rel'])}): "
                       f"wer „irgendeinen“ nimmt, nimmt irgendeine dieser Zahlen.")


def verdict_rules(rows: list[dict]) -> tuple[str, str]:
    """Experiment Regeln: stimmen die Regeln überein?"""
    keys = {r["vals"] for r in rows}
    if len(keys) == 1:
        return "info", "Alle Regeln wählen Pläne mit denselben Kennzahlen: hier ist die Regel folgenlos."
    by = {C.RULE_NAMES[r["rule"]]: r["vals"] for r in rows}
    best = by[C.RULE_NAMES["chain"]]
    return "warning", (f"Die {len(rows)} Regeln liefern **{len(keys)} verschiedene** Kennzahlensätze. Die volle Kette wählt {values_text(best)}; "
                       f"der erste Plan wählt {values_text(by[C.RULE_NAMES['first']])}.")


def verdict_chain(c: dict) -> tuple[str, str]:
    """Experiment Kette: nach welcher Ebene ist der Plan eindeutig?"""
    names = [C.CHAIN_NAMES[k] for k in c["keys"]]
    sizes = ", ".join(f"{nm} {s}" for nm, s in zip(names, c["sizes"]))
    if c["unique_at"] is None:
        end = ("alle übrigen Pläne haben dieselben Kennzahlen: die Wahl ist nur noch eine der Nummerierung, aber folgenlos" if c["residual_equivalent"]
               else "die übrigen Pläne unterscheiden sich in mindestens einer Kennzahl, und nur noch die Nummerierung entscheidet")
        return "warning", f"Optimalmenge nach jeder Ebene: {sizes}. **Auch nach der letzten Ebene bleiben {c['residual']} Pläne**: {end}."
    if c["unique_at"] == 0:
        return "info", f"Optimalmenge nach jeder Ebene: {sizes}. Schon das Ziel allein ist eindeutig."
    return "warning" if c["unique_at"] >= 2 else "info", (f"Optimalmenge nach jeder Ebene: {sizes}. **Eindeutig wird der Plan erst nach „{names[c['unique_at']]}“** "
                                                           f"(Ebene {c['unique_at'] + 1} von {len(names)}).")


def verdict_relabel(rc: dict) -> tuple[str, str]:
    """Experiment Umnummerieren: welche Regeln ändern ihre Kennzahlen?"""
    det = [r for r in rc["rows"] if r["rule"] != "random"]
    changed = [C.RULE_NAMES[r["rule"]] for r in det if r["changed"]]
    kept = [C.RULE_NAMES[r["rule"]] for r in det if not r["changed"]]
    if not changed:
        return "info", "Beim Umnummerieren ändert **keine** der festen Regeln die Kennzahlen des gewählten Plans: hier gibt es nichts zu verlieren."
    first = next(r for r in det if r["changed"])
    return "warning", (f"Dieselbe Instanz, andere Nummern: **{len(changed)} von {len(det)} festen Regeln {'ändert' if len(changed) == 1 else 'ändern'} die Kennzahlen** des gewählten Plans ({', '.join(changed)}), "
                       f"zum Beispiel „{C.RULE_NAMES[first['rule']]}“ von ({values_text(first['before'])}) auf ({values_text(first['after'])}). "
                       + (f"Unverändert bleiben: {', '.join(kept)}." if kept else "Keine Regel bleibt unverändert."))


def verdict_solvers(rows: list[dict]) -> tuple[str, str]:
    """Experiment Löser: wählen die Wege verschiedene Pläne?"""
    plans = {tuple(int(x) for x in r["plan"]) for r in rows}
    sums_a = {r["sum_a"] for r in rows}
    sums_b = {r["sum_b"] for r in rows}
    if len(plans) == 1:
        return "info", "Alle Wege wählen **denselben Plan**: hier ist die Optimalmenge der Summe wahrscheinlich eindeutig."
    kind = "warning" if len(sums_b) > 1 else "info"
    return kind, (f"Die Wege wählen **{len(plans)} verschiedene Pläne**, alle mit derselben Summe A ({value_text(next(iter(sums_a)))}) und {len(sums_b)} verschiedenen Summen B "
                  f"({', '.join(value_text(v) for v in sorted(sums_b))}): das Ziel kann sie nicht unterscheiden, der Löser und die Reihenfolge entscheiden.")


def _spread_str(r: dict) -> str:
    return "–" if r["median"] is None else f"Median {pct(r['median'])}, Maximum {pct(r['max'])}"


def verdict_ties_sweep(res: dict, n: int) -> tuple[str, str]:
    parts = []
    for obj in C.OBJECTIVES:
        cells = []
        for k in C.SWEEP_KS:
            r = res[(obj, k)]
            cells.append(f"K = {'reell' if k == 0 else k}: {r['ties']} von {r['seeds']} (Optimalmenge Median {de(r['median'])}, Maximum {r['max']})")
        parts.append(f"{C.OBJECTIVE_NAMES[obj]}: " + "; ".join(cells))
    return "info", f"Instanzen mit mindestens zwei gleich guten Plänen, n = {n}, je 20 feste Instanzen: " + ". ".join(parts) + "."


def verdict_spread_sweep(res: dict, n: int) -> tuple[str, str]:
    parts = []
    for (obj, k), r in res.items():
        parts.append(f"{C.OBJECTIVE_NAMES[obj]}, K = {k}: {r['ties']} Instanzen mit Gleichstand, Spanne über null in {r['positive']}, {_spread_str(r)}")
    return "info", f"Streuung der Nebenkennzahl über die Optimalmenge, n = {n}: " + "; ".join(parts) + "."


def verdict_chain_sweep(res: dict, n: int) -> tuple[str, str]:
    parts = []
    for k, r in res.items():
        parts.append(f"K = {k}: eindeutig nach Maximum / + Summe / + Quadratsumme / + C / + Leximax in " + " / ".join(str(u) for u in r["unique"]) + f" von {r['seeds']} (mittlere Optimalmenge " + " / ".join(de(m) for m in r["mean"]) + ")")
    return "info", f"Kette bis zur Eindeutigkeit, n = {n}: " + "; ".join(parts) + "."


def verdict_relabel_sweep(res: dict, n: int) -> tuple[str, str]:
    parts = []
    for k, r in res.items():
        cells = ", ".join(f"{C.OBJECTIVE_NAMES[o]} {C.RULE_NAMES[rule]}: {v}" for (o, rule), v in r.items())
        parts.append(f"K = {k}: " + cells)
    return "info", f"Instanzen von 20, in denen Umnummerieren (je {C.RELABEL_COUNT} Umnummerierungen) die Kennzahlen des gewählten Plans ändert, n = {n}: " + "; ".join(parts) + "."


def verdict_solver_sweep(res: dict) -> tuple[str, str]:
    parts = []
    for name, cases in res.items():
        cells = ", ".join(f"n = {n}, K = {k}: {'–' if v is None else str(v['plans']) + ' / ' + str(v['sum_b'])}" for (n, k), v in cases.items())
        parts.append(f"{name}: {cells}")
    return "info", "Instanzen von 20 mit anderem Plan / davon mit anderer Summe B: " + "; ".join(parts) + "."

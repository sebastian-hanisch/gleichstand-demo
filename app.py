"""Gleichstände - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 5 der Reihe „Zielfunktionsdesign“: dieselbe Zuordnung wie in Stück 1 bis 4. Gleichstände im Optimum sind kein Randfall: die Demo zeigt, wie oft sie vorkommen,
wie stark das Ergebnis darin streut, wie viele Regeln es bis zu einem eindeutigen Plan braucht und was passiert, wenn man sie nicht regelt (Umnummerieren, Löser).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gst_constants as C
from gst_evaluation import (
    Settings,
    analyse,
    chain_summary,
    chain_sweep,
    de,
    pct,
    plan_text,
    relabel_check,
    relabel_sweep,
    rule_rows,
    solver_rows,
    solver_sweep,
    spread_sweep,
    tie_summary,
    ties_sweep,
    value_text,
    values_text,
    verdict_chain,
    verdict_chain_sweep,
    verdict_relabel,
    verdict_relabel_sweep,
    verdict_rules,
    verdict_solver_sweep,
    verdict_solvers,
    verdict_spread,
    verdict_spread_sweep,
    verdict_ties,
    verdict_ties_sweep,
)
from gst_layout import dunkles_design, kopf_css
from gst_pdf_export import build_pdf
from gst_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from gst_visualization import build_chain, build_cloud, build_relabel_bars, build_ties_bars

st.set_page_config(page_title="Gleichstände – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _solvers(settings):
    return solver_rows(_analysis(settings).inst, settings.seed)


@st.cache_data(show_spinner="20 feste Instanzen werden gerechnet ...")
def _ties_sweep():
    return ties_sweep(), spread_sweep()


@st.cache_data(show_spinner="20 feste Instanzen werden gerechnet ...")
def _chain_sweep():
    return chain_sweep()


@st.cache_data(show_spinner="20 feste Instanzen werden mit je acht Umnummerierungen gerechnet ...")
def _relabel_sweep():
    return relabel_sweep()


@st.cache_data(show_spinner="Die Löser werden auf 20 festen Instanzen verglichen ...")
def _solver_sweep():
    return solver_sweep()


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gst_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🟰 Gleichstände")
st.markdown(
    """
**Wann entscheidet das zweite Ziel, und was entscheidet danach?** Dieselbe Aufgabe wie in Stück 1 bis 4: **n Personen** übernehmen **n Aufgaben**, jede Paarung hat drei Belastungen **A**, **B** und **C**.
Ein **Gleichstand** ist: Mehr als ein Plan hat den kleinsten Wert des Ziels. Das ist kein Randfall. Beim **Maximum** zählt nur ein einziger Eintrag, deshalb gibt es ihn fast immer; bei Summen, sobald die Werte grob sind.
Wer ihn nicht ausdrücklich regelt, lässt etwas anderes entscheiden: die **Nummerierung** der Personen, die Reihenfolge der Eingabe, den **Löser**. Die Demo misst, wie oft und wie viel.

Weiter unten: **🔬 Wie viele Pläne sind gleich gut?**, **🔬 Was die Willkür kostet**, **🔬 Die Kette bis zur Eindeutigkeit**, **🔬 Umnummerieren**, **🔬 Die Löser**, **🔬 Wie oft und wie viel?**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Vergleich der Regeln", expanded=True):
    st.markdown(
        """
1. **Die Optimalmenge** eines Ziels sind alle Pläne mit dem kleinsten Wert. Hat sie mehr als einen Plan, entscheidet das Ziel allein nicht.
2. **Fünf Regeln** wählen daraus einen Plan: der **erste Plan** (kleinster Index in der Reihenfolge der Aufzählung), der **letzte**, ein **Zufall** mit Seed, der mit der **kleinsten Nebenkennzahl** (bei Summe und Quadratsumme das Maximum, beim Maximum die Summe) und die **volle Kette** (Ziel, dann Maximum, Summe, Quadratsumme, C-Summe, Leximax).
3. **Kennzahlen** eines Plans sind Summe A, Maximum A, Summe B und Summe C. Sie ändern sich nicht, wenn man Personen und Aufgaben umnummeriert; der gewählte *Plan* schon. Eine Regel ist nur dann gut, wenn ihre Kennzahlen es nicht tun.
4. **„Erster Plan“ ist keine Regel des Problems**, sondern eine Folge der Nummerierung. Das zeigt das Umnummerieren: derselbe Sachverhalt, andere Nummern, anderes Ergebnis.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Personen und Aufgaben n", *bounds("n_slider"), key="n_slider",
                  help=f"Bis n = {C.ENUM_MAX} werden alle Pläne aufgezählt (exakt in ganzen Zahlen); bis n = {C.N_MAX} gibt es den Löservergleich.")
    family = st.selectbox("Wertgranularität K der Belastungen", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="Je gröber die Werte (kleineres K), desto mehr Gleichstände. Reelle Werte haben nur beim Maximum Gleichstände.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"n_slider": int(n), "family_select": int(family), "seed_input": int(seed)})

settings = Settings(int(n), int(family), int(seed))
a = _analysis(settings)

objective = st.radio("Ziel (auf den Belastungen A)", list(C.OBJECTIVES), index=C.DEFAULT_OBJECTIVE, format_func=lambda k: C.OBJECTIVE_NAMES[k], horizontal=True, key="objective_select")
c_seed, c_rel = st.columns(2)
rule_seed = int(c_seed.number_input("Seed der Zufallsregel", 0, C.SEED_MAX, 0, step=1, key="rule_seed"))
relabel_seed = int(c_rel.number_input("Seed der Umnummerierung", 0, C.SEED_MAX, 1, step=1, key="relabel_seed"))

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: wie viele Pläne sind gleich gut?")
if a.mode == "enum":
    t = tie_summary(a, objective)
    chain = chain_summary(a, objective)
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Gleich gute Pläne ({C.OBJECTIVE_NAMES[objective]})", f"{t['size']} von {t['total']}")
    m2.metric(f"Spanne der {C.CHAIN_NAMES[t['secondary']]}", "–" if t["size"] == 1 else f"{value_text(t['lo'])} bis {value_text(t['hi'])}", delta=None if t["size"] == 1 else pct(t["rel"]), delta_color="off")
    m3.metric("Eindeutig nach der Kette?", "ja" if chain["residual"] == 1 else f"nein, noch {chain['residual']}")
    rows = rule_rows(a, objective, rule_seed)
    st.plotly_chart(build_cloud(a, objective, t["idx"], rows), width="stretch", key="cloud_chart")
    st.caption("Jeder Punkt ist ein Plan. Blau: die gleich guten Pläne (die Optimalmenge); die Marken zeigen, welchen Plan welche Regel wählt (gleiche Pläne liegen übereinander, die Marken sind ineinander gesetzt).")
    st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a, objective, rule_seed), file_name="gleichstaende.pdf", mime="application/pdf", key="pdf_download")
else:
    st.info(f"Bei n = {a.inst.n} werden nicht alle Pläne aufgezählt (nur bis n = {C.ENUM_MAX}); die Optimalmenge, die Kette und das Umnummerieren gibt es hier nicht. Der Löservergleich unten läuft bis n = {C.N_MAX}.")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Entscheidet das Ziel, welcher Plan es wird?")
if a.mode == "enum":
    kind, text = verdict_ties(t)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Wie viele Pläne sind gleich gut?")
st.caption("Die Optimalmenge des gewählten Ziels. Beim Maximum zählt nur ein einziger Eintrag; bei Summen entstehen Gleichstände erst, wenn die Werte grob sind (kleines K).")
if a.mode == "enum":
    rows_md = ["| Ziel | gleich gute Pläne | Nebenkennzahl | Spanne der Nebenkennzahl |", "|---|---|---|---|"]
    for obj in C.OBJECTIVES:
        ts = tie_summary(a, obj)
        rows_md.append(f"| **{C.OBJECTIVE_NAMES[obj]}** | {ts['size']} von {ts['total']} | {C.CHAIN_NAMES[ts['secondary']]} | " + ("–" if ts["size"] == 1 else f"{value_text(ts['lo'])} bis {value_text(ts['hi'])} ({pct(ts['rel'])})") + " |")
    st.markdown("\n".join(rows_md))
else:
    st.info("Nur bis n = 8 (Aufzählung).")

st.markdown("---")

st.subheader("🔬 Was die Willkür kostet")
st.caption("Die Nebenkennzahl über die Optimalmenge und die fünf Regeln: Wer „irgendeinen“ der gleich guten Pläne nimmt, nimmt irgendeine dieser Zahlen.")
if a.mode == "enum":
    kind, text = verdict_spread(t)
    getattr(st, kind)(text)
    rows_md = ["| Regel | " + " | ".join(C.VALUE_NAMES) + " | Plan |", "|---|" + "---|" * (len(C.VALUE_NAMES) + 1)]
    for r in rows:
        rows_md.append(f"| **{C.RULE_NAMES[r['rule']]}** | " + " | ".join(value_text(v) for v in r["vals"]) + f" | {plan_text(r['plan'], a.inst.n)} |")
    st.markdown("\n".join(rows_md))
    kind, text = verdict_rules(rows)
    getattr(st, kind)(text)
else:
    st.info("Nur bis n = 8 (Aufzählung).")

st.markdown("---")

st.subheader("🔬 Die Kette bis zur Eindeutigkeit")
st.caption("Ziel, dann Maximum, Summe, Quadratsumme, C-Summe und Leximax (jede Ebene wählt aus den Plänen der vorigen die mit dem kleinsten Wert): wie viele Pläne bleiben übrig?")
if a.mode == "enum":
    st.plotly_chart(build_chain(chain), width="stretch", key="chain_chart")
    kind, text = verdict_chain(chain)
    getattr(st, kind)(text)
else:
    st.info("Nur bis n = 8 (Aufzählung).")

st.markdown("---")

st.subheader("🔬 Umnummerieren")
st.caption("Dieselbe Instanz, Personen und Aufgaben anders nummeriert: Die Kennzahlen eines Plans bleiben, aber „der erste Plan“ ist ein anderer. Welche Regeln ändern ihr Ergebnis?")
if a.mode == "enum":
    rc = relabel_check(a, objective, relabel_seed, rule_seed)
    rows_md = ["| Regel | vorher | nachher | geändert? |", "|---|---|---|---|"]
    for r in rc["rows"]:
        note = "ja" if r["changed"] else "nein"
        if r["rule"] == "random" and r["changed"]:
            note = "ja (Zufall wählt aus einer anderen Liste)"
        rows_md.append(f"| **{C.RULE_NAMES[r['rule']]}** | {values_text(r['before'])} | {values_text(r['after'])} | {note} |")
    st.markdown("\n".join(rows_md))
    kind, text = verdict_relabel(rc)
    getattr(st, kind)(text)
else:
    st.info("Nur bis n = 8 (Aufzählung).")

st.markdown("---")

st.subheader("🔬 Die Löser")
st.caption("Die Summe der Belastungen A, gelöst mit Aufzählung, Ungarischer Methode und HiGHS, und mit vertauschter Zeilenreihenfolge. Alle Wege finden das Optimum; welchen der gleich guten Pläne sie nennen, ist nirgends festgelegt.")
srows = _solvers(settings)
rows_md = ["| Weg | Summe A | Summe B | Plan |", "|---|---|---|---|"]
for r in srows:
    rows_md.append(f"| **{r['method']}** | {value_text(r['sum_a'])} | {value_text(r['sum_b'])} | {plan_text(r['plan'], a.inst.n)} |")
st.markdown("\n".join(rows_md))
kind, text = verdict_solvers(srows)
getattr(st, kind)(text)
st.caption("Laut Dokumentation geben `argmin` und `argmax` von NumPy bei mehreren gleichen Extremen das erste Vorkommen zurück und `sorted` von Python ist stabil; `scipy.optimize.linear_sum_assignment` und `scipy.optimize.milp` legen nicht fest, welches von mehreren Optima zurückkommt.")

st.markdown("---")

st.subheader("🔬 Wie oft und wie viel?")
st.caption(f"Je {len(C.SWEEP_SEEDS)} feste Instanzen (SWEEP_SEEDS), n = {C.SWEEP_N}, alle aufgezählt; die Zahlen sind Zählungen und Spannen über Instanzen, kein Satz.")
if st.toggle("Gleichstände und Streuung nachrechnen (je Zielart und Granularität)", value=False, key="sweep_ties"):
    ties_res, spread_res = _ties_sweep()
    kind, text = verdict_ties_sweep(ties_res, C.SWEEP_N)
    getattr(st, kind)(text)
    st.plotly_chart(build_ties_bars(ties_res), width="stretch", key="sweep_ties_chart")
    kind, text = verdict_spread_sweep(spread_res, C.SWEEP_N)
    getattr(st, kind)(text)
if st.toggle("Die Kette bis zur Eindeutigkeit nachrechnen", value=False, key="sweep_chain"):
    kind, text = verdict_chain_sweep(_chain_sweep(), C.SWEEP_N)
    getattr(st, kind)(text)
if st.toggle("Umnummerieren nachrechnen (je acht Umnummerierungen)", value=False, key="sweep_relabel"):
    rel_res = _relabel_sweep()
    kind, text = verdict_relabel_sweep(rel_res, C.SWEEP_N)
    getattr(st, kind)(text)
    st.plotly_chart(build_relabel_bars(rel_res), width="stretch", key="sweep_relabel_chart")
if st.toggle("Die Löser über die festen Instanzen vergleichen (n = 8, 10, 12)", value=False, key="sweep_solver"):
    kind, text = verdict_solver_sweep(_solver_sweep())
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Summenkriterien einer Zuordnung, drei unabhängige Matrizen** | Bei Nebenbedingungen, Wechselwirkungen oder abhängigen Kriterien sehen Optimalmengen anders aus; Stück 1 bis 4 zeigen andere Kriterien an derselben Zuordnung | Stück 1 (Dasselbe Problem, drei Ziele), Stück 3 (Zwei Kriterien) |
| **Ganze Zahlen 1 bis K oder reell** | Gerundete Dezimalzahlen haben Gleichstände, die in float64 nicht exakt sind: das ist Stück 4 | Stück 4 (Lexikographisch) |
| **Gleichheit heißt: gleiche Kennzahlen** | Verschiedene Pläne mit denselben Kennzahlen bleiben möglich; die Demo weist sie aus, die Wahl unter ihnen ist dann folgenlos für diese Kennzahlen, aber nicht für andere | – |
| **Die Löser in einer Version** | Gemessen sind die Ungarische Methode und HiGHS aus scipy in der benutzten Version; andere Löser oder Versionen können bei Gleichstand andere Pläne wählen | Dokumentation des Lösers |
| **n = 8 aufgezählt, Löser bis n = 12** | Optimalmengen und Ketten gibt es nur bis n = 8; darüber nur der Löservergleich | – |
| **Der Zufall ist ein Seed** | Die Zufallsregel ist reproduzierbar, aber sie wählt aus einer Liste, deren Reihenfolge die Nummerierung bestimmt: auch sie ändert sich beim Umnummerieren | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben $n$ Personen, $n$ Aufgaben und drei Belastungen $a_{ij}, b_{ij}, c_{ij}$. Ein Plan ist eine Permutation $\pi$; die Belastungen $b_i = a_{i,\pi(i)}$ von A, daraus $\Sigma(\pi) = \sum_i b_i$, $Q(\pi) = \sum_i b_i^2$, $M(\pi) = \max_i b_i$; die Summen $B(\pi)$ und $C(\pi)$ der anderen Matrizen.

**Optimalmenge.** Für ein Ziel $f \in \{\Sigma, Q, M\}$ ist $O_f = \{\pi : f(\pi) = \min_{\pi'} f(\pi')\}$. Ein **Gleichstand** liegt vor, wenn $|O_f| \ge 2$. Beim Maximum bestimmt ein einziger Eintrag $\max_i b_i$ den Wert: alle Pläne, die diesen Eintrag nicht überschreiten, sind gleich gut; bei Summen müssen mehrere Einträge zusammen denselben Wert ergeben, das passiert erst bei groben Werten.

**Kette.** Ebene $k$ wählt aus der Menge der Ebene $k-1$ die Pläne mit kleinstem Wert des $k$-ten Kennwerts; Reihenfolge: das gewählte Ziel, dann Maximum, Summe, Quadratsumme, $C(\pi)$, Leximax (den absteigend sortierten Belastungsvektor lexikographisch minimieren), ohne Wiederholung.

**Regeln.** „Erster Plan“ ist $\min O_f$ in der Reihenfolge von `itertools.permutations`; sie hängt von der Nummerierung ab: Sind $P, Q$ Permutationsmatrizen und $a' = P a Q$, so ist die Optimalmenge für $a'$ die entsprechend umbenannte Menge, der „erste“ Plan aber nicht der umbenannte erste Plan. Die **Kennzahlen** $(\Sigma, M, B, C)$ eines Plans sind invariant.

**Literatur.** NumPy-Dokumentation: `argmin`/`argmax` geben bei mehreren gleichen Extremen das erste Vorkommen zurück; Python: `sorted` ist stabil; SciPy: `linear_sum_assignment` (modifiziertes Jonker-Volgenant, Crouse 2016) und `milp` (HiGHS) sagen nichts darüber, welches von mehreren Optima zurückkommt (alles in der Dokumentation gelesen). Diese Demo übernimmt keine Zahl daraus; alle Zahlen sind Messungen an den Instanzfamilien der Demo.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)

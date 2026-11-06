"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import numpy as np
import plotly.graph_objects as go

import gst_algorithm as A
import gst_constants as C

MARK_SYMBOLS = {"first": "diamond", "last": "square", "random": "x", "secondary": "triangle-up", "chain": "star"}
MARK_COLORS = {"first": "#d8a13a", "last": "#c0504d", "random": "#7b5ea7", "secondary": "#4c78a8", "chain": "#111111"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_cloud(a, objective: str, idx: np.ndarray, rows: list[dict] | None = None):
    """Alle Pläne (Ziel gegen Nebenkennzahl); die Optimalmenge blau; die von den Regeln gewählten Pläne als Marken (gleiche Pläne liegen übereinander)."""
    sec = C.SECONDARY[objective]
    x, y = np.asarray(a.o[objective], dtype=float), np.asarray(a.o[sec], dtype=float)
    fig = go.Figure(go.Scattergl(x=x, y=y, mode="markers", marker=dict(size=4, color=C.COLOR_ALL), name="alle Pläne", hovertemplate="%{x:.1f} / %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=x[idx], y=y[idx], mode="markers", marker=dict(size=12, color=C.COLOR_OPT, line=dict(width=1, color="white")), name="gleich gute Pläne (Optimalmenge)",
                             hovertemplate="%{x:.1f} / %{y:.1f}<extra></extra>"))
    for rank, r in enumerate(rows or []):
        i = r["idx"]
        fig.add_trace(go.Scatter(x=[x[i]], y=[y[i]], mode="markers", marker=dict(symbol=MARK_SYMBOLS[r["rule"]], size=max(10, 22 - 3 * rank), color=MARK_COLORS[r["rule"]], line=dict(width=1, color="white")),
                                 name=C.RULE_NAMES[r["rule"]], hovertemplate=C.RULE_NAMES[r["rule"]] + ": %{x:.1f} / %{y:.1f}<extra></extra>"))
    fig.update_xaxes(title_text=f"{C.OBJECTIVE_NAMES[objective]} der Belastungen A (Ziel, kleiner ist besser)")
    fig.update_yaxes(title_text=f"{C.CHAIN_NAMES[sec]} der Belastungen A (Nebenkennzahl)")
    return _base(fig, height=420)


def build_chain(c: dict):
    """Größe der Optimalmenge nach jeder Ebene der Kette (logarithmische Achse); grün: genau ein Plan."""
    names = [C.CHAIN_NAMES[k] if i == 0 else f"+ {C.CHAIN_NAMES[k]}" for i, k in enumerate(c["keys"])]
    sizes = c["sizes"]
    fig = go.Figure(go.Bar(x=names, y=sizes, text=[str(s) for s in sizes], textposition="outside", marker_color=[C.COLOR_OK if s == 1 else C.COLOR_BAD for s in sizes],
                           hovertemplate="%{x}: %{y} Pläne<extra></extra>"))
    fig.update_yaxes(type="log", title_text="Pläne in der Optimalmenge", range=[0, max(1.0, float(np.log10(max(sizes)))) + 0.3])
    fig.update_xaxes(type="category")
    return _base(fig, height=320)


def build_ties_bars(res: dict, total: int = 20):
    """Instanzen mit Gleichstand je Granularität und Zielart (Anzahl von `total`)."""
    ks = sorted({k for _, k in res}, key=lambda k: (k == 0, k))
    xs = ["reell" if k == 0 else f"K = {k}" for k in ks]
    colors = {"sum": "#2F6B65", "sq": "#4c78a8", "max": "#c0504d"}
    fig = go.Figure([go.Bar(x=xs, y=[res[(o, k)]["ties"] for k in ks], name=C.OBJECTIVE_NAMES[o], marker_color=colors[o], hovertemplate=C.OBJECTIVE_NAMES[o] + ": %{y} von " + str(total) + "<extra></extra>")
                     for o in C.OBJECTIVES])
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, total], title_text=f"Instanzen mit Gleichstand (von {total})")
    return _base(fig, height=320)


def build_relabel_bars(res: dict, total: int = 20):
    """Instanzen, in denen Umnummerieren die Kennzahlen ändert, je Granularität und Regel (Anzahl von `total`)."""
    ks = sorted(res)
    xs = [f"K = {k}" for k in ks]
    cases = list(next(iter(res.values())))
    colors = ["#d8a13a", "#c0504d", "#4c78a8", "#2F6B65"]
    fig = go.Figure([go.Bar(x=xs, y=[res[k][c] for k in ks], name=f"{C.OBJECTIVE_NAMES[c[0]]}: {C.RULE_NAMES[c[1]]}", marker_color=colors[i % 4]) for i, c in enumerate(cases)])
    fig.update_layout(barmode="group")
    fig.update_yaxes(range=[0, total], title_text=f"Instanzen mit geänderten Kennzahlen (von {total})")
    return _base(fig, height=360)

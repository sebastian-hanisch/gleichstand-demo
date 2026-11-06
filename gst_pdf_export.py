"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import gst_constants as C
from gst_evaluation import Analysis, Settings, chain_summary, rule_rows, tie_summary, value_text

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "Δ": "Delta", "↔": "<->", "„": '"', "“": '"', "²": "2", "∞": "unendlich"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis, objective: str, rule_seed: int = 0) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Gleichstände"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Personen, {s.n} Aufgaben, Familie: {C.FAMILIES[s.family]}, Seed {s.seed}. Alles simuliert."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    if a.mode != "enum":
        pdf.multi_cell(0, 5, _s(f"Bei n = {s.n} werden nicht alle Pläne aufgezählt (nur bis n = {C.ENUM_MAX}); der Löservergleich steht in der App."), new_x="LMARGIN", new_y="NEXT")
        return bytes(pdf.output())
    t = tie_summary(a, objective)
    c = chain_summary(a, objective)
    pdf.multi_cell(0, 5, _s(f"Ziel: {C.OBJECTIVE_NAMES[objective]}. Gleich gute Pläne: {t['size']} von {t['total']}. {C.CHAIN_NAMES[t['secondary']]} in der Optimalmenge: {value_text(t['lo'])} bis {value_text(t['hi'])}."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s("Optimalmenge nach jeder Ebene: " + ", ".join(f"{C.CHAIN_NAMES[k]} {n}" for k, n in zip(c["keys"], c["sizes"])) + "."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    widths = (62, 32, 32, 32, 32)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Regel",) + C.VALUE_NAMES):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for r in rule_rows(a, objective, rule_seed):
        for w, v in zip(widths, (C.RULE_NAMES[r["rule"]],) + tuple(value_text(x) for x in r["vals"])):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Erster Plan: kleinster Index in der Reihenfolge der Aufzählung (hängt von der Nummerierung ab). Quelle: gleichstand-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())

# Gleichstände – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-gleichstand-demo.streamlit.app/)** -->

Stück 5 der Linie **Zielfunktionsdesign** („Das Ziel ist das Modell“) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Arbeitsname; Name, Bereich und Themenfeld werden erst bei der Einbindung in die Website festgelegt). Es baut auf Stück 1 bis 4 auf (`zielvergleich-demo`, `preis-der-fairness-demo`, `zwei-kriterien-demo`, `lexikographisch-demo`): dieselbe Zuordnung, jetzt mit der Frage, **was geschieht, wenn mehrere Pläne gleich gut sind**. Das Ziel wählt dann nicht mehr aus; es entscheidet etwas anderes: die Reihenfolge der Aufzählung, der Löser, die Nummerierung. Ein Plan hat bis zu drei Summen: **A** (Kosten), **B** (Zeit), **C** (Wünsche). Alles ist **simuliert**; keine Aussage über echte Personen, Betriebe oder Lasten.

## Warum dieses Problem

Ein Ziel nennt einen kleinsten Wert, keinen Plan. Gibt es mehrere Pläne mit diesem Wert, wählt irgendetwas Unbenanntes einen davon, und die anderen Kennzahlen des gewählten Plans schwanken, ohne dass es jemand beschlossen hat. Die Fragen: Wie oft kommt das vor? Wie stark streut das Ergebnis unter den gleich guten Plänen? Wie viele Regeln braucht es bis zu einem eindeutigen Plan? Und was verändert sich, wenn man dieselbe Instanz nur **umnummeriert** oder einen anderen **Löser** nimmt?

## Modell

Gegeben Belastungen `a[i][j]`, `b[i][j]`, `c[i][j]` (Zeile Person, Spalte Aufgabe), drei unabhängige Matrizen. Ein Plan ist eine Permutation `π`; `A(π) = Σ a[i][π(i)]`, ebenso `B(π)` und `C(π)`. Drei **Zielarten** auf A: die **Summe**, die **Quadratsumme** `Σ a²` und das **Maximum** `max a`. Die **Optimalmenge** eines Ziels ist die Menge aller Pläne mit dem kleinsten Wert; **Gleichstand** heißt, sie enthält mindestens zwei Pläne. **Regeln**, die einen Plan wählen: der **erste Plan** der Aufzählung (kleinster Index in `itertools.permutations`), der **letzte**, ein **Zufallsplan** (mit Seed), der mit der **kleinsten Nebenkennzahl** (Summe bei Maximum und Quadratsumme, Maximum bei Summe), und die **volle Kette**: erst das Ziel, dann Maximum, Summe, Quadratsumme, die C-Summe und der absteigend sortierte Belastungsvektor (Leximax), jede Ebene nur unter den Plänen der vorigen, ohne Wiederholung; bleibt danach mehr als ein Plan, gilt der erste. Die **Kennzahlen eines Plans** (Summe A, Maximum A, Summe B, Summe C) ändern sich nicht, wenn man Personen und Aufgaben **umnummeriert**; welcher Plan „der erste“ ist, ändert sich sehr wohl. Formeln stehen im 📐-Expander der App.

## Methodik

Fünf Instanzfamilien mit drei unabhängigen Matrizen: **ganze Zahlen 1 bis K** mit K = 3, 9, 99, 999 (je gröber, desto mehr Gleichstände) und **reell gleichverteilt 0 bis 100**. Bis n = 8 werden alle Pläne aufgezählt (bis 40 320, exakt in ganzen Zahlen); darüber vergleicht die App nur Löser. Die Löser sind die Aufzählung (erster Summen-optimaler Plan), die Ungarische Methode (`scipy.optimize.linear_sum_assignment`) und HiGHS (`scipy.optimize.milp`, Voreinstellungen), je mit vertauschter Zeilenreihenfolge der Eingabe (der gewählte Plan wird danach auf die ursprüngliche Nummerierung zurückgerechnet). Die App zeigt: die Optimalmenge je Zielart, die Streuung der Nebenkennzahl darin, alle fünf Regeln nebeneinander, die Kette Ebene für Ebene, das Umnummerieren und die Löser. Zählungen über 20 feste Instanzen liegen hinter Schaltern. Verdikte entstehen live aus der Rechnung, jede Zahl im Text kommt aus dem Ergebnis.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stammen aus den Auswertungsfunktionen der App und sind in `tests/test_claims.py` nachgerechnet. „Je 20 feste Instanzen“ heißt `SWEEP_SEEDS` (Seeds 100000 bis 100019), nie ein einzelner Seed; die Zahlen sind **Zählungen und Spannen über Instanzen**, kein Satz und keine Aussage über andere Instanzen. Soweit nicht anders angegeben n = 8 (alle 40 320 Pläne aufgezählt). Granularität K = 3 / 9 / 99 / 999 / reell.

| Frage | Befund |
|---|---|
| Wie oft gibt es einen Gleichstand? Instanzen mit mindestens zwei besten Plänen, **Summe** | **19 / 13 / 2 / 0 / 0** von 20; Optimalmenge Median **10,0 / 2,5 / 1,0 / 1,0 / 1,0** |
| dasselbe, **Quadratsumme** | **19 / 7 / 0 / 0 / 0** von 20 |
| dasselbe, **Maximum** | **20 / 19 / 16 / 15 / 17** von 20; Optimalmenge Median **26 / 13 / 2 / 2 / 4** (Maximum **3640 / 69 / 61 / 28 / 45**): **auch bei reellen Werten**, weil nur ein einziger Eintrag zählt |
| Wie stark streut die Summe unter den Maximum-optimalen Plänen? | K = 9: Spanne über null in **19** von 19, Median **38,5 %**, Maximum **57,1 %**; K = 99: **16** von 16, Median **19,7 %**, Maximum **80,7 %**; K = 3 nur in **9** von 20 (Maximum **77,8 %**) |
| Reicht „dann die Summe“? Instanzen mit genau einem Plan nach Maximum / + Summe / + Quadratsumme / + C / + Leximax (von 20) | K = 3: **0 / 1 / 1 / 12 / 12**; K = 9: **1 / 10 / 13 / 20 / 20**; K = 99: **4 / 18 / 20 / 20 / 20**; K = 999: **5 / 20 / 20 / 20 / 20** (mittlere Optimalmenge nach dem Maximum **533,5 / 17,9 / 8,1 / 5,7**) |
| Ändert Umnummerieren die Kennzahlen des gewählten Plans? Instanzen von 20, je acht Umnummerierungen, K = 3 / 9 / 99 | Summe, erster Plan: **19 / 13 / 2**; Maximum, erster Plan: **20 / 19 / 16**; Maximum, kleinste Nebenkennzahl: **19 / 10 / 2**; Maximum, volle Kette: **7 / 0 / 0** |
| Wählen die Löser verschiedene Pläne? Instanzen von 20 mit anderem Plan, K = 9, n = 8 | Aufzählung gegen Ungarisch **7**, Aufzählung gegen HiGHS **7**, Ungarisch gegen HiGHS **8**, Ungarisch mit vertauschten Zeilen **7**, HiGHS mit vertauschten Zeilen **7**; jedes Mal mit anderer Summe B |
| dasselbe bei n = 10 / n = 12 | Ungarisch gegen HiGHS **9 / 11**, Ungarisch mit vertauschten Zeilen **7 / 13**, HiGHS mit vertauschten Zeilen **7 / 9** |
| dasselbe bei K = 3 und K = 99, n = 8 | Ungarisch gegen HiGHS **17** und **1**; Ungarisch mit vertauschten Zeilen **16** und **0** |
| Preset „Maximum: viele gleich gute Pläne“ (n = 8, K = 9, Seed 0) | **37** Pläne von 40 320, die Summe reicht von **22** bis **35** (**59,1 %**); Kette **37 / 1 / 1 / 1 / 1**; die fünf Regeln liefern **4** Kennzahlensätze: der erste Plan hat Summe A **30**, die volle Kette **22**; **2** von 4 festen Regeln ändern sich beim Umnummerieren |
| Preset „Kleinstes Beispiel“ (n = 3, K = 3, Seed 22) | **3** gleich gute Pläne von 6, Summe **4** bis **5** (**25,0 %**), Kette **3 / 2 / 2 / 1 / 1**, eindeutig erst nach der C-Summe |
| Preset „Reell: die Summe hat keinen Gleichstand“ (Seed 5) | Summe: **ein** bester Plan; Maximum: **2**, Summe **89,3** bis **101,0** (**13,1 %**); alle Löser wählen denselben Plan |
| Preset „Reell, aber das Maximum hat Gleichstand“ (Seed 2) | **7** Pläne, Summe **179,2** bis **231,6** (**29,2 %**) |
| Preset „Die Kette bleibt uneindeutig“ (K = 3, Seed 3) | Kette **18 / 18 / 18 / 3 / 3**: es bleiben **3** Pläne mit verschiedenen Kennzahlen; bei der Summe als Ziel **18** Pläne, die Löser wählen **4** verschiedene mit Summe B **14**, **15**, **16** |
| Preset „Umnummerieren ändert das Ergebnis“ (Seed 10) | Kette **11 / 3 / 3 / 1 / 1**; **3** von 4 festen Regeln ändern sich, die volle Kette nicht |
| Preset „Löser wählen verschieden“ (Seed 2) | Summe A **17**, vier verschiedene Pläne mit Summe B **41** (Aufzählung), **42** (Ungarisch), **31** (HiGHS) und einem vierten bei vertauschten Zeilen |
| Preset „Löser bei n = 12“ (Seed 2) | Summe A **23**, drei Pläne mit Summe B **47** (HiGHS), **57** (Ungarisch) und **64** (HiGHS, Zeilen vertauscht) |

**Korrektur der Planungshypothese:** Vor der Messung stand „nach dem Maximum entscheidet die Summe“. Das stimmt nur teilweise: bei ganzen Zahlen 1 bis 9 ist der Plan nach „Maximum, dann Summe“ nur in **10** von 20 Instanzen eindeutig, und erst mit der C-Summe in der Kette in allen **20** (der Leximax ändert hier nichts). Außerdem ist „erster Plan“ kein Merkmal des Problems, sondern der Nummerierung: dieselbe Instanz, umnummeriert, liefert andere Kennzahlen. Die Dokumentation sagt zu Gleichständen: NumPy `argmin`/`argmax` liefern „das erste Vorkommen“; Pythons `sorted` ist stabil; die Dokumentation von `scipy.optimize.linear_sum_assignment` und `scipy.optimize.milp` äußert sich nicht dazu, welche von mehreren gleich guten Lösungen zurückkommt.

## Ehrliche Grenzen

- **Fünf Familien, n = 8 bis 12:** Wie oft Gleichstände vorkommen und wie stark das Ergebnis streut, hängt an Granularität und Größe; echte Daten können sich anders verhalten (gerundete Messwerte haben mehr Gleichstände als reelle).
- **Zwei Löser, eine Version:** Die Löser-Zahlen sind Messwerte der Ungarischen Methode (scipy) und von HiGHS über `scipy.optimize.milp` mit Voreinstellungen in der benutzten Version; andere Löser und andere Versionen können anders wählen.
- **Die Aufzählung ist nur eine Regel:** Der „erste Plan“ ist der kleinste Index in der Reihenfolge von `itertools.permutations`. Eine andere Reihenfolge wählt anders.
- **Reell heißt nicht gleichstandsfrei:** Beim Maximum entstehen Gleichstände auch bei reellen Werten; bei der Summe und der Quadratsumme praktisch nicht.
- **Die Kette ist eine Entscheidung:** Die Reihenfolge Maximum, Summe, Quadratsumme, C-Summe, Leximax ist eine Wahl der Demo, nicht die richtige.
- **Gleitkommavergleich:** Bei ganzen Zahlen exakt; bei reellen Werten gilt Gleichheit der berechneten Zahl, und die Kennzahlen eines umnummerierten Plans gelten als gleich mit relativer Toleranz 10⁻⁹ (die Summationsreihenfolge ändert die letzten Bits).

## Verifikation

Insgesamt 410 Tests (`pytest tests/`), alle grün (ein parametrisierter Eigenschaftstest überspringt sich selbst, wenn die Kette einer Instanz mit verschiedenen Kennzahlen endet).

- **Kern:** Handbeispiel (n = 3, sechs Pläne) von Hand: Kennzahlen aller sechs Pläne, Optimalmengen, Kette 4 / 2 / 2 / 1 / 1, alle Regeln, Spanne 6 bis 8, Umnummerieren; Optimalmengen, Regeln, Kette, Spanne, Umnummerierung und Löserwahl gegen reines Python (itertools, Tupelvergleich, ohne numpy im Referenzweg).
- **Eigenschaften:** die Optimalmenge ist nie leer und hält genau das Minimum; jede Kettenebene ist Teilmenge der vorigen und minimal; jede Regel wählt einen Plan der Optimalmenge; die Größen der Optimalmengen und die Kennzahlen aller Pläne bleiben beim Umnummerieren; die volle Kette ändert ihre Kennzahlen beim Umnummerieren nicht, wenn ihr Rest gleiche Kennzahlen hat; Determinismus.
- **Randfälle:** n = 3 bis 12, konstante Matrix (alle Pläne gleich gut), Nullspanne, Aufzählungsgrenze n = 8 / 9, unbekannte Regel, Wertebereiche je Granularität.
- **Verdikte:** reine Funktionen, jede Verzweigung und jede Zahl im Text an Hand- oder Presetwerten (`tests/test_verdicts.py`).
- **Presets:** Vollständigkeit, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung, kein anderes Preset gleich den Voreinstellungen, und dass jedes Preset zeigt, was sein Name sagt.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), jedes Preset, jedes Ziel, jede Granularität, Größen um die Aufzählungsgrenze, alle Schalter, Footer-Test, Layout.
- **Claims:** jede Zahl dieser README in `tests/test_claims.py`.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `gst_algorithm.py` | Kern: Aufzählung, Kennzahlen, Optimalmenge, Kette, Regeln, Spanne, Ungarische Methode, HiGHS |
| `gst_constants.py` | Regler-Grenzen, feste Annahmen, Farben, Presets |
| `gst_evaluation.py` | Experimente, Sweeps, Verdikte |
| `gst_layout.py` | Fester Kopf (Stylesheet) |
| `gst_pdf_export.py` | PDF-Export des Ergebnisses |
| `gst_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `gst_scenario.py` | Instanzen (drei Matrizen, fünf Granularitäten), Umnummerieren |
| `gst_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handbeispiel, Orakel, Eigenschaften, Randfälle, Verdikte, Presets, Claims, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Kein Weg, Gleichstände zu vermeiden:** Wie man das Ziel so umbaut, dass es hart oder weich gegen eine zweite Größe entscheidet, ist Stück 6.
- **Keine anderen Löser:** Gurobi, CP-SAT und andere Löser sind nicht gemessen.
- **Keine Zählung aller Optimalpläne bei n > 8:** darüber vergleicht die App nur die Wahl der Löser.
- **Keine Regel „Zufall“ in den Zählungen:** der Zufallsplan hängt am Seed und ist in den Tabellen der App, nicht in den Zählungen über Instanzen.
- **Kein Zweikriterien- und kein Prioritätennachbau:** Pareto-Front, Hülle und ε-Constraint sind Stück 3, Vorrang und Gewicht Stück 4.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).

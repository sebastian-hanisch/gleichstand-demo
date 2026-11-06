"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 3, 12, 8
ENUM_MAX = 8                                  # bis hierher werden alle n! Pläne aufgezählt (exakt in ganzen Zahlen)
SEED_MAX, DEFAULT_SEED = 999999, 0
GRANULARITIES = (3, 9, 99, 999, 0)            # ganze Zahlen 1 bis K; 0: reell gleichverteilt 0 bis 100
FAMILIES = ("Ganze Zahlen 1 bis 3", "Ganze Zahlen 1 bis 9", "Ganze Zahlen 1 bis 99", "Ganze Zahlen 1 bis 999", "Reell gleichverteilt 0 bis 100")
DEFAULT_FAMILY = 1

OBJECTIVES = ("sum", "sq", "max")
OBJECTIVE_NAMES = {"sum": "Summe", "sq": "Quadratsumme", "max": "Maximum"}
DEFAULT_OBJECTIVE = 2
CHAIN_KEYS = ("max", "sum", "sq", "sumC", "sorted")   # Standardreihenfolge der Kette; das gewählte Ziel rückt nach vorn
CHAIN_NAMES = {"max": "Maximum", "sum": "Summe", "sq": "Quadratsumme", "sumC": "C-Summe", "sorted": "Leximax"}
SECONDARY = {"sum": "max", "sq": "sum", "max": "sum"}
RULES = ("first", "last", "random", "secondary", "chain")
RULE_NAMES = {"first": "erster Plan", "last": "letzter Plan", "random": "Zufall (Seed)", "secondary": "kleinste Nebenkennzahl, dann erster", "chain": "volle Kette, dann erster"}
VALUE_NAMES = ("Summe A", "Maximum A", "Summe B", "Summe C")

SWEEP_SEEDS = tuple(range(100000, 100020))    # feste Instanzen für alle Sweeps: nie ein einzelner Seed als Befund
SWEEP_N = 8                                   # Instanzgröße der Sweeps (alle aufgezählt)
SWEEP_KS = (3, 9, 99, 999, 0)
RELABEL_COUNT = 8                             # Umnummerierungen je Instanz im Sweep
SOLVER_CASES = ((8, 3), (8, 9), (8, 99), (10, 9), (12, 9))   # (n, K) der Löser-Tabelle

COLOR_ALL = "rgba(150,150,150,0.35)"
COLOR_OPT = "#4c78a8"
COLOR_OK = "#2F6B65"
COLOR_BAD = "#c0504d"
COLOR_MARK = "#d8a13a"

PRESETS = {
    "Maximum: viele gleich gute Pläne (n = 8)": {"n": 8, "family": 1, "seed": 0},
    "Kleinstes Beispiel (n = 3, ganze Zahlen 1 bis 3)": {"n": 3, "family": 0, "seed": 22},
    "Reell: die Summe hat keinen Gleichstand": {"n": 8, "family": 4, "seed": 5},
    "Reell, aber das Maximum hat Gleichstand": {"n": 8, "family": 4, "seed": 2},
    "Die Kette bleibt uneindeutig (ganze Zahlen 1 bis 3)": {"n": 8, "family": 0, "seed": 3},
    "Umnummerieren ändert das Ergebnis": {"n": 8, "family": 1, "seed": 10},
    "Löser wählen verschieden (n = 8)": {"n": 8, "family": 1, "seed": 2},
    "Löser bei n = 12": {"n": 12, "family": 1, "seed": 2},
}
PRESET_HELP = {
    "Maximum: viele gleich gute Pläne (n = 8)": "37 Pläne haben dasselbe kleinste Maximum, und die Summe streut unter ihnen um 59 %.",
    "Kleinstes Beispiel (n = 3, ganze Zahlen 1 bis 3)": "Sechs Pläne: drei gleich gute beim Maximum, danach zwei, dann entscheidet erst die C-Summe.",
    "Reell: die Summe hat keinen Gleichstand": "Bei reellen Werten hat die Summe genau einen besten Plan, das Maximum aber zwei: nur ein einziger Eintrag zählt.",
    "Reell, aber das Maximum hat Gleichstand": "Sieben Pläne haben dasselbe kleinste Maximum, obwohl alle Werte reell sind.",
    "Die Kette bleibt uneindeutig (ganze Zahlen 1 bis 3)": "Nach Maximum, Summe, Quadratsumme und C bleiben noch drei Pläne mit verschiedenen Kennzahlen: nur die Nummerierung entscheidet.",
    "Umnummerieren ändert das Ergebnis": "Derselbe Sachverhalt mit anderen Nummern: „erster Plan“ wählt andere Kennzahlen, die volle Kette nicht.",
    "Löser wählen verschieden (n = 8)": "Aufzählung, Ungarische Methode und HiGHS wählen drei Pläne mit derselben Summe A, aber Summe B 41, 42 und 31.",
    "Löser bei n = 12": "Zu groß zum Aufzählen: Ungarische Methode und HiGHS wählen verschiedene Pläne, und das Vertauschen der Zeilen ändert die Wahl.",
}

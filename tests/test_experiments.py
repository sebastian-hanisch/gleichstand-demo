"""Experimente der App: jedes Preset, jedes Ziel, jede Granularität, jede Größe und alle Sweeps laufen ohne Fehler."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import gst_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for kind in ("success", "info", "warning") for m in getattr(at, kind))


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, (name, [str(e) for e in at.exception])
    text = _texts(at)
    assert "gleich gute Pläne" in text or "genau einen" in text or "verschiedene Pläne" in text


def test_default_preset_shows_the_thirty_seven_plans():
    assert "**37** gleich gute Pläne" in _texts(_app())


@pytest.mark.parametrize("objective", list(C.OBJECTIVES))
def test_every_objective_runs_and_is_named(objective):
    at = _app()
    at.radio(key="objective_select").set_value(objective).run()
    assert not at.exception, [str(e) for e in at.exception]
    assert C.OBJECTIVE_NAMES[objective] in _texts(at)


@pytest.mark.parametrize("family", range(len(C.FAMILIES)))
def test_every_granularity_runs(family):
    at = _app()
    at.sidebar.selectbox(key="family_select").set_value(family).run()
    assert not at.exception, [str(e) for e in at.exception]


@pytest.mark.parametrize("n", [3, 8, 9, 12])
def test_sizes_around_the_enumeration_limit_switch_the_experiments(n):
    at = _app()
    at.sidebar.slider(key="n_slider").set_value(n).run()
    assert not at.exception, [str(e) for e in at.exception]
    text = _texts(at) + " ".join(m.value for m in at.markdown)
    if n > C.ENUM_MAX:
        assert "Aufzählung" in text and "verschiedene Pläne" in _texts(at)
    else:
        assert "gleich gute Pläne" in _texts(at) or "genau einen" in _texts(at)


def test_the_random_rule_and_relabel_seeds_run():
    at = _app()
    at.number_input(key="rule_seed").set_value(17).run()
    at.number_input(key="relabel_seed").set_value(23).run()
    assert not at.exception, [str(e) for e in at.exception]


def test_the_sweeps_run_when_switched_on():
    at = _app()
    for key in ("sweep_ties", "sweep_chain", "sweep_relabel", "sweep_solver"):
        at.toggle(key=key).set_value(True).run()
        assert not at.exception, (key, [str(e) for e in at.exception])
    text = _texts(at)
    assert "je 20 feste Instanzen" in text and "Kette bis zur Eindeutigkeit" in text and "Umnummerieren" in text and "Instanzen von 20 mit anderem Plan" in text

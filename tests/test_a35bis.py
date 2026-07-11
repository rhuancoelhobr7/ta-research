# -*- coding: utf-8 -*-
"""Testes do a35-bis: move_at (Δíndice até offset) e build_obs (sustains)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a35bis_persistencia import move_at, build_obs


def _idx():
    t = pd.date_range("2020-01-01 00:00", periods=36, freq="5min")
    idx = pd.DataFrame({c: np.zeros(36) for c in G8}, index=t)
    # GBP sobe e continua subindo (sustenta +); JPY sobe cedo e inverte (nao sustenta)
    idx["GBP"] = np.linspace(0, 1, 36)
    idx["JPY"] = np.concatenate([np.linspace(0, 1, 12), np.linspace(1, -2, 24)])
    return idx


def test_move_at():
    m = move_at(_idx(), offset=60)      # primeiras 12 barras (1h)
    d = pd.Timestamp("2020-01-01")
    assert m.loc[d, "GBP"] > 0
    assert m.loc[d, "USD"] == 0.0


def test_build_obs_sustains():
    obs = build_obs(_idx(), k=60, fim=180)
    g = obs.set_index("cur")
    assert g.loc["GBP", "sustains"] == 1      # + em k e no fim
    assert g.loc["JPY", "sustains"] == 0      # + em k, - no fim (inverteu)
    assert g.loc["JPY", "residual"] < 0       # dir=+ mas moveu p/ baixo

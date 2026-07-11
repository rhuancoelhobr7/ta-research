# -*- coding: utf-8 -*-
"""Testes do a36: sign_at (sinal do Δíndice desde a abertura até offset)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a36_direcao import sign_at


def test_sign_at():
    t = pd.date_range("2020-01-01 00:00", periods=24, freq="5min")
    idx = pd.DataFrame({c: np.zeros(24) for c in G8}, index=t)
    idx["GBP"] = np.linspace(0, 1, 24)      # sobe -> sinal +
    idx["JPY"] = np.linspace(0, -1, 24)     # cai -> sinal -
    s = sign_at(idx, offset=60)             # primeira 1h
    d = pd.Timestamp("2020-01-01")
    assert s.loc[d, "GBP"] == 1.0
    assert s.loc[d, "JPY"] == -1.0
    assert s.loc[d, "USD"] == 0.0           # plano -> 0

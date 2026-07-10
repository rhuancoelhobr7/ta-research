# -*- coding: utf-8 -*-
"""Testes do a28: transição de liderança e painel de líderes por dia."""
import itertools

import numpy as np
import pandas as pd

from preponderante import G8
from a28_preponderante import transition, leaders_panel


def test_transition():
    a = pd.Series(["GBP", "EUR", "JPY", "USD"],
                  index=pd.date_range("2020-01-01", periods=4))
    b = pd.Series(["GBP", "EUR", "AUD", "CHF"],
                  index=pd.date_range("2020-01-01", periods=4))
    assert abs(transition(a, b) - 0.5) < 1e-9      # 2/4 coincidem


def _net_wide(strength_by_date):
    """net_wide (date x par) via modelo linear net=s[base]-s[quote]."""
    pairs = ["".join(c) for c in itertools.combinations(G8, 2)]
    rows = {}
    for date, s in strength_by_date.items():
        rows[date] = {p: s[p[:3]] - s[p[3:6]] for p in pairs}
    return pd.DataFrame(rows).T, pd.Series({p: 1.0 for p in pairs})


def test_leaders_panel_identifica_lider():
    d1, d2 = pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")
    base = {c: 0.0 for c in G8}
    s1 = {**base, "GBP": 10, "JPY": -8}
    s2 = {**base, "AUD": 9, "CHF": -6}
    nw, norm = _net_wide({d1: s1, d2: s2})
    pan = leaders_panel(nw, norm)
    assert pan.loc[d1, "leader"] == "GBP" and pan.loc[d1, "anti_leader"] == "JPY"
    assert pan.loc[d2, "leader"] == "AUD" and pan.loc[d2, "anti_leader"] == "CHF"
    assert pan.loc[d1, "leader_consist"] == 7      # GBP bate os 7

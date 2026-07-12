# -*- coding: utf-8 -*-
"""Testes do a43: backtest de amplitude e escolha operável do dia (pick_hoje)."""
import numpy as np
import pandas as pd

from a43_produto import backtest, pick_hoje


def test_backtest_metricas():
    ev = pd.DataFrame({"net1": [10.0, 20.0, 30.0], "eff1": [50.0, 60.0, 70.0],
                       "is_max": [1, 0, 1], "pct_ceil": [0.8, 0.6, 0.9]},
                      index=pd.date_range("2020-01-01", periods=3))
    b = backtest(ev, "X")
    assert abs(b["amp_liq_media_pips"] - 20.0) < 1e-9
    assert b["menor_amp_dia"] == 10.0
    assert abs(b["P(top1=maior_range)"] - 2/3) < 1e-9
    assert "maxDD_pips" not in b and "pior_dia" not in b       # métricas de risco removidas


def test_pick_hoje_ordena_por_modo():
    d = pd.date_range("2020-01-01", periods=2)
    A = pd.DataFrame({"GBPJPY": [50, 100], "EURCHF": [10, 20], "AUDNZD": [30, 40]},
                     index=d)                                   # último dia: GBPJPY maior
    Z = pd.DataFrame({"GBPJPY": [0, 0.1], "EURCHF": [0, 3.0], "AUDNZD": [0, 1.0]},
                     index=d)                                   # z-ATR: EURCHF maior
    scores = {"A": A, "Z250": Z}
    spread = {"GBPJPY": 1.0, "EURCHF": 0.2, "AUDNZD": 0.5}
    last, top_amp, top_efi = pick_hoje(scores, None, spread)
    assert last == d[-1]
    assert top_amp.index[0] == "GBPJPY"                        # modo amplitude: maior ATR
    assert top_efi.index[0] == "EURCHF"                        # modo eficiência: maior z-ATR

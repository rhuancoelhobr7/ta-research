# -*- coding: utf-8 -*-
"""Testes do a23: correção Benjamini-Hochberg e Q4/transição num painel
sintético onde asia prevê londres por construção."""
import numpy as np
import pandas as pd

from a23_intersessao import bh_reject, q4, transition_matrix


def test_bh_reject():
    # todos altos -> nenhuma rejeição; um zero -> pelo menos ele rejeita
    assert not bh_reject(np.array([0.9, 0.8, 0.7])).any()
    rej = bh_reject(np.array([0.0001, 0.9, 0.8, 0.7]))
    assert rej[0] and not rej[1:].any()
    # monotonicidade BH: p ordenados <= alpha*i/n
    p = np.array([0.001, 0.008, 0.02, 0.5])
    assert bh_reject(p, 0.05).sum() >= 1


def _panel_asia_preve_londres(n=400, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for pair in ("EURUSD", "GBPJPY"):
        dates = pd.date_range("2020-01-01", periods=n)
        asia = rng.lognormal(3, 0.5, n)
        londres = asia * 0.8 + rng.lognormal(2.5, 0.4, n)   # londres ~ asia
        rows.append(pd.DataFrame({"pair": pair, "date": dates, "asia": asia,
                                  "londres": londres, "ny": londres,
                                  "overlap": londres * 0.5,
                                  "day_range": asia + londres}))
    return pd.concat(rows, ignore_index=True)


def test_q4_detecta_autocorrelacao():
    tab, summ = q4(_panel_asia_preve_londres())
    assert summ["asia_londres_med"] > 0.3      # correlação forte por construção
    assert summ["n_signif_bh"] == summ["n_pairs"]


def test_transition_diagonal_pesada():
    ct = transition_matrix(_panel_asia_preve_londres())
    # P(londres Q4 | asia Q4) > P(londres Q4 | asia Q1): vol persiste
    assert ct.loc["asia_Q4", "lon_Q4"] > ct.loc["asia_Q1", "lon_Q4"]

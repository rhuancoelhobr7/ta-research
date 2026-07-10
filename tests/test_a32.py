# -*- coding: utf-8 -*-
"""Testes do a32: Spearman por célula (mesmo dia e wrap-around dia+1)."""
import numpy as np
import pandas as pd

from a32_matriz_sessoes import cell_spearman


def _wide(n=400, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n)
    asia = rng.uniform(10, 100, n)
    return pd.DataFrame({"asia": asia,
                         "londres": asia + rng.normal(0, 1, n),   # ~ asia (mesmo dia)
                         "ny": np.r_[asia[1:], asia[0]]},          # ny[d] = asia[d+1]
                        index=idx)


def test_cell_mesmo_dia():
    w = _wide()
    cut = w.index.to_series().quantile(0.0)        # usa tudo
    r = cell_spearman(w, "asia", "londres", False, cut)
    assert r > 0.95                                # londres ~ asia no mesmo dia


def test_cell_wrap_dia_seguinte():
    w = _wide()
    cut = w.index.to_series().quantile(0.0)
    # ny[d] == asia[d+1]; asia.shift(-1)[d] == asia[d+1] -> correlação ~1
    r = cell_spearman(w, "ny", "asia", True, cut)
    assert r > 0.95


def test_cell_amostra_insuficiente():
    w = _wide(n=50)
    cut = w.index.to_series().quantile(0.70)       # teste < 100 -> NaN
    assert np.isnan(cell_spearman(w, "asia", "londres", False, cut))

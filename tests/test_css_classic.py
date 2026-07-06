# -*- coding: utf-8 -*-
"""Testes do porte do CSS clássico (css_classic.py) — sintéticos + anti-lookahead."""
import numpy as np
import pandas as pd
import pytest

from css_classic import G8, css_geometry, css_lines, pair_slope, tma_causal

PARES_USD = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]


def _closes(n=400, seed=7, trend_eur=0.0):
    """Universo sintético dos 7 pares USD; EURUSD pode receber deriva."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-01-02", periods=n, freq="h")
    data = {}
    for sym in PARES_USD:
        r = rng.normal(0, 1e-4, n)
        if sym == "EURUSD":
            r = r + trend_eur
        data[sym] = 1.10 * np.exp(np.cumsum(r))
    return pd.DataFrame(data, index=idx)


def test_tma_causal_nao_repinta():
    """TMA causal: valor em t não muda quando chegam barras futuras."""
    c = _closes()["EURUSD"]
    full = tma_causal(c, 14)
    cut = tma_causal(c.iloc[:300], 14)
    pd.testing.assert_series_equal(full.iloc[:300], cut)


def test_pair_slope_sinal():
    """Par em alta constante → slope positivo; em queda → negativo."""
    idx = pd.date_range("2024-01-02", periods=200, freq="h")
    up = pd.Series(np.linspace(1.0, 1.2, 200), index=idx)
    dn = pd.Series(np.linspace(1.2, 1.0, 200), index=idx)
    assert pair_slope(up, 14, 3).iloc[-1] > 0
    assert pair_slope(dn, 14, 3).iloc[-1] < 0


def test_css_lines_direcao_e_orientacao():
    """EUR com deriva de alta → linha EUR positiva e a mais forte."""
    lines = css_lines(_closes(trend_eur=5e-4), per=14, suav=3)
    last = lines.dropna().iloc[-1]
    assert last["EUR"] > 0
    assert last.abs().idxmax() == "EUR"


def test_normalizacao_por_barra():
    """Em toda barra válida, max|valor| == 2*box (ranking relativo)."""
    lines = css_lines(_closes(), per=14, suav=3, box=0.2).dropna()
    max_abs = lines.abs().max(axis=1)
    assert np.allclose(max_abs.to_numpy(), 0.4, atol=1e-12)


def test_css_lines_anti_lookahead():
    """Linha em t idêntica com ou sem as barras futuras no input.

    A normalização é por barra (cross-sectional, mesma barra) — não pode
    vazar futuro. Este teste trava isso para sempre.
    """
    closes = _closes()
    full = css_lines(closes, per=14, suav=3)
    cut = css_lines(closes.iloc[:300], per=14, suav=3)
    pd.testing.assert_frame_equal(full.iloc[:300], cut)


def test_geometry_consistencia():
    """fora_box/dist_box/dist_zero coerentes entre si; dline = diff k."""
    lines = css_lines(_closes(trend_eur=5e-4)).dropna()
    g = css_geometry(lines, box=0.2, k_slope=3)
    assert ((g["dist_box"] >= 0) == (g["fora_box"] == 1.0)).all().all()
    assert (g["dist_zero"] >= g["dist_box"]).all().all()
    pd.testing.assert_frame_equal(g["dline"], lines - lines.shift(3))


def test_moeda_fora_do_g8_ignorada():
    """Símbolo com moeda fora do G8 não entra na conta."""
    closes = _closes()
    closes["XAUUSD"] = 2000.0
    a = css_lines(closes.drop(columns="XAUUSD"))
    b = css_lines(closes)
    pd.testing.assert_frame_equal(a, b)

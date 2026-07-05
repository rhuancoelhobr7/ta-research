"""Validação sintética da camada relacional (r1).

Cenário 1 — tendência absoluta genuína: EUR com drift latente forte.
  A matriz deve mostrar a linha do EUR ativa contra a maioria das contrapartes,
  breadth hard alto, e EUR como líder do nowcast.

Cenário 2 — contaminação cruzada (o argumento central da camada):
  APENAS o JPY colapsa. Os índices agregados das outras 7 moedas ganham força
  espúria (todas "sobem" contra a cesta), mas a matriz desambigua: a linha do
  JPY fica ativa contra ~todos, enquanto as linhas das outras moedas, excluindo
  a coluna JPY, permanecem em Ruído. O breadth hard identifica o verdadeiro
  protagonista.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from cssm_engine import G8, CssmParams, compute_currency, build_indices
from r1_relational import (pair_features, matrix_at, breadth_series,
                           calibrate_gate)


def make_closes(drifts: dict[str, float], T=6000, seed=5, vol=6e-4):
    rng = np.random.default_rng(seed)
    dt = pd.date_range("2025-01-06", periods=T, freq="1h")
    strength = {}
    for c in G8:
        r = rng.normal(0, vol, T)
        r[T // 2:] += drifts.get(c, 0.0)          # drift na 2ª metade
        strength[c] = np.cumsum(r)
    closes = {}
    for i in range(8):
        for j in range(i + 1, 8):
            closes[G8[i] + G8[j]] = pd.Series(
                np.exp(strength[G8[i]] - strength[G8[j]]), index=dt)
    return closes


@pytest.fixture(scope="module")
def gates():
    g = calibrate_gate(64, 0.05, n_walks=10, bars=8000)
    return g


def _setup(drifts, gates):
    p = CssmParams(w_mid=64, w_fast=16, z_win=500, t_gate=gates,
                   t_low=gates * 0.6)
    closes = make_closes(drifts)
    pf = pair_features(closes, p)
    idx = build_indices(closes, align="inner")
    idxf = {c: compute_currency(idx[c], p) for c in G8}
    ts = pf["USDEUR" if "USDEUR" in pf else "USDJPY"].index[-1]
    return closes, pf, idxf, ts, p


def test_scenario1_genuine_absolute_trend(gates):
    closes, pf, idxf, ts, p = _setup({"EUR": +4e-4}, gates)
    mx = matrix_at(pf, ts)
    eur = mx[mx.base == "EUR"]
    active_up = ((eur.state >= 1) & (eur["dir"] > 0)).sum()
    assert active_up >= 5, f"linha EUR ativa contra só {active_up}/7"
    br = breadth_series(pf, idxf, p.t_gate)
    last = br[br.ts == ts].sort_values("nowcast", ascending=False)
    assert last.iloc[0].currency == "EUR"
    assert last.iloc[0].breadth_hard >= 5 / 7


def test_scenario2_cross_contamination(gates):
    """JPY colapsa sozinho: a matriz desambigua o que o agregado confunde."""
    closes, pf, idxf, ts, p = _setup({"JPY": -6e-4}, gates)

    # 1) o agregado das inocentes infla: t do índice > 0 p/ maioria delas
    others = [c for c in G8 if c != "JPY"]
    t_idx = {c: idxf[c]["t"].loc[ts] for c in others}
    inflated = sum(1 for c in others if t_idx[c] > 0)
    assert inflated >= 5, "esperava inflação espúria nos índices agregados"

    # 2) mas a matriz desambigua: a linha do JPY está ativa contra ~todos,
    #    enquanto as inocentes (excluindo a coluna JPY) ficam, em média, quietas
    #    (silêncio absoluto não é exigível: random walks geram tendências
    #    genuínas ocasionais, que a matriz corretamente reporta)
    mx = matrix_at(pf, ts)
    jpy_row = mx[mx.base == "JPY"]
    jpy_active = ((jpy_row.state >= 1) & (jpy_row["dir"] < 0)).sum()
    assert jpy_active >= 6, f"linha JPY ativa contra só {jpy_active}/7"
    frac_active = []
    for c in others:
        row = mx[(mx.base == c) & (mx.vs != "JPY")]
        frac_active.append((row.state >= 1).mean())
    assert np.mean(frac_active) <= 0.35, \
        f"inocentes ativas demais em média: {np.mean(frac_active):.0%}"
    assert jpy_active / 7 > np.mean(frac_active) + 0.4, \
        "a linha do protagonista deveria separar com folga das inocentes"

    # 3) e o breadth hard aponta o verdadeiro protagonista
    br = breadth_series(pf, idxf, p.t_gate)
    last = br[br.ts == ts]
    jpy = last[last.currency == "JPY"].iloc[0]
    assert jpy["dir"] < 0 and jpy.breadth_hard >= 6 / 7
    worst_innocent = last[last.currency != "JPY"].breadth_hard.max()
    assert jpy.breadth_hard > worst_innocent + 0.4, \
        "breadth hard deveria separar protagonista de inocentes com folga"


def test_matrix_antisymmetry(gates):
    """Célula (A,B) deve ser o espelho de (B,A): t e M com sinais opostos."""
    closes, pf, idxf, ts, p = _setup({"GBP": +3e-4}, gates)
    mx = matrix_at(pf, ts)
    for a, b in [("GBP", "JPY"), ("EUR", "USD"), ("AUD", "NZD")]:
        ab = mx[(mx.base == a) & (mx.vs == b)].iloc[0]
        ba = mx[(mx.base == b) & (mx.vs == a)].iloc[0]
        assert ab.t == pytest.approx(-ba.t, abs=1e-12)
        assert ab.M == pytest.approx(-ba.M, abs=1e-12)
        assert ab.state == ba.state

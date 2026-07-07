# -*- coding: utf-8 -*-
"""Testes do a17 — t_lock/t_half sintéticos + anti-lookahead da R-CONF."""
import numpy as np
import pandas as pd

from a17_trava import (frac_restante, rconf_features, t_half_minutes,
                       t_lock_minutes)
from cssm_engine import G8, build_indices


def _cum(vals, freq="5min"):
    idx = pd.date_range("2026-03-03 00:00", periods=len(vals), freq=freq)
    return pd.Series(vals, index=idx)


def test_t_lock_tres_cruzamentos():
    """Série que cruza zero 3x e trava → t_lock = instante do 3º cruzamento."""
    cum = _cum([0.0, 1, -1, 1, -1, 2, 3, 4, 5])   # vira em i=2,3,4,5
    assert t_lock_minutes(cum) == 5 * 5.0          # último cruz.: i=5 (−1→2)


def test_t_lock_monotonica():
    """Série monotônica (nunca vira) → t_lock = primeira barra (0 min)."""
    cum = _cum([0.0, 1, 2, 3, 4, 5])
    assert t_lock_minutes(cum) == 0.0


def test_t_lock_com_zeros_exatos():
    """Zeros exatos não contam como cruzamento (propaga sinal anterior)."""
    cum = _cum([0.0, 1, 0, 1, 2, 3])               # toca zero mas não vira
    assert t_lock_minutes(cum) == 0.0


def test_t_half():
    """Primeiro |cum| >= 50% do final."""
    cum = _cum([0.0, 1, 2, 5, 6, 10])              # final=10; 50%=5 em i=3
    assert t_half_minutes(cum) == 3 * 5.0


def test_frac_restante():
    """Fração orientada do movimento que falta em T0+h."""
    idx = pd.date_range("2026-03-03 00:00", periods=25, freq="h")
    cum = pd.Series(np.linspace(0, 10, 25), index=idx)   # linear, 12h=5
    # em T0+6h cum=2.5 -> falta 7.5/10
    assert abs(frac_restante(cum, 6) - 0.75) < 1e-9


def test_rconf_anti_lookahead():
    """Truncar os dados DEPOIS de T0+k não muda a previsão da R-CONF(k).

    Mesmo estilo do test_no_leakage do v3: gera closes sintéticos, roda a
    R-CONF, corta tudo após T0+k, roda de novo e exige igualdade.
    """
    rng = np.random.default_rng(5)
    idx = pd.date_range("2026-02-02", "2026-03-06 23:55", freq="5min")
    idx = idx[idx.dayofweek < 5]
    pares = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
    closes = {p: pd.Series(np.exp(np.cumsum(rng.normal(0, 2e-4, len(idx)))),
                           index=idx) for p in pares}
    indices = build_indices(closes, align="inner")
    days = pd.DatetimeIndex(sorted(set(idx.normalize())))[15:20]

    # vol63 vem de dias anteriores aos avaliados (shift(1) já na função)
    fr = pd.DataFrame(rng.normal(0, 1e-3, (60, 8)),
                      index=pd.date_range("2025-11-01", periods=60, freq="B"),
                      columns=G8)
    full = pd.concat([fr, pd.DataFrame(np.nan, index=days, columns=G8)])

    k = 2
    a = rconf_features(closes, indices, days, k, full)

    day = days[2]
    cut = day + pd.Timedelta(hours=k)
    closes_cut = {p: s.loc[:cut] for p, s in closes.items()}
    indices_cut = build_indices(closes_cut, align="inner")
    b = rconf_features(closes_cut, indices_cut, [day], k, full)

    assert a[day] == b[day]

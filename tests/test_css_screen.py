# -*- coding: utf-8 -*-
"""Testes do css_screen — golden values calculados à mão (fórmulas do MQ5),
causalidade, clamp, orientação e a geometria da escala fixa."""
import numpy as np
import pandas as pd
import pytest

import css_screen as m
from css_classic import G8


def _series(n=140, seed=3, drift=0.0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2026-01-01", periods=n, freq="h")
    return pd.Series(1.10 * np.exp(np.cumsum(rng.normal(drift, 1e-4, n))),
                     index=idx)


# ----------------------------------------------------------------------------
# Golden values — réplica explícita da aritmética do MQ5 (cl em serie)
# ----------------------------------------------------------------------------

def _tma_mq5(cl_series: np.ndarray, i: int) -> float:
    """Cópia literal do TMA() do v2.20: cl[0]=atual, i=shift do candle."""
    copied = len(cl_series)
    s = cl_series[i] * 21.0
    w = 21.0
    jnx, knx = 1, 20
    while jnx <= 20:
        back = i + jnx
        if back < copied:
            s += cl_series[back] * knx
            w += knx
        if jnx <= i:
            fwd = i - jnx
            if fwd >= 0:
                s += cl_series[fwd] * knx
                w += knx
        jnx += 1
        knx -= 1
    return s / w


def _atrrel_mq5(cl_series: np.ndarray, per: int = 100,
                add_sunday: bool = True) -> float:
    """Cópia literal do ATRrel() do v2.20."""
    copied = len(cl_series)
    shift = 10 + (1 if add_sunday else 0)
    n = min(per, copied - 1 - shift)
    s, cnt = 0.0, 0
    for i in range(shift, shift + n):
        if i + 1 >= copied:
            break
        s += abs(cl_series[i] - cl_series[i + 1])
        cnt += 1
    atr = (s / cnt) / 10.0
    return atr / cl_series[0]


def test_golden_tma_live():
    """tma0/tma1 da última barra == TMA MQ5 em shift 0 e 1."""
    c = _series()
    cl = c.to_numpy()[::-1]                    # ordem "series" do MQ5
    tma0, tma1 = m.tma_live(c)
    assert np.isclose(tma0.iloc[-1], _tma_mq5(cl, 0), rtol=1e-12)
    assert np.isclose(tma1.iloc[-1], _tma_mq5(cl, 1), rtol=1e-12)


def test_golden_atrrel():
    c = _series()
    got = m.atr_rel(c).iloc[-1]
    assert np.isclose(got, _atrrel_mq5(c.to_numpy()[::-1]), rtol=1e-12)


def test_golden_contribution_formula():
    """Perna completa: z=((tma0−tma1)/price)/(ATRrel·√1); val=clamp(z·0.40)."""
    c = _series()
    cl = c.to_numpy()[::-1]
    z = ((_tma_mq5(cl, 0) - _tma_mq5(cl, 1)) / cl[0]) / \
        (_atrrel_mq5(cl) * 1.0 + 1e-12)
    esperado = np.clip(z * 0.40, -0.98, 0.98)
    assert np.isclose(m.pair_contribution(c).iloc[-1], esperado, rtol=1e-9)


# ----------------------------------------------------------------------------
# Causalidade, clamp, orientação
# ----------------------------------------------------------------------------

def test_causalidade():
    """Perturbar o futuro não muda a leitura passada (série 'ao vivo')."""
    c = _series(200)
    a = m.pair_contribution(c)
    c2 = c.copy()
    c2.iloc[150:] *= 1.10
    b = m.pair_contribution(c2)
    pd.testing.assert_series_equal(a.iloc[:150], b.iloc[:150])


def test_clamp():
    """Salto brutal satura a contribuição em ±(1.00−0.02)."""
    c = _series(140)
    c.iloc[-1] *= 1.5
    assert m.pair_contribution(c).iloc[-1] == pytest.approx(0.98)
    c.iloc[-1] /= 2.5
    assert m.pair_contribution(c).iloc[-1] == pytest.approx(-0.98)


def test_orientacao_base_quote():
    """EURUSD em alta → EUR positivo, USD negativo (espelhados, 1 par)."""
    closes = pd.DataFrame({"EURUSD": _series(drift=3e-4)})
    lines = m.css_screen_lines(closes)
    last = lines.dropna(how="all").iloc[-1]
    assert last["EUR"] > 0 and last["USD"] < 0
    assert np.isclose(last["EUR"], -last["USD"])


# ----------------------------------------------------------------------------
# Geometria da escala FIXA — o caso que não existe no css_classic
# ----------------------------------------------------------------------------

def test_mercado_lateral_todas_dentro_da_box():
    """Mercado lateral (oscilação sem direção): TODAS as moedas dentro da
    box. A TMA(21) achata a oscilação (slope→0) enquanto o ATR permanece
    cheio → z≈0 na escala FIXA. No css_classic (renormalizado por barra)
    SEMPRE existe moeda em ±0.4 — este teste trava a diferença de
    geometria que motivou o a12b/a13b.

    Nota honesta: um random walk quieto NÃO fica dentro da box — o z é
    adimensional (slope e ATR encolhem juntos). O que zera o CSS da tela
    é ausência de DIREÇÃO, não de volatilidade."""
    idx = pd.date_range("2026-01-01", periods=300, freq="h")
    t = np.arange(300)
    osc = np.sin(2 * np.pi * t / 4.0)          # período 4 barras, sem deriva
    closes = {}
    for a in ["EUR", "GBP", "AUD", "NZD"]:
        closes[f"{a}USD"] = pd.Series(1.2 + 1e-3 * osc, index=idx)
    for q in ["JPY", "CHF", "CAD"]:
        closes[f"USD{q}"] = pd.Series(120 + 0.1 * osc, index=idx)
    lines = m.css_screen_lines(pd.DataFrame(closes))
    g = m.css_screen_geometry(lines)
    valid = lines.dropna()
    assert len(valid) > 100
    assert g["fora_box"].loc[valid.index].to_numpy().sum() == 0


def test_geometry_features_iguais_a13():
    """css_screen_geometry entrega exatamente as features do a13."""
    lines = m.css_screen_lines(
        pd.DataFrame({"EURUSD": _series(drift=2e-4)}))
    g = m.css_screen_geometry(lines)
    assert set(g) >= {"val", "fora_box", "dist_box", "dline",
                      "dpeso", "conv", "retomada"}

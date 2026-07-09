# -*- coding: utf-8 -*-
"""Testes a21 — indicadores, sinais, simulação de trade e filtros."""
import numpy as np
import pandas as pd
import pytest

import a21_filtro as m


def _ohlc(closes, highs=None, lows=None, opens=None):
    idx = pd.date_range("2024-01-02", periods=len(closes), freq="h")
    c = np.asarray(closes, float)
    return pd.DataFrame({
        "open": opens if opens is not None else c,
        "high": highs if highs is not None else c,
        "low": lows if lows is not None else c,
        "close": c, "spread": 1.0}, index=idx)


# ----------------------------------------------------------------------------
# Indicadores
# ----------------------------------------------------------------------------

def test_atr_constante():
    """Range constante H-L => ATR = esse range."""
    n = 30
    df = _ohlc([10.0]*n, highs=[10.5]*n, lows=[9.5]*n)
    assert abs(m.atr(df).iloc[-1] - 1.0) < 1e-9


def test_rsi_extremos():
    """Série só subindo => RSI -> 100; só caindo => -> 0."""
    up = m.rsi(pd.Series(np.arange(1, 60, dtype=float)))
    dn = m.rsi(pd.Series(np.arange(60, 1, -1, dtype=float)))
    assert up.iloc[-1] > 99
    assert dn.iloc[-1] < 1


def test_signals_breakout():
    """Fecha acima da máxima de 20 barras => sinal long S1."""
    c = [10.0]*25 + [11.0]
    df = _ohlc(c, highs=[10.2]*25 + [11.0])
    lo, sh = m.signals(df, "S1")
    assert lo[-1] and not sh[-1]


def test_signals_rsi_cross():
    """RSI cruza 30 p/ cima => long S3."""
    c = list(np.linspace(60, 20, 40)) + list(np.linspace(20, 45, 20))
    df = _ohlc(c)
    lo, sh = m.signals(df, "S3")
    assert lo.any()


# ----------------------------------------------------------------------------
# Simulação de trade — stop, alvo, timeout, custo
# ----------------------------------------------------------------------------

def _ctx_neutro(idx):
    """Contexto CSS neutro (nenhum filtro dispara)."""
    z = pd.DataFrame(0.0, index=idx, columns=m.G8)
    strong = pd.Series("EUR", index=idx)
    weak = pd.Series("USD", index=idx)
    return z, z, z, strong, weak


def test_trade_alvo_atingido():
    """Long que sobe 2×ATR bate o alvo => R ~ +2 menos custo."""
    n = 60
    c = [1.10000]*25 + [1.10000] + [1.10500]*34   # entra em i=25 (ATR~fixo)
    hi = list(c)
    hi[30] = 1.20000                              # atinge alvo bem acima
    df = _ohlc(c, highs=hi, lows=c)
    # força ATR: injeta range constante de 0.001
    df["high"] = df["close"] + 0.0005
    df["low"] = df["close"] - 0.0005
    df.loc[df.index[30], "high"] = 1.30000
    meta = {"EURUSD": {"point": 1e-5, "spread_mediano_points": 1.0}}
    # sinal artificial: breakout em i=25
    df["high"] = df["high"].copy()
    trd = _run_single(df, meta)
    # alvo 2×ATR / risco 1.5×ATR = +1.33R no acerto (menos custo)
    assert trd and 1.25 < trd[0]["R"] < 1.34


def _run_single(df, meta):
    """Roda simulate com um sinal S1 garantido e contexto neutro."""
    ctx = _ctx_neutro(df.index)
    # monkeypatch signals p/ disparar 1 long em i=25
    orig = m.signals
    def fake(_df, _s):
        lo = np.zeros(len(_df), bool); sh = np.zeros(len(_df), bool)
        lo[25] = True
        return lo, sh
    m.signals = fake
    try:
        return m.simulate("EURUSD", df, "S1", meta, ctx,
                          pd.Timestamp("2000-01-01"), warmup=20)
    finally:
        m.signals = orig


def test_trade_stop_atingido():
    """Long que cai 1.5×ATR bate o stop => R ~ -1 menos custo."""
    n = 60
    c = [1.10000]*60
    df = _ohlc(c)
    df["high"] = df["close"] + 0.0005
    df["low"] = df["close"] - 0.0005
    df.loc[df.index[30], "low"] = 1.00000        # despenca: bate stop
    meta = {"EURUSD": {"point": 1e-5, "spread_mediano_points": 1.0}}
    trd = _run_single(df, meta)
    assert trd and -1.2 < trd[0]["R"] < -0.9


def test_custo_reduz_R():
    """Spread maior => R menor no MESMO trade."""
    c = [1.10000]*60
    df = _ohlc(c)
    df["high"] = df["close"] + 0.0005
    df["low"] = df["close"] - 0.0005
    df.loc[df.index[30], "high"] = 1.30000
    cheap = _run_single(df, {"EURUSD": {"point": 1e-5, "spread_mediano_points": 1.0}})
    pricey = _run_single(df, {"EURUSD": {"point": 1e-5, "spread_mediano_points": 200.0}})
    assert cheap[0]["R"] > pricey[0]["R"]


def test_sem_sobreposicao():
    """Após entrar, próximos sinais na posição são ignorados."""
    c = [1.10000]*60
    df = _ohlc(c)
    df["high"] = df["close"] + 0.0005
    df["low"] = df["close"] - 0.0005
    df.loc[df.index[30], "high"] = 1.30000        # alvo em j=30
    ctx = _ctx_neutro(df.index)
    def fake(_df, _s):
        lo = np.zeros(len(_df), bool)
        lo[25] = True; lo[27] = True              # 2º sinal durante a posição
        return lo, np.zeros(len(_df), bool)
    orig = m.signals; m.signals = fake
    try:
        trd = m.simulate("EURUSD", df, "S1",
                         {"EURUSD": {"point": 1e-5, "spread_mediano_points": 1.0}},
                         ctx, pd.Timestamp("2000-01-01"), warmup=20)
    finally:
        m.signals = orig
    assert len(trd) == 1                          # o 2º sinal foi ignorado


# ----------------------------------------------------------------------------
# Filtros
# ----------------------------------------------------------------------------

def test_filtro_f1_direcao():
    """F1 long liga só com base>=+box e quote<=-box no D1."""
    n = 60
    c = [1.10000]*60
    df = _ohlc(c)
    df["high"] = df["close"] + 0.0005
    df["low"] = df["close"] - 0.0005
    df.loc[df.index[30], "high"] = 1.30000
    idx = df.index
    cD1 = pd.DataFrame(0.0, index=idx, columns=m.G8)
    cD1["EUR"] = 0.30; cD1["USD"] = -0.30         # favorável a long EURUSD
    z = pd.DataFrame(3.0, index=idx, columns=m.G8)   # breadth alto
    ez = pd.DataFrame(0.0, index=idx, columns=m.G8)  # sem exaustão
    ctx = (cD1, z, ez, pd.Series("EUR", index=idx), pd.Series("USD", index=idx))
    def fake(_df, _s):
        lo = np.zeros(len(_df), bool); lo[25] = True
        return lo, np.zeros(len(_df), bool)
    orig = m.signals; m.signals = fake
    try:
        trd = m.simulate("EURUSD", df, "S1",
                         {"EURUSD": {"point": 1e-5, "spread_mediano_points": 1.0}},
                         ctx, pd.Timestamp("2000-01-01"), warmup=20)
    finally:
        m.signals = orig
    t = trd[0]
    assert t["f1"] and t["f2"] and t["f3"] and t["f4"]
    assert not t["f1inv"]


def test_expectancy_e_bh():
    R = np.array([2.0, -1, 2, -1, 2, -1])
    s = m.expectancy_stats(R)
    assert s["n"] == 6 and abs(s["exp"] - 0.5) < 1e-9 and s["pf"] == 2.0
    cells = [{"p": 0.001}, {"p": 0.9}, {"p": 0.5}]
    m.bh_flag(cells)
    assert cells[0]["bh"] and not cells[1]["bh"]

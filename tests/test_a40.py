# -*- coding: utf-8 -*-
"""Testes do a40: ranking a25 IMPORTADO, breakeven monotônico, vantagem de spread."""
import numpy as np
import pandas as pd

import a25_ranqueador
from a40_atr_economic import a25_build, breakeven, q11_spread_vs_atr, P_GRID


def test_ranking_a25_importado_nao_reimplementado():
    # trava: o a40 usa a MESMA função build do a25 (não uma cópia)
    assert a25_build is a25_ranqueador.build


def test_breakeven_monotonico_e_ponto():
    exp, p_be = breakeven(gross_range=100.0, cost=1.0)
    vals = [exp[p] for p in P_GRID]
    assert all(b > a for a, b in zip(vals, vals[1:]))     # cresce com p
    assert abs(p_be - (0.5 + 1.0 / 200.0)) < 1e-9          # 0.505


def _panel(spreads):
    rows = []
    for pair, atr in spreads:
        rows.append({"pair": pair, "base_atr": atr})
    return pd.DataFrame(rows)


def test_spread_menor_no_alto_atr_da_vantagem():
    # 8 pares de ATR alto c/ spread proporcionalmente BAIXO; 8 baixos c/ alto %
    hi = [(f"H{i}", 100.0) for i in range(8)]
    lo = [(f"L{i}", 20.0) for i in range(8)]
    panel = _panel(hi + lo)
    spread = {**{f"H{i}": 0.5 for i in range(8)},   # 0.5% do ATR
              **{f"L{i}": 0.4 for i in range(8)}}    # 2.0% do ATR
    _, q = q11_spread_vs_atr(panel, spread, None)
    assert q["spread_pct_top8"] < q["spread_pct_bot8"]    # vantagem estrutural


def test_spread_1a1_com_atr_zera_vantagem():
    pares = [(f"P{i}", 20.0 + 10 * i) for i in range(16)]
    panel = _panel(pares)
    spread = {p: 0.01 * atr for p, atr in pares}          # spread = 1% do ATR sempre
    _, q = q11_spread_vs_atr(panel, spread, None)
    assert abs(q["spread_pct_top8"] - q["spread_pct_bot8"]) < 1e-6   # sem vantagem

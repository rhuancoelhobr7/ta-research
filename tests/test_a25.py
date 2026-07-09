# -*- coding: utf-8 -*-
"""Testes do a25: backtest de captura, estabilidade e ajuste do ranqueador."""
import numpy as np
import pandas as pd

from a25_ranqueador import backtest, stability, fit_rank


def _te(seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for d in pd.date_range("2020-01-01", periods=50):
        for i in range(28):
            width = 20 + i * 3                      # par i é estruturalmente mais largo
            rng_pips = width + rng.normal(0, 5)
            rows.append({"date": d, "pair": f"P{i:02d}", "tgt_range": rng_pips,
                         "base_atr": width, "score": rng_pips})
    return pd.DataFrame(rows)


def test_backtest_score_perfeito_pega_o_teto():
    te = _te()
    bt = backtest(te, "score")           # score = tgt_range -> top1 == teto do dia
    assert abs(bt["top1_modelo"] - bt["teto_do_dia"]) < 1e-9
    assert bt["aleatorio"] < bt["top1_modelo"]        # aleatório abaixo do top-1


def test_stability_top1_estavel():
    # par estruturalmente mais largo quase sempre no topo -> alta estabilidade
    te = _te()
    st = stability(te.assign(score=te["base_atr"]), "score")
    assert st["top1_igual_ao_dia_anterior"] == 1.0
    assert st["n_pares_distintos_no_teste"] == 1


def test_fit_rank_aprende_largura():
    rng = np.random.default_rng(1)
    rows = []
    for d in pd.date_range("2020-01-01", periods=200):
        widths = rng.uniform(20, 120, 28)
        rng_pips = widths + rng.normal(0, 5, 28)
        thr = np.quantile(rng_pips, 0.75)
        anorm = rng.uniform(0.5, 1.5, 28)          # asia_norm com variância
        for i in range(28):
            rows.append({"date": d, "pair": f"P{i:02d}", "tgt_range": rng_pips[i],
                         "base_atr": widths[i], "base_asia": widths[i] * anorm[i],
                         "asia_norm": anorm[i], "log_atr": np.log(widths[i]),
                         "top_q": int(rng_pips[i] >= thr)})
    p = pd.DataFrame(rows)
    te, coefs = fit_rank(p, ["log_atr", "asia_norm"])
    assert coefs["log_atr"] > 0.5        # largura prevê top-quartil
    assert "score" in te.columns

# -*- coding: utf-8 -*-
"""Testes das agregações do a22 (ranking por intensidade e afinidade relativa)."""
import numpy as np
import pandas as pd

from a22_sessoes import q1_session_rank, q2b_affinity


def _long():
    # overlap com intensidade alta; tokyo baixa — 2 pares, alguns dias
    rng = np.random.default_rng(0)
    rows = []
    intens = {"overlap": 12.0, "londres": 6.0, "ny": 5.0, "tokyo": 4.0}
    for pair in ("GBPJPY", "EURUSD"):
        for d in pd.date_range("2020-01-01", periods=30):
            for s, base in intens.items():
                ph = base + rng.normal(0, 0.2)
                rows.append({"pair": pair, "date": d, "session": s,
                             "range_ph": ph, "range_pips": ph * 3})
    df = pd.DataFrame(rows)
    med = df.groupby("pair")["range_ph"].transform("median")
    df["range_norm"] = df["range_ph"] / med
    return df


def test_q1_ordena_por_intensidade():
    q1 = q1_session_rank(_long())
    assert list(q1.index)[0] == "overlap"          # mais intensa no topo
    assert list(q1.index)[-1] == "tokyo"           # mais calma no fim
    assert q1.loc["overlap", "pips_h_mediana"] > q1.loc["tokyo", "pips_h_mediana"]


def test_q2b_shares_somam_1():
    gmean, tok_share = q2b_affinity(_long())
    # cada linha (grupo) soma ~1 sobre tokyo/londres/ny
    assert np.allclose(gmean[["tokyo", "londres", "ny"]].sum(axis=1), 1.0)
    assert (tok_share.between(0, 1)).all()

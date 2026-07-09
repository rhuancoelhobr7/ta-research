# -*- coding: utf-8 -*-
"""Testes do a24: avaliação de ranqueamento, features P8 e a garantia de
não-lookahead (merge_asof backward EXCLUSIVO na virada)."""
import numpy as np
import pandas as pd

from a24_preditores import rank_eval, pair_features, G8, TFS


def test_rank_eval_perfeito_vs_embaralhado():
    # pred = target -> top-k pega os maiores; lift alto, spearman ~1
    days = pd.date_range("2020-01-01", periods=40)
    rows = []
    rng = np.random.default_rng(0)
    for d in days:
        for i in range(28):
            v = rng.uniform(10, 100)
            rows.append({"date": d, "pair": f"P{i}", "pred": v, "tgt": v,
                         "shuf": rng.uniform(10, 100)})
    df = pd.DataFrame(rows)
    good = rank_eval(df, "pred", "tgt")
    bad = rank_eval(df, "shuf", "tgt")
    assert good["lift"] > 1.3 and good["spearman"] > 0.9
    assert abs(bad["lift"] - 1.0) < 0.1 and abs(bad["spearman"]) < 0.1


def test_pair_features_P8_alinhamento():
    # estado: GBP forte (pct 95) e JPY fraco (pct 5) em todos os TFs ->
    # GBPJPY deve ter P8_mag alto; EURUSD (neutros) baixo.
    date = pd.Timestamp("2020-01-01")
    cols = {}
    for tf in TFS:
        for c in G8:
            pct = 95 if c == "GBP" else (5 if c == "JPY" else 50)
            cols[f"{c}|pct|{tf}"] = [pct]
            cols[f"{c}|val|{tf}"] = [0.5 if c == "GBP" else (-0.5 if c == "JPY" else 0.0)]
            cols[f"{c}|brd|{tf}"] = [7 if c in ("GBP", "JPY") else 3]
    state = pd.DataFrame(cols, index=pd.Index([date], name="date"))
    panel = pd.DataFrame({"pair": ["GBPJPY", "EURUSD"], "date": [date, date]})
    f = pair_features(panel, state)
    g = f.set_index("pair")["P8_mag"]
    assert g["GBPJPY"] > 80 and g["EURUSD"] < 10


def test_asof_exclusivo_sem_lookahead():
    """Documenta a garantia: na virada exata, pega a barra ANTERIOR, nunca a
    da abertura (allow_exact_matches=False)."""
    fr = pd.DataFrame({"utc": pd.to_datetime(
        ["2020-01-01 12:00", "2020-01-01 13:00", "2020-01-01 14:00"]),
        "x": [10, 20, 30]})
    turns = pd.DataFrame({"turn": [pd.Timestamp("2020-01-01 13:00")]})
    got = pd.merge_asof(turns, fr, left_on="turn", right_on="utc",
                        direction="backward", allow_exact_matches=False)
    assert got["x"].iloc[0] == 10   # barra das 12:00, NÃO as 13:00 (abertura)

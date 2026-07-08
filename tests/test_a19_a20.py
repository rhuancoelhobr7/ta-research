# -*- coding: utf-8 -*-
"""Testes a19/a20 — fases sintéticas, rotação, whipsaw, alinhamento fechado."""
import numpy as np
import pandas as pd

from a19_fases import (bh_correct, classify_phases, dwell_times,
                       rotation_rate, transitions, whipsaw_rate)
from a20_confluencia import align_closed, oriented_phase
from css_classic import G8


def _lines(vals):
    idx = pd.date_range("2026-01-05", periods=len(vals), freq="h")
    df = pd.DataFrame(0.0, index=idx, columns=G8)
    df["EUR"] = vals
    return df


def test_fases_ciclo_completo():
    """Sobe ao topo, esvazia, cai, retoma — as 4 fases na ordem (k=3)."""
    v = [0.0, 0.0, 0.0,
         0.30, 0.35, 0.40,      # FORÇA (>=box, delta>=0)
         0.30, 0.25, 0.22,      # EXAUSTÃO (>=box, delta<0)
         0.10, 0.00, -0.10,     # FRAQUEZA (<box, delta<0)
         0.05, 0.10, 0.15]      # EXPANSÃO (<box, delta>0)
    ph = classify_phases(_lines(v))["EUR"]
    assert ph.iloc[5] == "FORCA"
    assert ph.iloc[8] == "EXAUSTAO"
    assert ph.iloc[11] == "FRAQUEZA"
    assert ph.iloc[14] == "EXPANSAO"


def test_fase_espelho():
    """Mesma série negada → mesmas fases no ciclo vendedor."""
    v = [0.0, 0.0, 0.0, 0.30, 0.35, 0.40, 0.30, 0.25, 0.22]
    ph_buy = classify_phases(_lines(v))["EUR"]
    ph_sell = classify_phases(_lines([-x for x in v]), mirror=True)["EUR"]
    pd.testing.assert_series_equal(ph_buy, ph_sell, check_names=False)


def test_delta_zero_mantem_fase():
    v = [0.0, 0.0, 0.0, 0.05, 0.10, 0.15] + [0.15] * 4   # delta vira 0
    ph = classify_phases(_lines(v))["EUR"]
    assert ph.iloc[5] == "EXPANSAO"
    assert ph.iloc[9] == "EXPANSAO"        # mantida por ffill


def test_rotation_rate():
    seq = ["FORCA", "EXAUSTAO", "FRAQUEZA", "EXPANSAO", "FORCA",  # completa
           "EXAUSTAO", "FORCA"]                                    # abortada
    idx = pd.date_range("2026-01-05", periods=len(seq), freq="h")
    ok, exits = rotation_rate(pd.Series(seq, index=idx))
    assert (ok, exits) == (1, 2)


def test_transitions_matrix():
    seq = ["FORCA", "EXAUSTAO", "FRAQUEZA", "EXPANSAO", "FORCA", "EXAUSTAO"]
    idx = pd.date_range("2026-01-05", periods=len(seq), freq="h")
    T = transitions(pd.Series(seq, index=idx))
    assert T.loc["FORCA", "EXAUSTAO"] == 2
    assert T.loc["EXAUSTAO", "FRAQUEZA"] == 1
    assert T.to_numpy().sum() == 5


def test_whipsaw():
    """1ª saída reverte em 2 barras (whip); 2ª persiste 5 barras (ok)."""
    v = [0.0, 0.25, 0.10, 0.0,          # saída whip
         0.30, 0.35, 0.40, 0.45, 0.50,  # saída sustentada
         0.0]
    idx = pd.date_range("2026-01-05", periods=len(v), freq="h")
    rate, n = whipsaw_rate(pd.Series(v, index=idx))
    assert n == 2 and abs(rate - 0.5) < 1e-9


def test_dwell():
    seq = ["FORCA"] * 3 + ["EXAUSTAO"] * 2 + ["FORCA"] * 4
    idx = pd.date_range("2026-01-05", periods=len(seq), freq="h")
    d = dwell_times(pd.Series(seq, index=idx))
    assert sorted(d["FORCA"].tolist()) == [3, 4]
    assert d["EXAUSTAO"].tolist() == [2]


def test_bh_correct():
    cells = [{"p": 0.001}, {"p": 0.04}, {"p": 0.9}, {"p": 0.5}]
    n = bh_correct(cells, alpha=0.05)
    assert n >= 1 and cells[0]["bh_sig"]
    assert not cells[2]["bh_sig"]


def test_align_closed_anti_lookahead():
    """A barra D1 de hoje só aparece no H1 DEPOIS do fechamento dela."""
    h1_idx = pd.date_range("2026-01-05 00:00", "2026-01-07 23:00", freq="h")
    d1 = pd.DataFrame({"EUR": [1.0, 2.0, 3.0]},
                      index=pd.DatetimeIndex(["2026-01-05", "2026-01-06",
                                              "2026-01-07"]))
    al = align_closed(d1, "D1", h1_idx)
    # durante o dia 06, o último D1 FECHADO é o do dia 05 (valor 1.0)
    assert al.loc["2026-01-06 12:00", "EUR"] == 1.0
    # na barra H1 23:00 do dia 06 (fecha 00:00 do 07) o D1 do 06 fecha junto
    assert al.loc["2026-01-06 23:00", "EUR"] == 2.0
    assert al.loc["2026-01-05 03:00", "EUR"] != 3.0


def test_oriented_phase():
    idx = pd.date_range("2026-01-05", periods=2, freq="h")
    buy = pd.DataFrame({"EUR": ["FORCA", "FORCA"]}, index=idx)
    sell = pd.DataFrame({"EUR": ["FRAQUEZA", "FRAQUEZA"]}, index=idx)
    ref = pd.DataFrame({"EUR": [0.3, -0.3]}, index=idx)
    o = oriented_phase(buy, sell, ref)["EUR"]
    assert o.iloc[0] == "FORCA" and o.iloc[1] == "FRAQUEZA"

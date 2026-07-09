# -*- coding: utf-8 -*-
"""Testes do framework de sessões: conversão servidor->UTC DST-aware,
atribuição de sessão e agregação de range."""
import numpy as np
import pandas as pd

from sessions import server_to_utc, session_of, session_ranges


def test_server_to_utc_dst():
    # verão dos EUA (offset +3): 08/07/2026 16:00 servidor -> 13:00 UTC
    # inverno (offset +2):       15/01/2026 12:00 servidor -> 10:00 UTC
    idx = pd.DatetimeIndex(["2026-07-08 16:00", "2026-01-15 12:00"])
    utc = server_to_utc(idx)
    assert utc[0] == pd.Timestamp("2026-07-08 13:00")   # +3
    assert utc[1] == pd.Timestamp("2026-01-15 10:00")   # +2


def test_session_of_overlap():
    utc = pd.Series(pd.to_datetime(
        ["2026-07-08 02:00",   # tokyo
         "2026-07-08 08:00",   # tokyo + londres
         "2026-07-08 14:00",   # londres + ny + overlap
         "2026-07-08 20:00"])) # ny
    m = session_of(utc)
    assert m.loc[0, "tokyo"] and not m.loc[0, "londres"]
    assert m.loc[1, "tokyo"] and m.loc[1, "londres"]
    assert m.loc[2, "londres"] and m.loc[2, "ny"] and m.loc[2, "overlap"]
    assert m.loc[3, "ny"] and not m.loc[3, "overlap"]


def test_session_ranges_basico():
    # um dia de M15 no servidor cobrindo a janela de overlap (13-16 UTC =
    # 16-19 servidor no verao). Preco sobe limpo de 100.00 a 100.50.
    ts = pd.date_range("2026-07-08 16:00", "2026-07-08 18:45", freq="15min")
    n = len(ts)
    close = np.linspace(100.00, 100.50, n)
    df = pd.DataFrame({"open": close, "high": close + 0.01, "low": close - 0.01,
                       "close": close, "tick_volume": 1}, index=ts)
    r = session_ranges(df, pip=0.01)
    ov = r[r.session == "overlap"].iloc[0]
    # range = (max high - min low)/pip = (100.51 - 99.99)/0.01 = 52
    assert abs(ov["range_pips"] - 52.0) < 1e-6
    assert ov["net_pips"] > 0 and 0.9 < ov["traj"] <= 1.0   # movimento limpo

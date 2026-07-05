"""Testes do a11: guarda de disjunção (padrão v2) + snapshot de líder."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from a11_relational_study import leader_at, pair_window_return, pivots


def test_pair_target_inside_decision_raises():
    lp = pd.Series(np.linspace(0, 1, 25),
                   index=pd.date_range("2026-01-05 01:00", periods=25,
                                       freq="1h"))
    t0 = pd.Timestamp("2026-01-05")
    with pytest.raises(ValueError, match="invade"):
        pair_window_return(lp, t0, decision_end_h=4.0, target_start_h=2.0)
    with pytest.raises(ValueError, match="invade"):
        pair_window_return(lp, t0, decision_end_h=6.0, target_start_h=4.0)


def test_pair_target_value_and_windows():
    idx = pd.date_range("2026-01-05 01:00", periods=24, freq="1h")
    lp = pd.Series(np.arange(24, dtype=float), index=idx)  # +1 por hora
    t0 = pd.Timestamp("2026-01-05")
    r = pair_window_return(lp, t0)          # [T0+4h, T0+12h] = 8 barras
    assert r == pytest.approx(8.0)
    # sem barra nova no alvo => NaN
    lp2 = lp[lp.index <= t0 + pd.Timedelta(hours=4)]
    assert np.isnan(pair_window_return(lp2, t0))


def test_leader_at_uses_last_closed_bar():
    ts = pd.date_range("2026-01-05 01:00", periods=3, freq="1h")
    rows = []
    for i, t in enumerate(ts):
        for c, now in (("EUR", 0.5 + i * 0.1), ("JPY", 0.4), ("GBP", 0.1)):
            rows.append({"ts": t, "currency": c, "nowcast": now,
                         "breadth_hard": now, "dir": 1.0 if c != "JPY"
                         else -1.0, "t_idx": 1.0})
    piv = pivots(pd.DataFrame(rows))
    # às 02:30, última barra fechada é 02:00 (i=1): EUR 0.6 lidera
    led = leader_at(piv, pd.Timestamp("2026-01-05 02:30"), "nowcast")
    assert led[0] == "EUR" and led[1] == 1.0
    assert led[3][1][0] == "JPY"            # top-2 inclui JPY
    # antes da 1ª barra => None
    assert leader_at(piv, pd.Timestamp("2026-01-05 00:30"), "nowcast") is None

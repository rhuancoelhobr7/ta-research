# -*- coding: utf-8 -*-
"""Testes do a29: pick_at (argmax do indicador na última barra fechada <= turn)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a29_deteccao import pick_at


def _frame():
    t = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00",
                        "2020-01-01 02:00"])
    data = {c: [0.0, 0.0, 0.0] for c in G8}
    data["GBP"] = [5.0, 1.0, 1.0]      # forte na barra 00:00
    data["EUR"] = [1.0, 5.0, 1.0]      # forte na barra 01:00
    data["JPY"] = [1.0, 1.0, 5.0]      # forte na barra 02:00
    return pd.DataFrame(data, index=t)


def test_pick_at_barra_fechada():
    f = _frame()
    turns = np.array(["2020-01-01 00:30", "2020-01-01 01:30",
                      "2020-01-01 02:30"], dtype="datetime64[ns]")
    picks = pick_at(f, turns).tolist()
    assert picks == ["GBP", "EUR", "JPY"]      # usa a última barra <= turn


def test_pick_at_antes_do_inicio_e_nan():
    f = _frame()
    turns = np.array(["2019-12-31 23:00", "2020-01-01 00:30"],
                     dtype="datetime64[ns]")
    picks = pick_at(f, turns).tolist()
    assert not isinstance(picks[0], str)       # antes de qualquer barra -> NaN
    assert picks[1] == "GBP"

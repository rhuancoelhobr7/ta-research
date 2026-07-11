# -*- coding: utf-8 -*-
"""Testes do a33: scores_at (linha de scores na última barra fechada <= turn)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a33_cadeia import scores_at


def test_scores_at_ranking():
    t = pd.to_datetime(["2020-01-01 00:00", "2020-01-01 01:00"])
    data = {c: [0.0, 0.0] for c in G8}
    data["GBP"] = [9.0, 1.0]
    data["JPY"] = [-9.0, -1.0]
    frame = pd.DataFrame(data, index=t)
    turns = np.array(["2020-01-01 00:30", "2020-01-01 01:30"], dtype="datetime64[ns]")
    sc = scores_at(frame, turns)
    # barra 00:00 -> GBP top, JPY bottom
    r0 = sc.iloc[0].sort_values(ascending=False)
    assert r0.index[0] == "GBP" and r0.index[-1] == "JPY"
    assert list(sc.columns) == G8

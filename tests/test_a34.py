# -*- coding: utf-8 -*-
"""Testes do a34: acurácia régua A/B (acc) e momentum intradiário."""
import numpy as np
import pandas as pd

from preponderante import G8
from a34_varredura import acc, day_metrics


def test_acc_reguas():
    days = pd.to_datetime(["2020-01-01", "2020-01-02"])
    data = {c: [0.0, 0.0] for c in G8}
    data["GBP"] = [9.0, 9.0]; data["EUR"] = [5.0, 1.0]; data["JPY"] = [-9.0, -9.0]
    score = pd.DataFrame(data, index=days)
    truth = pd.DataFrame({"rank": [["GBP", "EUR", "USD"], ["EUR", "GBP", "USD"]]},
                         index=days)
    aA, aB, n = acc(score, truth, days)
    assert n == 2
    assert aA == 0.5          # dia1 GBP(ok); dia2 lider EUR mas score aponta GBP
    assert aB == 1.0          # top-3 do score contem o lider nos 2 dias


def test_day_metrics_momentum_sinal():
    # indice sobe p/ GBP, cai p/ JPY dentro do dia
    t = pd.date_range("2020-01-01 00:00", periods=12, freq="5min")
    idx = pd.DataFrame({c: np.zeros(12) for c in G8}, index=t)
    idx["GBP"] = np.linspace(0, 1, 12); idx["JPY"] = np.linspace(0, -1, 12)
    dm = day_metrics(idx, w=60)
    mom = dm["mom"]
    assert mom.loc[pd.Timestamp("2020-01-01"), "GBP"] > 0
    assert mom.loc[pd.Timestamp("2020-01-01"), "JPY"] < 0

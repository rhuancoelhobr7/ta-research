# -*- coding: utf-8 -*-
"""Testes do a30: curva de detecção e t mais cedo significativo (BH)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a30_volume_momentum import curve, earliest_sig


def test_curve_detecta_top():
    # frame onde GBP é sempre o maior -> pick=GBP; se GBP é a líder, accA=1
    t = pd.to_datetime(["2020-01-01 00:00", "2020-01-02 00:00"])
    data = {c: [0.0, 0.0] for c in G8}
    data["GBP"] = [9.0, 9.0]
    frame = pd.DataFrame(data, index=t)
    te_dates = pd.DatetimeIndex(["2020-01-01", "2020-01-02"])
    truth = pd.DataFrame({"rank": [["GBP", "EUR", "USD"], ["GBP", "JPY", "USD"]]},
                         index=te_dates)
    ranks = list(truth["rank"].values)
    # turns caem 30min+ após 00:00 -> pegam a barra 00:00 do dia
    c = curve(frame, truth, te_dates, ranks)
    assert (c["accA"] == 1.0).all() and (c["accB3"] == 1.0).all()


def test_earliest_sig():
    cur = pd.DataFrame({"t_min": [30, 60, 90],
                        "accB3": [0.40, 0.90, 0.92],
                        "accA": [0.1, 0.5, 0.5],
                        "n": [300, 300, 300]})
    r = earliest_sig(cur)
    assert r["t_signif"] == 60            # 0.40 não bate; 0.90 sim
    # tudo no acaso -> nenhum significativo
    flat = pd.DataFrame({"t_min": [30, 60], "accB3": [0.375, 0.38],
                         "accA": [0.12, 0.12], "n": [300, 300]})
    assert earliest_sig(flat)["t_signif"] is None

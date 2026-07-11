# -*- coding: utf-8 -*-
"""Testes do a35: hit_vector (líder verdadeira no top-3 do score, por dia)."""
import numpy as np
import pandas as pd

from preponderante import G8
from a35_holdout import hit_vector


def test_hit_vector():
    days = pd.to_datetime(["2020-01-01", "2020-01-02"])
    data = {c: [0.0, 0.0] for c in G8}
    data["GBP"] = [9, 9]; data["EUR"] = [5, 5]; data["CHF"] = [4, 4]
    score = pd.DataFrame(data, index=days)          # top-3 do score = GBP,EUR,CHF
    truth = pd.DataFrame({"rank": [["EUR", "X", "Y"], ["JPY", "X", "Y"]]},
                         index=days)
    h = hit_vector(score, truth, days)
    # dia1: lider EUR esta no top-3 -> 1; dia2: lider JPY nao esta -> 0
    assert list(h) == [1.0, 0.0]

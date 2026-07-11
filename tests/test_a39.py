# -*- coding: utf-8 -*-
"""Testes do a39: regra congelada (predict) e integridade append-only do log."""
import numpy as np
import pandas as pd

from preponderante import G8
from a39_prospective import predict, _append, _existing_ids, PRED_COLS


def _mom(vals):
    return pd.Series({c: vals.get(c, 0.01) for c in G8})


def test_predict_A_zscore():
    mean = pd.Series({c: 0.0 for c in G8}); std = pd.Series({c: 1.0 for c in G8})
    mom = _mom({"GBP": 3.0, "JPY": -3.0})
    dec = predict(mom, "A", mean, std, {"GBPJPY"})
    assert dec["leader"] == "GBP" and dec["counter"] == "JPY"
    assert dec["pair"] == "GBPJPY" and dec["side"] == +1


def test_predict_B_persistencia():
    # JPY tem o maior |mov| (negativo) -> lider JPY, direcao -1 (fraco);
    # contraparte = a mais oposta (GBP, +3). Par GBPJPY, short JPY = buy GBPJPY.
    mom = _mom({"JPY": -5.0, "GBP": 3.0})
    dec = predict(mom, "B", pd.Series(dtype=float), pd.Series(dtype=float), {"GBPJPY"})
    assert dec["leader"] == "JPY" and dec["direction"] == -1
    assert dec["counter"] == "GBP" and dec["pair"] == "GBPJPY" and dec["side"] == +1


def test_predict_insuficiente():
    mom = pd.Series({"GBP": 1.0, "JPY": -1.0})     # <8 moedas
    assert predict(mom, "A", pd.Series(dtype=float), pd.Series(dtype=float), {"GBPJPY"}) is None


def test_append_only_e_dedup(tmp_path):
    f = tmp_path / "predictions.csv"
    r = {c: "x" for c in PRED_COLS}; r["pred_id"] = "2026-07-11|A"
    assert _append(f, [r], PRED_COLS) == 1
    ids = _existing_ids(f)
    assert "2026-07-11|A" in ids
    # o chamador filtra por _existing_ids -> nada re-adicionado
    novos = [x for x in [r] if x["pred_id"] not in ids]
    assert _append(f, novos, PRED_COLS) == 0
    assert len(pd.read_csv(f)) == 1                # append-only, sem duplicata

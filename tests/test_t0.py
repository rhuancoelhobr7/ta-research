# -*- coding: utf-8 -*-
"""Testes da TAREFA 0 (t0_normalize): percentil rolante CAUSAL e formato."""
import numpy as np
import pandas as pd

from t0_normalize import rolling_pct, normalize_tf


def test_rolling_pct_valor_corrente():
    s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    p = rolling_pct(s, 3)
    assert p.iloc[0] != p.iloc[0]  # NaN (aquecimento)
    assert p.iloc[1] != p.iloc[1]
    # janela [1,2,3], corrente 3 = maximo -> 100
    assert p.iloc[2] == 100.0
    assert p.iloc[4] == 100.0     # [3,4,5], corrente 5 = maximo


def test_rolling_pct_minimo():
    s = pd.Series([5.0, 4.0, 3.0, 2.0, 1.0])
    p = rolling_pct(s, 3)
    # janela [5,4,3], corrente 3 = minimo -> 1/3 * 100
    assert abs(p.iloc[2] - 100.0 / 3.0) < 1e-9


def test_rolling_pct_sem_lookahead():
    """Mudar um valor FUTURO nao pode alterar o pct de um t anterior."""
    base = pd.Series([1.0, 3.0, 2.0, 5.0, 4.0, 6.0])
    p0 = rolling_pct(base, 3)
    fut = base.copy()
    fut.iloc[5] = 999.0                      # mexe so no ultimo
    p1 = rolling_pct(fut, 3)
    # pct ate o indice 4 (janela nao alcanca o 5) intacto
    assert p0.iloc[:5].equals(p1.iloc[:5])


def test_normalize_tf_colunas():
    idx = pd.date_range("2020-01-01", periods=10, freq="D")
    vals = pd.DataFrame({"GBP": np.arange(10.0), "JPY": np.arange(10.0)[::-1]},
                        index=idx)
    df = normalize_tf(vals, [3, 5])
    for c in ("val_GBP", "pct3_GBP", "pct5_GBP", "val_JPY", "pct3_JPY"):
        assert c in df.columns
    assert df["val_GBP"].equals(vals["GBP"])

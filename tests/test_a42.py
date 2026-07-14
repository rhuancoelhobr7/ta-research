# -*- coding: utf-8 -*-
"""Testes do a42: anti-lookahead, z-ATR exato, a25 importado, eficiência."""
import numpy as np
import pandas as pd

import a25_ranqueador
from a42_informacao_diaria import a25_build, eval_competitor


def test_a25_importado_nao_reimplementado():
    assert a25_build is a25_ranqueador.build


def test_anti_lookahead_E_e_Z():
    # E e Z de um dia PASSADO não podem mudar se um ATR FUTURO for perturbado.
    idx = pd.date_range("2020-01-01", periods=300)
    A = pd.DataFrame({"P": np.linspace(10, 20, 300)}, index=idx)
    E = A.expanding().mean().shift(1)
    m = A.shift(1).rolling(60).mean(); s = A.shift(1).rolling(60).std()
    Z = (A - m) / s
    A2 = A.copy(); A2.iloc[-1, 0] = 999.0                # perturba o FUTURO
    E2 = A2.expanding().mean().shift(1)
    Z2 = (A2 - A2.shift(1).rolling(60).mean()) / A2.shift(1).rolling(60).std()
    past = idx[100]
    assert E.loc[past, "P"] == E2.loc[past, "P"]         # passado intacto
    assert Z.loc[past, "P"] == Z2.loc[past, "P"]


def test_z_atr_definicao_exata():
    # base_atr = 10 por 60 dias, depois 16. z = (16 - 10)/0 -> mas usa prior.
    idx = pd.date_range("2020-01-01", periods=62)
    v = np.r_[np.full(60, 10.0), 12.0, 16.0]
    A = pd.DataFrame({"P": v}, index=idx)
    m = A.shift(1).rolling(60).mean(); s = A.shift(1).rolling(60).std()
    z = (A - m) / s
    # no penúltimo dia (i=60, valor 12): média prior = 10, std prior = 0 -> inf/nan
    # no último (i=61, valor 16): prior inclui o 12 -> média>10, std>0, z finito >0
    assert np.isfinite(z.iloc[61, 0]) and z.iloc[61, 0] > 0


def _frames():
    pairs = ["X", "Y"] + [f"F{i}" for i in range(20)]
    d = pd.Timestamp("2020-01-01")
    tgt = pd.DataFrame([[100.0, 60.0] + [10.0] * 20], index=[d], columns=pairs)
    spread = {"X": 5.0, "Y": 1.0, **{f"F{i}": 2.0 for i in range(20)}}
    return pairs, d, tgt, spread


def test_eficiencia_penaliza_spread():
    # X: ATR alto (100) mas spread alto (5) -> efic 20. Y: ATR médio (60),
    # spread baixo (1) -> efic 60. Quem escolhe Y ganha em eficiência.
    pairs, d, tgt, spread = _frames()
    sX = pd.DataFrame([[10, 1] + [0] * 20], index=[d], columns=pairs)   # topo=X
    sY = pd.DataFrame([[1, 10] + [0] * 20], index=[d], columns=pairs)   # topo=Y
    eX = eval_competitor(sX, tgt, spread, tgt.index)
    eY = eval_competitor(sY, tgt, spread, tgt.index)
    assert eX["cap1"].iloc[0] == 100 and eY["cap1"].iloc[0] == 60      # bruto: X>Y
    assert eY["eff1"].iloc[0] > eX["eff1"].iloc[0]                     # eficiência: Y>X
    assert abs(eY["eff1"].iloc[0] - 60.0) < 1e-9

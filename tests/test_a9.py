"""Testes do a9 (matriz MTF v2): condições do PROTOCOLO + não-lookahead."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from a9_mtf_matrix import (COND_FP, COND_FR, COND_N, build_v2_matrix,
                           protocol_full, protocol_reduced, _runlen,
                           _runlen_same_nonzero)
from cssm_engine import resample_closes
from tests.test_labeling import make_synthetic

DAY = pd.Timestamp("2025-01-06") + pd.Timedelta(days=30)


def test_runlen_helpers():
    m = np.array([True, True, False, True, True, True])
    assert list(_runlen(m)) == [1, 2, 0, 1, 2, 3]
    k = np.array([1.0, 1.0, -1.0, -1.0, 0.0, 1.0])
    assert list(_runlen_same_nonzero(k)) == [1, 2, 1, 2, 0, 1]


def test_protocol_full_fr_by_age_and_decel():
    n = 60
    f = pd.DataFrame({
        "state": np.full(n, 2.0), "dir": np.ones(n),
        "acc_z": np.ones(n), "M": np.ones(n)})
    c = protocol_full(f, fr_age=40)
    assert (c.cond.iloc[:40] == COND_FP).all()      # Madura jovem = FP
    assert (c.cond.iloc[41:] == COND_FR).all()      # idade > 40 => FR
    f2 = f.copy(); f2["acc_z"] = -1.0               # desaceleração contra
    c2 = protocol_full(f2, fr_age=40)
    assert (c2.cond == COND_FR).all()


def test_protocol_reduced_fp_fr_n():
    n = 20
    t = np.concatenate([np.linspace(0, 4, 10), np.linspace(4, 2.2, 10)])
    f = pd.DataFrame({"t": t, "pers": np.full(n, 0.8), "er": np.ones(n)})
    c = protocol_reduced(f, gate=2.5)
    assert c.cond.iloc[0] == COND_N                 # |t| abaixo do gate
    assert c.cond.iloc[9] == COND_FP                # forte e subindo
    assert c.cond.iloc[15] == COND_FR               # |t| caindo vs 5 atrás
    assert c.cond.iloc[19] == COND_N                # caiu abaixo do gate
    assert (c.dir.iloc[9] > 0)


@pytest.fixture(scope="module")
def synth():
    m5 = make_synthetic(events=(("CHF", +1, 28), ("CHF", +1, 29),
                                ("CHF", +1, 30)))
    return m5, resample_closes(m5, "1D")


def test_no_lookahead_decision_columns(synth):
    """Corromper após T0+4h não muda NENHUMA coluna de decisão do dia
    (snapshots T0 e T0+4h, realizado 4h). ret_4_12 é ALVO e fica de fora."""
    m5, d1 = synth
    days = pd.DatetimeIndex([DAY])
    base, _ = build_v2_matrix(m5, d1, days, 0.0, lenses=(16, 32),
                              gate_walks=3)
    cut = DAY + pd.Timedelta(hours=4)
    m5_c = {s: v.where(v.index <= cut, v * 1.07) for s, v in m5.items()}
    corr, _ = build_v2_matrix(m5_c, resample_closes(m5_c, "1D"), days, 0.0,
                              lenses=(16, 32), gate_walks=3)
    drop = ["day", "currency", "ret_4_12"]
    a = base.drop(columns=drop).to_numpy(dtype=float)
    b = corr.drop(columns=drop).to_numpy(dtype=float)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    np.testing.assert_allclose(a, b, rtol=0, atol=0)


def test_no_lookahead_full_row_past_12h(synth):
    """Corromper após T0+12h não muda NADA (nem o alvo ret_4_12)."""
    m5, d1 = synth
    days = pd.DatetimeIndex([DAY])
    base, _ = build_v2_matrix(m5, d1, days, 0.0, lenses=(16,), gate_walks=3)
    cut = DAY + pd.Timedelta(hours=12, minutes=10)
    m5_c = {s: v.where(v.index <= cut, v * 1.07) for s, v in m5.items()}
    corr, _ = build_v2_matrix(m5_c, resample_closes(m5_c, "1D"), days, 0.0,
                              lenses=(16,), gate_walks=3)
    a = base.drop(columns=["day", "currency"]).to_numpy(dtype=float)
    b = corr.drop(columns=["day", "currency"]).to_numpy(dtype=float)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    np.testing.assert_allclose(a, b, rtol=0, atol=0)


def test_event_day_realized_metrics(synth):
    """Dia do evento CHF ALTA: ret4h>0, mini-breadth alta, alvo 4->12 > 0
    (a deriva sintética cobre [T0, T0+12h])."""
    m5, d1 = synth
    df, meta = build_v2_matrix(m5, d1, pd.DatetimeIndex([DAY]), 0.0,
                               lenses=(16,), gate_walks=3)
    r = df[df.currency == "CHF"].iloc[0]
    assert r.ret4h > 0 and r.breadth4h >= 6 / 7 and r.ret_4_12 > 0
    assert meta["mn_disponivel"] is False           # 40 dias => sem MN

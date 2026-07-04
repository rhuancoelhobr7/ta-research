"""Teste obrigatório de NÃO-LOOKAHEAD das features em T0 (regra dura nº 3):
alterar os closes DEPOIS de T0 não pode mudar nenhuma feature do dia."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from a4_features_t0 import features_at_t0, tf_feature_tables
from cssm_engine import G8


def _synthetic(seed=0):
    """7 pares vs USD; M5 ~120 dias úteis, D1 ~800 dias úteis."""
    rng = np.random.default_rng(seed)
    m5_idx = pd.date_range("2025-01-06", periods=120 * 288, freq="5min")
    m5_idx = m5_idx[m5_idx.dayofweek < 5]
    d1_idx = pd.bdate_range("2022-06-01", "2025-06-27")
    m5, d1 = {}, {}
    for c in G8[1:]:
        sym = c + "USD"
        m5[sym] = pd.Series(
            np.exp(np.cumsum(rng.normal(0, 3e-4, len(m5_idx)))), index=m5_idx)
        d1[sym] = pd.Series(
            np.exp(np.cumsum(rng.normal(0, 5e-3, len(d1_idx)))), index=d1_idx)
    return m5, d1


def test_future_data_does_not_change_t0_features():
    m5, d1 = _synthetic()
    days = pd.DatetimeIndex(sorted(set(next(iter(m5.values())).index.normalize())))
    days = days[days.dayofweek < 5][-10:]     # últimos 10 dias úteis
    probe = days[4]                            # dia no meio da lista
    t0 = probe                                 # t0_hour = 0

    base = features_at_t0(tf_feature_tables(m5, d1), days, 0.0)

    # corrompe TUDO a partir de T0 do dia-sonda (M5 e D1)
    m5_c = {s: v.where(v.index < t0, v * (1 + 0.05)) for s, v in m5.items()}
    d1_c = {s: v.where(v.index < t0, v * (1 + 0.05)) for s, v in d1.items()}
    corr = features_at_t0(tf_feature_tables(m5_c, d1_c), days, 0.0)

    before = base.day <= probe                # dias com T0 <= dado corrompido
    a = base[before].drop(columns=["day", "currency"]).to_numpy(dtype=float)
    b = corr[before].drop(columns=["day", "currency"]).to_numpy(dtype=float)
    assert np.array_equal(np.isnan(a), np.isnan(b))
    np.testing.assert_allclose(a, b, rtol=0, atol=0)


def test_d1_row_is_yesterdays_bar():
    """A feature D1 do dia D deve vir da barra de ontem (fechamento <= T0)."""
    m5, d1 = _synthetic(1)
    days = pd.DatetimeIndex(sorted(set(next(iter(m5.values())).index.normalize())))
    days = days[days.dayofweek < 5][-6:]
    tables = tf_feature_tables(m5, d1)
    feats = features_at_t0(tables, days, 0.0)
    day = days[-1]
    for c in G8:
        f = tables["D1"][c]                    # indexado por FECHAMENTO
        expected = f[f.index <= day].iloc[-1]  # última barra fechada até T0
        got = feats[(feats.day == day) & (feats.currency == c)].iloc[0]
        assert got["D1_t"] == expected["t"]
        # fechamento <= T0 => barra ABRIU ontem ou antes
        assert f[f.index <= day].index[-1] <= day


def test_w1_reduced_mode_columns_and_states():
    m5, d1 = _synthetic(2)
    days = pd.DatetimeIndex(sorted(set(next(iter(m5.values())).index.normalize())))
    days = days[days.dayofweek < 5][-5:]
    feats = features_at_t0(tf_feature_tables(m5, d1), days, 0.0)
    assert "W1_acc_z" not in feats.columns and "W1_conv_z" not in feats.columns
    st = feats["W1_state"].dropna().unique()
    assert set(st) <= {-1.0, 0.0, 2.0}         # Ruído/Madura (+aquecimento)

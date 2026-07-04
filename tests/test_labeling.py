"""Validação sintética do rotulador a1 (Fase A1).

Gera 40 dias de M5 dos 28 pares a partir de forças latentes; injeta uma
tendência absoluta conhecida (CHF ALTA no dia 30, NZD BAIXA no dia 34) dentro
da janela [T0, T0+12h]; verifica detecção, direção e ranking. Verifica também
que a normalização z usa apenas o passado (causalidade do rótulo).
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from cssm_engine import G8
from a1_label_days import compute_day_table, apply_labels


def make_synthetic(seed=11, n_days=40, bars_per_day=288,
                   events=(("CHF", +1, 30), ("NZD", -1, 34))):
    rng = np.random.default_rng(seed)
    T = n_days * bars_per_day
    dt = pd.date_range("2025-01-06", periods=T, freq="5min")  # começa 2a-feira
    strength = {c: rng.normal(0, 4e-4, T) for c in G8}
    for cur, sign, day in events:
        i0 = day * bars_per_day
        i1 = i0 + bars_per_day // 2          # drift dentro de [00:00, 12:00]
        strength[cur][i0:i1] += sign * 3e-3  # >> vol de fundo -> ER alto
    strength = {c: np.cumsum(v) for c, v in strength.items()}
    closes = {}
    for i in range(8):
        for j in range(i + 1, 8):
            closes[G8[i] + G8[j]] = pd.Series(
                np.exp(strength[G8[i]] - strength[G8[j]]), index=dt)
    return closes


@pytest.fixture(scope="module")
def labels():
    closes = make_synthetic()
    raw = compute_day_table(closes, t0_hour=0.0, window_hours=12.0,
                            vol_lookback=20)
    return apply_labels(raw, breadth_min=6 / 7, z_min=1.0, er_min=0.25)


def test_event_days_detected(labels):
    d_chf = pd.Timestamp("2025-01-06") + pd.Timedelta(days=30)
    d_nzd = pd.Timestamp("2025-01-06") + pd.Timedelta(days=34)
    chf = labels[(labels.day == d_chf) & (labels.currency == "CHF")]
    nzd = labels[(labels.day == d_nzd) & (labels.currency == "NZD")]
    assert len(chf) and bool(chf.labeled.iloc[0]) and chf.direction.iloc[0] == "ALTA"
    assert len(nzd) and bool(nzd.labeled.iloc[0]) and nzd.direction.iloc[0] == "BAIXA"


def test_event_currency_is_top_score(labels):
    d_chf = pd.Timestamp("2025-01-06") + pd.Timedelta(days=30)
    day = labels[labels.day == d_chf].sort_values("score", ascending=False)
    assert day.iloc[0].currency == "CHF"


def test_quiet_days_mostly_unlabeled(labels):
    ev = {pd.Timestamp("2025-01-06") + pd.Timedelta(days=d) for d in (30, 34)}
    quiet = labels[~labels.day.isin(ev)]
    rate = quiet.labeled.mean()
    assert rate < 0.10, f"taxa de rótulo em dias quietos alta demais: {rate:.2%}"


def test_z_normalization_is_causal():
    """Alterar dias FUTUROS não pode mudar as métricas de um dia passado."""
    closes1 = make_synthetic()
    closes2 = make_synthetic(events=(("CHF", +1, 30), ("NZD", -1, 34),
                                     ("EUR", +1, 38)))  # evento extra no futuro
    kw = dict(t0_hour=0.0, window_hours=12.0, vol_lookback=20)
    d_chf = pd.Timestamp("2025-01-06") + pd.Timedelta(days=30)
    r1 = compute_day_table(closes1, **kw)
    r2 = compute_day_table(closes2, **kw)
    a = r1[(r1.day == d_chf) & (r1.currency == "CHF")][["breadth", "z", "er"]]
    b = r2[(r2.day == d_chf) & (r2.currency == "CHF")][["breadth", "z", "er"]]
    assert np.allclose(a.to_numpy(), b.to_numpy(), atol=1e-10)

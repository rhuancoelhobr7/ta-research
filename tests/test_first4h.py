"""Testes do a8 (dataset primeiras 4h): detecção sintética + não-lookahead."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from a1_label_days import compute_day_table, apply_labels
from a8_first4h import _day_block_ci, build_first4h
from cssm_engine import resample_closes
from tests.test_labeling import make_synthetic

T0H, EVENT_DAY = 0.0, 30
DAY = pd.Timestamp("2025-01-06") + pd.Timedelta(days=EVENT_DAY)


@pytest.fixture(scope="module")
def synth():
    # tendência CHF sustentada (dias 28-30): só 4 barras H1 de deriva não
    # ativam a máquina de estados (pers<0.55, acc~0) — o snapshot "ativo"
    # requer trend plurianterior, como nos dias reais de tendência absoluta
    m5 = make_synthetic(events=(("CHF", +1, 28), ("CHF", +1, 29),
                                ("CHF", +1, 30)))
    d1 = resample_closes(m5, "1D")
    raw = compute_day_table(m5, t0_hour=T0H, window_hours=12.0,
                            vol_lookback=20)
    labels = apply_labels(raw, breadth_min=6 / 7, z_min=1.0, er_min=0.25)
    return m5, d1, labels


@pytest.fixture(scope="module")
def table(synth):
    m5, d1, labels = synth
    days = pd.DatetimeIndex([DAY - pd.Timedelta(days=1), DAY])
    return build_first4h(m5, d1, labels, days, T0H)


def test_chf_event_h1_active_up_and_aligned(table):
    """No dia do evento CHF ALTA: H1 em T0+4h ativo na direção ALTA e
    align_4h True (especificação do a8)."""
    r = table[(table.day == DAY) & (table.currency == "CHF")].iloc[0]
    assert bool(r.labeled) and r.direction == "ALTA"
    assert r.H1_state_h4 >= 1, f"H1 em T0+4h inativo: {r.H1_state_h4}"
    assert r.H1_dir_h4 > 0
    assert bool(r.align_4h) and r.idx_ret_4h > 0


def test_no_lookahead_in_snapshots(synth):
    """Corromper os closes DEPOIS de T0+4h não muda nenhuma coluna do dia."""
    m5, d1, labels = synth
    days = pd.DatetimeIndex([DAY])
    base = build_first4h(m5, d1, labels, days, T0H)

    cut = DAY + pd.Timedelta(hours=T0H + 4)   # último instante usado no dia
    m5_c = {s: v.where(v.index <= cut, v * 1.05) for s, v in m5.items()}
    d1_c = resample_closes(m5_c, "1D")
    corr = build_first4h(m5_c, d1_c, labels, days, T0H)

    a = base.drop(columns=["day", "currency", "direction"])
    b = corr.drop(columns=["day", "currency", "direction"])
    a = a.astype(float).to_numpy(); b = b.astype(float).to_numpy()
    assert np.array_equal(np.isnan(a), np.isnan(b))
    np.testing.assert_allclose(a, b, rtol=0, atol=0)


def test_day_block_ci_constant():
    days = np.repeat(np.arange(20), 3)
    vals = np.full(60, 0.7)
    s, lo, hi = _day_block_ci(days.astype("datetime64[D]").astype(
        "datetime64[ns]"), vals, block=5)
    assert s == pytest.approx(0.7) and lo == pytest.approx(0.7) \
        and hi == pytest.approx(0.7)

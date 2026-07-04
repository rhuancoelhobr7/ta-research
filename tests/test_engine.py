"""Suíte de validação do cssm_engine — deve passar SEMPRE (pytest -q).

Codifica as validações de fidelidade ao MQ5 original:
  1. Calibração do TStat Newey-West em ruído puro (~5-7% de |t|>=2,
     conforme documentado no comentário do próprio indicador MQ5).
  2. Limites teóricos do EffRatio.
  3. Reconstrução exata de moedas latentes a partir de pares sintéticos.
  4. Comportamento da máquina de estados em regimes conhecidos.
  5. Ausência de lookahead nas features.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from cssm_engine import (G8, CssmParams, build_indices, compute_currency,
                         tstat_nw, eff_ratio, forward_returns)


def test_tstat_false_positive_calibration():
    """Random walk puro: fração de |t|>=2 deve ficar na faixa nominal 4-9%."""
    rng = np.random.default_rng(42)
    fps = []
    for _ in range(20):
        x = np.cumsum(rng.normal(0, 1, 20000))
        t = tstat_nw(x, 64)
        t = t[~np.isnan(t)]
        fps.append(np.mean(np.abs(t) >= 2.0))
    assert 0.04 <= np.mean(fps) <= 0.09, f"calibração fora da faixa: {np.mean(fps):.3f}"


def test_tstat_detects_real_drift():
    rng = np.random.default_rng(7)
    x = np.cumsum(rng.normal(0.15, 1, 5000))
    t = tstat_nw(x, 64)
    assert np.nanmedian(t) > 0.8


def test_effratio_bounds():
    lin = np.arange(500.0)
    assert np.nanmax(eff_ratio(lin, 64)) == pytest.approx(1.0)
    zig = np.tile([0.0, 1.0], 400)
    assert np.nanmedian(eff_ratio(zig, 64)) == pytest.approx(0.0, abs=1e-9)


def test_index_reconstruction_from_pairs():
    """28 pares gerados de forças latentes -> índice recupera a força (r>0.999)."""
    rng = np.random.default_rng(7)
    T = 4000
    dt = pd.date_range("2022", periods=T, freq="5min")
    strength = {c: np.cumsum(rng.normal(0, 0.001, T)) for c in G8}
    strength["EUR"] += np.linspace(0, 0.05, T)
    closes = {}
    for i in range(8):
        for j in range(i + 1, 8):
            closes[G8[i] + G8[j]] = pd.Series(
                np.exp(strength[G8[i]] - strength[G8[j]]), index=dt)
    idx = build_indices(closes)
    lat = pd.DataFrame(strength, index=dt)
    lat = lat.sub(lat.mean(axis=1), axis=0)
    for c in G8:
        r = np.corrcoef(idx[c].iloc[1:], lat[c].iloc[1:])[0, 1]
        assert r > 0.999, f"{c}: r={r:.4f}"


def test_state_machine_regimes():
    """Madura deve dominar a fase de tendência e ser rara na fase de ruído."""
    rng = np.random.default_rng(42)
    x = np.cumsum(np.concatenate([rng.normal(0, 1, 3000),
                                  rng.normal(0.25, 1, 800)]))
    idx = pd.Series(x, index=pd.date_range("2020", periods=len(x), freq="h"))
    out = compute_currency(idx, CssmParams())
    noise_phase = out.state.iloc[700:3000]
    trend_phase = out.state.iloc[3100:3800]
    frac_mature_noise = (noise_phase == 2).mean()
    frac_mature_trend = (trend_phase == 2).mean()
    assert frac_mature_trend > 0.30
    assert frac_mature_noise < 0.15
    assert frac_mature_trend > 3 * frac_mature_noise


def test_no_lookahead():
    """Alterar o futuro da série NÃO pode mudar features passadas."""
    rng = np.random.default_rng(3)
    x = np.cumsum(rng.normal(0, 1, 3000))
    idx1 = pd.Series(x, index=pd.date_range("2020", periods=3000, freq="h"))
    x2 = x.copy()
    x2[2000:] += np.linspace(0, 50, 1000)          # futuro radicalmente diferente
    idx2 = pd.Series(x2, index=idx1.index)
    a = compute_currency(idx1).iloc[:1990]
    b = compute_currency(idx2).iloc[:1990]
    pd.testing.assert_frame_equal(a, b)


def test_forward_returns_are_strictly_future():
    s = pd.Series(np.arange(100.0),
                  index=pd.date_range("2020", periods=100, freq="h"))
    fr = forward_returns(s, [5])
    assert fr[5].iloc[0] == 5.0
    assert np.isnan(fr[5].iloc[-1])

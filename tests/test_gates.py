"""Calibração de gates por lente (v2, etapa 1): com o gate calibrado em
random walks, a taxa de falsos positivos em walks FRESCOS (seeds distintos
dos de calibração) deve ficar na faixa 4-7% para cada w da grade."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pytest

from cssm_engine import calibrate_gates, lens_params, tstat_nw

GRID = (16, 24, 32, 48)


@pytest.mark.parametrize("w", GRID)
def test_calibrated_gate_fp_in_band(w):
    gate = calibrate_gates(w, n_walks=15, bars=20000, target_fp=0.05, seed=0)
    rng = np.random.default_rng(1000 + w)      # walks frescos p/ verificação
    fps = []
    for _ in range(15):
        x = np.cumsum(rng.normal(0, 1, 20000))
        t = tstat_nw(x, w)
        t = t[~np.isnan(t)]
        fps.append(np.mean(np.abs(t) >= gate))
    assert 0.04 <= np.mean(fps) <= 0.07, \
        f"w={w}: FP {np.mean(fps):.3f} fora de [0.04, 0.07] (gate {gate:.2f})"


def test_gate_grows_as_w_shrinks():
    """Lentes curtas têm cauda mais pesada: gate calibrado deve crescer
    quando w diminui (a razão de existir da calibração)."""
    gates = {w: calibrate_gates(w, n_walks=10, bars=20000, seed=0)
             for w in (16, 64)}
    assert gates[16] > gates[64]


def test_low_gate_below_high_gate():
    hi = calibrate_gates(24, n_walks=10, bars=20000, target_fp=0.05, seed=0)
    lo = calibrate_gates(24, n_walks=10, bars=20000, target_fp=0.20, seed=0)
    assert lo < hi


def test_lens_params_wiring():
    p = lens_params(16, n_walks=5, bars=10000)
    assert p.w_fast == 4 and p.w_mid == 16 and p.z_win == 128
    assert p.t_low < p.t_gate


def test_calibration_deterministic():
    a = calibrate_gates(32, n_walks=5, bars=10000, seed=7)
    b = calibrate_gates(32, n_walks=5, bars=10000, seed=7)
    assert a == b

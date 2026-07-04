"""Testes do a10: guarda de disjunção decisão/alvo + peças puras."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from a10_v2_study import (mini_scores, oriented_target, plateau_lens,
                          t2_pick)


def _rows(ret412=(0.01, -0.02)):
    return pd.DataFrame({"ret_4_12": ret412})


def test_target_inside_decision_window_raises():
    """Mover o alvo p/ dentro da janela de decisão DEVE disparar erro."""
    with pytest.raises(ValueError, match="invade"):
        oriented_target(_rows(), np.array([1.0, -1.0]),
                        decision_end_h=4.0, target_start_h=2.0)
    with pytest.raises(ValueError, match="invade"):
        oriented_target(_rows(), np.array([1.0, -1.0]),
                        decision_end_h=6.0, target_start_h=4.0)


def test_target_orientation():
    r = oriented_target(_rows((0.01, -0.02)), np.array([1.0, -1.0]))
    assert r[0] == pytest.approx(0.01)      # comprado, subiu
    assert r[1] == pytest.approx(0.02)      # vendido, caiu => ganho


def test_only_materialized_target_window():
    with pytest.raises(ValueError, match="materializado"):
        oriented_target(_rows(), np.array([1.0, 1.0]),
                        decision_end_h=4.0, target_start_h=5.0,
                        target_end_h=12.0)


def test_mini_scores_and_pick():
    df = pd.DataFrame({
        "day": [pd.Timestamp("2026-01-05")] * 3,
        "currency": ["EUR", "GBP", "JPY"],
        "ret4h": [0.004, -0.006, 0.0005],
        "breadth4h": [6 / 7, 0.0, 0.5],      # GBP caiu: breadth_dir = 1-0 = 1
        "er4h": [0.5, 0.6, 0.1],
        "H1_cond_4h": [2.0, 0.0, 0.0], "H1_dir_4h": [1.0, -1.0, 1.0],
        "H4_cond_4h": [0.0, 0.0, 0.0], "H4_dir_4h": [1.0, -1.0, 1.0],
        "ret_4_12": [0.002, -0.003, 0.0]})
    d = mini_scores(df)
    pick = t2_pick(d, theta=0.0, mtf=False)
    assert len(pick) == 1 and pick.currency.iloc[0] == "GBP"   # maior score
    pick_mtf = t2_pick(d, theta=0.0, mtf=True)
    assert len(pick_mtf) == 1 and pick_mtf.currency.iloc[0] == "EUR"
    # GBP sem condição MTF a favor => cai; EUR tem H1 FP a favor


def test_plateau_prefers_stable_region():
    # pico isolado em 16; platô estável em 32/48
    sc = {16: 0.30, 24: 0.05, 32: 0.22, 48: 0.24}
    assert plateau_lens(sc) in (32, 48)

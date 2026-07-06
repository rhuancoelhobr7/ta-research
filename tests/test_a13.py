# -*- coding: utf-8 -*-
"""Testes do a13 — features de peso (causais), regras de veto e alvo."""
import numpy as np
import pandas as pd

from a13_peso_tokyo_ny import (FEATS13, KSLOPE, TARGET_HOURS, build_target,
                               peso_features, rule_RA_exaustao_contra,
                               rule_RB_transferencia_H4, rule_RC_amparo_D1)
from a12_css_geometry import TFS
from css_classic import G8


# ----------------------------------------------------------------------------
# Features de peso são causais (não veem o futuro)
# ----------------------------------------------------------------------------

def test_dpeso_causal():
    """Perturbar barras FUTURAS não muda dpeso/conv/retomada no presente."""
    idx = pd.date_range("2026-01-01", periods=60, freq="D")
    rng = np.random.default_rng(0)
    lines = pd.DataFrame(rng.normal(0, 0.2, (60, 8)), index=idx, columns=G8)
    cut = 40
    g1 = peso_features(lines)
    lines2 = lines.copy()
    lines2.iloc[cut:] += 5.0                      # futuro adulterado
    g2 = peso_features(lines2)
    for f in ("dpeso", "conv", "retomada", "dline"):
        pd.testing.assert_frame_equal(g1[f].iloc[:cut], g2[f].iloc[:cut])


def test_dpeso_definicao():
    """dpeso = |val|_t − |val|_{t−k}; conv exige fora da box E dpeso<0."""
    idx = pd.date_range("2026-01-01", periods=10, freq="D")
    lines = pd.DataFrame(0.0, index=idx, columns=G8)
    lines["EUR"] = [0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.3, 0.3, 0.3, 0.1]
    g = peso_features(lines)
    # t=6: |0.3| − |0.5| (k=3) = −0.2, fora da box → conv
    assert np.isclose(g["dpeso"].iloc[6]["EUR"], -0.2)
    assert g["conv"].iloc[6]["EUR"] == 1.0
    # t=9: dentro da box (0.1) → conv=0 mesmo com dpeso<0
    assert g["conv"].iloc[9]["EUR"] == 0.0


def test_retomada():
    """retomada = dentro da box, |val| crescendo, dline a favor da linha."""
    idx = pd.date_range("2026-01-01", periods=8, freq="D")
    lines = pd.DataFrame(0.0, index=idx, columns=G8)
    lines["GBP"] = [0.0, 0.0, 0.0, 0.02, 0.05, 0.08, 0.12, 0.18]
    g = peso_features(lines)
    assert g["retomada"].iloc[7]["GBP"] == 1.0    # 0.18 ≤ box, subindo
    lines.loc[:, "GBP"] = [0.0, 0.0, 0.0, 0.02, 0.05, 0.08, 0.12, 0.30]
    g2 = peso_features(lines)
    assert g2["retomada"].iloc[7]["GBP"] == 0.0   # 0.30 > box: já fora


# ----------------------------------------------------------------------------
# Regras de veto (frames sintéticos, padrão do test_a12)
# ----------------------------------------------------------------------------

def _g(overrides: dict) -> pd.DataFrame:
    g = pd.DataFrame({"currency": G8})
    for tf in TFS:
        for f in FEATS13:
            g[f"{tf}_{f}"] = 0.0
    for (cur, col), v in overrides.items():
        g.loc[g.currency == cur, col] = v
    return g


def test_RA_contra_o_macro():
    """CHF: macro (MN) fora da box esvaziando → prevê o CONTRÁRIO."""
    g = _g({("CHF", "MN_val"): -0.35, ("CHF", "MN_fora_box"): 1.0,
            ("CHF", "MN_dpeso"): -0.08})
    r = rule_RA_exaustao_contra(g)
    assert r and r[0][0] == "CHF" and r[0][1] == "ALTA"


def test_RA_bloqueada_pelo_D1():
    """Se o D1 está fora da box E abrindo no mesmo sinal do macro, veta."""
    g = _g({("CHF", "MN_val"): -0.35, ("CHF", "MN_fora_box"): 1.0,
            ("CHF", "MN_dpeso"): -0.08,
            ("CHF", "D1_val"): -0.30, ("CHF", "D1_fora_box"): 1.0,
            ("CHF", "D1_dpeso"): 0.05})
    assert rule_RA_exaustao_contra(g) == []


def test_RA_usa_W1_sem_MN():
    """Sem MN (NaN), o tier macro cai para o W1."""
    g = _g({("CHF", "W1_val"): -0.35, ("CHF", "W1_fora_box"): 1.0,
            ("CHF", "W1_dpeso"): -0.08})
    g.loc[:, [f"MN_{f}" for f in FEATS13]] = np.nan
    r = rule_RA_exaustao_contra(g)
    assert r and r[0][0] == "CHF" and r[0][1] == "ALTA"


def test_RB_transferencia_para_H4():
    """GBP: macro todo sem peso, H4 fora da box abrindo → segue o H4."""
    g = _g({("GBP", "MN_conv"): 1.0, ("GBP", "MN_fora_box"): 1.0,
            ("GBP", "MN_val"): -0.3, ("GBP", "MN_dpeso"): -0.02,
            ("GBP", "W1_conv"): 1.0, ("GBP", "W1_fora_box"): 1.0,
            ("GBP", "W1_val"): 0.25, ("GBP", "W1_dpeso"): -0.03,
            ("GBP", "D1_val"): -0.1, ("GBP", "D1_fora_box"): 0.0,
            ("GBP", "H4_val"): 0.3, ("GBP", "H4_fora_box"): 1.0,
            ("GBP", "H4_dpeso"): 0.07})
    r = rule_RB_transferencia_H4(g)
    assert r and r[0][0] == "GBP" and r[0][1] == "ALTA"


def test_RB_vetada_por_macro_com_peso():
    """Se o D1 está fora da box e NÃO convergindo, ainda tem peso: veta."""
    g = _g({("GBP", "D1_val"): -0.3, ("GBP", "D1_fora_box"): 1.0,
            ("GBP", "D1_conv"): 0.0,
            ("GBP", "H4_val"): 0.3, ("GBP", "H4_fora_box"): 1.0,
            ("GBP", "H4_dpeso"): 0.07})
    assert rule_RB_transferencia_H4(g) == []


def test_RC_segue_amparo_do_D1():
    """NZD: macro ALTA com peso, D1 fora da box em BAIXA abrindo + H1
    confirma → segue o D1 (BAIXA)."""
    g = _g({("NZD", "MN_val"): 0.35, ("NZD", "MN_fora_box"): 1.0,
            ("NZD", "D1_val"): -0.28, ("NZD", "D1_fora_box"): 1.0,
            ("NZD", "D1_dpeso"): 0.06, ("NZD", "H1_val"): -0.15})
    r = rule_RC_amparo_D1(g)
    assert r and r[0][0] == "NZD" and r[0][1] == "BAIXA"
    g2 = _g({("NZD", "MN_val"): 0.35, ("NZD", "MN_fora_box"): 1.0,
             ("NZD", "D1_val"): -0.28, ("NZD", "D1_fora_box"): 1.0,
             ("NZD", "D1_dpeso"): 0.06, ("NZD", "H1_val"): 0.15})
    assert rule_RC_amparo_D1(g2) == []            # H1 não confirma


# ----------------------------------------------------------------------------
# Alvo: só [T0, T0+15h)
# ----------------------------------------------------------------------------

def test_target_window(monkeypatch, tmp_path):
    """Perturbar closes DEPOIS de T0+15h não muda o alvo do dia."""
    idx = pd.date_range("2026-03-02 00:00", "2026-03-06 23:55", freq="5min")
    rng = np.random.default_rng(1)
    base = {}
    for a in ["EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]:
        sym = f"{a}USD" if a in ("EUR", "GBP", "AUD", "NZD") else f"USD{a}"
        base[sym] = pd.Series(
            np.exp(np.cumsum(rng.normal(0, 1e-4, len(idx)))), index=idx)

    import a13_peso_tokyo_ny as m
    monkeypatch.setattr(m, "load_closes", lambda: base)
    y1 = m.build_target(TARGET_HOURS)

    pert = {k: v.copy() for k, v in base.items()}
    day = pd.Timestamp("2026-03-03")
    after = day + pd.Timedelta(hours=TARGET_HOURS)
    for k in pert:
        pert[k].loc[pert[k].index >= after] *= 1.05
    monkeypatch.setattr(m, "load_closes", lambda: pert)
    y2 = m.build_target(TARGET_HOURS)

    a = y1[y1.day == day].set_index("currency").y
    b = y2[y2.day == day].set_index("currency").y
    pd.testing.assert_series_equal(a, b)

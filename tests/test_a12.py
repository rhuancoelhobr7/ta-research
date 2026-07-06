# -*- coding: utf-8 -*-
"""Testes do a12 — cutoffs anti-lookahead e regras pré-registradas."""
import numpy as np
import pandas as pd
import pytest

from a12_css_geometry import (_cutoff, rule_R1_exaustao_macro, rule_R2_cascata,
                              rule_R3_peso_relativo, GEOFEATS, TFS)
from css_classic import G8


def test_cutoffs_anti_lookahead():
    """Barra usada em T0 tem que estar FECHADA antes de T0 (regra dura 3)."""
    day = pd.Timestamp("2026-03-04")  # quarta-feira
    # H1: barra carimbada 23:00 de ontem fecha exatamente em T0 — permitida;
    # barra 00:00 do próprio dia NÃO.
    assert _cutoff("H1", day) == day - pd.Timedelta(hours=1)
    assert _cutoff("H4", day) == day - pd.Timedelta(hours=4)
    # D1: barra de ontem (carimbo D-1) fecha em T0 — permitida; a de hoje não.
    assert _cutoff("D1", day) == day - pd.Timedelta(days=1)
    # W1/MN: só período encerrado estritamente antes do dia.
    assert _cutoff("W1", day) < day
    assert _cutoff("MN", day) < day


def _g(overrides: dict) -> pd.DataFrame:
    """Grupo-dia sintético: 8 moedas, tudo neutro, com overrides pontuais."""
    g = pd.DataFrame({"currency": G8})
    for tf in TFS:
        for f in GEOFEATS:
            g[f"{tf}_{f}"] = 0.0
    for (cur, col), v in overrides.items():
        g.loc[g.currency == cur, col] = v
    return g


def test_R1_opera_contra_o_macro():
    """EUR fora da box (+0.35) com dline negativa → R1 prevê BAIXA no EUR."""
    g = _g({("EUR", "D1_val"): 0.35, ("EUR", "D1_fora_box"): 1.0,
            ("EUR", "D1_dline"): -0.10})
    r = rule_R1_exaustao_macro(g)
    assert r and r[0][0] == "EUR" and r[0][1] == "BAIXA"


def test_R1_nao_dispara_dentro_da_box():
    g = _g({("EUR", "D1_val"): 0.10, ("EUR", "D1_fora_box"): 0.0,
            ("EUR", "D1_dline"): -0.10})
    assert rule_R1_exaustao_macro(g) == []


def test_R2_segue_dline_confirmada():
    """dline_D1>0 com H4/H1 positivos → R2 prevê ALTA; sem confirmação, nada."""
    g = _g({("JPY", "D1_dline"): 0.08, ("JPY", "H4_val"): 0.15,
            ("JPY", "H1_val"): 0.22})
    r = rule_R2_cascata(g)
    assert r and r[0][0] == "JPY" and r[0][1] == "ALTA"
    g2 = _g({("JPY", "D1_dline"): 0.08, ("JPY", "H4_val"): -0.15,
             ("JPY", "H1_val"): 0.22})
    assert rule_R2_cascata(g2) == []


def test_R3_pondera_tfs_abertos():
    """GBP fora da box e abrindo em D1+H4 vence NZD só no H1."""
    g = _g({("GBP", "D1_val"): 0.30, ("GBP", "D1_fora_box"): 1.0,
            ("GBP", "D1_dline"): 0.05,
            ("GBP", "H4_val"): 0.25, ("GBP", "H4_fora_box"): 1.0,
            ("GBP", "H4_dline"): 0.04,
            ("NZD", "H1_val"): -0.30, ("NZD", "H1_fora_box"): 1.0,
            ("NZD", "H1_dline"): -0.05})
    r = rule_R3_peso_relativo(g)
    assert r[0][0] == "GBP" and r[0][1] == "ALTA"
    assert ("NZD", "BAIXA") in [(c, d) for c, d, _ in r]


def test_build_matrix_nao_ve_futuro():
    """Recorte da grade: posição buscada nunca ultrapassa o cutoff.

    Reproduz o searchsorted do build_matrix num índice sintético e garante
    que o carimbo escolhido é <= cutoff para todos os TFs.
    """
    idx = pd.date_range("2026-01-01", "2026-03-01", freq="h")
    day = pd.Timestamp("2026-02-10")
    for tf in TFS:
        cut = _cutoff(tf, day)
        pos = idx.searchsorted(cut, side="right") - 1
        assert idx[pos] <= cut < day

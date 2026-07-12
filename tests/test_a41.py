# -*- coding: utf-8 -*-
"""Testes do a41: TRAVA DO a38 (medir da entrada, não do início do dia),
gatilho condicional e saída inválida."""
import numpy as np

from costs import Costs
from preponderante import G8
from a41_mapa import basket_net, entry_state, exit_cols, NCOL, col_of


def _costs():
    return Costs(spread_pips={"GBPJPY": 1.0}, pip_size={"GBPJPY": 0.01},
                 slippage_pips=0.0, commission_pips=0.0)


def test_trava_a38_mede_da_entrada_nao_do_dia():
    # preço: 100 no início do dia, sobe a 200 na ENTRADA (col 24), FLAT até a saída.
    g = np.full((1, NCOL), 200.0, dtype="float32")
    g[0, :24] = np.linspace(100, 200, 24)          # todo o movimento ANTES da entrada
    pair_grids = {"GBPJPY": g}
    c = _costs()
    # entrada col 24 (=120min), saída col 48: movimento capturável = 0
    net, gross = basket_net(pair_grids, {"GBPJPY": 0.01}, "GBP",
                            np.array([24]), np.array([48]), np.array([1.0]), c)
    assert abs(gross[0]) < 1e-3                     # capturável ~0 (nada da entrada->saída)
    assert abs(net[0] - (-1.0)) < 1e-3             # só o custo (1 pip), NAO +100 pips
    # sanidade: se medisse do INÍCIO do dia (col 0) daria +10000 pips -> provaria o bug
    net0, gross0 = basket_net(pair_grids, {"GBPJPY": 0.01}, "GBP",
                              np.array([0]), np.array([48]), np.array([1.0]), c)
    assert gross0[0] > 9000                         # confirma que col 0 seria o erro


def _cur_grids(gbp):
    return {c: (gbp if c == "GBP" else np.zeros((1, NCOL), dtype="float32"))
            for c in G8}


def test_gatilho_condicional_dispara_e_ausencia_nao_gera_trade():
    gbp = np.linspace(0, 10, NCOL).reshape(1, NCOL).astype("float32")  # ER=1 sempre
    ecol, direction = entry_state(_cur_grids(gbp), 0, ("ER", 0.4))
    j = G8.index("GBP")
    assert ecol[0, j] >= 0 and direction[0, j] == 1.0     # GBP dispara cedo, sobe
    assert ecol[0, G8.index("USD")] == -1                  # USD plano: nunca dispara


def test_saida_antes_da_entrada_e_invalida():
    ecol = np.array([[col_of(120)]])                       # entrada col 24
    xc = exit_cols("tokyo", ecol, col_of(60))              # saída absoluta col 12 < entrada
    assert xc[0, 0] == -1

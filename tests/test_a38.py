# -*- coding: utf-8 -*-
"""Testes do a38: custo (net_pnl), regras congeladas e baseline simétrico."""
import numpy as np
import pandas as pd

from costs import Costs
from a38_economic import (side_for, build_trades, random_baseline,
                          A_ENTRY, B_ENTRY, EXIT)


def _costs():
    return Costs(spread_pips={"EURUSD": 1.0, "USDJPY": 1.0, "EURGBP": 1.0,
                              "GBPJPY": 1.0},
                 pip_size={"EURUSD": 0.0001, "USDJPY": 0.01, "EURGBP": 0.0001,
                           "GBPJPY": 0.01},
                 slippage_pips=0.1, commission_pips=0.0)


def test_net_pnl_buy_sell_e_custo_duas_pontas():
    c = _costs()
    # buy EURUSD 50 pips brutos; custo = spread 1.0 + 2x0.1 = 1.2
    r = c.net_pnl(1.1000, 1.1050, +1, "EURUSD")
    assert abs(r["gross_pips"] - 50) < 1e-6 and abs(r["cost_pips"] - 1.2) < 1e-9
    assert abs(r["net_pips"] - 48.8) < 1e-6
    # sell o mesmo movimento -> bruto -50, custo aplicado igual
    rs = c.net_pnl(1.1000, 1.1050, -1, "EURUSD")
    assert abs(rs["net_pips"] - (-51.2)) < 1e-6
    # par JPY: pip 0.01
    rj = c.net_pnl(150.00, 150.50, +1, "USDJPY")
    assert abs(rj["gross_pips"] - 50) < 1e-6


def test_side_for():
    assert side_for("GBP", "GBPJPY", +1) == +1      # base=GBP -> long GBP = buy
    assert side_for("GBP", "EURGBP", +1) == -1      # base=EUR -> long GBP = sell
    assert side_for("GBP", "GBPUSD", -1) == -1      # sinal negativo inverte


def test_regra_A_congelada_produz_trade_esperado():
    d = pd.Timestamp("2020-01-01")
    z = pd.DataFrame({"GBP": [3.0], "USD": [0.0], "EUR": [0.5], "JPY": [-3.0],
                      "CHF": [0.1], "CAD": [-0.2], "AUD": [0.3], "NZD": [-0.1]},
                     index=[d])
    px = pd.DataFrame({"GBPJPY": [200.0]}, index=[d])
    px2 = pd.DataFrame({"GBPJPY": [201.0]}, index=[d])
    single, _ = build_trades(z, px, px2, {"GBPJPY"}, "A")
    assert len(single) == 1
    t = single[0]
    assert t["pair"] == "GBPJPY" and t["side"] == +1    # top=GBP, bottom=JPY, long GBP


def test_baseline_aleatorio_mesmo_custo():
    c = _costs()
    # entry == exit -> bruto 0; net = -custo p/ QUALQUER lado (simetria do custo)
    tr = [{"pair": "EURUSD", "entry": 1.10, "exit": 1.10}]
    assert abs(random_baseline(tr, c) - (-1.2)) < 1e-9


def test_offsets_congelados():
    # trava contra "melhorias" futuras: horarios vem fixos do a35/a35-bis
    assert (A_ENTRY, B_ENTRY, EXIT) == (180, 240, 900)

# -*- coding: utf-8 -*-
"""Testes de preponderante.py: perfil de força, líder/anti-líder, réguas A/B."""
import itertools

import numpy as np

from preponderante import G8, currency_strength, leaders, regua_acerto


def _net_from_strength(s: dict) -> dict:
    """28 pares; net(base,quote) = s[base]-s[quote] (modelo linear de força)."""
    net = {}
    for a, b in itertools.combinations(G8, 2):
        net[a + b] = s[a] - s[b]
    return net


def test_currency_strength_lider_limpo():
    s = {"GBP": 10, "USD": 0, "EUR": 1, "JPY": -8, "CHF": 2, "CAD": -1,
         "AUD": 0.5, "NZD": -3}
    net = _net_from_strength(s)
    norm = {p: 1.0 for p in net}
    cs = currency_strength(net, norm)
    # GBP forte contra os 7 -> up=7, consist=7, dir=+1
    assert cs.loc["GBP", "up"] == 7 and cs.loc["GBP", "consist"] == 7
    assert cs.loc["GBP", "dir"] == 1
    # JPY fraco contra os 7 -> dn=7, dir=-1
    assert cs.loc["JPY", "dn"] == 7 and cs.loc["JPY", "dir"] == -1
    # net_strength ordena com a força latente
    assert cs["net_strength"].idxmax() == "GBP"
    assert cs["net_strength"].idxmin() == "JPY"


def test_leaders():
    s = {"GBP": 10, "USD": 0, "EUR": 1, "JPY": -8, "CHF": 2, "CAD": -1,
         "AUD": 0.5, "NZD": -3}
    net = _net_from_strength(s)
    L = leaders(currency_strength(net, {p: 1.0 for p in net}))
    assert L["leader"] == "GBP" and L["anti_leader"] == "JPY"
    assert L["prep_consist"] == 7


def test_regua_acerto():
    rank = ["GBP", "CHF", "EUR", "AUD", "USD", "CAD", "NZD", "JPY"]
    assert regua_acerto("GBP", rank) == {"A": True, "B2": True, "B3": True}
    assert regua_acerto("CHF", rank) == {"A": False, "B2": True, "B3": True}
    assert regua_acerto("EUR", rank) == {"A": False, "B2": False, "B3": True}
    assert regua_acerto("JPY", rank) == {"A": False, "B2": False, "B3": False}

# -*- coding: utf-8 -*-
"""Testes do a31: resolução do símbolo do par líder×anti-líder (pair_of)."""
from a31_par_campeao import pair_of


def test_pair_of_resolve_ordem():
    cols = {"EURUSD", "GBPJPY", "AUDNZD", "USDCAD"}
    assert pair_of("GBP", "JPY", cols) == "GBPJPY"    # ordem direta
    assert pair_of("JPY", "GBP", cols) == "GBPJPY"    # ordem invertida
    assert pair_of("USD", "EUR", cols) == "EURUSD"    # so a invertida existe
    assert pair_of("GBP", "CHF", cols) is None        # par ausente

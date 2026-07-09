# -*- coding: utf-8 -*-
"""Testes do a26b: duração até devolver ≥30% do pico de excursão favorável."""
import numpy as np

from a26b_persistencia import giveback_duration


def test_giveback_devolve_no_ponto_certo():
    # pico 10, cai p/ 5 na barra 3 -> devolveu 50% >= 30% -> retorna 3
    assert giveback_duration(np.array([10., 10., 10., 5.]), 0.30) == 3


def test_giveback_censura_se_nunca_devolve():
    fe = np.array([1., 2., 3., 4., 5.])       # só sobe
    assert giveback_duration(fe, 0.30) == len(fe)


def test_giveback_zero_sem_excursao():
    fe = np.array([0., 0., 0.])                # nada favorável -> censura
    assert giveback_duration(fe, 0.30) == 3


def test_giveback_pequeno_recuo_nao_dispara():
    # pico 10, recua só p/ 8 (20% < 30%) -> não dispara, censura no fim
    assert giveback_duration(np.array([10., 8., 9.]), 0.30) == 3

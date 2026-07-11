# -*- coding: utf-8 -*-
"""Testes do a37: controle pareado amostra do mesmo bin de volatilidade."""
import numpy as np
import pandas as pd

from a37_vol_pareado import match_control


def test_match_control_mesmo_bin():
    # bin 0: controle mfe=1; bin 1: controle mfe=100. Alinhados: 3 no bin0, 2 no bin1.
    al = pd.DataFrame({"vol": [1, 1, 1, 9, 9], "mfe": [50, 50, 50, 50, 50],
                       "bin": [0, 0, 0, 1, 1]})
    non = pd.DataFrame({"vol": [1, 1, 9, 9], "mfe": [1.0, 1.0, 100.0, 100.0],
                        "bin": [0, 0, 1, 1]})
    cm = match_control(al, non, seed=0)
    assert len(cm) == 5
    # 3 controles do bin0 (=1) e 2 do bin1 (=100)
    assert sorted(cm.tolist()) == [1.0, 1.0, 1.0, 100.0, 100.0]

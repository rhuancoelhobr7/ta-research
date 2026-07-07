"""Valores conhecidos das features F1-F3 em cenários construídos."""
import numpy as np
import pandas as pd

from comum import config
from fase3_features import features_do_dia, preparar

PARES = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]


def _dados(mov_h1_or: float):
    """120 dias úteis; ruído mínimo; nas últimas 48 BARRAS geradas cada par
    anda `mov_h1_or` por barra orientado ao USD (linha reta = 2 dias)."""
    cfg = config()
    dias = pd.bdate_range("2024-01-02", periods=121)
    alvo = dias[-1]
    rng = np.random.default_rng(1)
    idx = pd.DatetimeIndex([d + pd.Timedelta(hours=hh)
                            for d in dias[:-1] for hh in range(1, 25)])
    h1, d1 = {}, {}
    for par in PARES:
        sinal = 1.0 if par in cfg["dados"]["usd_base"] else -1.0
        inc = rng.normal(0, 2e-4, len(idx))
        inc[-48:] = sinal * mov_h1_or               # rampa USD-forte por BARRA
        s = pd.Series(np.exp(np.cumsum(inc)), index=idx)
        h1[par] = pd.DataFrame({"open": s, "high": s * 1.0003,
                                "low": s * 0.9997, "close": s,
                                "tick_volume": 1.0})
        dcl = s.resample("1D", label="right", closed="right").last().dropna()
        dop = s.resample("1D", label="right", closed="right").first().dropna()
        d1[par] = pd.DataFrame({"open": dop,
                                "high": pd.concat([dop, dcl], axis=1).max(axis=1) * 1.0002,
                                "low": pd.concat([dop, dcl], axis=1).min(axis=1) * 0.9998,
                                "close": dcl, "tick_volume": 1.0})
    labels = pd.DataFrame({"classe": "none", "breadth": 0, "mag_med": 0.5,
                           "atividade": 0.5}, index=dias[:-1])
    return cfg, h1, d1, labels, alvo


def test_f1_rampa_usd():
    """Rampa USD-forte nas 48h: breadth +1, ER ~1, magnitude alta."""
    cfg, h1, d1, labels, alvo = _dados(mov_h1_or=5e-4)
    f = features_do_dia(preparar(h1, d1, labels, cfg), alvo)
    assert f is not None
    for h in (8, 24, 48):
        assert f[f"f1_breadth_{h}"] == 1.0            # 7/7 a favor
        assert f[f"f1_er_{h}"] > 0.95                 # linha reta
        assert f[f"f1_mag_{h}"] > 3.0                 # >> mediana histórica
    assert f["f1_usd_share_24"] > 0.99                # movimento é do USD
    assert f["f2_close_pos"] > 0.8                    # fechou no topo (orientado)
    assert f["f3_usd_prot_prev"] == 0.0


def test_f1_simetria_baixa():
    cfg, h1, d1, labels, alvo = _dados(mov_h1_or=-5e-4)
    f = features_do_dia(preparar(h1, d1, labels, cfg), alvo)
    assert f["f1_breadth_24"] == -1.0
    assert f["f1_mag_24"] < -3.0
    assert f["f2_close_pos"] < 0.2


def test_f2_run_len_e_f3():
    """3 dias consecutivos USD-alta antes do alvo => run=+3; rótulo prévio
    aparece em f3."""
    cfg, h1, d1, labels, alvo = _dados(mov_h1_or=5e-4)
    # os últimos 2 dias completos da rampa são de alta orientada + o dia
    # parcial; conta a sequência terminando em D-1
    f = features_do_dia(preparar(h1, d1, labels, cfg), alvo)
    assert f["f2_run_len"] >= 2.0
    labels2 = labels.copy()
    labels2.iloc[-1] = {"classe": "up", "breadth": 7, "mag_med": 2.0,
                        "atividade": 2.0}
    f2 = features_do_dia(preparar(h1, d1, labels2, cfg), alvo)
    assert f2["f3_usd_prot_prev"] == 1.0
    assert f2["f3_atividade_prev"] == 2.0

"""Casos sintéticos com resposta conhecida para a rotulagem tri-classe."""
import numpy as np
import pandas as pd
import pytest

from comum import config, eh_usd_base
from fase1_rotulagem import rotular

PARES = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]


def _d1_sintetico(eventos: dict[int, dict[str, float]], n_dias: int = 110):
    """OHLC D1 dos 7 pares. `eventos[d][par]` = movimento ORIENTADO ao USD do
    dia d (positivo = USD forte). Dias sem evento: ruído +-0.001 alternado.
    Índice = FECHAMENTO da barra (contrato de carregar_ohlc)."""
    cfg = config()
    dias = pd.bdate_range("2024-01-02", periods=n_dias)
    rng = np.random.default_rng(7)
    out = {}
    for j, par in enumerate(PARES):
        mov_or = rng.choice([-0.001, 0.001], size=n_dias)      # ruído
        for d, m in eventos.items():
            mov_or[d] = m[par]
        # desfaz a orientação p/ obter o movimento cru do par
        mov = mov_or if eh_usd_base(par, cfg) else -mov_or
        o = np.full(n_dias, 1.0)
        c = o + mov
        h = np.maximum(o, c) + 0.001
        l = np.minimum(o, c) - 0.001
        out[par] = pd.DataFrame(
            {"open": o, "high": h, "low": l, "close": c,
             "tick_volume": np.ones(n_dias)},
            index=dias + pd.Timedelta(days=1))                  # fechamento
    return out, dias


BIG, TINY = 0.012, 0.0004


def test_rotulagem_casos_conhecidos():
    cfg = config()
    ev = {
        80: {p: +BIG for p in PARES},                            # 7/7 alta forte -> up
        85: {p: -BIG for p in PARES},                            # 7/7 baixa forte -> down
        90: {p: (+BIG if i < 5 else -BIG)                        # 5/7 -> none
             for i, p in enumerate(PARES)},
        95: {p: +TINY for p in PARES},                           # 7/7 mas magro -> none
        100: {p: (+BIG if i < 6 else -BIG)                       # 6/7 exato -> up
              for i, p in enumerate(PARES)},
    }
    d1, dias = _d1_sintetico(ev)
    lab = rotular(d1, cfg)

    assert lab.loc[dias[80], "classe"] == "up"
    assert lab.loc[dias[85], "classe"] == "down"
    assert lab.loc[dias[90], "classe"] == "none"
    assert lab.loc[dias[95], "classe"] == "none"     # magnitude < limiar
    assert lab.loc[dias[100], "classe"] == "up"      # breadth mínimo 6/7
    assert lab.loc[dias[80], "breadth"] == 7
    assert lab.loc[dias[85], "breadth"] == -7
    assert lab.loc[dias[100], "breadth"] == 5        # 6 up - 1 down
    # aquecimento das 60d: primeiros dias sem limiar ficam fora
    assert dias[10] not in lab.index


def test_rotulagem_dia_sem_limiar_do_proprio_dia():
    """O limiar vem dos 60 dias ANTERIORES: um dia gigante não pode elevar o
    próprio limiar a ponto de se desqualificar."""
    cfg = config()
    ev = {80: {p: +BIG for p in PARES}}
    d1, dias = _d1_sintetico(ev)
    lab = rotular(d1, cfg)
    assert lab.loc[dias[80], "classe"] == "up"
    assert lab.loc[dias[80], "mag_med"] == pytest.approx(
        lab.loc[dias[80], "atividade"])

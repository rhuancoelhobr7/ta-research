# -*- coding: utf-8 -*-
"""css_screen.py — Porte EXATO do CurrencySlopeStrength v2.20 (o CSS da TELA).

POR QUE DOIS PORTES COEXISTEM (este e css_classic.py):
  css_classic.py é o que a12/a13 TESTARAM (TMA=SMA(SMA) per=14, suav=3,
  slope relativo em ‰, renormalização por barra p/ ±2*box). É registro
  histórico congelado dos estudos — NÃO alterar. Este módulo porta o
  indicador que o dono efetivamente OLHA (indicators/
  CurrencySlopeStrength_v2_20.mq5), cuja matemática é materialmente
  diferente:

  | aspecto      | tela (v2.20, este módulo)         | css_classic (a12/a13) |
  |--------------|-----------------------------------|-----------------------|
  | TMA          | triangular Gernard, janela 20     | SMA(SMA), per=14      |
  | slope        | lookback 1, norm × sqrt(slope)    | suav=3                |
  | normalização | ATRrel(100) shift+10(+1), ÷10     | relativa (‰)          |
  | escala       | ×0.40, clamp ±(1.00−0.02), FIXA   | renorm por barra ±0.4 |

  A última linha muda a GEOMETRIA: com renorm por barra sempre existe
  moeda "fora da box"; na escala fixa pode não existir nenhuma (dia
  parado) — o caso que o css_classic não representa.

FIDELIDADE vs CAUSALIDADE (decisão documentada, não escondida):
  A TMA do MQ5 é CENTRADA no histórico — na barra de shift i ela usa até
  min(i,20) barras FUTURAS (repaint das últimas 20 barras da tela). Na
  barra corrente (i=0) não há futuro: a TMA é unilateral, e em i=1 usa
  1 barra futura (a corrente), etc. Este porte reproduz a LEITURA AO
  VIVO: para cada barra t, calcula o que a tela mostraria com t sendo a
  barra corrente (tma0 = TMA unilateral em t; tma1 = TMA em t−1 vendo a
  barra t como único futuro; ATRrel ancorado em t). É a única série
  causal, e é exatamente a sequência de leituras que o dono experimenta
  dia após dia. A linha HISTÓRICA desenhada na tela num instante fixo
  (centrada, com futuro ≤ instante) não é reproduzida — divergência
  inevitável, registrada aqui e no CHANGELOG.

CANDLE DE DOMINGO (InpAddSunday=true, default da tela): o shift do ATR
  vira 10+1=11. O feed desta corretora NÃO tem candles de domingo no D1
  (verificado: semanas de 5 barras), então o "+1" desloca uma barra a
  mais que o necessário — mas é o que a TELA usa; replicamos o default.

Números mágicos = defaults do indicador da tela (congelados):
  per=20 (fixo na fórmula Gernard, peso central 21), slope=1, atr_win=100,
  atr_shift=10(+1 domingo), atr_div=10, scale=0.40, scale_max=1.00
  (clamp em ±(scale_max−0.02)=±0.98), box=0.2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from css_classic import G8

# defaults do CurrencySlopeStrength v2.20 (a TELA) — congelados
PER = 20                 # janela Gernard (peso central 21, fixo na fórmula)
SLOPE = 1                # InpSlope
ATR_WIN = 100            # InpATRPeriod
ATR_SHIFT = 10           # shift base do ATRrel
ADD_SUNDAY = True        # InpAddSunday (default da tela) → shift efetivo 11
ATR_DIV = 10.0           # divisão por 10 do ATRrel original
SCALE = 0.40             # InpScale
SCALE_MAX = 1.00         # InpScaleMax → clamp ±(SCALE_MAX−0.02)
BOX = 0.20               # InpBox
KSLOPE = 3               # k das features de peso (pré-registrado no a13)

_W = np.array([21 - j for j in range(0, PER + 1)], dtype=float)  # 21,20,...,1
_SUMW0 = float(_W.sum())                 # TMA unilateral: 21+210 = 231
_SUMW1 = _SUMW0 + PER                    # TMA em t−1 com 1 futuro: +20 = 251


def tma_live(c: pd.Series) -> tuple[pd.Series, pd.Series]:
    """(tma0, tma1) da leitura ao vivo na barra t.

    tma0[t] — TMA Gernard em shift 0 (sem futuro):  Σ_{j=0..20} c[t−j]·(21−j) / 231
    tma1[t] — TMA Gernard em shift 1 vista de t (1 futuro disponível):
              (Σ_{j=0..20} c[t−1−j]·(21−j) + c[t]·20) / 251
    Ambas usam apenas dados ≤ t (causais)."""
    tma0_num = sum(c.shift(j) * _W[j] for j in range(PER + 1))
    tma0 = tma0_num / _SUMW0
    tma1 = (tma0_num.shift(1) + c * float(PER)) / _SUMW1
    return tma0, tma1


def atr_rel(c: pd.Series, win: int = ATR_WIN, add_sunday: bool = ADD_SUNDAY,
            div: float = ATR_DIV) -> pd.Series:
    """ATRrel causal ancorado em cada barra t (réplica do ATRrel do MQ5).

    MQ5: média de |Δclose| nos shifts [s, s+n), s=10(+1 domingo),
    n=min(100, copied−1−s), dividida por 10 e pelo preço atual. A versão
    por barra usa rolling(win, min_periods=2) — reproduz o encurtamento
    adaptativo do MQ5 quando há pouco histórico (ex.: MN)."""
    s = ATR_SHIFT + (1 if add_sunday else 0)
    d = c.diff().abs()
    atr = d.rolling(win, min_periods=2).mean().shift(s) / div
    return atr / c


def pair_contribution(c: pd.Series, scale: float = SCALE,
                      scale_max: float = SCALE_MAX) -> pd.Series:
    """Contribuição clampada do par na leitura ao vivo (ComputeNow, k=0):

    z = ((tma0 − tma1)/price) / (ATRrel·√slope);  val = clamp(z·scale, ±(max−0.02))
    """
    tma0, tma1 = tma_live(c)
    rs = np.sqrt(float(SLOPE))
    z = ((tma0 - tma1) / c) / (atr_rel(c) * rs + 1e-12)
    return (z * scale).clip(-(scale_max - 0.02), scale_max - 0.02)


def css_screen_lines(closes: pd.DataFrame, scale: float = SCALE,
                     scale_max: float = SCALE_MAX) -> pd.DataFrame:
    """Linhas do CSS da tela: média das contribuições orientadas por moeda.

    closes: colunas = símbolos; universo = o que for passado (o MQ5 detecta
    todos os pares G8 do Market Watch — replicado pelo chamador: usd7 ou
    all28, como nos estudos). SEM renormalização por barra — escala FIXA.
    """
    acc = pd.DataFrame(0.0, index=closes.index, columns=G8)
    cnt = pd.Series(0, index=G8, dtype=int)
    for sym in closes.columns:
        base, quote = sym[:3], sym[3:6]
        if base not in G8 or quote not in G8:
            continue
        val = pair_contribution(closes[sym], scale, scale_max)
        acc[base] = acc[base].add(val, fill_value=np.nan)
        acc[quote] = acc[quote].sub(val, fill_value=np.nan)
        cnt[base] += 1
        cnt[quote] += 1
    for c in G8:
        acc[c] = acc[c] / cnt[c] if cnt[c] > 0 else np.nan
    return acc


def css_screen_geometry(lines: pd.DataFrame, box: float = BOX,
                        k: int = KSLOPE) -> dict[str, pd.DataFrame]:
    """MESMAS features do a13 (val, fora_box, dist_box, dline, dpeso, conv,
    retomada), k_slope=3 pré-registrado — só a fonte das linhas muda."""
    from a13_peso_tokyo_ny import peso_features
    return peso_features(lines, box=box, k=k)

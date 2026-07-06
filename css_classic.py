# -*- coding: utf-8 -*-
"""css_classic.py — Porte fiel do Currency Slope Strength "clássico" (TMA-slope).

Diferenças estruturais vs. cssm_engine (motivo do a12, ver PLAN/CHANGELOG):
  1. slope da TMA causal por PAR, agregado por moeda (não índice sintético);
  2. NORMALIZAÇÃO POR BARRA: a cada barra, os 8 valores são reescalados para
     que a moeda mais forte fique em ±(2*box) — o CSS é um RANKING relativo,
     não força absoluta;
  3. a "box" ±box na escala normalizada é o objeto geométrico que o
     especialista lê (dentro/fora, linha subindo/descendo, perto do zero).

Fórmulas idênticas ao Cssm/CurrencySlopeStrength.mq5 (v2.x) fornecido pelo
usuário: TMA = SMA(SMA(close, per), per) causal (só barras fechadas — a TMA
"centrada" clássica repinta e NÃO é usada); slope_par = (TMA_t - TMA_{t-s})
/ TMA_{t-s} * 1000; moeda = média dos slopes orientados dos seus pares.

Funções puras; janelas para trás; sem estado global.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]


def tma_causal(close: pd.Series, per: int) -> pd.Series:
    """TMA causal: SMA(SMA(close, per), per). Só passado — não repinta."""
    return close.rolling(per).mean().rolling(per).mean()


def pair_slope(close: pd.Series, per: int, suav: int) -> pd.Series:
    """slope do par em "por mil": (TMA_t - TMA_{t-suav}) / TMA_{t-suav} * 1000."""
    t = tma_causal(close, per)
    t_ant = t.shift(suav)
    return (t - t_ant) / t_ant * 1000.0


def css_lines(closes: pd.DataFrame, per: int = 14, suav: int = 3,
              box: float = 0.2) -> pd.DataFrame:
    """Linhas do CSS clássico: DataFrame(time x G8), normalizado por barra.

    closes: colunas = símbolos ('EURUSD', ...); qualquer universo de pares —
    com os 7 pares USD reproduz o CurrencySlopeStrength.mq5 do usuário;
    com os 28 pares, a variante "full basket" do CSS original.
    A cada barra: valor_moeda = média dos slopes orientados; depois todos os
    8 valores são multiplicados por (2*box)/max|valor| — a mais forte fecha
    a barra em ±2*box, e a box ±box vira fronteira de ranking relativo.
    """
    acc = pd.DataFrame(0.0, index=closes.index, columns=G8)
    cnt = pd.Series(0, index=G8, dtype=int)
    for sym in closes.columns:
        base, quote = sym[:3], sym[3:6]
        if base not in G8 or quote not in G8:
            continue
        sp = pair_slope(closes[sym], per, suav)
        acc[base] = acc[base].add(sp, fill_value=0.0)
        acc[quote] = acc[quote].sub(sp, fill_value=0.0)
        cnt[base] += 1
        cnt[quote] += 1
    for c in G8:
        if cnt[c] > 0:
            acc[c] /= cnt[c]

    # normalização por barra (ranking relativo): mais forte = ±2*box
    max_abs = acc.abs().max(axis=1)
    fator = (2.0 * box) / max_abs.replace(0.0, np.nan)
    return acc.mul(fator, axis=0)


def css_geometry(lines: pd.DataFrame, box: float = 0.2,
                 k_slope: int = 3) -> dict[str, pd.DataFrame]:
    """Features geométricas da leitura do especialista, por moeda.

    val       — valor da linha normalizada
    fora_box  — |val| >= box (força/fraqueza "com peso")
    dist_box  — |val| - box (>0 fora; <0 dentro; contínua)
    dline     — inclinação da LINHA: val_t - val_{t-k} (ascendente/descendente)
    dist_zero — |val| (proximidade do zero = "combustível no fim")
    """
    aval = lines.abs()
    return {
        "val": lines,
        "fora_box": (aval >= box).astype(float),
        "dist_box": aval - box,
        "dline": lines - lines.shift(k_slope),
        "dist_zero": aval,
    }

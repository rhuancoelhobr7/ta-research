# -*- coding: utf-8 -*-
"""t0_normalize.py — TAREFA 0: escala percentil 0-100 do CSS (recria o site).

Para cada moeda G8 e cada TF, calcula o `val` bruto do CSS e o percentil
ROLANTE CAUSAL desse val dentro da propria serie do TF (janelas 100/200/500),
mapeado p/ 0-100 — "quao extremo e esse valor vs o historico recente", que e o
que currencystrengthzone.com mostra. Normalizacao POR TF (o percentil de H1 sai
da serie H1; nao mistura TFs) e SEM lookahead (a janela olha so p/ tras).

DOIS MOTORES em paralelo (decisao do dono, 2026-07-09):
  screen — css_screen.py: porte exato do CurrencySlopeStrength v2.20 (o CSS da
           TELA/site, escala fixa, box 0.2). E o PRODUTO — o val do a19/a20 e de
           toda a linguagem box/val/alinhamento da agenda a22-a26.
  cssm   — cssm_engine.py: motor CSSM_Contexto (val M = sign(t)*min(|t|/2,1)*ER).
           Objeto diferente; entra p/ COMPARACAO/ablacao no a24 (o CSSM agrega
           algo sobre o CSS da tela?).

Base: data/raw/M15_{SYMBOL}.parquet (s4_ingest_ta), tempo de servidor. TFs
maiores reamostrados de M15 por .last() do close (fechamento da barra agregada).

Saida: data/derived/css_{engine}_{tf}.parquet — por moeda C, colunas
  val_{C}, pct100_{C}, pct200_{C}, pct500_{C}. Insumo de a22-a26.

Uso: python t0_normalize.py [--tfs M15,H1,H4,D1,W1,MN] [--windows 100,200,500]
                            [--engines screen,cssm] [--no-parity]
"""
from __future__ import annotations

import argparse
import pathlib
import time

import numpy as np
import pandas as pd

from css_classic import G8
from css_screen import css_screen_lines
from cssm_engine import build_indices, compute_all, CssmParams

RAW = pathlib.Path("data/raw")
DERIVED = pathlib.Path("data/derived")

# base = M15; regras de reamostragem (H1 tb reamostrado, nao nativo aqui)
TF_RULES = {"M15": None, "H1": "1h", "H4": "4h", "D1": "1D",
            "W1": "W-FRI", "MN": "ME"}


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------

def load_m15_closes() -> pd.DataFrame:
    files = sorted(RAW.glob("M15_*.parquet"))
    if not files:
        raise SystemExit("sem data/raw/M15_*.parquet — rode s4_ingest_ta.py")
    return pd.DataFrame({f.stem.removeprefix("M15_"):
                         pd.read_parquet(f)["close"] for f in files})


def grid_tf(m15: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Reamostra os closes M15 p/ o TF (last close); M15 fica nativo."""
    rule = TF_RULES[tf]
    if rule is None:
        return m15
    return m15.resample(rule).last().dropna(how="all")


# ----------------------------------------------------------------------------
# val por motor
# ----------------------------------------------------------------------------

def val_screen(closes: pd.DataFrame) -> pd.DataFrame:
    """val do CSS da tela (css_screen): linhas por moeda, escala fixa."""
    return css_screen_lines(closes)


def val_cssm(closes: pd.DataFrame, p: CssmParams = CssmParams()) -> pd.DataFrame:
    """val M do CSSM_Contexto por moeda (coluna 'M' do motor)."""
    idx = build_indices({s: closes[s].dropna() for s in closes.columns},
                        align="inner")
    out = compute_all(idx, p)
    return pd.DataFrame({c: out[c]["M"] for c in G8}, index=idx.index)


VALFUN = {"screen": val_screen, "cssm": val_cssm}


# ----------------------------------------------------------------------------
# Percentil rolante causal
# ----------------------------------------------------------------------------

def rolling_pct(s: pd.Series, win: int) -> pd.Series:
    """Percentil 0-100 CAUSAL do valor corrente na janela dos ultimos `win`
    valores (inclui o atual). Usa Rolling.rank(pct=True): posto do valor
    corrente entre os `win` anteriores -> fracao [0,1] -> x100. min_periods=win
    (aquecimento = NaN). Sem lookahead: a janela termina em t."""
    return s.rolling(win, min_periods=win).rank(pct=True) * 100.0


def normalize_tf(vals: pd.DataFrame, windows: list[int]) -> pd.DataFrame:
    """val + pct{W} por moeda, num TF. Colunas: val_C, pct{W}_C."""
    cols = {}
    for c in vals.columns:
        cols[f"val_{c}"] = vals[c]
        for w in windows:
            cols[f"pct{w}_{c}"] = rolling_pct(vals[c], w)
    return pd.DataFrame(cols, index=vals.index)


# ----------------------------------------------------------------------------
# Paridade (sanity): H1 do css_screen vs css_parity_H1.csv congelado
# ----------------------------------------------------------------------------

def parity_check(m15: pd.DataFrame) -> str:
    ref_path = pathlib.Path("css_parity_H1.csv")
    if not ref_path.exists():
        return "parity: css_parity_H1.csv ausente — pulado"
    ref = pd.read_csv(ref_path)
    ref["ts"] = pd.to_datetime(ref["ts"], format="%Y.%m.%d %H:%M")
    ref = ref.set_index("ts")[G8]
    h1 = grid_tf(m15, "H1")
    got = val_screen(h1).reindex(ref.index).dropna(how="all")
    common = ref.index.intersection(got.index)
    if len(common) == 0:
        return "parity: sem timestamps em comum com a referencia"
    diff = (got.loc[common] - ref.loc[common]).abs()
    return (f"parity H1 (n={len(common)}): max|dif|={diff.values.max():.2e} "
            f"mediana={np.nanmedian(diff.values):.2e}")


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

def main(tfs: list[str], windows: list[int], engines: list[str],
         do_parity: bool = True) -> None:
    DERIVED.mkdir(parents=True, exist_ok=True)
    m15 = load_m15_closes()
    print(f"t0: M15 {m15.shape[0]} barras x {m15.shape[1]} pares")

    if do_parity:
        print("t0:", parity_check(m15))

    for tf in tfs:
        closes = grid_tf(m15, tf)
        for eng in engines:
            t = time.time()
            vals = VALFUN[eng](closes)
            df = normalize_tf(vals, windows)
            out = DERIVED / f"css_{eng}_{tf}.parquet"
            df.to_parquet(out)
            valid = int(df[[f"pct{windows[0]}_{G8[0]}"]].notna().sum().iloc[0])
            print(f"t0: {eng:6s} {tf:3s} {len(df):>7} barras "
                  f"(pct valido>={valid}) {time.time()-t:.1f}s -> {out.name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tfs", default="M15,H1,H4,D1,W1,MN")
    ap.add_argument("--windows", default="100,200,500")
    ap.add_argument("--engines", default="screen,cssm")
    ap.add_argument("--no-parity", action="store_true")
    a = ap.parse_args()
    main(a.tfs.split(","), [int(w) for w in a.windows.split(",")],
         a.engines.split(","), do_parity=not a.no_parity)

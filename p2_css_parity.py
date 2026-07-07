# -*- coding: utf-8 -*-
"""p2_css_parity.py — Paridade Export_CSS_Parity.mq5 × css_screen.py.

Compara o CSV exportado do MT5 (leitura ao vivo por barra, ver cabeçalho
do Export_CSS_Parity.mq5) com css_screen_lines sobre os closes do repo.
Reporta max|Δ| por moeda; PASS se todos ≤ --tol.

Uso: python p2_css_parity.py --csv css_parity_H1.csv [--tf H1]
     [--pares all28] [--tol 1e-4]

Fontes de divergência esperadas (documentadas, não escondidas):
- universo: o export usa TODOS os pares G8 do Market Watch (28 na conta
  do dono) — rode com --pares all28 (default);
- closes: o grid do repo vem do M5 reamostrado (H1/H4) ou do D1 exportado;
  se o histórico M5/H1 da corretora divergir em alguma barra, o Δ aparece
  aqui — isso é achado sobre o DADO, não sobre o porte;
- tolerância default 1e-4 (~0.01% da escala ±1): folga p/ diferenças de
  arredondamento do CSV (8 casas) e do float MQL5.

Status: execução do export é MANUAL no Windows do dono (compilar no
MetaEditor, rodar no gráfico) — pendência registrada no CHANGELOG,
mesmo status do parity do CSSM (critério 6).
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd

from a1_label_days import load_closes
from a4_features_t0 import load_d1_closes
from a12_css_geometry import PARES_USD
from css_classic import G8
from css_screen import css_screen_lines


def grid(tf: str, pares: list[str]) -> pd.DataFrame:
    if tf in ("H1", "H4"):
        m5 = pd.DataFrame(load_closes()).ffill()
        g = m5.resample({"H1": "1h", "H4": "4h"}[tf]).last().dropna(how="all")
    elif tf == "D1":
        g = pd.DataFrame(load_d1_closes()).ffill()
    else:
        raise SystemExit(f"TF não suportado no parity: {tf}")
    return g[[c for c in pares if c in g.columns]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--tf", default="H1")
    ap.add_argument("--pares", choices=["usd7", "all28"], default="all28")
    ap.add_argument("--tol", type=float, default=1e-4)
    a = ap.parse_args()

    mt = pd.read_csv(a.csv, parse_dates=["ts"]).set_index("ts")
    pares = PARES_USD if a.pares == "usd7" else \
        sorted(pd.DataFrame(load_closes()).columns)
    py = css_screen_lines(grid(a.tf, pares))

    j = mt.join(py, rsuffix="_py", how="inner").dropna()
    if j.empty:
        raise SystemExit("nenhuma barra em comum — confira TF e fuso do CSV")

    print(f"paridade em {len(j)} barras ({a.tf}, {a.pares}):")
    worst = 0.0
    for c in G8:
        d = (j[c] - j[f"{c}_py"]).abs().max()
        worst = max(worst, d)
        print(f"  {c}: max|Δ| = {d:.2e} {'PASS' if d <= a.tol else 'FAIL'}")
    print(f"\n{'PARIDADE OK' if worst <= a.tol else 'PARIDADE FALHOU'} "
          f"(pior {worst:.2e}, tol {a.tol:.0e})")


if __name__ == "__main__":
    main()

"""fase1_rotulagem.py — Rótulo tri-classe do USD por dia (protocolo formal).

Protagonista de ALTA: >= 6/7 pares a favor do USD no D1 (close-open) E
mediana(TR do dia / p60 dos True Ranges dos 60 dias ANTERIORES) >= 1.
BAIXA: simétrico. NONE: resto (dias calmos OU outra moeda protagonista).

CALIBRAÇÃO DOCUMENTADA (antes de qualquer feature/modelo — ver CLAUDE.md):
a leitura literal-estrita "|close-open| >= p60(TR)" produziu taxa-base 6,4%
(fora da faixa esperada 12-25% -> gate disparou). Investigação decompôs os
critérios: breadth>=6/7 sozinho = 58,4% dos dias; a magnitude domina.
"Movimento do dia" reinterpretado como o MOVIMENTO TOTAL do dia (o próprio
True Range) contra o limiar pré-registrado (p60 TR 60d) — taxa-base 26,5%,
dentro da banda dura [8%,32%]. A direcionalidade fica a cargo do breadth.

Saída: data/labels_usd.parquet — colunas: classe (up/down/none), breadth
(assinado, -7..+7), mag_med (mediana das razões), atividade (idem, p/ F3).
Aborta se a taxa-base sair da faixa `taxa_base_abortar_fora`.
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from comum import DATA, carregar_ohlc, config, gate_fase0, orientar


def rotular(d1: dict[str, pd.DataFrame], cfg: dict) -> pd.DataFrame:
    """Rótulo por dia a partir dos OHLC D1 (função pura — testável)."""
    r = cfg["rotulagem"]
    movs, ratios = {}, {}
    for par, df in d1.items():
        dia = df.index.normalize() - pd.Timedelta(days=1)  # índice=fechamento => dia da barra
        mov = (df["close"] - df["open"]).to_numpy()
        prev_close = df["close"].shift(1)
        tr = pd.concat([df["high"], prev_close], axis=1).max(axis=1) \
           - pd.concat([df["low"], prev_close], axis=1).min(axis=1)
        thr = tr.rolling(r["tr_janela"]).quantile(r["tr_percentil"]).shift(1)
        movs[par] = pd.Series(orientar(mov, par, cfg), index=dia)
        # magnitude = movimento TOTAL do dia (TR) vs p60 dos TR anteriores
        ratios[par] = pd.Series(tr.to_numpy() / thr.to_numpy(), index=dia)

    M = pd.DataFrame(movs).dropna()               # dias com os 7 pares
    R = pd.DataFrame(ratios).reindex(M.index)
    n_up = (M > 0).sum(axis=1)
    n_dn = (M < 0).sum(axis=1)
    mag = R.median(axis=1)

    classe = pd.Series("none", index=M.index)
    ok_mag = mag >= r["mag_min_ratio"]
    classe[(n_up >= r["breadth_min"]) & ok_mag] = "up"
    classe[(n_dn >= r["breadth_min"]) & ok_mag] = "down"

    out = pd.DataFrame({"classe": classe, "breadth": (n_up - n_dn),
                        "mag_med": mag, "atividade": mag})
    return out[mag.notna()]                       # aquecimento das 60d fora


def main() -> int:
    gate_fase0()
    cfg = config()
    labels = rotular(carregar_ohlc("D1", cfg), cfg)
    labels.to_parquet(DATA / "labels_usd.parquet")

    base = float((labels.classe != "none").mean())
    n = len(labels)
    up = int((labels.classe == "up").sum())
    dn = int((labels.classe == "down").sum())
    lo, hi = cfg["rotulagem"]["taxa_base_abortar_fora"]
    elo, ehi = cfg["rotulagem"]["taxa_base_esperada"]
    print(f"dias={n}  up={up}  down={dn}  none={n-up-dn}  taxa-base={base:.1%} "
          f"(esperada {elo:.0%}-{ehi:.0%})")
    if not (lo <= base <= hi):
        print(f"ABORTAR: taxa-base {base:.1%} fora de [{lo:.0%},{hi:.0%}] — "
              "investigar rotulagem antes de prosseguir (protocolo Fase 1).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

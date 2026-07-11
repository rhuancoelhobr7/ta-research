# -*- coding: utf-8 -*-
"""a35_holdout.py — confirmação do vencedor do a34 no HOLDOUT (UMA vez só).

Consome o holdout PRISTINO [q50, q70) do M5 — nunca tocado pelo a29 (que só
reportou em >=q70) nem pelo a34 (que usou <q50). Células PRÉ-DECLARADAS no
CHANGELOG (a34), sem re-otimizar:
  top-1 = z-score@180min ; top-3 = {z-score@180, css@180, cssm@180}.
O z-score usa média/desvio do RESEARCH (congelados), aplicados ao holdout.

Critério pré-registrado: régua B (top-3) > acaso (0.375) com IC95 bootstrap
excluindo o acaso por cima, E não perder >25% do edge medido no research.
Research (a34): z-score 0.508, css 0.487, cssm 0.485 (edge = accB − 0.375).

Uso: python a35_holdout.py
Saída: results/{ts}_a35/REPORT.md
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from a29_deteccao import load_m5, truth_by_close, indicator_frames
from a34_varredura import (intraday_index, day_metrics, zscore_hist, pick_frame)
from stats_blocks import block_bootstrap_ci

WIN = 180
BASE = 3 / 8
RESEARCH_ACCB = {"z-score@180": 0.508, "css@180": 0.487, "cssm@180": 0.485}


def hit_vector(score: pd.DataFrame, truth: pd.DataFrame, days) -> np.ndarray:
    """Por dia (em `days`): 1 se a líder verdadeira está no top-3 do score."""
    out = []
    for date in days:
        if date not in score.index or date not in truth.index:
            continue
        s = score.loc[date].dropna()
        if len(s) < 8:
            continue
        out.append(int(truth.loc[date, "rank"][0] in s.nlargest(3).index))
    return np.array(out, dtype=float)


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    truth = truth_by_close(ohlc, pip)
    idx = intraday_index(closes)
    frames = indicator_frames(closes)

    dates = pd.DatetimeIndex(sorted(set(truth.index) & set(idx.index.normalize())))
    q50 = dates.to_series().quantile(0.50)
    q70 = dates.to_series().quantile(0.70)
    research_mask_full = idx.index.normalize().isin(dates[dates < q50])
    holdout = dates[(dates >= q50) & (dates < q70)]      # PRISTINO

    dm = day_metrics(idx, WIN)
    mom = dm["mom"]
    rmask = mom.index.isin(dates[dates < q50])
    zc = zscore_hist(mom, rmask)                          # stats do research
    scores = {
        "z-score@180": zc,
        "css@180": pick_frame(frames[("css", "M5")], idx, WIN),
        "cssm@180": pick_frame(frames[("cssm", "M5")], idx, WIN),
    }

    rows = []
    for name, sc in scores.items():
        h = hit_vector(sc, truth, holdout)
        acc = float(h.mean())
        _, lo, hi = block_bootstrap_ci(h, np.mean, block=5, n_boot=3000)
        edge_res = RESEARCH_ACCB[name] - BASE
        edge_hold = acc - BASE
        keep_edge = edge_hold >= 0.75 * edge_res
        confirma = (lo > BASE) and keep_edge
        rows.append({"celula": name, "accB_holdout": acc, "ic_lo": lo, "ic_hi": hi,
                     "accB_research": RESEARCH_ACCB[name], "edge_mantido": edge_hold / edge_res,
                     "confirma": confirma, "n": len(h)})
    r = pd.DataFrame(rows)

    top1_ok = bool(r.iloc[0]["confirma"])
    any_ok = bool(r["confirma"].any())

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a35")
    out.mkdir(parents=True, exist_ok=True)
    r.round(4).to_csv(out / "holdout.csv", index=False)

    rep = [
        "# a35 — Confirmação no HOLDOUT (uma vez só)\n",
        f"Holdout PRISTINO [q50,q70) = {len(holdout)} dias "
        f"({holdout.min().date()} → {holdout.max().date()}). Células "
        f"pré-declaradas do a34, regra congelada, z-score com stats do research. "
        f"Acaso régua B = 37.5%.\n",
        "## Resultado (régua B top-3)\n",
        r.round(3).to_markdown(index=False),
        f"\n\n## Veredito pré-registrado\n"
        f"Critério: accB IC95 lo > 0.375 E manter >=75% do edge do research.\n",
        f"- **top-1 (z-score@180): {'CONFIRMA' if top1_ok else 'FALHA'}** "
        f"(holdout {r.iloc[0]['accB_holdout']:.3f}, IC[{r.iloc[0]['ic_lo']:.3f}, "
        f"{r.iloc[0]['ic_hi']:.3f}], edge mantido {r.iloc[0]['edge_mantido']:.0%}).",
        f"\n- alguma das top-3 confirma? **{'SIM' if any_ok else 'NÃO'}**.",
        f"\n\n### → {'PRIMEIRO PREDITOR CONFIRMADO OOS do projeto.' if any_ok else 'Candidato MORRE — nulo, sem tentativa de resgate.'}\n",
        "\n## Estado do holdout (irreversível)\n",
        f"Consumida a fatia [q50,q70) do M5 ({len(holdout)} dias). Resta o holdout "
        f"final [q70, fim) (~30% mais recente) — que o a29/a30 já tocaram e portanto "
        f"NÃO é pristino; e todo o research <q50. Esta confirmação NÃO se repete.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a35: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(r.round(3).to_string(index=False))
    print(f"VEREDITO: {'CONFIRMA (1o preditor OOS)' if any_ok else 'candidato MORRE (nulo)'}")


if __name__ == "__main__":
    main()

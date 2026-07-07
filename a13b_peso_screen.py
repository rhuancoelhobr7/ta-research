# -*- coding: utf-8 -*-
"""a13b_peso_screen.py — a13 re-executado com a lente da TELA (css_screen).

RE-EXECUÇÃO DE FIDELIDADE, PRÉ-REGISTRADA (mesma exceção única do a12b —
ver CHANGELOG 2026-07-06). Cópia mínima do a13 trocando SÓ a fonte das
linhas: css_screen_lines (defaults do v2.20, escala fixa).

TUDO idêntico ao a13 (por import): mesmas regras (RA exaustão-contra,
RB transferência-H4, RC amparo-D1), mesmo alvo (sinal do Δ índice
sintético em [T0, T0+15h) — Tokyo→pré-NY; sensibilidade 12h), mesmos
baselines, reality check 200 permutações, dias research, usd7 primário /
all28 sensibilidade, n<100 = insuficiente, teto de ML. Nada além disso.

Prior honesto: idem a12b — positivo improvável; o valor é fechar a lacuna
de fidelidade.

Uso: python a13b_peso_screen.py [--pares {usd7,all28}] [--target-hours 15]
     [--build-only]
Saída: data/features/css_screen_peso_t0*.parquet + results/{ts}_a13b/
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a12_css_geometry import PARES_USD, TFS, _cutoff, _grids
from a13_peso_tokyo_ny import (FEATS13, TARGET_HOURS, build_target,
                               evaluate, ml_ceiling, peso_features)
from css_classic import G8
from css_screen import BOX, KSLOPE, css_screen_lines
from splits_days import research_days

FEAT_PATH = pathlib.Path("data/features/css_screen_peso_t0.parquet")


def build_matrix(pares: list[str]) -> pd.DataFrame:
    """Idêntico ao a13.build_matrix, trocando css_lines -> css_screen_lines."""
    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    days = pd.DatetimeIndex(sorted(lab.day.unique()))
    grids = _grids(pares)

    per_tf: dict[str, dict[str, pd.DataFrame]] = {}
    for tf, closes in grids.items():
        lines = css_screen_lines(closes)          # <- ÚNICA mudança de fonte
        per_tf[tf] = peso_features(lines, box=BOX, k=KSLOPE)

    rows = []
    for day in days:
        snap = {}
        for tf in TFS:
            idx = per_tf[tf]["val"].index
            pos = idx.searchsorted(_cutoff(tf, day), side="right") - 1
            snap[tf] = None if pos < 0 else pos
        for cur in G8:
            rec = {"day": day, "currency": cur}
            for tf in TFS:
                pos = snap[tf]
                for feat in FEATS13:
                    rec[f"{tf}_{feat}"] = (np.nan if pos is None
                                           else per_tf[tf][feat][cur].iloc[pos])
            rows.append(rec)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", choices=["usd7", "all28"], default="usd7")
    ap.add_argument("--target-hours", type=float, default=TARGET_HOURS)
    ap.add_argument("--build-only", action="store_true")
    a = ap.parse_args()
    secundario = a.target_hours != TARGET_HOURS

    from a1_label_days import load_closes
    pares = PARES_USD if a.pares == "usd7" else \
        sorted(pd.DataFrame(load_closes()).columns)

    t0 = time.time()
    feat = build_matrix(pares)
    FEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    suffix = "" if a.pares == "usd7" else "_all28"
    path = FEAT_PATH.with_name(FEAT_PATH.stem + suffix + ".parquet")
    feat.to_parquet(path)
    print(f"matriz {feat.shape} -> {path} ({time.time()-t0:.0f}s)")
    if a.build_only:
        return

    ydf = build_target(a.target_hours)
    ymat = ydf.pivot(index="day", columns="currency", values="y")
    train, valid = research_days(pd.DatetimeIndex(feat.day.unique()))
    keep = set(train) | set(valid)
    df = feat[feat.day.isin(keep)].sort_values(
        ["day", "currency"]).reset_index(drop=True)
    ymat = ymat[ymat.index.isin(keep)]

    lines = [f"# a13b — Peso do CSS DA TELA em T0 → sinal Tokyo→NY "
             f"(pares: {a.pares}, janela: {a.target_hours:.0f}h"
             f"{' — SENSIBILIDADE' if secundario else ''})", "",
             f"Matriz: {feat.shape[0]} linhas | dias research: {len(keep)} | "
             f"lente: css_screen (v2.20, escala fixa) | k={KSLOPE}", "",
             "Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; "
             "exceção única autorizada pelo dono). Regras, alvo, baselines e "
             "critérios IDÊNTICOS ao a13 — só a fonte das linhas muda. "
             "Rótulo v1 e holdout intocados.", ""]
    survivors = evaluate(df, ymat, lines)
    ml_ceiling(df, ymat, lines)

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a13b")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"pares": a.pares, "target_hours": a.target_hours,
         "lente": "css_screen_v2.20", "k_slope": KSLOPE, "tfs": TFS,
         "n_dias_research": len(keep), "secundario": secundario}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md | sobreviventes: {survivors or 'nenhuma'}")


if __name__ == "__main__":
    main()

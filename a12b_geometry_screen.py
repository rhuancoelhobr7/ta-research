# -*- coding: utf-8 -*-
"""a12b_geometry_screen.py — a12 re-executado com a lente da TELA (css_screen).

RE-EXECUÇÃO DE FIDELIDADE, PRÉ-REGISTRADA (autorizada pelo dono em
2026-07-06 como exceção única ao compromisso "nada de retrospectivo até o
veredito do a14" — ver CHANGELOG):

O a12 testou a geometria do css_classic (renormalizado por barra); o
indicador da TELA (v2.20) usa escala FIXA — geometria diferente (pode não
haver moeda fora da box). Este estudo é a CÓPIA MÍNIMA do a12 trocando SÓ
a fonte das linhas: css_screen_lines (defaults da tela congelados).

TUDO idêntico ao a12 (por import, sem duplicação): mesmas regras
pré-registradas (R1 exaustão-macro, R2 cascata, R3 peso-relativo), mesmo
alvo (rótulo v1), mesmos 3 baselines, reality check 200 permutações, dias
research, usd7 primário / all28 sensibilidade, n<100 = insuficiente, teto
de ML. PROIBIDO e não feito: grid de parâmetros, regras novas, janelas
novas.

Prior honesto: a correção de lente pode mudar o resultado, mas os nulos do
motor (a5) e o teto de ML ~0.50 em todas as formulações anteriores tornam
um positivo improvável; o valor é fechar a lacuna de fidelidade de vez.

Uso: python a12b_geometry_screen.py [--pares {usd7,all28}] [--build-only]
Saída: data/features/css_screen_geometry_t0*.parquet + results/{ts}_a12b/
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a12_css_geometry import (GEOFEATS, PARES_USD, TFS, _cutoff, _grids,
                              contrast, evaluate, ml_ceiling)
from css_classic import G8, css_geometry
from css_screen import BOX, css_screen_lines
from splits_days import research_days

KSLOPE = 3                                   # mesmo k pré-registrado do a12
FEAT_PATH = pathlib.Path("data/features/css_screen_geometry_t0.parquet")


def build_matrix(pares: list[str]) -> pd.DataFrame:
    """Idêntico ao a12.build_matrix, trocando css_lines -> css_screen_lines."""
    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    days = pd.DatetimeIndex(sorted(lab.day.unique()))
    grids = _grids(pares)

    per_tf: dict[str, dict[str, pd.DataFrame]] = {}
    for tf, closes in grids.items():
        lines = css_screen_lines(closes)          # <- ÚNICA mudança de fonte
        per_tf[tf] = css_geometry(lines, box=BOX, k_slope=KSLOPE)

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
                for feat in GEOFEATS:
                    rec[f"{tf}_{feat}"] = (np.nan if pos is None
                                           else per_tf[tf][feat][cur].iloc[pos])
            rows.append(rec)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", choices=["usd7", "all28"], default="usd7")
    ap.add_argument("--build-only", action="store_true")
    a = ap.parse_args()

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

    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = set(train) | set(valid)
    df = feat.merge(lab[["day", "currency", "labeled", "direction", "score"]],
                    on=["day", "currency"], how="left")
    df["labeled"] = df["labeled"].fillna(False)
    df = df[df.day.isin(keep)].sort_values(["day", "currency"]).reset_index(drop=True)

    lines = [f"# a12b — Geometria do CSS DA TELA em T0 (pares: {a.pares})", "",
             f"Matriz: {feat.shape[0]} linhas | dias research: {len(keep)} | "
             f"lente: css_screen (v2.20, escala fixa) | k_slope={KSLOPE}", "",
             "Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; "
             "exceção única autorizada pelo dono). Regras, alvo, baselines e "
             "critérios IDÊNTICOS ao a12 — só a fonte das linhas muda.", ""]
    contrast(df, lines)
    survivors = evaluate(df, lines)
    ml_ceiling(df, lines)

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a12b")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"pares": a.pares, "lente": "css_screen_v2.20", "k_slope": KSLOPE,
         "tfs": TFS, "n_dias_research": len(keep)}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md | sobreviventes: {survivors or 'nenhuma'}")


if __name__ == "__main__":
    main()

"""a4_features_t0.py — Fase B: matriz de features do CSSM em T0.

ESPECIFICAÇÃO (PLAN.md §5 e §3):
Entrada: data/raw M5 (2a) e D1_ (4a); labels p/ obter a lista de dias e T0.
TFs e MODO por disponibilidade de barras (gravados nos metadados por TF):
  COMPLETO (M30, H1, H4 dos M5; D1 dos D1_): features + estados 0-3; um dia
    só recebe z-features/estado se >= w_mid + 150 barras FECHADAS antes do
    seu T0 (z_win efetivo = min(500, disponível) — o rolling com min_periods
    do engine implementa o min automaticamente; o piso de 150 é o gate).
  REDUZIDO (W1, resample W-FRI dos D1_): t, er, M, pers, dir; SEM acc_z e
    conv_z; estados restritos a Ruído/Madura; gate = w_mid + 20 barras.
  OMITIDO: MN (exigiria 9-20 anos; W1 é o macro-teto).
SEM LOOKAHEAD: cada TF é indexado pelo timestamp de FECHAMENTO da barra
(label da barra + duração) e a linha (dia, moeda) usa a última barra com
fechamento <= T0 (D1 => a barra de ontem). Teste em tests/test_features_t0.py.
Saída: data/features/features_t0.parquet + features_t0_meta.json.

Uso: python a4_features_t0.py
"""
from __future__ import annotations

import json, pathlib
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes
from cssm_engine import (G8, CssmParams, ST_MATURE, ST_NOISE, build_indices,
                         compute_currency, resample_closes)

RAW = pathlib.Path("data/raw")
OUT = pathlib.Path("data/features")

BASE_COLS = ["state", "dir", "M", "t", "pers", "er"]
Z_COLS = ["acc_z", "conv_z"]

# (nome, fonte, regra resample, duração da barra, modo, gate de feature-barras)
TF_SPECS = [
    ("M30", "m5", "30min", pd.Timedelta("30min"), "completo", 150),
    ("H1",  "m5", "1h",    pd.Timedelta("1h"),    "completo", 150),
    ("H4",  "m5", "4h",    pd.Timedelta("4h"),    "completo", 150),
    ("D1",  "d1", None,    pd.Timedelta("1D"),    "completo", 150),
    ("W1",  "d1", "W-FRI", pd.Timedelta("1D"),    "reduzido", 20),
]


def load_d1_closes() -> dict[str, pd.Series]:
    files = sorted(RAW.glob("D1_*.parquet"))
    if not files:
        raise SystemExit("data/raw sem D1_*.parquet — rode s0 (CLAUDE.md).")
    return {f.stem.removeprefix("D1_"): pd.read_parquet(f)["close"]
            for f in files}


def _reduced_state(t: np.ndarray, pers: np.ndarray, p: CssmParams) -> np.ndarray:
    """Modo reduzido: só Ruído/Madura (sem z-features não há Emergindo/Exausta)."""
    state = np.where((np.abs(t) >= p.t_gate) & (pers >= p.persist),
                     float(ST_MATURE), float(ST_NOISE))
    return np.where(np.isnan(t) | np.isnan(pers), -1.0, state)


def tf_feature_tables(m5_closes: dict[str, pd.Series],
                      d1_closes: dict[str, pd.Series],
                      p: CssmParams = CssmParams()):
    """{tf: {moeda: DataFrame de features indexado pelo FECHAMENTO da barra}}.

    Função pura — testável para lookahead: truncar os closes em T0 não pode
    mudar nenhuma linha com índice (fechamento) <= T0.
    """
    tables: dict[str, dict[str, pd.DataFrame]] = {}
    for tf, src, rule, delta, mode, _gate in TF_SPECS:
        closes = m5_closes if src == "m5" else d1_closes
        closes_tf = resample_closes(closes, rule) if rule else closes
        indices = build_indices(closes_tf, align="inner")
        per_cur = {}
        for c in G8:
            f = compute_currency(indices[c], p)
            if mode == "reduzido":
                f = f[["t", "er", "pers", "M", "dir"]].copy()
                f["state"] = _reduced_state(f["t"].to_numpy(),
                                            f["pers"].to_numpy(), p)
            else:
                f = f[BASE_COLS + Z_COLS].copy()
            f.index = f.index + delta          # timestamp de FECHAMENTO
            per_cur[c] = f
        tables[tf] = per_cur
    return tables


def features_at_t0(tables, days: pd.DatetimeIndex, t0_hour: float,
                   p: CssmParams = CssmParams()) -> pd.DataFrame:
    """Uma linha por (dia, moeda): última barra FECHADA (<= T0) de cada TF."""
    t0s = pd.DatetimeIndex([d + timedelta(hours=t0_hour) for d in days])
    rows = {"day": np.repeat(days, len(G8)),
            "currency": np.tile(G8, len(days))}
    out = pd.DataFrame(rows)

    gates = {tf: gate for tf, *_rest, gate in
             [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in TF_SPECS]}
    modes = {s[0]: s[4] for s in TF_SPECS}
    for tf, per_cur in tables.items():
        cols = BASE_COLS + (Z_COLS if modes[tf] == "completo" else [])
        block = {f"{tf}_{col}": np.full(len(out), np.nan) for col in cols}
        for ci, c in enumerate(G8):
            f = per_cur[c]
            close_times = f.index.to_numpy()
            pos = np.searchsorted(close_times, t0s.to_numpy(), side="right") - 1
            ok = pos >= 0
            # gate de aquecimento: exige w_mid + gate barras fechadas até T0
            enough = pos + 1 >= p.w_mid + gates[tf]
            sel = np.where(ok, pos, 0)
            for col in cols:
                vals = f[col].to_numpy()[sel]
                vals = np.where(ok, vals, np.nan)
                if col in ("state", *Z_COLS):
                    vals = np.where(enough, vals, np.nan)
                block[f"{tf}_{col}"][ci::len(G8)] = vals
        for k, v in block.items():
            out[k] = v
    return out


def main():
    meta_lab = json.loads(
        pathlib.Path("data/labels/labels_v1_meta.json").read_text())
    if not meta_lab.get("frozen"):
        raise SystemExit("Definição v1 NÃO congelada — rode a1 --freeze antes "
                         "de qualquer feature da Fase B (regra dura nº 1).")
    labels = pd.read_parquet("data/labels/labels_v1.parquet")
    days = pd.DatetimeIndex(sorted(labels.day.unique()))

    m5 = load_closes()
    d1 = load_d1_closes()
    tables = tf_feature_tables(m5, d1)
    feats = features_at_t0(tables, days, meta_lab["t0_hour"])

    OUT.mkdir(parents=True, exist_ok=True)
    feats.to_parquet(OUT / "features_t0.parquet")

    tf_meta = {}
    for tf, src, rule, delta, mode, gate in TF_SPECS:
        cover = feats[[c for c in feats.columns if c.startswith(f"{tf}_")]]
        tf_meta[tf] = {
            "fonte": src, "resample": rule, "modo": mode,
            "gate_feature_barras": gate,
            "cobertura_state_pct": round(100 * float(
                cover[f"{tf}_state"].notna().mean()), 1),
        }
    meta = {"t0_hour": meta_lab["t0_hour"], "n_days": len(days),
            "n_rows": len(feats), "tfs": tf_meta, "mn": "omitido (PLAN §3)",
            "labels_version": meta_lab["version"]}
    (OUT / "features_t0_meta.json").write_text(json.dumps(meta, indent=2))
    print(f"{len(feats)} linhas (dia x moeda) | TFs: "
          + ", ".join(f"{tf}({m['modo']},{m['cobertura_state_pct']}%)"
                      for tf, m in tf_meta.items()))


if __name__ == "__main__":
    main()

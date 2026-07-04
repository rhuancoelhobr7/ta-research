"""a1_label_days.py — Fase A1: rotula dias de tendência absoluta por moeda.

Definição operacional v1 (PLAN.md §2), para cada dia D e moeda C na janela
W = [T0, T0+window_hours]:
  breadth : fração dos pares de C com log-retorno orientado > 0 na janela
  z       : retorno do índice sintético de C em W ÷ desvio-padrão dos retornos
            de janela dos ÚLTIMOS vol_lookback dias (shift(1) — só passado)
  er      : Efficiency Ratio intraday do índice de C dentro de W (barras M5)
Rótulo: breadth >= breadth_min E |z| >= z_min E er >= er_min.
Direção = sinal de z. score = |z| * breadth * er.

Entrada : data/raw/{SYMBOL}.parquet (closes M5, contrato do CLAUDE.md)
Saída   : data/labels/labels_v1.parquet  (uma linha por dia x moeda)
          data/labels/labels_v1_meta.json (parâmetros — CONGELAMENTO)
          data/labels/sensitivity_grid.csv (taxa-base por combinação de limiares)

Uso: python a1_label_days.py [--t0-hour 0] [--window-hours 12]
     [--breadth-min 0.857] [--z-min 1.0] [--er-min 0.25] [--freeze]

Sem --freeze, roda em modo exploração (não grava meta de congelamento).
"""
from __future__ import annotations

import argparse, json, pathlib
from datetime import timedelta

import numpy as np
import pandas as pd

from cssm_engine import G8, build_indices

RAW = pathlib.Path("data/raw")
OUT = pathlib.Path("data/labels")


# ----------------------------------------------------------------------------

def load_closes() -> dict[str, pd.Series]:
    files = sorted(RAW.glob("*.parquet"))
    files = [f for f in files if not f.name.startswith("_") and "D1_" not in f.name]
    if not files:
        raise SystemExit("data/raw vazio — rode s0 ou forneça os dados (CLAUDE.md).")
    return {f.stem: pd.read_parquet(f)["close"] for f in files}


def pair_map(symbols: list[str]) -> dict[str, list[tuple[str, int]]]:
    """{moeda: [(symbol, +1 se base / -1 se cotada), ...]}"""
    out: dict[str, list[tuple[str, int]]] = {c: [] for c in G8}
    for sym in symbols:
        found = sorted({c for c in G8 if c in sym.upper()},
                       key=lambda c: sym.upper().find(c))
        if len(found) != 2:
            continue
        out[found[0]].append((sym, +1))
        out[found[1]].append((sym, -1))
    return out


def window_bounds(day: pd.Timestamp, t0_hour: float, window_hours: float):
    t0 = day + timedelta(hours=t0_hour)
    return t0, t0 + timedelta(hours=window_hours)


def window_return(series: pd.Series, t0, t1) -> float:
    """log-retorno do primeiro close >= t0 ao último close <= t1 (NaN se vazio)."""
    w = series.loc[t0:t1]
    if len(w) < 2:
        return np.nan
    return float(np.log(w.iloc[-1] / w.iloc[0]))


def window_diff(series: pd.Series, t0, t1) -> float:
    """Variação do ÍNDICE SINTÉTICO na janela (já em log-espaço: diferença)."""
    w = series.loc[t0:t1]
    if len(w) < 2:
        return np.nan
    return float(w.iloc[-1] - w.iloc[0])


def window_er(series: pd.Series, t0, t1) -> float:
    """Efficiency Ratio da série (índice sintético) dentro da janela."""
    w = series.loc[t0:t1].to_numpy()
    if len(w) < 8:
        return np.nan
    d = np.diff(w)
    path = np.abs(d).sum()
    return float(abs(w[-1] - w[0]) / path) if path > 0 else 0.0


# ----------------------------------------------------------------------------

def compute_day_table(closes: dict[str, pd.Series], t0_hour: float,
                      window_hours: float, vol_lookback: int = 63,
                      min_pairs: int = 6) -> pd.DataFrame:
    """Tabela dia x moeda com breadth, idx_ret, er (métricas cruas, sem limiar)."""
    pm = pair_map(list(closes))
    indices = build_indices(closes, align="inner")
    days = pd.DatetimeIndex(sorted(set(indices.index.normalize())))

    rows = []
    for day in days:
        t0, t1 = window_bounds(day, t0_hour, window_hours)
        if len(indices.loc[t0:t1]) < 8:      # dia sem pregão na janela (fds/feriado)
            continue
        for c in G8:
            rets = np.array([sgn * window_return(closes[sym], t0, t1)
                             for sym, sgn in pm[c]], dtype=float)
            rets = rets[~np.isnan(rets)]
            if len(rets) < min_pairs:
                continue
            rows.append({
                "day": day, "currency": c,
                "n_pairs": len(rets),
                "breadth": float((rets > 0).mean()),
                "idx_ret": window_diff(indices[c], t0, t1),
                "er": window_er(indices[c], t0, t1),
            })
    df = pd.DataFrame(rows)

    # z: normaliza idx_ret pela volatilidade PASSADA das janelas da mesma moeda
    df = df.sort_values(["currency", "day"]).reset_index(drop=True)
    sd = df.groupby("currency")["idx_ret"].transform(
        lambda s: s.rolling(vol_lookback, min_periods=20).std(ddof=1).shift(1))
    df["z"] = df["idx_ret"] / sd
    return df.dropna(subset=["z", "er", "breadth"]).reset_index(drop=True)


def apply_labels(df: pd.DataFrame, breadth_min: float, z_min: float,
                 er_min: float) -> pd.DataFrame:
    out = df.copy()
    # breadth orientado à direção do movimento (breadth mede fração >0;
    # para baixa, a fração relevante é 1-breadth)
    dir_sign = np.sign(out["z"])
    breadth_dir = np.where(dir_sign >= 0, out["breadth"], 1.0 - out["breadth"])
    out["breadth_dir"] = breadth_dir
    out["labeled"] = ((breadth_dir >= breadth_min) &
                      (out["z"].abs() >= z_min) & (out["er"] >= er_min))
    out["direction"] = np.where(dir_sign >= 0, "ALTA", "BAIXA")
    out["score"] = out["z"].abs() * breadth_dir * out["er"]
    return out


def sensitivity_grid(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for b in (5 / 7, 6 / 7, 1.0):
        for z in (0.8, 1.0, 1.5):
            for e in (0.15, 0.25, 0.35):
                lab = apply_labels(df, b, z, e)
                per_day = lab[lab.labeled].groupby("day").size()
                n_days = df["day"].nunique()
                rows.append({
                    "breadth_min": round(b, 3), "z_min": z, "er_min": e,
                    "labels_total": int(lab.labeled.sum()),
                    "days_with_label_pct": round(100 * len(per_day) / n_days, 1),
                    "mean_labels_per_day": round(lab.labeled.sum() / n_days, 2),
                })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--t0-hour", type=float, default=0.0,
                    help="hora do dia (fuso do servidor) do T0; 0 = meia-noite "
                         "do servidor (~pré-Tokyo em servidores GMT+2/3)")
    ap.add_argument("--window-hours", type=float, default=12.0)
    ap.add_argument("--breadth-min", type=float, default=6 / 7)
    ap.add_argument("--z-min", type=float, default=1.0)
    ap.add_argument("--er-min", type=float, default=0.25)
    ap.add_argument("--vol-lookback", type=int, default=63)
    ap.add_argument("--freeze", action="store_true",
                    help="grava meta de CONGELAMENTO v1 (PLAN.md §7)")
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    closes = load_closes()
    raw = compute_day_table(closes, a.t0_hour, a.window_hours, a.vol_lookback)
    labeled = apply_labels(raw, a.breadth_min, a.z_min, a.er_min)
    labeled.to_parquet(OUT / "labels_v1.parquet")
    sensitivity_grid(raw).to_csv(OUT / "sensitivity_grid.csv", index=False)

    meta = {"version": "v1", "frozen": bool(a.freeze),
            "t0_hour": a.t0_hour, "window_hours": a.window_hours,
            "breadth_min": a.breadth_min, "z_min": a.z_min,
            "er_min": a.er_min, "vol_lookback": a.vol_lookback,
            "n_days": int(raw["day"].nunique()),
            "n_labels": int(labeled.labeled.sum())}
    (OUT / "labels_v1_meta.json").write_text(json.dumps(meta, indent=2))

    n_days = raw["day"].nunique()
    per_day = labeled[labeled.labeled].groupby("day").size()
    print(f"{n_days} dias avaliados | {int(labeled.labeled.sum())} rótulos | "
          f"{100 * len(per_day) / n_days:.1f}% dos dias com >=1 rótulo | "
          f"média {labeled.labeled.sum() / n_days:.2f} rótulos/dia")
    if a.freeze:
        print("DEFINIÇÃO v1 CONGELADA (labels_v1_meta.json).")


if __name__ == "__main__":
    main()

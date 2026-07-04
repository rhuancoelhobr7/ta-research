"""a9_mtf_matrix.py — Estudo v2, etapa 2: matriz MTF fiel em T0 e T0+4h.

Para cada (dia, moeda) do período RESEARCH e cada lente intraday da grade
(w_mid ∈ {16,24,32,48} aplicada a M30/H1/H4), calcula as CONDIÇÕES do
PROTOCOLO.md (N/FN/FP/FR/EX + direção) em MN, W1, D1, H4, H1, M30:

  - snapshot em T0: só barras FECHADAS antes de T0 (teste de lookahead em
    tests/test_a9.py);
  - snapshot em T0+4h: condições nos TFs intraday + realizado de [T0,T0+4h]
    (ret4h, mini-breadth dos 7 pares, mini-ER) e ret_4_12 (alvo bruto da
    tarefa 2 do a10 — [T0+4h, T0+12h]; NUNCA usar como feature).

Lentes/TFs: M30/H1/H4 completos com gates calibrados (calibrate_gates);
D1 completo com a lente padrão v1 (w=64); W1 reduzido (w=64 semanas);
MN reduzido (w=24 meses) — exige D1 de ~7 anos, senão MN sai registrado.
Condições em modo reduzido: FP/FR/N apenas (PROTOCOLO.md §1).

Saída: data/features/v2_mtf.parquet (formato longo, coluna `lens`)
       + v2_mtf_meta.json (gates por lente, modos, cobertura).

Uso: python a9_mtf_matrix.py
"""
from __future__ import annotations

import json, pathlib
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes, pair_map, window_er, window_return
from a4_features_t0 import load_d1_closes
from cssm_engine import (G8, CssmParams, build_indices, calibrate_gates,
                         compute_currency, lens_params, resample_closes)
from splits_days import research_days

OUT = pathlib.Path("data/features")

LENSES = (16, 24, 32, 48)
FR_AGE = 40                      # PROTOCOLO §1: idade > 40 barras => FR
COND_N, COND_FN, COND_FP, COND_FR, COND_EX = 0.0, 1.0, 2.0, 3.0, 4.0
W_W1, W_MN = 64, 24
COND_NAMES = {0: "N", 1: "FN", 2: "FP", 3: "FR", 4: "EX"}


# ----------------------------------------------------------------------------
# Condições do PROTOCOLO
# ----------------------------------------------------------------------------

def _runlen(mask: np.ndarray) -> np.ndarray:
    """Comprimento da sequência de True terminando em cada posição."""
    idx = np.arange(len(mask))
    last_false = np.maximum.accumulate(np.where(~mask, idx, -1))
    return np.where(mask, idx - last_false, 0)


def _runlen_same_nonzero(key: np.ndarray) -> np.ndarray:
    """Comprimento da sequência do MESMO valor não-zero de key."""
    same = np.zeros(len(key), dtype=bool)
    same[1:] = (key[1:] == key[:-1]) & (key[1:] != 0)
    start = (key != 0) & ~same
    out = np.zeros(len(key), dtype=int)
    run = 0
    for i in range(len(key)):          # O(n); séries de TF são pequenas
        run = run + 1 if same[i] else (1 if start[i] else 0)
        out[i] = run
    return out


def protocol_full(f: pd.DataFrame, fr_age: int = FR_AGE) -> pd.DataFrame:
    """Condições em modo completo (PROTOCOLO §1). f = saída do engine."""
    state = f["state"].to_numpy(dtype=float)
    d = f["dir"].to_numpy(dtype=float)
    accz = f["acc_z"].to_numpy(dtype=float)
    mature = state == 2
    age_mat = _runlen(mature)
    decel = accz * d < 0
    cond = np.full(len(f), COND_N)
    cond[state == 1] = COND_FN
    cond[mature] = COND_FP
    cond[mature & (decel | (age_mat > fr_age))] = COND_FR
    cond[state == 3] = COND_EX
    cond[state == -1] = np.nan

    active = np.isin(cond, (COND_FN, COND_FP, COND_FR))
    key = np.where(active, d, 0.0)
    return pd.DataFrame({"cond": cond, "dir": d, "M": f["M"].to_numpy(),
                         "age": _runlen_same_nonzero(key)}, index=f.index)


def protocol_reduced(f: pd.DataFrame, gate: float) -> pd.DataFrame:
    """Condições em modo reduzido: FP/FR/N (FN/EX indisponíveis)."""
    t = f["t"].to_numpy(dtype=float)
    pers = f["pers"].to_numpy(dtype=float)
    at = np.abs(t)
    fp = (at >= gate) & (pers >= 0.55)
    at_prev5 = np.concatenate([np.full(5, np.nan), at[:-5]])
    falling = at < at_prev5
    cond = np.where(fp, np.where(falling, COND_FR, COND_FP), COND_N)
    cond = np.where(np.isnan(t) | np.isnan(pers), np.nan, cond)
    return pd.DataFrame({"cond": cond, "dir": np.sign(t), "t": t},
                        index=f.index)


# ----------------------------------------------------------------------------
# Núcleo puro
# ----------------------------------------------------------------------------

def _close_indexed(indices: pd.DataFrame, p: CssmParams, shift) -> dict:
    out = {}
    for c in G8:
        f = compute_currency(indices[c], p)
        f.index = shift(f.index)
        out[c] = f
    return out


def _lookup(f: pd.DataFrame, cols: list[str], when: np.ndarray,
            min_bars: int) -> dict:
    pos = np.searchsorted(f.index.to_numpy(), when, side="right") - 1
    ok = pos + 1 >= min_bars                    # gate de aquecimento
    sel = np.where(pos >= 0, pos, 0)
    return {c: np.where(ok, f[c].to_numpy(dtype=float)[sel], np.nan)
            for c in cols}


def build_v2_matrix(m5_closes: dict[str, pd.Series],
                    d1_closes: dict[str, pd.Series],
                    days: pd.DatetimeIndex, t0_hour: float,
                    lenses: tuple = LENSES, gate_walks: int = 40,
                    mn_min_bars_total: int = 60) -> tuple[pd.DataFrame, dict]:
    """Matriz longa (dia × moeda × lente) + metadados. Função pura."""
    days = pd.DatetimeIndex(sorted(days))
    t0s = np.array([np.datetime64(d + timedelta(hours=t0_hour)) for d in days])
    t4s = t0s + np.timedelta64(4, "h")
    n_dc = len(days) * len(G8)

    # --- TFs macro (independentes de lente) ---------------------------------
    d1_idx = build_indices(d1_closes, align="inner")
    p_d1 = CssmParams()                          # lente padrão v1 (w=64)
    tab_d1 = {c: protocol_full(f) for c, f in _close_indexed(
        d1_idx, p_d1, lambda ix: ix + pd.Timedelta("1D")).items()}

    w1_closes = resample_closes(d1_closes, "W-FRI")
    w1_idx = build_indices(w1_closes, align="inner")
    gate_w1 = calibrate_gates(W_W1, n_walks=gate_walks, target_fp=0.05)
    tab_w1 = {}
    for c in G8:
        f = compute_currency(w1_idx[c], CssmParams(w_mid=W_W1))
        f.index = f.index + pd.Timedelta("1D")
        tab_w1[c] = protocol_reduced(f, gate_w1)

    mn_closes = resample_closes(d1_closes, "MS")
    n_mn = len(next(iter(mn_closes.values())))
    mn_ok = n_mn >= mn_min_bars_total
    gate_mn = calibrate_gates(W_MN, n_walks=gate_walks, target_fp=0.05)
    tab_mn = {}
    if mn_ok:
        mn_idx = build_indices(mn_closes, align="inner")
        for c in G8:
            f = compute_currency(mn_idx[c], CssmParams(w_mid=W_MN))
            f.index = f.index + pd.offsets.MonthBegin(1)
            tab_mn[c] = protocol_reduced(f, gate_mn)

    # --- realizado [T0, T0+4h] e alvo bruto [T0+4h, T0+12h] -----------------
    m5_idx = build_indices(m5_closes, align="inner")
    pm = pair_map(list(m5_closes))
    ret4 = np.full(n_dc, np.nan); ret412 = np.full(n_dc, np.nan)
    br4 = np.full(n_dc, np.nan); er4 = np.full(n_dc, np.nan)
    for ci, c in enumerate(G8):
        s = m5_idx[c]
        for di, d in enumerate(days):
            t0 = d + timedelta(hours=t0_hour)
            t4 = t0 + timedelta(hours=4)
            t12 = t0 + timedelta(hours=12)
            w = s.loc[t0:t4]
            if len(w) >= 8:
                ret4[di * 8 + ci] = float(w.iloc[-1] - w.iloc[0])
                er4[di * 8 + ci] = window_er(s, t0, t4)
            w2 = s.loc[t4:t12]
            if len(w2) >= 2:
                ret412[di * 8 + ci] = float(w2.iloc[-1] - w2.iloc[0])
            rets = np.array([sgn * window_return(m5_closes[sym], t0, t4)
                             for sym, sgn in pm[c]], dtype=float)
            rets = rets[~np.isnan(rets)]
            if len(rets) >= 6:
                br4[di * 8 + ci] = float((rets > 0).mean())

    base = pd.DataFrame({"day": np.repeat(days, len(G8)),
                         "currency": np.tile(G8, len(days)),
                         "ret4h": ret4, "breadth4h": br4, "er4h": er4,
                         "ret_4_12": ret412})

    def fill_tf(df, tab, tf, cols, when, min_bars):
        block = {f"{tf}_{col}{suf}": np.full(len(df), np.nan)
                 for col in cols for suf in [""]}
        for ci, c in enumerate(G8):
            vals = _lookup(tab[c], cols, when, min_bars)
            for col in cols:
                block[f"{tf}_{col}"][ci::len(G8)] = vals[col]
        for k, v in block.items():
            df[k.replace("_cond", "_cond").replace("_dir", "_dir")] = v

    # --- por lente -----------------------------------------------------------
    m30 = build_indices(resample_closes(m5_closes, "30min"), align="inner")
    h1 = build_indices(resample_closes(m5_closes, "1h"), align="inner")
    h4 = build_indices(resample_closes(m5_closes, "4h"), align="inner")
    tf_idx = {"M30": (m30, pd.Timedelta("30min")),
              "H1": (h1, pd.Timedelta("1h")), "H4": (h4, pd.Timedelta("4h"))}

    frames, meta_lens = [], {}
    for w in lenses:
        p = lens_params(w, n_walks=gate_walks)
        meta_lens[w] = {"w_fast": p.w_fast, "z_win": p.z_win,
                        "t_gate": round(p.t_gate, 3),
                        "t_low": round(p.t_low, 3)}
        df = base.copy()
        df["lens"] = w
        min_bars = p.w_mid + p.z_win
        for tf, (idx, delta) in tf_idx.items():
            tab = {c: protocol_full(f) for c, f in _close_indexed(
                idx, p, lambda ix, d=delta: ix + d).items()}
            fill_tf(df, tab, tf, ["cond", "dir", "M"], t0s, min_bars)
            for ci, c in enumerate(G8):
                vals = _lookup(tab[c], ["cond", "dir"], t4s, min_bars)
                df.loc[ci::len(G8), f"{tf}_cond_4h"] = vals["cond"]
                df.loc[ci::len(G8), f"{tf}_dir_4h"] = vals["dir"]
        fill_tf(df, tab_d1, "D1", ["cond", "dir", "M", "age"], t0s,
                p_d1.w_mid + 150)
        fill_tf(df, tab_w1, "W1", ["cond", "dir", "t"], t0s, W_W1 + 20)
        if mn_ok:
            fill_tf(df, tab_mn, "MN", ["cond", "dir", "t"], t0s, W_MN + 20)
        else:
            df["MN_cond"] = np.nan; df["MN_dir"] = np.nan; df["MN_t"] = np.nan
        frames.append(df)

    out = pd.concat(frames, ignore_index=True)
    meta = {"lenses": meta_lens, "fr_age": FR_AGE,
            "w_w1": W_W1, "w_mn": W_MN,
            "gate_w1": round(gate_w1, 3), "gate_mn": round(gate_mn, 3),
            "mn_disponivel": bool(mn_ok), "n_barras_mensais": int(n_mn),
            "modo_reduzido": "W1/MN: FP/FR/N apenas (FN/EX indisponíveis)"}
    return out, meta


def main():
    meta_lab = json.loads(
        pathlib.Path("data/labels/labels_v1_meta.json").read_text())
    labels = pd.read_parquet("data/labels/labels_v1.parquet")
    all_days = pd.DatetimeIndex(sorted(labels.day.unique()))
    train, valid = research_days(all_days)
    days = pd.DatetimeIndex(np.concatenate([train, valid]))

    df, meta = build_v2_matrix(load_closes(), load_d1_closes(), days,
                               meta_lab["t0_hour"])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "v2_mtf.parquet")
    meta["n_rows"] = len(df); meta["n_days"] = int(df.day.nunique())
    meta["periodo"] = [str(df.day.min().date()), str(df.day.max().date())]
    (OUT / "v2_mtf_meta.json").write_text(json.dumps(meta, indent=2))
    cov = {tf: round(100 * float(df[f"{tf}_cond"].notna().mean()), 1)
           for tf in ("MN", "W1", "D1", "H4", "H1", "M30")}
    print(f"{len(df)} linhas ({df.day.nunique()} dias x 8 moedas x "
          f"{df.lens.nunique()} lentes) | cobertura cond%: {cov}")


if __name__ == "__main__":
    main()

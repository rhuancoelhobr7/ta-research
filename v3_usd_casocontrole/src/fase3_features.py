"""fase3_features.py — Features pré-registradas F1-F4 em T0 (lista FECHADA).

F1-F3: engine-agnostic, direto do OHLC dos 7 pares (base matemática do
r1_relational — breadth/nowcast/dominância/dispersão — reimplementada sem
o motor CSSM). F4: benchmark CSSM v1.41 em QUARENTENA (lentes H1 w=18 e
H4 w=30, gates calibrados) — nunca no mesmo modelo que F1-F3.

Regra de vazamento: toda feature do dia D usa apenas timestamps de
FECHAMENTO <= T0 (meia-noite do servidor de D). `tests/test_no_leakage.py`
é gate de execução; este módulo também roda um self-check de truncagem em
dias amostrados dos dados reais.

Janelas F1 em BARRAS H1 de pregão (8/24/48), não horas-calendário — uma
janela de 8h atravessando o fim de semana usaria as últimas 8 barras
negociadas (decisão documentada pré-resultados).
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from comum import DATA, carregar_ohlc, config, gate_fase0, eh_usd_base, log_usd, t0_do_dia

# imports do programa (raiz já no sys.path via comum)
from cssm_engine import CssmParams, build_indices, compute_currency, calibrate_gates


# ----------------------------------------------------------------------------
# Preparação (estruturas rolantes; tudo backward + shift => truncagem-invariante)
# ----------------------------------------------------------------------------

def preparar(h1: dict[str, pd.DataFrame], d1: dict[str, pd.DataFrame],
             labels: pd.DataFrame, cfg: dict) -> dict:
    fc = cfg["features"]
    prep: dict = {"cfg": cfg, "pares": list(h1), "labels": labels}

    # F1 — H1: log-close orientado + normalizador de magnitude por janela
    barras_dia = 24
    prep["h1_lc"] = {p: log_usd(df["close"], p, cfg) for p, df in h1.items()}
    prep["h1_absmed"] = {}
    for h in fc["f1_janelas_h"]:
        med = {}
        for p, lc in prep["h1_lc"].items():
            ret = (lc - lc.shift(h)).abs()
            med[p] = ret.rolling(fc["f1_norm_janela_dias"] * barras_dia,
                                 min_periods=5 * barras_dia).median().shift(1)
        prep["h1_absmed"][h] = med

    # F2 — D1: posição no range, TR, extremos, direção majoritária do dia
    prep["d1"] = d1
    prep["d1_lc"] = {p: log_usd(df["close"], p, cfg) for p, df in d1.items()}
    prep["d1_tr"] = {}
    prep["d1_trmed"] = {}
    prep["d1_sd"] = {}
    movs = {}
    for p, df in d1.items():
        pc = df["close"].shift(1)
        tr = (pd.concat([df["high"], pc], axis=1).max(axis=1)
              - pd.concat([df["low"], pc], axis=1).min(axis=1))
        prep["d1_tr"][p] = tr
        prep["d1_trmed"][p] = tr.rolling(fc["f2_range_janela"]).median().shift(1)
        lc = prep["d1_lc"][p]
        prep["d1_sd"][p] = lc.diff().rolling(fc["f2_dist_sd_janela"]).std().shift(1)
        mov = df["close"] - df["open"]
        movs[p] = mov if eh_usd_base(p, cfg) else -mov
    M = pd.DataFrame(movs)
    n_up, n_dn = (M > 0).sum(axis=1), (M < 0).sum(axis=1)
    dirr = pd.Series(0, index=M.index)
    dirr[(n_up >= fc["f2_run_min_breadth"]) & (n_up > n_dn)] = 1
    dirr[(n_dn >= fc["f2_run_min_breadth"]) & (n_dn > n_up)] = -1
    prep["d1_dir"] = dirr                      # índice = fechamento do dia
    return prep


def _janela(lc: pd.Series, t0: pd.Timestamp, h: int) -> pd.Series | None:
    """Últimas h+1 barras H1 com fechamento <= t0 (janela de h retornos)."""
    pos = lc.index.searchsorted(t0, side="right")
    if pos < h + 1:
        return None
    return lc.iloc[pos - h - 1:pos]


def features_do_dia(prep: dict, dia: pd.Timestamp) -> dict | None:
    """F1+F2+F3 do dia (função pura; usada pelo pipeline e pelo gate de
    vazamento). Devolve também max_ts (auditoria: maior timestamp usado)."""
    cfg = prep["cfg"]
    fc = cfg["features"]
    t0 = t0_do_dia(dia)
    out: dict = {"t0": t0}
    max_ts = pd.Timestamp.min

    # ---------------- F1: relacional em T0 -------------------------------
    for h in fc["f1_janelas_h"]:
        rets, mags, ers = [], [], []
        for p in prep["pares"]:
            w = _janela(prep["h1_lc"][p], t0, h)
            if w is None:
                return None
            max_ts = max(max_ts, w.index[-1])
            ret = float(w.iloc[-1] - w.iloc[0])
            path = float(np.abs(np.diff(w.to_numpy())).sum())
            norm = prep["h1_absmed"][h][p].asof(t0)
            if not np.isfinite(norm) or norm <= 0:
                return None
            rets.append(ret)
            mags.append(ret / norm)
            ers.append(abs(ret) / path if path > 0 else 0.0)
        rets, mags = np.array(rets), np.array(mags)
        out[f"f1_breadth_{h}"] = float(((rets > 0).sum() - (rets < 0).sum()) / 7)
        out[f"f1_mag_{h}"] = float(np.median(mags))
        out[f"f1_er_{h}"] = float(np.median(ers))
        if h == 24:
            out["f1_usd_share_24"] = float(np.abs(rets).mean() and
                                           abs(rets.mean()) / np.abs(rets).mean())
            out["f1_disp_24"] = float(np.std(mags))

    # ---------------- F2: estrutura do dia anterior ----------------------
    pos_l, exp_l = [], []
    dist = {k: [] for k in fc["f2_dist_horizontes"] for k in
            (f"hi{k}", f"lo{k}")}
    for p in prep["pares"]:
        df = prep["d1"][p]
        pos_i = df.index.searchsorted(t0, side="right") - 1
        if pos_i < max(fc["f2_dist_horizontes"]) + 1:
            return None
        r = df.iloc[pos_i]                     # barra de D-1 (fecha em T0)
        max_ts = max(max_ts, df.index[pos_i])
        rng = float(r.high - r.low)
        pos = (float(r.close - r.low) / rng) if rng > 0 else 0.5
        pos_l.append(pos if eh_usd_base(p, cfg) else 1.0 - pos)
        trmed = prep["d1_trmed"][p].iloc[pos_i]
        tr = prep["d1_tr"][p].iloc[pos_i]
        if not np.isfinite(trmed) or trmed <= 0:
            return None
        exp_l.append(float(tr / trmed))
        lc = prep["d1_lc"][p]
        sd = prep["d1_sd"][p].iloc[pos_i]
        if not np.isfinite(sd) or sd <= 0:
            return None
        for k in fc["f2_dist_horizontes"]:
            w = lc.iloc[pos_i - k + 1:pos_i + 1]
            denom = sd * np.sqrt(k)
            dist[f"hi{k}"].append(float((lc.iloc[pos_i] - w.max()) / denom))
            dist[f"lo{k}"].append(float((lc.iloc[pos_i] - w.min()) / denom))
    out["f2_close_pos"] = float(np.median(pos_l))
    out["f2_range_exp"] = float(np.median(exp_l))
    for k in fc["f2_dist_horizontes"]:
        out[f"f2_dist_hi{k}"] = float(np.median(dist[f"hi{k}"]))
        out[f"f2_dist_lo{k}"] = float(np.median(dist[f"lo{k}"]))

    # sequência de dias na mesma direção do USD (termina em D-1)
    dirr = prep["d1_dir"]
    pos_i = dirr.index.searchsorted(t0, side="right") - 1
    run = 0
    if pos_i >= 0 and dirr.iloc[pos_i] != 0:
        s = dirr.iloc[pos_i]
        j = pos_i
        while j >= 0 and dirr.iloc[j] == s:
            run += 1
            j -= 1
        run *= int(s)
    out["f2_run_len"] = float(run)

    # ---------------- F3: persistência ------------------------------------
    lab = prep["labels"]
    pos_i = lab.index.searchsorted(dia) - 1     # dia rotulado anterior
    if pos_i < 0:
        return None
    prev = lab.iloc[pos_i]
    out["f3_usd_prot_prev"] = float({"up": 1, "down": -1, "none": 0}[prev.classe])
    out["f3_atividade_prev"] = float(prev.atividade)
    out["max_ts_f13"] = max_ts
    return out


# ----------------------------------------------------------------------------
# F4 — benchmark CSSM v1.41 (quarentena)
# ----------------------------------------------------------------------------

def _gates(w_mid: int, cfg: dict) -> tuple[float, float]:
    cache = DATA / "gates_v3.json"
    db = json.loads(cache.read_text()) if cache.exists() else {}
    k = str(w_mid)
    if k not in db:
        fps = cfg["features"]["f4_gates_fp"]
        db[k] = [calibrate_gates(w_mid, n_walks=20, bars=12000, target_fp=fp)
                 for fp in fps]
        cache.parent.mkdir(parents=True, exist_ok=True)  # clone fresco não tem data/
        cache.write_text(json.dumps(db, indent=2))
    return tuple(db[k])


def f4_series(closes: dict[str, pd.Series], w_mid: int, cfg: dict,
              sufixo: str) -> pd.DataFrame:
    """Leituras CSSM (índice USD + breadth por par) numa lente v1.41.
    `closes`: close CRU por par, índice = fechamento da barra do TF."""
    t_gate, t_low = _gates(w_mid, cfg)
    p = CssmParams(w_fast=max(4, w_mid // 4), w_mid=w_mid,
                   z_win=min(500, max(150, 8 * w_mid)),
                   t_gate=t_gate, t_low=t_low)
    idx = build_indices(closes, align="inner")
    usd = compute_currency(idx["USD"], p)
    cols = {f"f4_{sufixo}_{c}": usd[c] for c in
            ("t", "er", "M", "pers", "acc_z", "conv_z", "state", "dir")}
    # breadth v1.41: t do PAR orientado ao USD vs gate da própria lente
    ts = {}
    for par, s in closes.items():
        pf = compute_currency(np.log(s.astype(float)).rename(par), p)
        ts[par] = pf["t"] if eh_usd_base(par, cfg) else -pf["t"]
    T = pd.DataFrame(ts).reindex(usd.index)
    d = np.sign(usd["t"])
    ok = T.notna().sum(axis=1)
    ali = np.sign(T).mul(d, axis=0) > 0
    cols[f"f4_{sufixo}_bsoft"] = ali.sum(axis=1) / ok
    cols[f"f4_{sufixo}_bhard"] = (ali & (T.abs() >= t_gate)).sum(axis=1) / ok
    return pd.DataFrame(cols)


def f4_em_t0(f4h1: pd.DataFrame, f4h4: pd.DataFrame,
             dias: pd.DatetimeIndex) -> pd.DataFrame:
    rows = {}
    for tag, df in (("h1", f4h1), ("h4", f4h4)):
        pos = df.index.searchsorted([t0_do_dia(d) for d in dias], side="right") - 1
        val = df.iloc[pos].reset_index(drop=True)
        val[f"max_ts_f4_{tag}"] = df.index[pos]
        rows[tag] = val.set_index(dias)
    return pd.concat([rows["h1"], rows["h4"]], axis=1)


def resample_h4(closes: dict[str, pd.Series]) -> dict[str, pd.Series]:
    """H1 (índice=fechamento) -> H4 alinhado ao servidor (00/04/.../24)."""
    return {p: s.resample("4h", label="right", closed="right").last().dropna()
            for p, s in closes.items()}


# ----------------------------------------------------------------------------

def montar(h1, d1, labels, cfg) -> pd.DataFrame:
    prep = preparar(h1, d1, labels, cfg)
    linhas = {}
    for dia in labels.index:
        f = features_do_dia(prep, dia)
        if f is not None:
            linhas[dia] = f
    F = pd.DataFrame(linhas).T
    F.index.name = "dia"

    closes_h1 = {p: df["close"] for p, df in h1.items()}
    lentes = cfg["features"]["f4_lentes"]
    f4h1 = f4_series(closes_h1, lentes["H1"], cfg, "h1")
    f4h4 = f4_series(resample_h4(closes_h1), lentes["H4"], cfg, "h4")
    F4 = f4_em_t0(f4h1, f4h4, F.index)
    return pd.concat([F, F4], axis=1)


def self_check_truncagem(h1, d1, labels, cfg, feats: pd.DataFrame,
                         n_dias: int = 12, seed: int = 0) -> None:
    """Gate nos dados REAIS: recomputa F1-F3 com dados truncados em T0."""
    rng = np.random.default_rng(seed)
    dias = feats.index[rng.choice(len(feats), n_dias, replace=False)]
    for dia in dias:
        t0 = t0_do_dia(dia)
        h1t = {p: df[df.index <= t0] for p, df in h1.items()}
        d1t = {p: df[df.index <= t0] for p, df in d1.items()}
        prep_t = preparar(h1t, d1t, labels[labels.index < dia], cfg)
        f_t = features_do_dia(prep_t, dia)
        assert f_t is not None, f"truncagem quebrou {dia}"
        for k, v in f_t.items():
            if k in ("t0", "max_ts_f13"):
                continue
            ref = feats.loc[dia, k]
            assert np.isclose(v, ref, rtol=1e-10, atol=1e-12), \
                f"VAZAMENTO em {k} @ {dia}: trunc={v} full={ref}"
    print(f"self-check de truncagem OK ({n_dias} dias amostrados)")


def main() -> int:
    gate_fase0()
    cfg = config()
    labels = pd.read_parquet(DATA / "labels_usd.parquet")
    h1, d1 = carregar_ohlc("H1", cfg), carregar_ohlc("D1", cfg)
    feats = montar(h1, d1, labels, cfg)

    # auditoria de timestamps (regra 1)
    t0s = pd.to_datetime(feats["t0"])
    for col in ("max_ts_f13", "max_ts_f4_h1", "max_ts_f4_h4"):
        viol = (pd.to_datetime(feats[col]) > t0s).sum()
        assert viol == 0, f"{col}: {viol} dias com timestamp > T0"
    self_check_truncagem(h1, d1, labels, cfg, feats)

    feats.to_parquet(DATA / "features.parquet")
    n_f4_nan = int(feats.filter(like="f4_").isna().any(axis=1).sum())
    print(f"features: {len(feats)} dias x {feats.shape[1]} colunas "
          f"(dias com F4 em aquecimento: {n_f4_nan})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

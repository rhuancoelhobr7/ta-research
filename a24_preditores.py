# -*- coding: utf-8 -*-
"""a24_preditores.py — o CSS prevê range? Foco no PROCESSO REAL do trader
(P8 alinhamento percentil, P9 par limpo×conflitado, P10 breadth direcional),
medido NA VIRADA de NY (13:00 UTC = barra fechada anterior à abertura), contra
o baseline que o a22/a23 já entregam.

Duas perguntas, dois enquadramentos:
  (A) ABSOLUTO — ranquear os 28 pares por range esperado na janela pós-abertura
      [13,17) UTC e ver se o top-3 do CSS bate o top-3 do baseline ATR. É a
      pergunta do trader ("qual par move mais hoje").
  (B) RELATIVO — alvo = range/ATR-do-próprio-par: o CSS prevê o par que se move
      ACIMA da sua largura estrutural? Testa se o CSS tem informação ALÉM do
      óbvio (GBPNZD sempre é largo).

Preditores (estado na virada, TFs H1/H4=intra, D1/W1=longo; pct200 padrão):
  base_atr  — mediana causal do range diário (20d, shift 1). O baseline a bater.
  base_asia — range de asia do dia (a23; conhecido às 07:00 < 13:00).
  P8_mag    — |mean_TF(pct_base − pct_quote)| (separação de força das 2 moedas).
  P8_intra / P8_long — idem só intra ou só longo (tendência vs impulso).
  P10_brd   — breadth direcional somado das 2 moedas (nº de crosses concordantes).
  P9_diverg — divergência da moeda FRACA entre TFs longos e curtos (p/ Q trajet.).

Metodologia: sem lookahead (merge_asof backward EXCLUSIVO na virada), split
70/30 temporal, avaliação no TESTE, bootstrap semanal, controle negativo
(estado embaralhado entre pares no dia). Nulo é publicável.

Uso: python a24_preditores.py [--pct 200]
Saída: results/{ts}_a24/REPORT.md + ranking_eval.csv
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from sessions import add_utc, server_to_utc, session_ranges, daily_range
from stats_blocks import block_bootstrap_ci

RAW = pathlib.Path("data/raw")
DERIVED = pathlib.Path("data/derived")
G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
INTRA = ["H1", "H4"]
LONG = ["D1", "W1"]
TFS = INTRA + LONG
TURN_H, TARGET = 13, (13, 17)     # virada e janela-alvo (UTC)
TRAIN_FRAC = 0.70


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


# ----------------------------------------------------------------------------
# 1. Alvos + baseline por par
# ----------------------------------------------------------------------------

def targets_baselines() -> pd.DataFrame:
    pips = load_pips()
    win = {"post": TARGET, "asia": (0, 7)}
    rows = []
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        df = pd.read_parquet(f)
        sr = session_ranges(df, pips[sym], win)
        w = sr.pivot_table(index="date", columns="session", values="range_pips")
        tr = sr[sr.session == "post"].set_index("date")["traj"]
        dr = daily_range(df, pips[sym])["day_range"]
        base_atr = dr.rolling(20, min_periods=10).median().shift(1)  # causal
        g = pd.DataFrame({"tgt_range": w.get("post"), "tgt_traj": tr,
                          "base_asia": w.get("asia"), "base_atr": base_atr})
        g["pair"] = sym
        rows.append(g.reset_index())
    p = pd.concat(rows, ignore_index=True).dropna(subset=["tgt_range", "base_atr"])
    p["tgt_norm"] = p["tgt_range"] / p["base_atr"]        # alvo relativo (B)
    return p


# ----------------------------------------------------------------------------
# 2. Estado do CSS na virada (sem lookahead)
# ----------------------------------------------------------------------------

def css_state_at_turns(dates: pd.DatetimeIndex, pct_col: str,
                       turn_h: int = TURN_H) -> pd.DataFrame:
    """Para cada dia, val/pct/breadth por moeda em cada TF na barra fechada
    ANTES de `turn_h`:00 UTC. merge_asof backward EXCLUSIVO (não pega a barra da
    abertura). turn_h=13 (virada NY, a24) ou 0 (manhã pré-Tokyo, a26)."""
    turns = pd.DataFrame({"turn": pd.to_datetime(dates) + pd.Timedelta(hours=turn_h)})
    turns = turns.sort_values("turn").reset_index(drop=True)
    out = turns.copy()
    for tf in TFS:
        fr = pd.read_parquet(DERIVED / f"css_screen_{tf}.parquet")
        fr = fr.assign(utc=server_to_utc(fr.index))
        fr = fr[fr["utc"].notna()].sort_values("utc")
        cols_val = [f"val_{c}" for c in G8]
        cols_pct = [f"{pct_col}_{c}" for c in G8]
        sub = fr[["utc"] + cols_val + cols_pct].copy()
        # breadth direcional por moeda: nº de outras 7 do mesmo lado da média
        V = sub[cols_val].to_numpy()
        mean = np.nanmean(V, axis=1, keepdims=True)
        brd = np.zeros_like(V)
        for i in range(8):
            same = np.sign(V[:, [i]] - V) == np.sign(V[:, [i]] - mean)
            brd[:, i] = (same.sum(axis=1) - 1)   # exclui a própria coluna
        for i, c in enumerate(G8):
            sub[f"brd_{c}"] = brd[:, i]
        sub = sub.rename(columns={**{f"val_{c}": f"{c}|val|{tf}" for c in G8},
                                  **{f"{pct_col}_{c}": f"{c}|pct|{tf}" for c in G8},
                                  **{f"brd_{c}": f"{c}|brd|{tf}" for c in G8}})
        out = pd.merge_asof(out, sub, left_on="turn", right_on="utc",
                            direction="backward", allow_exact_matches=False)
        out = out.drop(columns=["utc"])
    out["date"] = out["turn"].dt.normalize()
    return out.set_index("date").drop(columns=["turn"])


# ----------------------------------------------------------------------------
# 3. Features por par a partir do estado das moedas
# ----------------------------------------------------------------------------

def pair_features(panel: pd.DataFrame, state: pd.DataFrame) -> pd.DataFrame:
    """Vetorizado: alinha o estado (por dia) às linhas do painel uma vez e
    seleciona a coluna da moeda base/quote por índice."""
    n = len(panel)
    st = state.reindex(panel["date"].to_numpy()).reset_index(drop=True)
    base_idx = panel["pair"].str[:3].map(G8.index).to_numpy()
    quote_idx = panel["pair"].str[3:6].map(G8.index).to_numpy()
    r = np.arange(n)

    def sel(kind, tf):
        mat = st[[f"{c}|{kind}|{tf}" for c in G8]].to_numpy(dtype=float)
        return mat[r, base_idx], mat[r, quote_idx]

    pb = np.column_stack([sel("pct", tf)[0] for tf in TFS])
    pq = np.column_stack([sel("pct", tf)[1] for tf in TFS])
    sep = pb - pq
    i_intra = [TFS.index(t) for t in INTRA]
    i_long = [TFS.index(t) for t in LONG]
    out = panel.copy()
    out["P8_mag"] = np.abs(np.nanmean(sep, axis=1))
    out["P8_intra"] = np.abs(np.nanmean(sep[:, i_intra], axis=1))
    out["P8_long"] = np.abs(np.nanmean(sep[:, i_long], axis=1))
    # P9: divergência da moeda FRACA (menor pct médio) entre longo e intra
    weak_is_quote = np.nanmean(pb, axis=1) >= np.nanmean(pq, axis=1)
    weak = np.where(weak_is_quote[:, None], pq, pb)
    out["P9_diverg"] = np.abs(np.nanmean(weak[:, i_long], axis=1)
                              - np.nanmean(weak[:, i_intra], axis=1))
    # P10: breadth somado das 2 moedas (média entre H1 e D1)
    brd = []
    for tf in ("H1", "D1"):
        bb, qq = sel("brd", tf)
        brd.append(bb + qq)
    out["P10_brd"] = np.nanmean(np.column_stack(brd), axis=1)
    return out


# ----------------------------------------------------------------------------
# 4. Avaliação de ranqueamento
# ----------------------------------------------------------------------------

def rank_eval(df: pd.DataFrame, pred: str, target: str, k: int = 3,
              seed: int = 0) -> dict:
    """Por dia: ranqueia pares por `pred` desc, mede alvo do top-k e Spearman.
    Retorna média do top-k, lift (top-k / média do dia), Spearman médio e IC."""
    daily_top, daily_lift, daily_sp = [], [], []
    for _, g in df.groupby("date"):
        g = g.dropna(subset=[pred, target])
        if len(g) < 10:
            continue
        top = g.nlargest(k, pred)[target].mean()
        allm = g[target].mean()
        daily_top.append(top)
        daily_lift.append(top / allm if allm else np.nan)
        if g[pred].nunique() > 2:
            daily_sp.append(spearmanr(g[pred], g[target])[0])
    top_arr = np.array(daily_top, dtype=float)
    stat, lo, hi = block_bootstrap_ci(top_arr, np.mean, block=5, seed=seed)
    return {"pred": pred, "target": target,
            "top{}_mean".format(k): stat, "ci_lo": lo, "ci_hi": hi,
            "lift": float(np.nanmean(daily_lift)),
            "spearman": float(np.nanmean(daily_sp)) if daily_sp else np.nan,
            "n_days": len(top_arr)}


def zrank(s: pd.Series) -> pd.Series:
    return s.rank()


def main(pct_win: int) -> None:
    t0 = time.time()
    pct_col = f"pct{pct_win}"
    panel = targets_baselines()
    dates = pd.DatetimeIndex(sorted(panel["date"].unique()))
    state = css_state_at_turns(dates, pct_col)
    feat = pair_features(panel, state)

    # stack simples: média dos postos de base_atr e P8_mag (por dia)
    feat["stack_atr_P8"] = (feat.groupby("date")["base_atr"].transform(zrank)
                            + feat.groupby("date")["P8_mag"].transform(zrank))
    # controle negativo: P8 embaralhado entre pares no mesmo dia
    rng = np.random.default_rng(0)
    feat["P8_shuf"] = feat.groupby("date")["P8_mag"].transform(
        lambda s: rng.permutation(s.values))

    cut = panel["date"].quantile(TRAIN_FRAC)
    te = feat[feat["date"] >= cut]

    preds = ["base_atr", "base_asia", "P8_mag", "P8_intra", "P8_long",
             "P10_brd", "stack_atr_P8", "P8_shuf"]
    # (A) absoluto e (B) relativo ao próprio ATR
    rowsA = [rank_eval(te, p, "tgt_range") for p in preds]
    rowsB = [rank_eval(te, p, "tgt_norm") for p in preds]
    A = pd.DataFrame(rowsA).set_index("pred")
    B = pd.DataFrame(rowsB).set_index("pred")

    # P9 vs trajetória: par limpo (baixa diverg) tem traj melhor?
    te2 = te.dropna(subset=["P9_diverg", "tgt_traj"])
    q = te2["P9_diverg"].quantile([0.25, 0.75])
    clean = te2[te2["P9_diverg"] <= q.iloc[0]]["tgt_traj"].median()
    conflict = te2[te2["P9_diverg"] >= q.iloc[1]]["tgt_traj"].median()

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a24")
    out.mkdir(parents=True, exist_ok=True)
    A.to_csv(out / "ranking_eval_absoluto.csv")
    B.to_csv(out / "ranking_eval_relativo.csv")

    rep = [
        "# a24 — CSS como preditor de range (P8/P9/P10 vs baseline)\n",
        f"Virada NY 13:00 UTC, alvo range [13,17) UTC. Estado na barra fechada "
        f"anterior (sem lookahead). Split 70/30, teste = {te['date'].nunique()} "
        f"dias. pct{pct_win}. Baseline a bater: **base_atr** (o par estruturalmente "
        f"mais largo). Controle negativo: **P8_shuf**.\n",
        "## (A) ABSOLUTO — top-3 range pós-abertura (pips) — pergunta do trader\n",
        A.round(3).to_markdown(),
        "\n_Se P8/P10/stack não superam base_atr aqui, o CSS não ajuda a escolher "
        "o par de maior amplitude além da largura estrutural._\n",
        "\n## (B) RELATIVO — alvo = range/ATR-do-próprio-par — o CSS tem info?\n",
        B.round(3).to_markdown(),
        "\n_lift>1 e spearman>0 acima do controle P8_shuf = o CSS prevê o par que "
        "excede a PRÓPRIA norma. É o teste limpo de conteúdo informativo.\n",
        "\n## P9 — par limpo × conflitado (trajetória da janela-alvo)\n",
        f"- traj mediana com moeda fraca LIMPA (P9_diverg baixo): **{clean:.3f}**",
        f"\n- traj mediana com moeda fraca CONFLITADA (alto): **{conflict:.3f}**",
        f"\n\n_traj mais alta = movimento mais limpo (menos choppy). "
        f"{'Limpo > conflitado, na direção do P9.' if clean>conflict else 'Sem vantagem do limpo — P9 não se sustenta aqui.'}_\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a24: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print("\n(A) absoluto:\n", A[["top3_mean", "lift", "spearman"]].round(3).to_string())
    print("\n(B) relativo:\n", B[["top3_mean", "lift", "spearman"]].round(3).to_string())
    print(f"\nP9 traj limpo={clean:.3f} vs conflitado={conflict:.3f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--pct", type=int, default=200)
    main(ap.parse_args().pct)

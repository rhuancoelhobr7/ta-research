# -*- coding: utf-8 -*-
"""a33_cadeia.py — a cadeia composta, ponta a ponta, líquida de custo.

CONFIRMATÓRIO, uma execução, sem grade. Reusa código congelado do a29/a30
(momentum), a31 (par líder×anti) e a25 (ATR de sessão). Só research (primeiros
80% dos dias M5); HOLDOUT INTOCADO.

Pipeline causal (barras fechadas):
1. Em T0+90min (M5), score por moeda = momentum de preço (índice sintético −
   abertura, do a30). Ranking das 8.
2. top-3 ESTIMADO = 3 maiores; líder = maior; anti-líder = MENOR entre as 8.
3. Par candidato = líder × anti-líder (regra a31).
4. Comparador a25: par de maior ATR de sessão.

Métricas (research/OOS): P(candidato = par de maior range do dia) vs 14% (a31) e
1/28; range capturado (pips) líquido de spread real e em múltiplos de spread;
decomposição condicional a acertar a líder; baselines (aleatório, maior-ATR,
persistência). Veredito pré-registrado no CHANGELOG.

Uso: python a33_cadeia.py
Saída: results/{ts}_a33/REPORT.md
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd

from a29_deteccao import load_m5, truth_by_close, pick_at
from a30_volume_momentum import intraday_signals
from a31_par_campeao import pair_of
from preponderante import G8

RAW = pathlib.Path("data/raw")
TURN_MIN = 90
RESEARCH_FRAC = 0.80        # holdout = últimos 20% (intocado aqui)


def scores_at(frame: pd.DataFrame, turns: np.ndarray) -> pd.DataFrame:
    """Linha de scores por moeda na última barra fechada <= cada turn."""
    ff = frame.dropna(how="all").sort_index().reset_index()
    ff = ff.rename(columns={ff.columns[0]: "t"})
    ff["t"] = ff["t"].astype("datetime64[ns]")
    tdf = pd.DataFrame({"turn": pd.Series(turns).astype("datetime64[ns]")})
    m = pd.merge_asof(tdf, ff, left_on="turn", right_on="t", direction="backward")
    return m[G8]


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    mom = intraday_signals(closes, ohlc)["momentum"]
    truth = truth_by_close(ohlc, pip)                    # ranking de força (líder)

    # range e net por (dia, par) em pips
    rng = {}
    for sym, df in ohlc.items():
        day = df.index.normalize()
        g = df.groupby(day)
        rng[sym] = (g["high"].max() - g["low"].min()) / pip[sym]
    rng = pd.DataFrame(rng)
    atr = rng.rolling(20, min_periods=10).median().shift(1)    # ATR causal por par
    # spread mediano em pips (piso 0.1 pip: spread 0 pts é artefato de feed)
    spread_pips = {s: max(float(df["spread"].median()) / 10.0, 0.1)
                   for s, df in ohlc.items()}

    dates = pd.DatetimeIndex(sorted(set(truth.index) & set(rng.index)))
    hcut = dates.to_series().quantile(RESEARCH_FRAC)
    dr = dates[dates < hcut]                              # research (80%), sem holdout

    turns = (dr + pd.Timedelta(minutes=TURN_MIN)).values
    sc = scores_at(mom, turns)                            # scores no T0+90min
    cols = set(rng.columns)

    recs = []
    for i, date in enumerate(dr):
        row = sc.iloc[i].dropna()
        if len(row) < 8:
            continue
        rank = row.sort_values(ascending=False).index.tolist()
        est_leader, est_anti = rank[0], rank[-1]
        cand = pair_of(est_leader, est_anti, cols)
        if cand is None:
            continue
        r = rng.loc[date].dropna()
        if len(r) < 20:
            continue
        true_leader = truth.loc[date, "rank"][0]
        max_pair = r.idxmax()
        a = atr.loc[date].dropna()
        atr_pair = a.idxmax() if len(a) else None          # maior ATR de sessão
        recs.append({
            "date": date, "cand": cand, "est_leader": est_leader,
            "true_leader": true_leader, "leader_ok": est_leader == true_leader,
            "max_pair": max_pair,
            "cand_is_max": cand == max_pair,
            "cand_range": r.get(cand, np.nan),
            "cand_net": r.get(cand, np.nan) - spread_pips[cand],
            "cand_spread_mult": r.get(cand, np.nan) / spread_pips[cand],
            "mean_range": r.mean(),
            "cand_excess_atr": (r.get(cand, np.nan) - r.mean()) / atr.loc[date].get(cand, np.nan)
                if not np.isnan(atr.loc[date].get(cand, np.nan)) else np.nan,
            "atr_pair": atr_pair, "atr_is_max": atr_pair == max_pair,
            "atr_pair_range": r.get(atr_pair, np.nan) if atr_pair else np.nan,
        })
    d = pd.DataFrame(recs)

    # persistência: par de maior range de ONTEM
    maxpair_series = d.set_index("date")["max_pair"]
    prev = maxpair_series.shift(1)
    d = d.set_index("date")
    d["persist_is_max"] = (prev == d["max_pair"])
    d = d.reset_index()

    n = len(d)
    P = lambda c: float(d[c].mean())
    p_cand = P("cand_is_max"); p_atr = P("atr_is_max"); p_persist = d["persist_is_max"].mean()
    p_rand = 1 / 28
    p_cond_ok = float(d[d.leader_ok]["cand_is_max"].mean())
    p_cond_no = float(d[~d.leader_ok]["cand_is_max"].mean())
    p_leader = P("leader_ok")
    cand_range_med = float(d["cand_range"].median())
    cand_net_med = float(d["cand_net"].median())
    cand_mult_med = float(d["cand_spread_mult"].median())
    atr_range_med = float(d["atr_pair_range"].median())
    spread_med = float(np.median(list(spread_pips.values())))

    beats_baselines = (p_cand > p_atr and p_cand > p_persist and p_cand > p_rand)
    net_ok = cand_range_med > 2 * d["cand"].map(spread_pips).median()
    sustains = beats_baselines and net_ok

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a33")
    out.mkdir(parents=True, exist_ok=True)
    d.to_parquet(out / "cadeia.parquet")

    rep = [
        "# a33 — A cadeia composta, ponta a ponta, líquida de custo\n",
        f"CONFIRMATÓRIO, uma execução. {n} dias de RESEARCH (primeiros 80% do M5; "
        f"holdout intocado). Pipeline: momentum T0+90min → líder×anti → par.\n",
        "## P(par candidato = par de MAIOR range do dia)\n",
        f"| fonte | P(=max) |\n|---|---|\n"
        f"| **cadeia (candidato)** | **{p_cand:.1%}** |\n"
        f"| baseline maior-ATR (a25) | {p_atr:.1%} |\n"
        f"| baseline persistência | {p_persist:.1%} |\n"
        f"| aleatório (1/28) | {p_rand:.1%} |\n"
        f"| referência a31 (conhecendo a líder) | 14% |\n",
        "\n## Decomposição — o custo do erro de detecção\n",
        f"- acerta a líder estimada = a verdadeira em **{p_leader:.1%}** dos dias.",
        f"\n- P(candidato=max | líder correta) = **{p_cond_ok:.1%}** vs "
        f"P(candidato=max | líder errada) = **{p_cond_no:.1%}**.",
        f"\n- → a queda do 14%(a31) para {p_cand:.1%} vem sobretudo de NÃO conhecer "
        f"a líder ({p_leader:.0%} de acerto).\n",
        "## Range capturado e custo (spread real por par, mediana do M5)\n",
        f"- range mediano do candidato: **{cand_range_med:.1f} pips**; "
        f"líquido de spread: **{cand_net_med:.1f} pips**; "
        f"**{cand_mult_med:.1f}× o spread** do par.",
        f"\n- excesso de ATR do candidato vs média dos 28: mediana "
        f"{d['cand_excess_atr'].median():.2f} ATR (a31 achou +0.67 conhecendo a líder).",
        f"\n- comparador maior-ATR (a25): range mediano {atr_range_med:.1f} pips.\n",
        "## Veredito pré-registrado\n",
        f"- bate TODOS os baselines em P(=max)? **{'SIM' if beats_baselines else 'NÃO'}** "
        f"(cand {p_cand:.1%} vs ATR {p_atr:.1%}, persist {p_persist:.1%}, aleat {p_rand:.1%}).",
        f"\n- range líquido > 2× spread? **{'SIM' if net_ok else 'NÃO'}** "
        f"({cand_mult_med:.1f}× spread).",
        f"\n\n### → A cadeia {'SE SUSTENTA' if sustains else 'NÃO se sustenta'} "
        f"(critério pré-registrado).\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a33: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"P(cand=max)={p_cand:.1%} | ATR={p_atr:.1%} persist={p_persist:.1%} "
          f"aleat={p_rand:.1%} | a31ref=14%")
    print(f"leader_ok={p_leader:.1%} | cond ok={p_cond_ok:.1%} no={p_cond_no:.1%}")
    print(f"cand range={cand_range_med:.1f}p net={cand_net_med:.1f}p mult={cand_mult_med:.1f}x")
    print(f"VEREDITO: cadeia {'SE SUSTENTA' if sustains else 'NAO se sustenta'}")


if __name__ == "__main__":
    main()

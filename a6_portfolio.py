"""a6_portfolio.py — Fase C: portfólio diário de 7 pares.

ESPECIFICAÇÃO (PLAN.md §6). Como a5 NÃO produziu regra sobrevivente
(resultado nulo), este script simula, em dias research:
  - os 2 baselines do B3 (continuação-D1 e persistência de rótulo);
  - a melhor regra NÃO-sobrevivente de a5 (apenas referência, rotulada);
  - um teto oracle (protagonista real do dia) p/ dimensionar custos.
Execução: escolha em T0; 7 pares orientados, peso igual; entrada no 1º close
>= T0; saída no último close <= T0+12h; custo por par em bps descontado do
retorno do par. Métricas: retorno líquido/dia, % dias vencedores, equity,
max drawdown; ICs por bootstrap em blocos.

Custos default (bps por par, ida-e-volta): majors (com USD) 1.0; crosses com
EUR/GBP/JPY 2.0; demais crosses G8 3.0. Configurável via --cost-majors etc.

Uso: python a6_portfolio.py
"""
from __future__ import annotations

import argparse, json, pathlib, time
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes, window_return
from a4_features_t0 import load_d1_closes
from a5_reverse import RULES, load_research
from cssm_engine import G8, build_indices
from splits_days import research_days
from stats_blocks import block_bootstrap_ci

REFERENCE_RULE = "maior_|M|_D1"   # melhor top-1 de a5; NÃO sobreviveu


def pair_cost_bps(sym: str, majors: float, crosses: float, exotic: float) -> float:
    if "USD" in sym:
        return majors
    if any(c in sym for c in ("EUR", "GBP", "JPY")):
        return crosses
    return exotic


def day_portfolio_return(closes, pm, currency, direction, t0, t1, costs):
    """Média dos 7 pares orientados, cada um líquido do seu custo em bps."""
    sgn_dir = 1.0 if direction == "ALTA" else -1.0
    rets = []
    for sym, sgn in pm[currency]:
        r = window_return(closes[sym], t0, t1)
        if np.isnan(r):
            continue
        rets.append(sgn_dir * sgn * r - costs[sym] * 1e-4)
    return float(np.mean(rets)) if len(rets) >= 6 else np.nan


def simulate(preds: dict, closes, pm, t0_hour, window_h, costs) -> pd.Series:
    out = {}
    for day, ranking in preds.items():
        if not ranking:
            continue
        cur, direction, _ = ranking[0]
        t0 = day + timedelta(hours=t0_hour)
        r = day_portfolio_return(closes, pm, cur, direction, t0,
                                 t0 + timedelta(hours=window_h), costs)
        if not np.isnan(r):
            out[day] = r
    return pd.Series(out).sort_index()


def metrics(r: pd.Series, block: int) -> dict:
    eq = r.cumsum()
    dd = float((eq - eq.cummax()).min())
    mu, lo, hi = block_bootstrap_ci(r.to_numpy(), block=block)
    return {"n": len(r), "mean_bp": mu * 1e4, "lo_bp": lo * 1e4,
            "hi_bp": hi * 1e4, "win": float((r > 0).mean()),
            "total_pct": float(eq.iloc[-1]) * 100, "maxdd_pct": dd * 100}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cost-majors", type=float, default=1.0)
    ap.add_argument("--cost-crosses", type=float, default=2.0)
    ap.add_argument("--cost-exotic", type=float, default=3.0)
    ap.add_argument("--boot-block", type=int, default=5)
    a = ap.parse_args()

    meta_lab = json.loads(
        pathlib.Path("data/labels/labels_v1_meta.json").read_text())
    t0_hour, window_h = meta_lab["t0_hour"], meta_lab["window_hours"]

    df = load_research()
    days = sorted(df.day.unique())
    groups = {d: g for d, g in df.groupby("day")}

    closes = load_closes()
    costs = {s: pair_cost_bps(s, a.cost_majors, a.cost_crosses, a.cost_exotic)
             for s in closes}
    from a1_label_days import pair_map
    pm = pair_map(list(closes))

    # ---- estratégias -------------------------------------------------------
    strategies: dict[str, dict] = {}
    # referência (não-sobrevivente)
    strategies[f"regra_{REFERENCE_RULE} [NAO sobrevivente]"] = {
        d: RULES[REFERENCE_RULE](groups[d]) for d in days}
    # baseline continuação
    d1 = load_d1_closes()
    dd_idx = build_indices(d1, align="inner").diff()
    cont = {}
    for d in days:
        prev = dd_idx[dd_idx.index < d]
        if prev.empty:
            cont[d] = []; continue
        row = prev.iloc[-1]
        c = row.abs().idxmax()
        cont[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA", float(abs(row[c])))]
    strategies["baseline_continuacao_D1"] = cont
    # baseline persistência
    top_by_day = (df[df.labeled].sort_values("score", ascending=False)
                  .groupby("day").first())
    pers = {}
    for i, d in enumerate(days):
        prevs = [x for x in days[:i] if x in top_by_day.index]
        pers[d] = ([(top_by_day.loc[prevs[-1]].currency,
                     top_by_day.loc[prevs[-1]].direction, 1.0)]
                   if prevs else [])
    strategies["baseline_persistencia"] = pers
    # teto oracle (protagonista REAL do dia — impossível de operar; só teto)
    oracle = {d: ([(top_by_day.loc[d].currency, top_by_day.loc[d].direction,
                    1.0)] if d in top_by_day.index else []) for d in days}
    strategies["teto_oracle [lookahead: só p/ dimensionar custos]"] = oracle

    # ---- simulação + relatório --------------------------------------------
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_portfolio")
    out.mkdir(parents=True, exist_ok=True)
    lines = ["# A6 — Portfólio diário de 7 pares (dias research)",
             "", "a5 não produziu regra sobrevivente; a regra abaixo é apenas "
             "REFERÊNCIA (resultado nulo — regra dura nº 7). Custos por par: "
             f"majors {a.cost_majors} bp, crosses {a.cost_crosses} bp, "
             f"exóticos G8 {a.cost_exotic} bp.", "",
             "| estratégia | n dias | média/dia (bp) | IC95% (bp) | % dias "
             "vencedores | total | max DD |", "|---|---|---|---|---|---|---|"]
    res = {}
    for name, preds in strategies.items():
        r = simulate(preds, closes, pm, t0_hour, window_h, costs)
        m = metrics(r, a.boot_block)
        res[name] = m
        flag = " (n<100!)" if m["n"] < 100 else ""
        lines.append(f"| {name} | {m['n']}{flag} | {m['mean_bp']:+.2f} | "
                     f"[{m['lo_bp']:+.2f}, {m['hi_bp']:+.2f}] | "
                     f"{100*m['win']:.1f}% | {m['total_pct']:+.2f}% | "
                     f"{m['maxdd_pct']:.2f}% |")
        r.rename("net_ret").to_frame().to_parquet(
            out / f"daily_{name.split(' ')[0].replace('|','')}.parquet")
    lines += ["", "Leitura: IC95% por bootstrap em blocos "
              f"(blocos de {a.boot_block} dias). Estratégia só seria "
              "reportável como positiva com IC inteiro acima de 0 E acima "
              "dos baselines — condição não atingida se os ICs cruzam 0.", ""]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "params.json").write_text(json.dumps(
        {"costs_bps": {"majors": a.cost_majors, "crosses": a.cost_crosses,
                       "exotic": a.cost_exotic},
         "boot_block": a.boot_block, "reference_rule": REFERENCE_RULE,
         "metrics": res}, indent=2))
    print(f"OK -> {out}/REPORT.md")


if __name__ == "__main__":
    main()

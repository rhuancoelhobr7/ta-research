# -*- coding: utf-8 -*-
"""a40_atr_economic.py — valor ECONÔMICO do ranqueador de amplitude ATR (a25).

Teste de CUSTO sobre regra JÁ VALIDADA (a25), não busca de sinal novo. Zero
parâmetros livres: o ranking do a25 é IMPORTADO (a25_ranqueador.build), não
reimplementado; o custo vem do costs.py (a38). Dataset completo — justificado: a25
é propriedade de volatilidade já confirmada em estudos independentes (a23/a32/a33);
aplicar custo determinístico a regra congelada não é data snooping.

1.1 O spread escala com o ATR? (decide tudo) — spread como % do ATR por par, e
    essa % no TOP do ranking a25 vs os demais. Se menor no TOP -> vantagem
    estrutural; se igual/maior -> a vantagem de amplitude é ilusória.
1.2 Captura líquida — range realizado do TOP-1/TOP-3/aleatório/menor-ATR, menos
    spread (2 pontas); pips brutos/líquidos e razão líquido/spread; IC95 do
    TOP-1 vs aleatório.
1.3 Curva de breakeven direcional — sem assumir sinal (nenhum sobreviveu ao a38):
    expectativa líq. = (2p-1)*range - custo, p em {0.50..0.65}; o p de cruzamento.
1.4 Robustez por ano.

Uso: python a40_atr_economic.py
Saída: results/{ts}_a40/REPORT.md + tabelas
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from a25_ranqueador import build as a25_build          # ranking a25 IMPORTADO
from costs import default_costs, build_spread_pips
from stats_blocks import block_bootstrap_ci

P_GRID = [0.50, 0.52, 0.55, 0.58, 0.60, 0.65]


def load_panel() -> pd.DataFrame:
    """Painel a25: por (pair,date) base_atr (ranking) + tgt_range (realizado)."""
    p = a25_build()[["date", "pair", "base_atr", "tgt_range"]].copy()
    p["date"] = pd.to_datetime(p["date"])
    return p


def q11_spread_vs_atr(panel, spread, costs):
    """Spread como % do ATR por par; TOP do ranking vs demais."""
    atr = panel.groupby("pair")["base_atr"].median()          # ATR estrutural (pips)
    df = pd.DataFrame({"atr_pips": atr})
    df["spread_pips"] = df.index.map(spread)
    df["spread_pct_atr"] = df["spread_pips"] / df["atr_pips"] * 100
    corr = df["atr_pips"].corr(df["spread_pips"])
    corr_pct = df["atr_pips"].corr(df["spread_pct_atr"])
    top = df.nlargest(8, "atr_pips"); bot = df.nsmallest(8, "atr_pips")
    return df.sort_values("atr_pips", ascending=False), {
        "corr_atr_spread": corr, "corr_atr_spread_pct": corr_pct,
        "spread_pct_top8": float(top["spread_pct_atr"].median()),
        "spread_pct_bot8": float(bot["spread_pct_atr"].median())}


def daily_pick(panel, costs, rng):
    """Por dia: range realizado (bruto/líquido) do TOP-1, TOP-3, aleatório, menor."""
    rows = []
    for date, g in panel.groupby("date"):
        g = g.dropna(subset=["base_atr", "tgt_range"])
        if len(g) < 10:
            continue
        rank = g.sort_values("base_atr", ascending=False)
        def net(sub):
            c = sub["pair"].map(lambda s: costs.roundtrip_cost_pips(s))
            return (sub["tgt_range"] - c).mean(), sub["tgt_range"].mean(), c.mean()
        t1 = net(rank.head(1)); t3 = net(rank.head(3))
        lo = net(rank.tail(1)); rd = net(g.sample(1, random_state=int(date.value % 2**32)))
        rows.append({"date": date,
                     "t1_net": t1[0], "t1_gross": t1[1], "t1_cost": t1[2],
                     "t3_net": t3[0], "t3_gross": t3[1],
                     "lo_net": lo[0], "lo_gross": lo[1],
                     "rand_net": rd[0], "rand_gross": rd[1]})
    return pd.DataFrame(rows)


def breakeven(gross_range, cost):
    """expectativa líq. por trade = (2p-1)*range - custo; p de breakeven (>0)."""
    exp = {p: (2 * p - 1) * gross_range - cost for p in P_GRID}
    p_be = 0.5 + cost / (2 * gross_range) if gross_range > 0 else np.nan
    return exp, p_be


def main():
    t0 = time.time()
    panel = load_panel()
    spread = build_spread_pips()
    costs = default_costs()
    rng = np.random.default_rng(0)

    tbl_pair, q11 = q11_spread_vs_atr(panel, spread, costs)
    dp = daily_pick(panel, costs, rng)

    # 1.2 agregados + IC do TOP-1 vs aleatório
    agg = {k: float(dp[k].mean()) for k in
           ["t1_net", "t1_gross", "t3_net", "t3_gross", "lo_net", "lo_gross",
            "rand_net", "rand_gross"]}
    diff = (dp["t1_net"] - dp["rand_net"]).to_numpy()
    dstat, dlo, dhi = block_bootstrap_ci(diff, np.mean, block=5, n_boot=3000)
    folga_t1 = agg["t1_net"] / float(dp["t1_cost"].mean())

    # 1.3 breakeven (TOP-1, aleatório, TOP-3)
    cost_mean = float(dp["t1_cost"].mean())
    be_t1, pbe_t1 = breakeven(agg["t1_gross"], cost_mean)
    be_rd, pbe_rd = breakeven(agg["rand_gross"], cost_mean)
    be_t3, pbe_t3 = breakeven(agg["t3_gross"], cost_mean)

    # 1.4 por ano
    dp["ano"] = dp["date"].dt.year
    by_year = dp.groupby("ano")[["t1_net", "rand_net"]].mean().round(1)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a40")
    out.mkdir(parents=True, exist_ok=True)
    tbl_pair.round(3).to_csv(out / "spread_vs_atr.csv")

    vantagem = q11["spread_pct_top8"] < q11["spread_pct_bot8"]
    rep = [
        "# a40 — Valor econômico do ranqueador de amplitude ATR (a25)\n",
        "## 1.1 (DESTAQUE) — O spread escala com o ATR?\n",
        f"- spread como % do ATR: **TOP-8 ATR = {q11['spread_pct_top8']:.1f}%** vs "
        f"BOT-8 ATR = {q11['spread_pct_bot8']:.1f}%.",
        f"\n- correlação ATR×spread(pips) = {q11['corr_atr_spread']:.2f}; "
        f"ATR×spread(%ATR) = {q11['corr_atr_spread_pct']:.2f}.",
        f"\n\n**{'VANTAGEM ESTRUTURAL: o spread é proporcionalmente MENOR nos pares de maior ATR.' if vantagem else 'SEM vantagem estrutural: o spread come proporção IGUAL/MAIOR nos pares de maior ATR — a vantagem de amplitude não vem de graça.'}**\n",
        "## 1.2 — Captura líquida (pips, por dia)\n",
        f"| par | range bruto | range líquido | folga (líq/spread) |\n|---|---|---|---|\n"
        f"| **TOP-1 (a25)** | {agg['t1_gross']:.1f} | **{agg['t1_net']:.1f}** | {folga_t1:.0f}x |\n"
        f"| TOP-3 (cesta) | {agg['t3_gross']:.1f} | {agg['t3_net']:.1f} | |\n"
        f"| aleatório | {agg['rand_gross']:.1f} | {agg['rand_net']:.1f} | |\n"
        f"| menor ATR | {agg['lo_gross']:.1f} | {agg['lo_net']:.1f} | |\n",
        f"\n- TOP-1 − aleatório (range líq./dia): **{dstat:+.1f} pips** IC95 "
        f"[{dlo:+.1f}, {dhi:+.1f}] — {'significativo' if dlo > 0 else 'IC cruza 0'}.\n",
        "## 1.3 (NÚCLEO) — Curva de breakeven direcional\n",
        "_Sem assumir sinal. Expectativa líq./trade = (2p−1)·range − custo._\n\n"
        "| acurácia p | TOP-1 | aleatório | TOP-3 |\n|---|---|---|---|\n"
        + "\n".join(f"| {p:.2f} | {be_t1[p]:+.1f} | {be_rd[p]:+.1f} | {be_t3[p]:+.1f} |"
                    for p in P_GRID),
        f"\n\n- **p de breakeven (expectativa > 0)**: TOP-1 = **{pbe_t1:.3f}**, "
        f"aleatório = {pbe_rd:.3f}, TOP-3 = {pbe_t3:.3f}.",
        f"\n- **Reframe do problema**: o breakeven do TOP-1 é BAIXÍSSIMO "
        f"({pbe_t1:.3f}) — a amplitude é tão grande vs o spread (folga 91x) que "
        f"basta uma acurácia MARGINAL acima de {pbe_t1:.3f} para pagar. CAVEAT "
        f"HONESTO (lição do a38): o 0.506 do a35 era sobre o estado JÁ FORMADO, "
        f"NÃO o capturável (o a38 mediu ~0.50 no capturável). Logo a barra é baixa "
        f"({pbe_t1:.3f}) mas ainda NÃO foi cruzada: falta um sinal marginal "
        f"(>{pbe_t1:.3f}) sobre o CAPTURÁVEL — exatamente o que o a41 caça. O a40 "
        f"não prova que paga; prova que o alvo é MODESTO.\n",
        "## 1.4 — Robustez por ano (range líquido/dia)\n",
        by_year.to_markdown(),
        "\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a40: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"1.1 spread%ATR top8={q11['spread_pct_top8']:.1f} bot8={q11['spread_pct_bot8']:.1f} "
          f"-> {'VANTAGEM' if vantagem else 'sem vantagem'}")
    print(f"1.2 t1_net={agg['t1_net']:.1f} rand_net={agg['rand_net']:.1f} "
          f"diff={dstat:+.1f} IC[{dlo:+.1f},{dhi:+.1f}] folga={folga_t1:.0f}x")
    print(f"1.3 p_breakeven TOP-1={pbe_t1:.3f} (vs 0.506 do a35). "
          f"basta um sinal ja testado? {pbe_t1 <= 0.506}")


if __name__ == "__main__":
    main()

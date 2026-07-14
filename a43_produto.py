# -*- coding: utf-8 -*-
"""a43_produto.py — empacota o a25 como PRODUTO operável de AMPLITUDE.

O a25 é o único produto que sobreviveu a todo o projeto (a33: 29.8% vs 23.8% da
persistência vs 4.1% da cadeia composta; a42: tem informação diária real, +3.7
pips/dia sobre o estático; a40: economia favorável, breakeven 0.505). Aqui ele é
empacotado para uso, com dois MODOS validados no a42:

  MODO AMPLITUDE (A = base_atr): top-1/top-3 por ATR de sessão -> os pares de
    MAIOR movimento absoluto (crosses de GBP). ~80 pips líquidos/dia.
  MODO EFICIÊNCIA (Z = z-ATR 250d): top por anormalidade -> mais movimento POR
    SPREAD (razão de eficiência 160 vs 135 do ATR), útil p/ operador sensível a
    custo, mesmo captando menos pips absolutos.

HONESTIDADE (no card e no REPORT): isto seleciona AMPLITUDE (qual par anda mais /
com mais eficiência), NÃO direção nem lucro. A direção e a gestão são do trader.
A "amplitude líquida" do backtest é o TETO capturável (se a direção acertar), não
P&L. Reusa a25 (importado via a42), costs.py. Sem parâmetros livres.

Uso: python a43_produto.py
Saída: results/{ts}_a43/REPORT.md + pick_hoje.csv + PRODUTO_a25.md (raiz)
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd

from a42_informacao_diaria import build_scores, eval_competitor, random_bench
from costs import build_spread_pips


def backtest(ev, label):
    # amplitude DISPONÍVEL líquida (range − custo). É sempre >0 por construção
    # (range > spread), então NÃO tem drawdown: risco/DD só existem depois que a
    # DIREÇÃO entra — que o a25 não fornece. Por isso reporta-se só o piso.
    net = ev["net1"].dropna().to_numpy()
    return {"modo": label, "n_dias": len(net), "amp_liq_media_pips": float(net.mean()),
            "efic_range/spread": float(ev["eff1"].mean()),
            "P(top1=maior_range)": float(ev["is_max"].mean()),
            "pct_teto": float(ev["pct_ceil"].mean()),
            "menor_amp_dia": float(net.min())}


def pick_hoje(scores, tgt, spread):
    """Ranking do ÚLTIMO dia disponível, nos dois modos, como artefato operável."""
    last = scores["A"].dropna(how="all").index.max()
    A = scores["A"].loc[last]; Z = scores["Z250"].loc[last]
    sp = pd.Series(spread)
    ampl = pd.DataFrame({"atr_est_pips": A, "spread_pips": sp,
                         "folga_range/spread": A / sp}).dropna()
    top_amp = ampl.sort_values("atr_est_pips", ascending=False).head(3)
    top_efi = ampl.assign(zatr=Z).dropna().sort_values("zatr", ascending=False).head(3)
    return last, top_amp, top_efi


def main():
    t0 = time.time()
    scores, tgt = build_scores()
    spread = build_spread_pips()
    start = scores["Z250"].dropna(how="all").index.min()
    dates = tgt.index[tgt.index >= start]

    evA = eval_competitor(scores["A"], tgt, spread, dates)      # modo amplitude
    evZ = eval_competitor(scores["Z250"], tgt, spread, dates)   # modo eficiência
    evE = eval_competitor(scores["E"], tgt, spread, dates)      # estático (ref)
    rb = random_bench(tgt, spread, dates)

    btA = backtest(evA, "AMPLITUDE (a25/ATR)")
    btZ = backtest(evZ, "EFICIÊNCIA (z-ATR)")
    bt = pd.DataFrame([btA, btZ]).set_index("modo")
    bt.loc["estático (ref)"] = [len(evE), evE["net1"].mean(), evE["eff1"].mean(),
                                evE["is_max"].mean(), evE["pct_ceil"].mean(),
                                evE["net1"].min()]
    bt.loc["aleatório (ref)"] = [len(rb), rb["net1"].mean(), rb["eff1"].mean(),
                                 1/28, np.nan, rb["net1"].min()]

    # estabilidade por ano (amplitude líquida média do modo AMPLITUDE)
    yr = evA["net1"].groupby(evA.index.year).mean().round(1)
    last, top_amp, top_efi = pick_hoje(scores, tgt, spread)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a43")
    out.mkdir(parents=True, exist_ok=True)
    top_amp.round(2).to_csv(out / "pick_hoje_amplitude.csv")
    top_efi.round(2).to_csv(out / "pick_hoje_eficiencia.csv")

    rep = [
        "# a43 — O produto a25, empacotado (seletor de AMPLITUDE)\n",
        "**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de "
        "spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO "
        "capturável (se a direção acertar), não P&L. Direção e gestão são do "
        f"trader. {len(dates)} dias.\n",
        "## Backtest — amplitude líquida capturável por modo (pips)\n",
        bt.round(2).to_markdown(),
        f"\n\n- Modo AMPLITUDE: **{btA['amp_liq_media_pips']:.1f} pips líq/dia** "
        f"({btA['pct_teto']:.0%} do teto do dia), acerta o par de maior range em "
        f"{btA['P(top1=maior_range)']:.0%} vs 3.6% do acaso.",
        f"\n- Modo EFICIÊNCIA: menos pips ({btZ['amp_liq_media_pips']:.1f}) mas "
        f"**{btZ['efic_range/spread']:.0f} de razão range/spread** vs "
        f"{btA['efic_range/spread']:.0f} do amplitude — mais movimento por custo.\n",
        "## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)\n",
        yr.to_frame("pips").to_markdown(),
        f"\n\n## Escolha operável — último dia disponível ({last.date()})\n",
        "**Modo AMPLITUDE (maior movimento):**\n",
        top_amp.round(2).to_markdown(),
        "\n\n**Modo EFICIÊNCIA (mais movimento por spread):**\n",
        top_efi[["atr_est_pips", "spread_pips", "folga_range/spread"]].round(2).to_markdown(),
        "\n\n_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir "
        "M5 novo. Card do produto em PRODUTO_a25.md.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")

    # --- card do produto (raiz do repo) ---
    card = f"""# Produto a25 — Ranqueador de AMPLITUDE (o único sobrevivente do projeto)

## O que é
Todo dia, ordena os 28 pares G8 por MOVIMENTO esperado, usando o ATR de sessão.
Dois modos:
- **AMPLITUDE** — os pares de maior movimento absoluto (~{btA['amp_liq_media_pips']:.0f} pips
  líq/dia, {btA['pct_teto']:.0%} do teto do dia; acerta o maior-range em
  {btA['P(top1=maior_range)']:.0%} vs 3.6% do acaso). Tende a apontar crosses de GBP.
- **EFICIÊNCIA** — mais movimento POR SPREAD (razão {btZ['efic_range/spread']:.0f} vs
  {btA['efic_range/spread']:.0f}), para quem é sensível a custo.

## O que NÃO é (honestidade dura)
- **NÃO é sinal de direção.** O projeto testou ~12 formulações direcionais; todas
  mortas (a5→a41). Você escolhe a direção; o a25 só diz ONDE há movimento.
- **NÃO é P&L.** A "amplitude líquida" é o teto capturável se a direção acertar.
- **NÃO é preditor de T0 nem usa CSS** (o CSS é preço reembalado — a30/a34/a37).

## Base de evidência
a33 (29.8% vs 23.8% persistência vs 4.1% da cadeia); a40 (breakeven direcional
0.505 — economia favorável; spread é 0.5% do ATR nos pares grandes vs 1.0% nos
pequenos); a42 (tem informação diária real, +3.7 pips/dia vs estático, BH).

## Como operar
1. Ingerir M5 novo; `python a43_produto.py` gera a escolha do dia (pick_hoje_*.csv).
2. Escolher o modo (amplitude ou eficiência) conforme sensibilidade a custo.
3. Aplicar a SUA direção e gestão sobre o par escolhido.
4. Registrar prospectivamente (a39) para acumular evidência OOS honesta.

## Badge no indicador (proposta)
Exibir no painel o **top-3 de amplitude** e o **top-3 de eficiência** do dia,
marcados como "movimento esperado, não direção". Nunca sugerir lado. Latência:
o ATR de sessão é conhecido na abertura (sem espera).
"""
    pathlib.Path("PRODUTO_a25.md").write_text(card, encoding="utf-8")
    print(f"a43: {out}/REPORT.md + PRODUTO_a25.md ({time.time()-t0:.1f}s)")
    print(bt.round(1).to_string())
    print(f"\nescolha de hoje ({last.date()}) AMPLITUDE:\n", top_amp.round(1).to_string())


if __name__ == "__main__":
    main()

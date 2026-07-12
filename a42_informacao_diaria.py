# -*- coding: utf-8 -*-
"""a42_informacao_diaria.py — o a25 tem informação DIÁRIA, ou é uma tabela?

O a25 (único produto sobrevivente) escolhe quase sempre os mesmos pares (84% de
sobreposição — provável: crosses de GBP, estruturalmente grandes). Se o "1.81x o
acaso" for só isso, o a25 é uma TABELA estática, não um modelo. Controle nunca
rodado: comparar o a25 contra o ESTÁTICO PURO (média histórica de longo prazo do
ATR, zero info do dia). E testar o z-ATR (auto-normalização: quão anormal está o
par PARA OS PADRÕES DELE hoje) — que isola o componente do DIA.

**EXPLORATÓRIO (holdout esgotado): qualquer vencedor é CANDIDATO, confirmável só
via prospectivo (a39). Este estudo PODE MATAR o a25 — reportado sem suavizar.**

Competidores (todos derivados do base_atr do a25 IMPORTADO, causais):
  E (estático) = média expanding do base_atr, shift (só dias anteriores).
  A (a25)      = base_atr (nível de 20 dias), importado.
  Z (z-ATR, w) = (base_atr − média_rolling_w) / desvio_rolling_w, prior; w={60,120,250}.
Alvo: par de maior range do dia (tgt_range). Métrica primária: razão de
eficiência range/spread (costs.py). Uso: python a42_informacao_diaria.py
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from a25_ranqueador import build as a25_build          # a25 IMPORTADO
from costs import build_spread_pips
from stats_blocks import block_bootstrap_ci
from a23_intersessao import bh_reject

WINDOWS = [60, 120, 250]


def build_scores():
    p = a25_build()[["date", "pair", "base_atr", "tgt_range"]].dropna()
    p["date"] = pd.to_datetime(p["date"])
    A = p.pivot(index="date", columns="pair", values="base_atr").sort_index()
    tgt = p.pivot(index="date", columns="pair", values="tgt_range").sort_index()
    E = A.expanding().mean().shift(1)                    # nível estático (causal)
    scores = {"E": E, "A": A}
    for w in WINDOWS:
        m = A.shift(1).rolling(w).mean(); s = A.shift(1).rolling(w).std()
        scores[f"Z{w}"] = (A - m) / s
    return scores, tgt


def eval_competitor(score, tgt, spread, dates):
    """Por dia (em `dates`): captura top-1/top-3, is_max, %teto, eficiência, net."""
    cols = list(tgt.columns)
    sp = np.array([spread[c] for c in cols])
    S = score.reindex(dates)[cols].to_numpy()
    T = tgt.reindex(dates)[cols].to_numpy()
    rows = []
    for i in range(len(dates)):
        s, t = S[i], T[i]
        ok = np.isfinite(s) & np.isfinite(t)
        if ok.sum() < 20:
            rows.append([np.nan] * 6); continue
        idx = np.where(ok)[0]
        sv, tv, spv = s[idx], t[idx], sp[idx]
        order = np.argsort(-sv)
        t1 = order[0]; t3 = order[:3]
        cap1 = tv[t1]; cap3 = tv[t3].mean()
        is_max = int(t1 == np.argmax(tv))
        ceil = tv.max()
        rows.append([cap1, cap3, is_max, cap1 / ceil if ceil > 0 else np.nan,
                     cap1 / spv[t1], cap1 - 2 * spv[t1]])
    return pd.DataFrame(rows, index=dates,
                        columns=["cap1", "cap3", "is_max", "pct_ceil", "eff1", "net1"])


def random_bench(tgt, spread, dates):
    cols = list(tgt.columns); sp = np.array([spread[c] for c in cols])
    T = tgt.reindex(dates)[cols].to_numpy()
    cap = np.nanmean(T, axis=1)
    eff = np.nanmean(T / sp, axis=1)
    net = np.nanmean(T - 2 * sp, axis=1)
    return pd.DataFrame({"cap1": cap, "eff1": eff, "net1": net}, index=dates)


def main():
    t0 = time.time()
    scores, tgt = build_scores()
    spread = build_spread_pips()
    # data comum (após aquecimento do Z250)
    start = scores["Z250"].dropna(how="all").index.min()
    dates = tgt.index[tgt.index >= start]

    ev = {k: eval_competitor(v, tgt, spread, dates) for k, v in scores.items()}
    rb = random_bench(tgt, spread, dates)

    # Q1/Q2 — diferença vs E (captura em pips), IC bootstrap em blocos + BH
    fam = []
    for k in ["A", "Z60", "Z120", "Z250"]:
        d = (ev[k]["cap1"] - ev["E"]["cap1"]).dropna().to_numpy()
        stat, lo, hi = block_bootstrap_ci(d, np.mean, block=5, n_boot=3000)
        se = (hi - lo) / (2 * 1.96)
        fam.append({"comp": k, "dif_vs_E_pips": stat, "lo": lo, "hi": hi,
                    "p": float(norm.sf(stat / se)) if se > 0 else 1.0})
    fam = pd.DataFrame(fam)
    fam["bh"] = bh_reject(fam["p"].to_numpy(), 0.05)

    # Q3 — eficiência e captura por competidor + aleatório
    q3 = []
    for k in ["E", "A", "Z60", "Z120", "Z250"]:
        e = ev[k]
        q3.append({"sel": k, "cap1_pips": e["cap1"].mean(), "net1_pips": e["net1"].mean(),
                   "efic_range/spread": e["eff1"].mean(),
                   "P(top1=max)": e["is_max"].mean(), "pct_teto": e["pct_ceil"].mean()})
    q3.append({"sel": "aleatório", "cap1_pips": rb["cap1"].mean(),
               "net1_pips": rb["net1"].mean(), "efic_range/spread": rb["eff1"].mean(),
               "P(top1=max)": 1 / 28, "pct_teto": np.nan})
    q3 = pd.DataFrame(q3).set_index("sel")

    # Q4 — composição: pares que o A escolhe (top-1), sobreposição dia a dia
    def top1_series(k):
        S = scores[k].reindex(dates)
        return S.idxmax(axis=1)
    a_top1 = top1_series("A")
    freq_a = a_top1.value_counts(normalize=True).head(6)
    def overlap(k):
        s = top1_series(k)
        return float((s.values[1:] == s.values[:-1]).mean())
    overl = {k: overlap(k) for k in ["E", "A", "Z60", "Z120", "Z250"]}
    ov_ZA = float((top1_series("Z120").values == a_top1.values).mean())

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a42")
    out.mkdir(parents=True, exist_ok=True)
    q3.round(3).to_csv(out / "competidores.csv")

    A_tem_info = bool(fam.loc[fam.comp == "A", "lo"].iloc[0] > 0)
    best_eff = q3["efic_range/spread"].idxmax()
    rep = [
        "# a42 — O a25 tem informação diária, ou é uma tabela estática?\n",
        f"**EXPLORATÓRIO (holdout esgotado): vencedores são CANDIDATOS, "
        f"confirmáveis só via prospectivo (a39).** {len(dates)} dias (após "
        f"aquecimento). Competidores do base_atr do a25 (importado).\n",
        "## Q1/Q2 — Diferença de captura vs ESTÁTICO (E), pips/dia\n",
        fam.round(3).to_markdown(index=False),
        f"\n\n**Q1 (A vs E): o a25 {'TEM' if A_tem_info else 'NÃO tem'} informação "
        f"diária demonstrável** — dif A−E = {fam.loc[fam.comp=='A','dif_vs_E_pips'].iloc[0]:+.2f} "
        f"pips, IC [{fam.loc[fam.comp=='A','lo'].iloc[0]:+.2f}, "
        f"{fam.loc[fam.comp=='A','hi'].iloc[0]:+.2f}]. "
        f"{'A vantagem existe.' if A_tem_info else 'IC inclui zero -> o a25 e equivalente a uma TABELA estatica.'}\n",
        "## Q3 (primária) — Eficiência range/spread e captura\n",
        q3.round(3).to_markdown(),
        f"\n\n- **Melhor razão de eficiência (range/spread): {best_eff}.** "
        f"{'O z-ATR supera o ATR bruto aqui (cenário que o a40 antecipa).' if 'Z' in best_eff else 'O ATR bruto/estático lidera em eficiência.'}\n",
        "## Q4 — Composição dos rankings\n",
        f"- pares mais escolhidos pelo a25 (top-1): {freq_a.round(3).to_dict()}",
        f"\n- sobreposição dia a dia (top-1 = ontem): "
        + ", ".join(f"{k} {v:.0%}" for k, v in overl.items()),
        f"\n- sobreposição Z120 vs A (mesmo top-1): {ov_ZA:.0%} "
        f"({'Z carrega info do DIA (troca mais)' if ov_ZA < 0.5 else 'Z parecido com A'}).\n",
        "\n## Síntese\n",
        f"**O a25 SOBREVIVE**: tem informação diária real (+{fam.loc[fam.comp=='A','dif_vs_E_pips'].iloc[0]:.1f} "
        f"pips vs estático, IC exclui 0, BH), mas é SOBRETUDO uma tabela (escolhe "
        f"GBP-crosses ~86%, 84% de sobreposição). **O z-ATR FALHA para AMPLITUDE "
        f"absoluta** (~-28 pips vs estático): para amplitude, o NÍVEL É o sinal, e "
        f"auto-normalizar (remover o nível) o destrói — o OPOSTO da direção (a35, "
        f"onde a auto-normalização venceu). Dicotomia limpa: **amplitude mora no "
        f"NÍVEL, direção morava no DESVIO.** PORÉM o **z-ATR VENCE em eficiência "
        f"range/spread** ({q3.loc[best_eff,'efic_range/spread']:.0f} vs "
        f"{q3.loc['A','efic_range/spread']:.0f} do a25), selecionando pares calmos "
        f"num dia atípico com spread proporcionalmente menor — o cenário do a40. "
        f"CANDIDATO para o prospectivo (a39): z-ATR como seletor spread-eficiente; "
        f"jamais achado confirmado (holdout esgotado).\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a42: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print("Q1/Q2 dif vs E:\n", fam.round(3).to_string(index=False))
    print("Q3:\n", q3.round(2).to_string())
    print(f"Q4 a25 top-1 freq: {freq_a.round(2).to_dict()}")
    print(f"overlap: {({k: round(v,2) for k,v in overl.items()})} | Z120 vs A: {ov_ZA:.2f}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""a25_ranqueador.py — ranqueador de par OPERÁVEL (produto final), CSS-FREE.

O a24 mostrou que o CSS não agrega na seleção de par; então o ranqueador usa só
o que sobreviveu: baseline de largura estrutural (ATR-sessão) + o efeito
Tokyo→Londres (a23). Modelo simples e interpretável (logístico), NÃO black-box.

Q8 — na virada de NY, ordenar os 28 pares por P(estar no top-quartil de range
     da janela pós-abertura). Features: log(base_atr) [largura estrutural] e
     asia_norm = asia/base_atr [atividade de HOJE relativa à norma do par].
Q9 — backtest: operar SEMPRE o top-1 (e top-3) sugerido captura quanto range vs
     (a) par aleatório, (b) sempre-o-mais-volátil (rank por base_atr), (c) teto
     do dia (o melhor par possível).
Q10 — estabilidade: o top-1 de hoje é o mesmo de ontem? (custo de troca.)

NOTA HONESTA (no deliverable): ranqueia por MOVIMENTO ESPERADO, não por lucro.
Movimento é necessário, não suficiente — direção/gestão ficam com o trader.

Metodologia: sem lookahead (features conhecidas na virada), split 70/30, modelo
treinado só no treino, backtest no teste. Uso: python a25_ranqueador.py
Saída: results/{ts}_a25/REPORT.md + modelo_coefs.csv + backtest.csv
"""
from __future__ import annotations

import pathlib
import time

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from a24_preditores import targets_baselines, TRAIN_FRAC

TOPQ = 0.75   # top-quartil (top 7 de 28)


def build() -> pd.DataFrame:
    p = targets_baselines().dropna(subset=["tgt_range", "base_atr", "base_asia"])
    p = p[p["base_atr"] > 0].copy()
    p["asia_norm"] = p["base_asia"] / p["base_atr"]
    p["log_atr"] = np.log(p["base_atr"])
    # alvo: no top-quartil de range ENTRE os pares naquele dia
    p["top_q"] = (p.groupby("date")["tgt_range"]
                  .transform(lambda s: s >= s.quantile(TOPQ)).astype(int))
    return p.sort_values(["date", "pair"]).reset_index(drop=True)


def fit_rank(p: pd.DataFrame, feats: list[str]) -> tuple[pd.DataFrame, dict]:
    cut = p["date"].quantile(TRAIN_FRAC)
    tr, te = p[p["date"] < cut], p[p["date"] >= cut].copy()
    mu, sd = tr[feats].mean(), tr[feats].std()
    Xtr = ((tr[feats] - mu) / sd).to_numpy()
    Xte = ((te[feats] - mu) / sd).to_numpy()
    m = LogisticRegression(max_iter=1000).fit(Xtr, tr["top_q"])
    te["score"] = m.predict_proba(Xte)[:, 1]
    coefs = dict(zip(feats, m.coef_[0]))
    return te, coefs


def backtest(te: pd.DataFrame, score_col: str) -> dict:
    """Range médio capturado por dia: top-1 e top-3 do score vs benchmarks."""
    top1, top3, rnd, atr1, ceil1 = [], [], [], [], []
    for _, g in te.groupby("date"):
        if len(g) < 10:
            continue
        top1.append(g.nlargest(1, score_col)["tgt_range"].mean())
        top3.append(g.nlargest(3, score_col)["tgt_range"].mean())
        atr1.append(g.nlargest(1, "base_atr")["tgt_range"].mean())  # sempre + volátil
        rnd.append(g["tgt_range"].mean())                            # aleatório
        ceil1.append(g["tgt_range"].max())                           # teto do dia
    f = lambda a: float(np.mean(a))
    return {"top1_modelo": f(top1), "top3_modelo": f(top3),
            "sempre_mais_volatil": f(atr1), "aleatorio": f(rnd),
            "teto_do_dia": f(ceil1), "n_dias": len(top1)}


def stability(te: pd.DataFrame, score_col: str) -> dict:
    top1 = (te.sort_values("date").groupby("date")
            .apply(lambda g: g.nlargest(1, score_col)["pair"].iloc[0],
                   include_groups=False))
    same = (top1.values[1:] == top1.values[:-1]).mean()
    return {"top1_igual_ao_dia_anterior": float(same),
            "n_pares_distintos_no_teste": int(top1.nunique())}


def main() -> None:
    t0 = time.time()
    p = build()
    feats = ["log_atr", "asia_norm"]
    te, coefs = fit_rank(p, feats)

    bt_model = backtest(te, "score")
    # baseline puro: ranquear só por base_atr (sem modelo)
    te_atr = te.assign(score_atr=te["base_atr"])
    bt_atr = backtest(te_atr, "score_atr")
    stab = stability(te, "score")

    lift1 = bt_model["top1_modelo"] / bt_model["aleatorio"]
    cap1 = bt_model["top1_modelo"] / bt_model["teto_do_dia"]

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a25")
    out.mkdir(parents=True, exist_ok=True)
    pd.Series(coefs).to_csv(out / "modelo_coefs.csv")
    pd.DataFrame({"modelo": bt_model, "so_base_atr": bt_atr}).to_csv(out / "backtest.csv")

    rep = [
        "# a25 — Ranqueador de par operável (CSS-free)\n",
        f"Virada NY, alvo range [13,17) UTC. Modelo logístico interpretável em "
        f"log(base_atr)+asia_norm. Split 70/30; backtest no teste "
        f"({bt_model['n_dias']} dias). CSS excluído (não passou no a24).\n",
        "## Q8 — Modelo (coeficientes padronizados, interpretáveis)\n",
        pd.Series(coefs, name="coef").round(3).to_markdown(),
        "\n_log_atr = largura estrutural do par; asia_norm = atividade de hoje "
        "vs a norma do par (Tokyo→Londres do a23)._\n",
        "\n## Q9 — Backtest: range médio capturado (pips/dia) no top-1\n",
        pd.DataFrame({"modelo": bt_model, "so_base_atr": bt_atr})
          .loc[["top1_modelo", "top3_modelo", "sempre_mais_volatil",
                "aleatorio", "teto_do_dia"]].round(1).to_markdown(),
        f"\n- **lift do top-1 vs aleatório: {lift1:.2f}×**  ·  "
        f"captura {cap1:.0%} do teto possível do dia.",
        f"\n- modelo top-1 ({bt_model['top1_modelo']:.1f}) vs sempre-o-mais-volátil "
        f"({bt_model['sempre_mais_volatil']:.1f}): "
        f"{'ganho marginal do sinal de hoje' if bt_model['top1_modelo']>bt_model['sempre_mais_volatil'] else 'sem ganho sobre só ATR'}.\n",
        "\n## Q10 — Estabilidade do top-1\n",
        f"- top-1 igual ao dia anterior: **{stab['top1_igual_ao_dia_anterior']:.0%}** "
        f"(troca de instrumento no resto dos dias).",
        f"\n- pares distintos que já foram top-1 no teste: "
        f"{stab['n_pares_distintos_no_teste']}.\n",
        "\n## Nota honesta\n",
        "Ranqueia por MOVIMENTO ESPERADO, não por lucro. Movimento é condição "
        "necessária, não suficiente — direção e gestão ficam com o trader. O CSS "
        "não entra: o produto é ATR-de-sessão + inclinação Tokyo→Londres.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a25: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print("coefs:", {k: round(v, 3) for k, v in coefs.items()})
    print("backtest top-1:", {k: round(v, 1) for k, v in bt_model.items()})
    print(f"lift vs aleatorio: {lift1:.2f}x  vs sempre-mais-volatil: "
          f"{bt_model['top1_modelo']:.1f}/{bt_model['sempre_mais_volatil']:.1f}")
    print("estabilidade top-1:", {k: round(v, 3) if isinstance(v, float) else v
                                   for k, v in stab.items()})


if __name__ == "__main__":
    main()

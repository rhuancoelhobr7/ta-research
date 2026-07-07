"""fase5_estatistica.py — métricas, inferência e a CONFIRMAÇÃO (uma vez).

Métricas: AUC, Brier, precision@k (k = taxa-base da janela; empates
resolvidos por valor esperado). Inferência: bootstrap em blocos (IC 95%
do lift sobre o melhor baseline) e permutação em blocos (p do AUC) —
reutiliza stats_blocks do programa (testado em tests/ da raiz).

Rodar este módulo = tocar a janela de confirmação (CLAUDE.md regra 2):
recusa-se a rodar se RELATORIO_CONFIRMACAO.md já existe; a flag
--autorizado-por-humano registra a violação no próprio relatório.
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, roc_auc_score

from comum import DATA, RES, config
from stats_blocks import _circular_blocks, block_permute  # raiz do programa


# ----------------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------------

def precision_at_k(y: np.ndarray, score: np.ndarray, k: int) -> float:
    """Precisão nos k maiores scores; empates no corte -> valor esperado."""
    if k <= 0:
        return float("nan")
    ordem = np.argsort(-score, kind="stable")
    s_ord, y_ord = score[ordem], y[ordem]
    corte = s_ord[k - 1]
    acima = s_ord > corte
    n_acima = int(acima.sum())
    ties = s_ord == corte
    y_ties = y_ord[ties]
    esperado = y_ord[acima].sum() + (k - n_acima) * y_ties.mean()
    return float(esperado / k)


def metricas(y: np.ndarray, score: np.ndarray) -> dict:
    base = float(y.mean())
    k = max(1, int(round(base * len(y))))
    auc = float(roc_auc_score(y, score)) if len(np.unique(score)) > 1 else 0.5
    return {"n": len(y), "taxa_base": base, "k": k, "auc": auc,
            "p_at_k": precision_at_k(y, score, k),
            "brier": float(brier_score_loss(y, np.clip(score, 0, 1)))}


def baselines_scores(feats: pd.DataFrame, y: np.ndarray) -> dict[str, np.ndarray]:
    prot_prev = (feats["f3_usd_prot_prev"].to_numpy(dtype=float) != 0)
    return {"taxa_base": np.full(len(y), float(y.mean())),
            "persistencia": prot_prev.astype(float),
            "reversao": (~prot_prev).astype(float)}


# ----------------------------------------------------------------------------
# Inferência
# ----------------------------------------------------------------------------

def ic_lift_bootstrap(y: np.ndarray, score: np.ndarray, score_base: np.ndarray,
                      cfg: dict, seed: int = 0) -> tuple[float, float, float]:
    """(lift, lo, hi): IC 95% do lift de precision@k sobre um baseline,
    bootstrap circular em blocos de dias."""
    e = cfg["estatistica"]
    rng = np.random.default_rng(seed)
    n = len(y)

    def lift(idx):
        yy = y[idx]
        k = max(1, int(round(yy.mean() * len(yy))))
        if yy.sum() in (0, len(yy)):
            return np.nan
        return (precision_at_k(yy, score[idx], k)
                - precision_at_k(yy, score_base[idx], k))

    obs = lift(np.arange(n))
    dist = [lift(_circular_blocks(n, e["boot_bloco_dias"], rng))
            for _ in range(e["boot_n"])]
    dist = np.array([d for d in dist if np.isfinite(d)])
    lo, hi = np.percentile(dist, [100 * e["alpha"] / 2, 100 * (1 - e["alpha"] / 2)])
    return float(obs), float(lo), float(hi)


def p_perm_auc(y: np.ndarray, score: np.ndarray, cfg: dict,
               seed: int = 1) -> float:
    """p-valor do AUC por permutação dos rótulos em blocos."""
    e = cfg["estatistica"]
    rng = np.random.default_rng(seed)
    obs = roc_auc_score(y, score)
    n = len(y)
    piores = 0
    for _ in range(e["perm_n"]):
        yp = y[block_permute(n, e["perm_bloco_dias"], rng)]
        if yp.sum() in (0, n):
            piores += 1
            continue
        if roc_auc_score(yp, score) >= obs:
            piores += 1
    return float((1 + piores) / (1 + e["perm_n"]))


# ----------------------------------------------------------------------------
# Confirmação — UMA vez
# ----------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--autorizado-por-humano", action="store_true",
                    help="segunda execução: exige autorização explícita")
    a = ap.parse_args()

    rel = RES / "RELATORIO_CONFIRMACAO.md"
    violacao = ""
    if rel.exists():
        if not a.autorizado_por_humano:
            print("RECUSADO: a confirmação já foi tocada (CLAUDE.md regra 2). "
                  "Segunda execução exige --autorizado-por-humano.")
            return 2
        violacao = ("\n> **VIOLAÇÃO DE PROTOCOLO REGISTRADA**: segunda execução "
                    "da confirmação, autorizada por humano via flag.\n")

    cfg = config()
    frozen = pickle.loads((RES / "modelo_congelado.pkl").read_bytes())
    split = json.loads((RES / "split.json").read_text())
    feats = pd.read_parquet(DATA / "features.parquet")
    labels = pd.read_parquet(DATA / "labels_usd.parquet").reindex(feats.index)

    conf = feats.loc[feats.index >= pd.Timestamp(split["confirmacao_inicio"])]
    y = (labels.loc[conf.index, "classe"] != "none").to_numpy()
    bases = baselines_scores(conf, y)

    L = [f"# RELATÓRIO DE CONFIRMAÇÃO — v3 USD caso-controle{violacao}",
         f"\nJanela: {conf.index[0].date()} → {conf.index[-1].date()} "
         f"({len(conf)} dias; descoberta congelada em {split['descoberta_fim']}; "
         f"buffer {split['buffer_dias']} dias úteis descartado).",
         f"\nTaxa-base na confirmação: **{y.mean():.1%}** "
         f"({int(y.sum())}/{len(y)} dias protagonista).\n"]

    resultados = {}
    for nome, art in frozen.items():                 # primario_f13, benchmark_f4
        score = art["model"].predict_proba(conf[art["cols"]].to_numpy(dtype=float))[:, 1]
        m = metricas(y, score)
        pk_bases = {b: precision_at_k(y, s, m["k"]) for b, s in bases.items()}
        melhor = max(pk_bases, key=pk_bases.get)
        lift, lo, hi = ic_lift_bootstrap(y, score, bases[melhor], cfg)
        pperm = p_perm_auc(y, score, cfg)
        resultados[nome] = {"m": m, "pk_bases": pk_bases, "melhor": melhor,
                            "lift": (lift, lo, hi), "p": pperm}

        L += [f"\n## {nome} ({art['familia']}, {len(art['cols'])} features)\n",
              "| métrica | valor |", "|---|---|",
              f"| AUC | {m['auc']:.4f} (p-perm = {pperm:.4f}) |",
              f"| precision@k (k={m['k']}) | {m['p_at_k']:.3f} |",
              f"| Brier | {m['brier']:.4f} |"]
        L += [f"| p@k baseline `{b}` | {v:.3f} |" for b, v in pk_bases.items()]
        L += [f"| **lift vs melhor baseline (`{melhor}`)** | "
              f"**{lift:+.3f}** IC95% [{lo:+.3f}, {hi:+.3f}] |"]

    # ------------- critérios de saída (pré-registrados) -------------------
    prim = resultados["primario_f13"]
    positivo = (prim["lift"][1] > 0) and (prim["p"] < cfg["estatistica"]["alpha"])
    f4 = resultados["benchmark_f4"]
    f4_positivo = (f4["lift"][1] > 0) and (f4["p"] < cfg["estatistica"]["alpha"])

    L += ["\n## Veredito (critérios pré-registrados)\n"]
    if positivo:
        L += ["**POSITIVO**: IC 95% do lift sobre o melhor baseline não cruza "
              "zero E p-perm < 0.05. Previsibilidade em T0 existe; próxima "
              "etapa é redesenhar o motor em torno das features vencedoras."]
    else:
        L += ["**NULO**: o critério positivo não foi atingido. Com estas "
              "features, o USD protagonista **não é previsível em T0**."]
    if positivo and not f4_positivo:
        L += ["\nDiagnóstico do benchmark: F1–F3 com lift e F4 sem — evidência "
              "definitiva para substituição do motor CSSM."]
    elif not positivo and not f4_positivo:
        L += ["\nF1–F3 e F4 ambos nulos: a evidência aponta que o fenômeno é "
              "primariamente **identificável em retrospecto**, não previsível "
              "em T0 — resposta direta à questão aberta do programa."]
    elif f4_positivo:
        L += ["\nF4 atingiu o critério positivo: a quarentena do CSSM termina "
              "em absolvição neste recorte."]

    L += ["\n## Interpretação\n",
          "Este teste foi executado UMA única vez sobre o modelo congelado da "
          "descoberta, como pré-registrado. O que este resultado muda na "
          "decisão de trading: um resultado NULO significa que nenhuma das "
          "leituras disponíveis à meia-noite do servidor (véspera da abertura "
          "de Tóquio) — nem as relacionais brutas, nem o CSSM — antecipa o "
          "dia de tendência absoluta do USD melhor que regras triviais; "
          "qualquer uso operacional do fenômeno continua sendo REAÇÃO "
          "(reconhecimento em curso), não antecipação.",
          "\n## Limitações\n",
          "- Amostra de confirmação limitada (~9-10 meses de dias úteis).",
          "- Rótulo calibrado na leitura C da magnitude (ver CLAUDE.md).",
          "- F3 'qualquer moeda' usa proxy contínuo (7 pares apenas).",
          "- F4 exclui a lente D1 estrutural (aquecimento > metade da amostra)."]

    rel.write_text("\n".join(L), encoding="utf-8")
    print(f"CONFIRMAÇÃO escrita em {rel}")
    print(f"primário F13: AUC={prim['m']['auc']:.4f} p={prim['p']:.4f} "
          f"lift={prim['lift'][0]:+.3f} IC[{prim['lift'][1]:+.3f},{prim['lift'][2]:+.3f}] "
          f"-> {'POSITIVO' if positivo else 'NULO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

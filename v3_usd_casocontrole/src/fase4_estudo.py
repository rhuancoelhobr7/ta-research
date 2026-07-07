"""fase4_estudo.py — Descoberta (primeiros ~70%), modelo congelado.

- Split temporal disjunto: descoberta 70% -> buffer 10 dias úteis
  descartados -> confirmação 30% (intocada aqui).
- Descoberta: CV purgada (5 folds contíguos, gap 10 dias) p/ escolher a
  família (logit vs GBM raso) por AUC out-of-fold; H2 (alta vs baixa) e
  H3 (F1-F3 vs F4) só na descoberta.
- Congela: melhor modelo pooled F1-F3 (teste primário pré-registrado) e
  melhor F4 (diagnóstico do benchmark) treinados na descoberta inteira.
  F4 NUNCA entra no mesmo modelo que F1-F3 (CLAUDE.md regra 5).
"""
from __future__ import annotations

import json
import pickle
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from comum import DATA, RES, config, gate_fase0
from stats_blocks import purged_cv_splits          # raiz do programa
from fase5_estatistica import baselines_scores, metricas, precision_at_k


def fazer_modelo(familia: str, cfg: dict):
    m = cfg["modelos"]
    if familia == "logit":
        return make_pipeline(StandardScaler(),
                             LogisticRegression(max_iter=2000))
    return GradientBoostingClassifier(
        max_depth=m["gbm_max_depth"], n_estimators=m["gbm_n_estimators"],
        learning_rate=m["gbm_learning_rate"], random_state=0)


def oof_scores(X: np.ndarray, y: np.ndarray, familia: str, cfg: dict) -> np.ndarray:
    m = cfg["modelos"]
    out = np.full(len(y), np.nan)
    for tr, te in purged_cv_splits(len(y), m["cv_folds"], m["cv_gap_dias"]):
        if len(np.unique(y[tr])) < 2:
            continue
        mod = fazer_modelo(familia, cfg).fit(X[tr], y[tr])
        out[te] = mod.predict_proba(X[te])[:, 1]
    return out


def main() -> int:
    gate_fase0()
    cfg = config()
    feats = pd.read_parquet(DATA / "features.parquet")
    labels = pd.read_parquet(DATA / "labels_usd.parquet").reindex(feats.index)

    n = len(feats)
    n_disc = int(np.floor(cfg["split"]["descoberta_frac"] * n))
    buf = cfg["split"]["buffer_dias_uteis"]
    disc = feats.iloc[:n_disc]
    conf_inicio = feats.index[n_disc + buf]
    split = {"n_total": n, "n_descoberta": n_disc, "buffer_dias": buf,
             "descoberta_fim": str(disc.index[-1].date()),
             "confirmacao_inicio": str(conf_inicio.date())}
    (RES / "split.json").write_text(json.dumps(split, indent=2))

    y = (labels.loc[disc.index, "classe"] != "none").to_numpy()
    y_up = (labels.loc[disc.index, "classe"] == "up").to_numpy()
    y_dn = (labels.loc[disc.index, "classe"] == "down").to_numpy()

    cols_f13 = [c for c in feats.columns if c[:3] in ("f1_", "f2_", "f3_")]
    cols_f4 = [c for c in feats.columns if c.startswith("f4_")]
    conjuntos = {"F1-F3": cols_f13, "F4": cols_f4}

    L = ["# RELATÓRIO DE DESCOBERTA — v3 USD caso-controle",
         "\n## Sumário executivo\n", "(preenchido ao final)\n",
         f"\n## Janela e classes\n",
         f"- Descoberta: {disc.index[0].date()} → {disc.index[-1].date()} "
         f"({n_disc} dias); buffer de {buf} dias úteis descartado; "
         f"confirmação começa em {split['confirmacao_inicio']} (intocada).",
         f"- Taxa-base pooled: **{y.mean():.1%}** "
         f"(up {y_up.mean():.1%}, down {y_dn.mean():.1%}).\n"]

    # ------------------- pooled: CV por família x conjunto ----------------
    L += ["## Modelos pooled (AUC out-of-fold, CV purgada 5 folds gap 10)\n",
          "| conjunto | família | AUC OOF | p@k OOF |", "|---|---|---|---|"]
    oof = {}
    resumo_cv = {}
    for cj, cols in conjuntos.items():
        X = disc[cols].to_numpy(dtype=float)
        for fam in cfg["modelos"]["familias"]:
            s = oof_scores(X, y, fam, cfg)
            ok = np.isfinite(s)
            m = metricas(y[ok], s[ok])
            oof[(cj, fam)] = s
            resumo_cv[(cj, fam)] = m["auc"]
            L.append(f"| {cj} | {fam} | {m['auc']:.4f} | {m['p_at_k']:.3f} |")

    # baselines na descoberta
    bases = baselines_scores(disc, y)
    k = max(1, int(round(y.mean() * len(y))))
    L += ["\n## Baselines na descoberta\n",
          "| baseline | AUC | p@k |", "|---|---|---|"]
    for b, s in bases.items():
        auc_b = roc_auc_score(y, s) if len(np.unique(s)) > 1 else 0.5
        L.append(f"| {b} | {auc_b:.4f} | {precision_at_k(y, s, k):.3f} |")

    # ------------------- H2: alta vs baixa (exploratório) -----------------
    L += ["\n## H2 — precursores de alta vs baixa (exploratório, só descoberta)\n",
          "| alvo | família | AUC OOF |", "|---|---|---|"]
    X13 = disc[cols_f13].to_numpy(dtype=float)
    for alvo, yy in (("up", y_up), ("down", y_dn)):
        for fam in cfg["modelos"]["familias"]:
            s = oof_scores(X13, yy, fam, cfg)
            ok = np.isfinite(s)
            auc_a = roc_auc_score(yy[ok], s[ok])
            L.append(f"| USD {alvo} | {fam} | {auc_a:.4f} |")
    # coeficientes direcionais do logit (sinal dos precursores)
    lu = fazer_modelo("logit", cfg).fit(X13, y_up)
    ld = fazer_modelo("logit", cfg).fit(X13, y_dn)
    cu = lu.named_steps["logisticregression"].coef_[0]
    cd = ld.named_steps["logisticregression"].coef_[0]
    ordem = np.argsort(-np.abs(cu - cd))[:8]
    L += ["\nMaiores divergências de coeficiente (up − down):\n",
          "| feature | coef up | coef down |", "|---|---|---|"]
    for i in ordem:
        L.append(f"| {cols_f13[i]} | {cu[i]:+.3f} | {cd[i]:+.3f} |")

    # ------------------- congelamento -------------------------------------
    fam13 = max(cfg["modelos"]["familias"], key=lambda f: resumo_cv[("F1-F3", f)])
    fam4 = max(cfg["modelos"]["familias"], key=lambda f: resumo_cv[("F4", f)])
    frozen = {}
    for nome, cols, fam in (("primario_f13", cols_f13, fam13),
                            ("benchmark_f4", cols_f4, fam4)):
        mod = fazer_modelo(fam, cfg).fit(disc[cols].to_numpy(dtype=float),
                                         (labels.loc[disc.index, "classe"] != "none"))
        frozen[nome] = {"model": mod, "cols": cols, "familia": fam}
    (RES / "modelo_congelado.pkl").write_bytes(pickle.dumps(frozen))

    # ------------------- sumário + H3 -------------------------------------
    a13 = resumo_cv[("F1-F3", fam13)]
    a4 = resumo_cv[("F4", fam4)]
    sumario = [
        f"Na descoberta ({n_disc} dias), o melhor modelo com as features "
        f"relacionais brutas (F1-F3, família {fam13}) atinge AUC out-of-fold "
        f"de **{a13:.3f}**; o benchmark CSSM v1.41 (F4, família {fam4}) "
        f"atinge **{a4:.3f}** (H3: {'F1-F3 supera F4' if a13 > a4 + 0.01 else ('F4 supera F1-F3' if a4 > a13 + 0.01 else 'empate prático')} "
        f"neste dataset).",
        "AUC ~0.5 = indistinguível de moeda ao ar. O teste que DECIDE é a "
        "confirmação (única, modelo congelado) — este relatório não autoriza "
        "conclusão preditiva.",
        f"\nModelos congelados: primário F1-F3 ({fam13}) e benchmark F4 "
        f"({fam4}), treinados na descoberta inteira, salvos em "
        "resultados/modelo_congelado.pkl."]
    L[2] = "\n".join(sumario)

    L += ["\n## Limitações\n",
          "- Tudo acima é DESCOBERTA: números OOF, sem garantia fora dela.",
          "- Lista de features fechada (CLAUDE.md regra 3); ideias novas em "
          "IDEIAS_FUTURAS.md.",
          "- Ver trilha de calibração do rótulo em CLAUDE.md (leitura C)."]
    (RES / "RELATORIO_DESCOBERTA.md").write_text("\n".join(L), encoding="utf-8")
    print(f"descoberta OK: F1-F3 {fam13} AUC={a13:.4f} | F4 {fam4} AUC={a4:.4f}")
    print(f"relatório em {RES/'RELATORIO_DESCOBERTA.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

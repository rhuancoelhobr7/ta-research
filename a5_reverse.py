"""a5_reverse.py — Fase B: contraste (B1), regras (B2), baselines (B3), ML (B4).

ESPECIFICAÇÃO (PLAN.md §5): usa features_t0 + labels, APENAS dias research
(treino+validação de splits_days). Saída: results/{ts}_reverse/REPORT.md.

NOTA sobre 'cenários A/B/C do Protocolo': o documento do Protocolo não está
no repositório; as regras P_A/P_B/P_C abaixo são APROXIMAÇÕES declaradas
(maturidade multi-TF / emergência alinhada / exaustão contrária) e estão
rotuladas como tal no relatório.

Avaliação de regra: previsão diária = ranking de (moeda, direção) por score;
acerto top-1 = a 1ª candidata estava rotulada naquele dia com a direção
prevista; hit@2 = alguma das 2 primeiras acertou; precision@2 = média de
acertos entre as 2 primeiras. Regra só sobrevive se top-1 > os 3 baselines
E > p95 dos máximos de 200 permutações em bloco (reality check).
"""
from __future__ import annotations

import json, pathlib, time
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes
from a4_features_t0 import load_d1_closes
from cssm_engine import G8, build_indices
from splits_days import research_days
from stats_blocks import block_permute, purged_cv_splits, reality_check_p95


# ----------------------------------------------------------------------------
# Carga e recortes
# ----------------------------------------------------------------------------

def load_research():
    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    feat = pd.read_parquet("data/features/features_t0.parquet")
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = set(train) | set(valid)
    lab = lab[lab.day.isin(keep)].reset_index(drop=True)
    feat = feat[feat.day.isin(keep)].reset_index(drop=True)
    df = feat.merge(lab[["day", "currency", "labeled", "direction", "score"]],
                    on=["day", "currency"], how="left")
    df["labeled"] = df["labeled"].fillna(False)
    return df.sort_values(["day", "currency"]).reset_index(drop=True)


# ----------------------------------------------------------------------------
# B1 — contraste descritivo
# ----------------------------------------------------------------------------

def b1_contrast(df: pd.DataFrame, lines: list[str]):
    lines.append("## B1 — Contraste descritivo (rotulado vs não)")
    fcols = [c for c in df.columns if any(c.startswith(f"{tf}_")
             for tf in ("M30", "H1", "H4", "D1", "W1"))]
    num = [c for c in fcols if not c.endswith("_state")]
    rows = []
    for c in num:
        a = df.loc[df.labeled, c].dropna()
        b = df.loc[~df.labeled, c].dropna()
        if len(a) < 30 or len(b) < 30:
            continue
        pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        d = (a.mean() - b.mean()) / pooled if pooled > 0 else np.nan
        rows.append({"feature": c, "d_cohen": d,
                     "mean_rot": a.mean(), "mean_nao": b.mean()})
    top = (pd.DataFrame(rows).assign(absd=lambda x: x.d_cohen.abs())
           .sort_values("absd", ascending=False).head(12))
    lines += ["", "Maiores separações (d de Cohen):", "",
              "| feature | d | média rot. | média não |", "|---|---|---|---|"]
    lines += [f"| {r.feature} | {r.d_cohen:+.2f} | {r.mean_rot:+.3f} | "
              f"{r.mean_nao:+.3f} |" for r in top.itertuples()]

    # 'grade típica': alinhamento do dir de cada TF com a direção do rótulo
    lines += ["", "Alinhamento do `dir` de cada TF com a direção rotulada "
              "(dias rotulados):", "", "| TF | % alinhado | estado modal |",
              "|---|---|---|"]
    sgn = np.where(df.direction == "ALTA", 1.0, -1.0)
    for tf in ("M30", "H1", "H4", "D1", "W1"):
        m = df.labeled & df[f"{tf}_dir"].notna()
        align = (df.loc[m, f"{tf}_dir"] * sgn[m] > 0).mean()
        stm = df.loc[df.labeled, f"{tf}_state"].mode()
        stname = {0: "Ruído", 1: "Emergindo", 2: "Madura", 3: "Exausta",
                  -1: "aquecimento"}.get(int(stm.iloc[0]) if len(stm) else -1)
        lines.append(f"| {tf} | {100*align:.1f}% | {stname} |")
    lines.append("")


# ----------------------------------------------------------------------------
# B2 — regras candidatas (cada uma devolve ranking diário de (moeda, dir))
# ----------------------------------------------------------------------------

def _rank_by(df_day: pd.DataFrame, score: pd.Series, dir_col: str):
    """Ranking [(moeda, direção, score)] decrescente; NaN = abstenção."""
    s = score.copy()
    out = []
    for i in s.sort_values(ascending=False).index:
        if np.isnan(s[i]) or s[i] <= 0:
            continue
        d = df_day.loc[i, dir_col]
        if pd.isna(d) or d == 0:
            continue
        out.append((df_day.loc[i, "currency"], "ALTA" if d > 0 else "BAIXA",
                    float(s[i])))
    return out


def rule_absM(tf):
    def f(g):
        return _rank_by(g, g[f"{tf}_M"].abs(), f"{tf}_dir")
    return f


def rule_alignment(g):
    """Contagem de alinhamento D1/H4/H1 (desempate por soma de |M|)."""
    dirs = g[["D1_dir", "H4_dir", "H1_dir"]].to_numpy()
    msum = g[["D1_M", "H4_M", "H1_M"]].abs().sum(axis=1)
    maj = np.sign(np.nansum(dirs, axis=1))
    agree = (dirs == maj[:, None]).sum(axis=1)
    score = pd.Series(np.where(maj == 0, np.nan, agree + msum / 10), index=g.index)
    gg = g.copy(); gg["_maj"] = maj
    return _rank_by(gg, score, "_maj")


def rule_state_combo(g):
    """D1 Madura & H4 ∈ {Emergindo, Madura} & dirs iguais."""
    ok = ((g.D1_state == 2) & g.H4_state.isin([1, 2]) &
          (g.D1_dir * g.H4_dir > 0))
    score = pd.Series(np.where(ok, g.D1_M.abs() + g.H4_M.abs(), np.nan),
                      index=g.index)
    return _rank_by(g, score, "D1_dir")


def rule_macro_align(g):
    """W1 e D1 alinhados (macro-teto)."""
    ok = g.W1_dir * g.D1_dir > 0
    score = pd.Series(np.where(ok, g.W1_M.abs() + g.D1_M.abs(), np.nan),
                      index=g.index)
    return _rank_by(g, score, "D1_dir")


def rule_proto_A(g):
    """[APROX] Protocolo A: maturidade multi-TF (D1 e H4 Maduras, dir igual)."""
    ok = (g.D1_state == 2) & (g.H4_state == 2) & (g.D1_dir * g.H4_dir > 0)
    score = pd.Series(np.where(ok, g.H4_M.abs(), np.nan), index=g.index)
    return _rank_by(g, score, "D1_dir")


def rule_proto_B(g):
    """[APROX] Protocolo B: emergência H4/H1 alinhada ao D1."""
    emg = (g.H4_state == 1) | (g.H1_state == 1)
    ok = emg & (g.H4_dir * g.D1_dir > 0)
    score = pd.Series(np.where(ok, g.H4_M.abs() + g.H1_M.abs(), np.nan),
                      index=g.index)
    return _rank_by(g, score, "D1_dir")


def rule_proto_C(g):
    """[APROX] Protocolo C: H4 Exausta => aposta CONTRA a direção do H4."""
    ok = g.H4_state == 3
    score = pd.Series(np.where(ok, g.H4_M.abs(), np.nan), index=g.index)
    gg = g.copy(); gg["_anti"] = -g.H4_dir
    return _rank_by(gg, score, "_anti")


RULES = {
    "maior_|M|_H4": rule_absM("H4"),
    "maior_|M|_D1": rule_absM("D1"),
    "maior_|M|_M30": rule_absM("M30"),
    "alinhamento_D1_H4_H1": rule_alignment,
    "estado_D1xH4": rule_state_combo,
    "macro_W1_D1": rule_macro_align,
    "protoA_aprox": rule_proto_A,
    "protoB_aprox": rule_proto_B,
    "protoC_aprox": rule_proto_C,
}


def eval_predictions(preds: dict, truth: dict) -> dict:
    """preds: {day: [(cur, dir, score)...]}; truth: {day: {(cur, dir)}}."""
    top1, hit2, p2, n = 0, 0, 0.0, 0
    for day, ranking in preds.items():
        if not ranking:
            continue
        n += 1
        tset = truth.get(day, set())
        c1 = (ranking[0][0], ranking[0][1]) in tset
        top1 += c1
        two = ranking[:2]
        hits = sum((c, d) in tset for c, d, _ in two)
        hit2 += hits > 0
        p2 += hits / 2
    if n == 0:
        return {"n": 0, "top1": np.nan, "hit2": np.nan, "p2": np.nan}
    return {"n": n, "top1": top1 / n, "hit2": hit2 / n, "p2": p2 / n}


def b2_b3(df: pd.DataFrame, lines: list[str], n_perm: int = 200,
          perm_block: int = 5, seed: int = 0):
    days = sorted(df.day.unique())
    truth = {d: set() for d in days}
    for r in df[df.labeled].itertuples():
        truth[r.day].add((r.currency, r.direction))

    groups = {d: g for d, g in df.groupby("day")}
    all_preds = {name: {d: fn(groups[d]) for d in days}
                 for name, fn in RULES.items()}

    # ---- B3 baselines ----------------------------------------------------
    # (i) continuação: retorno D1 de ontem do índice sintético
    m5, d1 = load_closes(), load_d1_closes()
    idx_d1 = build_indices(d1, align="inner")
    dd = idx_d1.diff()          # variação diária do índice (log-espaço)
    cont_preds = {}
    for d in days:
        prev = dd[dd.index < d]
        if prev.empty:
            cont_preds[d] = []
            continue
        row = prev.iloc[-1]
        c = row.abs().idxmax()
        cont_preds[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA",
                          float(abs(row[c])))]
    # (ii) persistência: protagonista rotulada de ontem repete
    pers_preds = {}
    top_by_day = (df[df.labeled].sort_values("score", ascending=False)
                  .groupby("day").first())
    for i, d in enumerate(days):
        prevs = [x for x in days[:i] if x in top_by_day.index]
        if prevs:
            r = top_by_day.loc[prevs[-1]]
            pers_preds[d] = [(r.currency, r.direction, float(r.score))]
        else:
            pers_preds[d] = []
    # (iii) aleatório pareado: acurácia esperada analítica por dia
    rand_top1 = float(np.mean([len(truth[d]) / 16 for d in days]))

    base_evals = {"baseline_continuacao_D1": eval_predictions(cont_preds, truth),
                  "baseline_persistencia": eval_predictions(pers_preds, truth)}

    # ---- reality check: 200 permutações em bloco dos rótulos por dia -----
    rng = np.random.default_rng(seed)
    day_arr = np.array(days, dtype="datetime64[ns]")
    maxima = np.empty(n_perm)
    for k in range(n_perm):
        p = block_permute(len(days), perm_block, rng)
        # o dia i recebe o conjunto-verdade do dia p[i] (features intactas)
        truth_p = {days[i]: truth[pd.Timestamp(day_arr[p[i]])]
                   for i in range(len(days))}
        best = 0.0
        for name in RULES:
            ev = eval_predictions(all_preds[name], truth_p)
            if ev["n"] >= 100 and np.isfinite(ev["top1"]):
                best = max(best, ev["top1"])
        maxima[k] = best
    p95 = reality_check_p95(maxima)

    # ---- relatório --------------------------------------------------------
    lines += ["## B2/B3 — Regras candidatas vs baselines",
              "", f"Dias research: {len(days)} | acaso pareado (top-1 "
              f"esperado): **{100*rand_top1:.1f}%** | reality check p95 dos "
              f"máximos permutados (200 perm., blocos de {perm_block}): "
              f"**{100*p95:.1f}%**", "",
              "| regra | n dias c/ previsão | top-1 | hit@2 | precision@2 | "
              "bate 3 baselines? | > p95 perm.? |",
              "|---|---|---|---|---|---|---|"]
    b_cont = base_evals["baseline_continuacao_D1"]["top1"]
    b_pers = base_evals["baseline_persistencia"]["top1"]
    survivors = []
    for name in RULES:
        ev = eval_predictions(all_preds[name], truth)
        if ev["n"] == 0:
            lines.append(f"| {name} | 0 | — | — | — | — | — |")
            continue
        small = " (n<100!)" if ev["n"] < 100 else ""
        beats = (ev["top1"] > max(b_cont, b_pers, rand_top1))
        beyond = ev["top1"] > p95
        if beats and beyond and ev["n"] >= 100:
            survivors.append((name, ev))
        lines.append(f"| {name} | {ev['n']}{small} | {100*ev['top1']:.1f}% | "
                     f"{100*ev['hit2']:.1f}% | {100*ev['p2']:.1f}% | "
                     f"{'SIM' if beats else 'não'} | "
                     f"{'SIM' if beyond else 'não'} |")
    for name, ev in base_evals.items():
        lines.append(f"| {name} | {ev['n']} | {100*ev['top1']:.1f}% | "
                     f"{100*ev['hit2']:.1f}% | {100*ev['p2']:.1f}% | — | — |")
    lines += ["", "Cenários P_A/P_B/P_C são APROXIMAÇÕES (documento do "
              "Protocolo ausente do repositório).", ""]
    if survivors:
        lines.append("**Sobreviventes** (batem os 3 baselines E o reality "
                     "check): " + ", ".join(n for n, _ in survivors) + "\n")
    else:
        lines.append("**Nenhuma regra sobreviveu** aos baselines + reality "
                     "check — resultado nulo reportado (regra dura nº 7).\n")
    return survivors, base_evals, rand_top1


# ----------------------------------------------------------------------------
# B4 — teto com ML honesto
# ----------------------------------------------------------------------------

def b4_ml(df: pd.DataFrame, lines: list[str], gap: int = 5):
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    fcols = [c for c in df.columns if any(c.startswith(f"{tf}_")
             for tf in ("M30", "H1", "H4", "D1", "W1"))]
    days = np.array(sorted(df.day.unique()))
    day_pos = {d: i for i, d in enumerate(days)}
    dpos = df.day.map(day_pos).to_numpy()

    X = df[fcols].to_numpy(dtype=float)
    y = df.labeled.to_numpy(dtype=int)

    results = {}
    for mname, mk in [("logistic", lambda: LogisticRegression(
                          max_iter=2000, class_weight="balanced")),
                      ("gboost_raso", lambda: GradientBoostingClassifier(
                          max_depth=2, n_estimators=200, learning_rate=0.05,
                          subsample=0.8, random_state=0))]:
        aucs, imps = [], []
        for tr_d, te_d in purged_cv_splits(len(days), n_folds=5, gap=gap):
            tr = np.isin(dpos, tr_d); te = np.isin(dpos, te_d)
            med = np.nanmedian(X[tr], axis=0)
            Xtr = np.where(np.isnan(X[tr]), med, X[tr])
            Xte = np.where(np.isnan(X[te]), med, X[te])
            sc = StandardScaler().fit(Xtr)
            m = mk().fit(sc.transform(Xtr), y[tr])
            prob = m.predict_proba(sc.transform(Xte))[:, 1]
            if len(np.unique(y[te])) == 2:
                aucs.append(roc_auc_score(y[te], prob))
            imps.append(np.abs(m.coef_[0]) if mname == "logistic"
                        else m.feature_importances_)
        imp = np.mean(imps, axis=0)
        top = sorted(zip(fcols, imp), key=lambda x: -x[1])[:8]
        results[mname] = (float(np.mean(aucs)), float(np.std(aucs)), top)

    lines += ["## B4 — Teto com ML honesto (alvo: rotula?)",
              f"Purged CV 5 folds, gap {gap} dias; imputação por mediana do "
              "treino; AUC média ± dp entre folds.", ""]
    for mname, (mu, sd, top) in results.items():
        lines += [f"### {mname}: AUC = **{mu:.3f} ± {sd:.3f}**",
                  "Top features: " + ", ".join(f"{f} ({v:.3f})"
                                               for f, v in top), ""]

    # alvo secundário: direção (entre rotulados)
    sub = df[df.labeled]
    Xd = sub[fcols].to_numpy(dtype=float)
    yd = (sub.direction == "ALTA").astype(int).to_numpy()
    dsub = sub.day.map(day_pos).to_numpy()
    aucs = []
    for tr_d, te_d in purged_cv_splits(len(days), n_folds=5, gap=gap):
        tr = np.isin(dsub, tr_d); te = np.isin(dsub, te_d)
        if tr.sum() < 50 or te.sum() < 20 or len(np.unique(yd[te])) < 2:
            continue
        med = np.nanmedian(Xd[tr], axis=0)
        Xtr = np.where(np.isnan(Xd[tr]), med, Xd[tr])
        Xte = np.where(np.isnan(Xd[te]), med, Xd[te])
        sc = StandardScaler().fit(Xtr)
        m = LogisticRegression(max_iter=2000).fit(sc.transform(Xtr), yd[tr])
        aucs.append(roc_auc_score(yd[te], m.predict_proba(
            sc.transform(Xte))[:, 1]))
    if aucs:
        lines += [f"### direção (logistic, só rotulados): AUC = "
                  f"**{np.mean(aucs):.3f} ± {np.std(aucs):.3f}** "
                  f"({len(aucs)} folds válidos)", ""]
    return results


# ----------------------------------------------------------------------------

def main():
    df = load_research()
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_reverse")
    out.mkdir(parents=True, exist_ok=True)

    lines = ["# A5 — Engenharia reversa em T0 (dias research)", ""]
    b1_contrast(df, lines)
    survivors, base_evals, rand_top1 = b2_b3(df, lines)
    ml = b4_ml(df, lines)

    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "params.json").write_text(json.dumps({
        "n_perm": 200, "perm_block": 5, "cv_gap": 5,
        "survivors": [s for s, _ in survivors],
        "baseline_top1": {k: v["top1"] for k, v in base_evals.items()},
        "random_top1": rand_top1,
        "ml_auc": {k: v[0] for k, v in ml.items()}}, indent=2))
    print(f"OK -> {out}/REPORT.md | sobreviventes: "
          f"{[s for s, _ in survivors] or 'NENHUM'}")


if __name__ == "__main__":
    main()

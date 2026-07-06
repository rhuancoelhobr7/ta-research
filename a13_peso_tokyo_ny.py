# -*- coding: utf-8 -*-
"""a13_peso_tokyo_ny.py — "Peso" (derivada da geometria do CSS) em T0 prevê
o retorno da cesta na janela Tokyo→NY?

MOTIVAÇÃO (3 posts públicos do especialista, 2026-07, CHF/GBP/NZD): a leitura
dele não é a POSIÇÃO da linha (a12, nulo) e sim a VARIAÇÃO DE INTENSIDADE —
"fraqueza reduzida", "combustível no fim", "perde o fôlego", "força bruta",
"região de retomada". Além disso a decisão é hierárquica (veto de TF maior
"sem peso" → comando passa ao TF menor) e a janela operacional declarada é
"abre em Tokyo, fecha antes de NY", sem gain/stop — alvo distinto do rótulo v1.

O RÓTULO v1 NÃO É TOCADO (regra dura 1): este estudo usa um ALVO NOVO e
pré-registrado, não redefine o rótulo. Holdout intocado (regra dura 2).

HIPÓTESES PRÉ-REGISTRADAS (antes de qualquer contato com os dados):

Alvo: y(D, C) = variação do índice sintético da moeda C em
  [T0, T0+15h) — 00:00→15:00 servidor = 17:00→08:00 NY (Tokyo → pré-NY).
  Primário: sinal de y em 15h. Sensibilidade (secundária): 12h.

Features novas por TF (derivadas de css_geometry, k = K_SLOPE barras):
  dpeso    = |val|_t − |val|_{t−k}   (intensidade subindo/caindo)
  conv     = fora_box E dpeso < 0    ("fora mas esvaziando" = sem peso)
  retomada = |val| ≤ box E dpeso > 0 E dline·sign(val) > 0 (re-expansão)

Regras (árvore de veto dos 3 posts; macro = MN se disponível, senão W1):
  RA_exaustao_contra (post CHF): macro fora da box E convergindo (dpeso<0)
      E D1 não bloqueia (D1 não está fora da box E abrindo no MESMO sinal
      do macro) → dir = −sign(val_macro). score = |dpeso_macro|.
  RB_transferencia_H4 (post GBP): MN, W1 e D1 todos "sem peso" (conv OU
      dentro da box) E H4 fora da box E abrindo (dpeso>0) →
      dir = sign(val_H4). score = dpeso_H4.
  RC_amparo_D1 (post NZD): macro fora da box a favor de s=sign(val_macro)
      E D1 fora da box com sinal −s E abrindo (dpeso_D1>0) E
      sign(val_H1) = −s → dir = −s (segue o D1). score = dpeso_D1.

CRITÉRIO DE SUCESSO (idêntico ao a5/a10/a12): uma regra só sobrevive se a
acurácia top-1 no SINAL do alvo > 3 baselines (continuação-D1, persistência
do próprio alvo, acaso pareado 50%) E > p95 dos máximos de 200 permutações
em bloco do alvo entre dias. n < 100 predições = amostra insuficiente
(regra dura 6). Dias research apenas. Universo primário usd7; all28 como
sensibilidade. Tudo fora do acima é EXPLORATÓRIO e será rotulado como tal.

Anti-lookahead: features em T0 usam só barras FECHADAS antes de T0 (cutoffs
do a12, testados); o alvo usa só [T0, T0+15h). Testes em tests/test_a13.py.

Uso: python a13_peso_tokyo_ny.py [--pares {usd7,all28}] [--target-hours 15]
     [--build-only]
Saída: data/features/css_peso_t0*.parquet + results/{ts}_a13/REPORT.md
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a1_label_days import load_closes, window_diff
from a12_css_geometry import PARES_USD, TFS, _cutoff, _grids
from a5_reverse import _rank_by
from css_classic import G8, css_geometry, css_lines
from cssm_engine import build_indices
from splits_days import research_days
from stats_blocks import block_permute, purged_cv_splits, reality_check_p95

BOX, PER, SUAV, KSLOPE = 0.2, 14, 3, 3          # mesmos do a12 (fiéis ao CSS)
TARGET_HOURS = 15.0                              # T0 → pré-NY (08:00 NY)
FEATS13 = ["val", "fora_box", "dist_box", "dline", "dpeso", "conv", "retomada"]
FEAT_PATH = pathlib.Path("data/features/css_peso_t0.parquet")


# ----------------------------------------------------------------------------
# Features de "peso" (derivada da geometria)
# ----------------------------------------------------------------------------

def peso_features(lines: pd.DataFrame, box: float = BOX,
                  k: int = KSLOPE) -> dict[str, pd.DataFrame]:
    """Geometria do a12 + derivadas de intensidade (só passado: shift(k))."""
    g = css_geometry(lines, box=box, k_slope=k)
    aval = lines.abs()
    dpeso = aval - aval.shift(k)
    g["dpeso"] = dpeso
    g["conv"] = ((g["fora_box"] == 1.0) & (dpeso < 0)).astype(float)
    g["retomada"] = ((aval <= box) & (dpeso > 0) &
                     (g["dline"] * np.sign(lines) > 0)).astype(float)
    return g


def build_matrix(pares: list[str]) -> pd.DataFrame:
    """Matriz (dia, moeda) x {TF}_{feature} em T0 (mesmo recorte do a12)."""
    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    days = pd.DatetimeIndex(sorted(lab.day.unique()))
    grids = _grids(pares)

    per_tf: dict[str, dict[str, pd.DataFrame]] = {}
    for tf, closes in grids.items():
        lines = css_lines(closes, per=PER, suav=SUAV, box=BOX)
        per_tf[tf] = peso_features(lines, box=BOX, k=KSLOPE)

    rows = []
    for day in days:
        snap = {}
        for tf in TFS:
            idx = per_tf[tf]["val"].index
            pos = idx.searchsorted(_cutoff(tf, day), side="right") - 1
            snap[tf] = None if pos < 0 else pos
        for cur in G8:
            rec = {"day": day, "currency": cur}
            for tf in TFS:
                pos = snap[tf]
                for feat in FEATS13:
                    rec[f"{tf}_{feat}"] = (np.nan if pos is None
                                           else per_tf[tf][feat][cur].iloc[pos])
            rows.append(rec)
    return pd.DataFrame(rows)


def build_target(hours: float = TARGET_HOURS) -> pd.DataFrame:
    """Alvo: Δ índice sintético por (dia, moeda) em [T0, T0+hours)."""
    closes = load_closes()
    indices = build_indices(closes, align="inner")
    days = pd.DatetimeIndex(sorted(set(indices.index.normalize())))
    rows = []
    for day in days:
        # [T0, T0+hours): a barra carimbada em T0+hours já é NY — não entra.
        t0 = day
        t1 = day + pd.Timedelta(hours=hours) - pd.Timedelta(seconds=1)
        w = indices.loc[t0:t1]
        if len(w) < 8:                       # fds/feriado
            continue
        for c in G8:
            rows.append({"day": day, "currency": c,
                         "y": window_diff(indices[c], t0, t1)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Regras pré-registradas (árvore de veto; macro = MN, senão W1)
# ----------------------------------------------------------------------------

def _macro(g: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series]:
    """(val, fora_box, dpeso) do tier macro: MN se disponível, senão W1."""
    use_mn = g["MN_val"].notna()
    val = g["MN_val"].where(use_mn, g["W1_val"])
    fora = g["MN_fora_box"].where(use_mn, g["W1_fora_box"])
    dpeso = g["MN_dpeso"].where(use_mn, g["W1_dpeso"])
    return val, fora, dpeso


def rule_RA_exaustao_contra(g: pd.DataFrame):
    """Macro fora da box esvaziando, D1 não bloqueia → operar CONTRA."""
    mval, mfora, mdp = _macro(g)
    s = np.sign(mval)
    d1_bloqueia = (g["D1_fora_box"] == 1.0) & (g["D1_dpeso"] > 0) & \
                  (np.sign(g["D1_val"]) == s)
    elig = (mfora == 1.0) & (mdp < 0) & ~d1_bloqueia
    score = mdp.abs().where(elig)
    return _rank_by(g.assign(_dir=-s), score, "_dir")


def rule_RB_transferencia_H4(g: pd.DataFrame):
    """MN/W1/D1 sem peso E H4 fora da box abrindo → seguir o H4."""
    sem_peso = pd.Series(True, index=g.index)
    for tf in ("MN", "W1", "D1"):
        tf_sem = (g[f"{tf}_conv"] == 1.0) | (g[f"{tf}_fora_box"] == 0.0)
        sem_peso &= tf_sem | g[f"{tf}_val"].isna()   # TF ausente não veta
    h4_manda = (g["H4_fora_box"] == 1.0) & (g["H4_dpeso"] > 0)
    elig = sem_peso & h4_manda
    score = g["H4_dpeso"].where(elig)
    return _rank_by(g.assign(_dir=np.sign(g["H4_val"])), score, "_dir")


def rule_RC_amparo_D1(g: pd.DataFrame):
    """Macro a favor de s, D1 fora da box contra s e abrindo, H1 confirma
    → seguir o D1 (contra o macro)."""
    mval, mfora, _ = _macro(g)
    s = np.sign(mval)
    d1_contra = (g["D1_fora_box"] == 1.0) & (np.sign(g["D1_val"]) == -s) & \
                (g["D1_dpeso"] > 0)
    h1_conf = np.sign(g["H1_val"]) == -s
    elig = (mfora == 1.0) & (s != 0) & d1_contra & h1_conf
    score = g["D1_dpeso"].where(elig)
    return _rank_by(g.assign(_dir=-s), score, "_dir")


RULES = {"RA_exaustao_contra": rule_RA_exaustao_contra,
         "RB_transferencia_H4": rule_RB_transferencia_H4,
         "RC_amparo_D1": rule_RC_amparo_D1}


# ----------------------------------------------------------------------------
# Avaliação: acurácia top-1 no SINAL do alvo, baselines, reality check
# ----------------------------------------------------------------------------

def eval_sign(preds: dict, y: pd.DataFrame) -> dict:
    """preds: {day: [(cur, 'ALTA'/'BAIXA', score), ...]}; y: day x currency."""
    hits = n = 0
    for day, plist in preds.items():
        if not plist:
            continue
        cur, dirs, _ = plist[0]
        yv = y.at[day, cur] if (day in y.index and cur in y.columns) else np.nan
        if np.isnan(yv) or yv == 0:
            continue
        n += 1
        hits += int((yv > 0) == (dirs == "ALTA"))
    return {"n": n, "top1": hits / n if n else np.nan}


def evaluate(df: pd.DataFrame, ymat: pd.DataFrame, lines: list[str],
             n_perm: int = 200, perm_block: int = 5, seed: int = 0):
    days = sorted(df.day.unique())
    groups = {d: g.reset_index(drop=True) for d, g in df.groupby("day")}
    all_preds = {name: {d: fn(groups[d]) for d in days}
                 for name, fn in RULES.items()}

    # baseline 1 — continuação-D1: maior |Δ índice D1 de ontem|, mesmo sinal
    from a4_features_t0 import load_d1_closes
    d1 = pd.DataFrame(load_d1_closes()).ffill()
    dd = build_indices(d1, align="inner").diff()
    cont = {}
    for d in days:
        prev = dd[dd.index < d]
        if prev.empty:
            cont[d] = []; continue
        row = prev.iloc[-1]
        c = row.abs().idxmax()
        cont[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA", float(abs(row[c])))]
    # baseline 2 — persistência do próprio alvo: repete o maior |y| de ontem
    pers = {}
    for i, d in enumerate(days):
        prevs = [x for x in days[:i] if x in ymat.index]
        if not prevs:
            pers[d] = []; continue
        row = ymat.loc[prevs[-1]].dropna()
        if row.empty:
            pers[d] = []; continue
        c = row.abs().idxmax()
        pers[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA", float(abs(row[c])))]
    base = {"baseline_continuacao_D1": eval_sign(cont, ymat),
            "baseline_persistencia_y": eval_sign(pers, ymat)}
    rand_top1 = 0.5                              # direção aleatória pareada

    # reality check: permuta o ALVO entre dias (em blocos), max das 3 regras
    rng = np.random.default_rng(seed)
    yr = ymat.reindex(days)
    maxima = np.empty(n_perm)
    for kk in range(n_perm):
        p = block_permute(len(days), perm_block, rng)
        yp = pd.DataFrame(yr.to_numpy()[p], index=days, columns=yr.columns)
        best = 0.0
        for name in RULES:
            ev = eval_sign(all_preds[name], yp)
            if ev["n"] >= 100 and np.isfinite(ev["top1"]):
                best = max(best, ev["top1"])
        maxima[kk] = best
    p95 = reality_check_p95(maxima)

    b = max(base["baseline_continuacao_D1"]["top1"] or 0,
            base["baseline_persistencia_y"]["top1"] or 0, rand_top1)
    lines += ["## Regras pré-registradas vs baselines (sinal do alvo, research)",
              "", f"Dias: {len(days)} | acaso pareado: **50.0%** | "
              f"reality check p95: **{100*p95:.1f}%**", "",
              "| regra | n | top-1 | bate baselines? | > p95? |",
              "|---|---|---|---|---|"]
    survivors = []
    for name in RULES:
        ev = eval_sign(all_preds[name], ymat)
        if ev["n"] == 0:
            lines.append(f"| {name} | 0 | — | — | — |"); continue
        small = " (n<100!)" if ev["n"] < 100 else ""
        beats, beyond = ev["top1"] > b, ev["top1"] > p95
        if beats and beyond and ev["n"] >= 100:
            survivors.append(name)
        lines.append(f"| {name} | {ev['n']}{small} | {100*ev['top1']:.1f}% | "
                     f"{'SIM' if beats else 'não'} | "
                     f"{'SIM' if beyond else 'não'} |")
    for name, ev in base.items():
        t = f"{100*ev['top1']:.1f}%" if np.isfinite(ev["top1"]) else "—"
        lines.append(f"| {name} | {ev['n']} | {t} | — | — |")
    lines.append("")
    lines.append(f"**Sobreviventes:** {', '.join(survivors)}\n" if survivors
                 else "**Nenhuma regra sobreviveu** — nulo reportado "
                      "(regra dura nº 7).\n")
    return survivors


def ml_ceiling(df: pd.DataFrame, ymat: pd.DataFrame, lines: list[str],
               gap: int = 5):
    """Teto de ML (purged CV): features de peso → sinal do alvo."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    fcols = [f"{tf}_{f}" for tf in TFS for f in FEATS13]
    d = df.copy()
    d["y"] = [ymat.at[r.day, r.currency]
              if (r.day in ymat.index and r.currency in ymat.columns)
              else np.nan for r in d.itertuples()]
    d = d.dropna(subset=fcols + ["y"]).reset_index(drop=True)
    d = d[d.y != 0]
    days = np.array(sorted(d.day.unique()))
    X, y = d[fcols].to_numpy(), (d.y > 0).to_numpy()
    aucs = {"logistic": [], "gboost": []}
    for tr_i, te_i in purged_cv_splits(len(days), 5, gap):
        tr = d.day.isin(set(days[tr_i])).to_numpy()
        te = d.day.isin(set(days[te_i])).to_numpy()
        if y[tr].sum() < 10 or y[te].sum() < 10:
            continue
        sc = StandardScaler().fit(X[tr])
        lo = LogisticRegression(max_iter=1000).fit(sc.transform(X[tr]), y[tr])
        gb = GradientBoostingClassifier(max_depth=2, n_estimators=100,
                                        random_state=0).fit(X[tr], y[tr])
        aucs["logistic"].append(roc_auc_score(
            y[te], lo.predict_proba(sc.transform(X[te]))[:, 1]))
        aucs["gboost"].append(roc_auc_score(
            y[te], gb.predict_proba(X[te])[:, 1]))
    lines += ["## Teto de ML (purged CV, gap 5 dias) — alvo: sinal Tokyo→NY", ""]
    for k, v in aucs.items():
        lines.append(f"- {k}: AUC **{np.mean(v):.3f}** ± {np.std(v):.3f} "
                     f"({len(v)} folds)")
    lines.append("")


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", choices=["usd7", "all28"], default="usd7")
    ap.add_argument("--target-hours", type=float, default=TARGET_HOURS)
    ap.add_argument("--build-only", action="store_true")
    a = ap.parse_args()
    secundario = a.target_hours != TARGET_HOURS
    pares = PARES_USD if a.pares == "usd7" else sorted(
        pd.DataFrame(load_closes()).columns)

    t0 = time.time()
    feat = build_matrix(pares)
    FEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    suffix = "" if a.pares == "usd7" else "_all28"
    path = FEAT_PATH.with_name(FEAT_PATH.stem + suffix + ".parquet")
    feat.to_parquet(path)
    print(f"matriz {feat.shape} -> {path} ({time.time()-t0:.0f}s)")
    if a.build_only:
        return

    ydf = build_target(a.target_hours)
    ymat = ydf.pivot(index="day", columns="currency", values="y")
    train, valid = research_days(pd.DatetimeIndex(feat.day.unique()))
    keep = set(train) | set(valid)
    df = feat[feat.day.isin(keep)].sort_values(
        ["day", "currency"]).reset_index(drop=True)
    ymat = ymat[ymat.index.isin(keep)]

    lines = [f"# a13 — Peso (derivada do CSS) em T0 → sinal Tokyo→NY "
             f"(pares: {a.pares}, janela: {a.target_hours:.0f}h"
             f"{' — SENSIBILIDADE' if secundario else ''})", "",
             f"Matriz: {feat.shape[0]} linhas | dias research: {len(keep)} | "
             f"params: per={PER} suav={SUAV} box={BOX} k={KSLOPE}", "",
             "Hipóteses e critérios PRÉ-REGISTRADOS no CHANGELOG (2026-07-06) "
             "e no cabeçalho deste script, ANTES da primeira execução. "
             "Rótulo v1 e holdout intocados.", ""]
    survivors = evaluate(df, ymat, lines)
    ml_ceiling(df, ymat, lines)

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a13")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"pares": a.pares, "target_hours": a.target_hours, "per": PER,
         "suav": SUAV, "box": BOX, "k_slope": KSLOPE, "tfs": TFS,
         "n_dias_research": len(keep), "secundario": secundario}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md | sobreviventes: {survivors or 'nenhuma'}")


if __name__ == "__main__":
    main()

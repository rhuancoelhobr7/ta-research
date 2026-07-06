# -*- coding: utf-8 -*-
"""a12_css_geometry.py — Geometria literal do CSS clássico em T0 prevê o rótulo?

HIPÓTESE (pré-registrada no CHANGELOG 2026-07-06, ANTES de contato com dados):
o "score de inflação/deflação" do especialista seria a GEOMETRIA das linhas
do CSS clássico (TMA-slope normalizado por barra) lida em MN/W1/D1/H4/H1:
dentro/fora da box ±0.2, linha ascendente/descendente (dline), proximidade
do zero. Regras pré-registradas:

  R1 exaustão-macro : linha D1 fora da box com dline CONTRA o sinal da linha
                      ("combustível no fim") → operar CONTRA o macro;
                      score = |dline_D1| entre as moedas elegíveis.
  R2 cascata        : dline_D1 define a direção s; H4 e H1 confirmam
                      (sinal da linha = s) → seguir s; score = |dline_D1|.
  R3 peso-relativo  : seguir a moeda com mais TFs "fora da box E abrindo"
                      (dline a favor), ponderados por |val|; direção = sinal
                      da linha nos TFs que pontuaram.

CRITÉRIO DE SUCESSO (idêntico ao a5/a10, pré-registrado): uma regra só
sobrevive se top-1 > 3 baselines (continuação-D1, persistência, acaso
pareado) E > p95 dos máximos de 200 permutações em bloco. Dias research
apenas (treino+validação); holdout intocado. Universo primário do CSS =
7 pares USD (fiel ao CurrencySlopeStrength.mq5 do usuário); sensibilidade
com 28 pares reportada como secundária. Tudo fora disso é EXPLORATÓRIO.

Anti-lookahead: features em T0 usam só barras FECHADAS antes de T0
(intraday: carimbo <= T0 - duração do TF; D1: carimbo < dia; W1/MN:
período encerrado antes do dia). Testes em tests/test_a12.py.

Uso: python a12_css_geometry.py [--pares {usd7,all28}] [--build-only]
Saída: data/features/css_geometry_t0.parquet + results/{ts}_a12/REPORT.md
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a1_label_days import load_closes
from a4_features_t0 import load_d1_closes
from a5_reverse import _rank_by, eval_predictions
from css_classic import G8, css_geometry, css_lines
from splits_days import research_days
from stats_blocks import block_permute, purged_cv_splits, reality_check_p95

PARES_USD = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
TFS = ["MN", "W1", "D1", "H4", "H1"]
GEOFEATS = ["val", "fora_box", "dist_box", "dline", "dist_zero"]
BOX, PER, SUAV, KSLOPE = 0.2, 14, 3, 3
FEAT_PATH = pathlib.Path("data/features/css_geometry_t0.parquet")


# ----------------------------------------------------------------------------
# Construção da matriz (dia x moeda) de geometria em T0
# ----------------------------------------------------------------------------

def _grids(pares: list[str]) -> dict[str, pd.DataFrame]:
    """Grades de close por TF a partir do bruto (M5 p/ intraday, D1 p/ macro)."""
    m5 = pd.DataFrame(load_closes()).ffill()
    d1 = pd.DataFrame(load_d1_closes()).ffill()
    cols = [c for c in pares if c in m5.columns]
    m5, d1 = m5[cols], d1[[c for c in cols if c in d1.columns]]
    return {
        "H1": m5.resample("1h").last().dropna(how="all"),
        "H4": m5.resample("4h").last().dropna(how="all"),
        "D1": d1,
        "W1": d1.resample("W-FRI").last().dropna(how="all"),
        "MN": d1.resample("ME").last().dropna(how="all"),
    }


def _cutoff(tf: str, day: pd.Timestamp) -> pd.Timestamp:
    """Último carimbo cujo BAR está fechado antes de T0 = day 00:00 (servidor).

    Intraday (carimbo = abertura): fechado sse carimbo + dur <= T0.
    D1 (carimbo = dia): a barra de ontem fecha em T0 → carimbo <= day - 1d.
    W1 (carimbo = sexta, dados até sexta 23:55): fechado sse carimbo < day.
    MN (carimbo = fim do mês): idem, carimbo < day.
    """
    if tf == "H1":
        return day - pd.Timedelta(hours=1)
    if tf == "H4":
        return day - pd.Timedelta(hours=4)
    if tf == "D1":
        return day - pd.Timedelta(days=1)
    return day - pd.Timedelta(seconds=1)          # W1/MN: estritamente < day


def build_matrix(pares: list[str]) -> pd.DataFrame:
    """Matriz (dia, moeda) x {TF}_{feature} da geometria do CSS em T0."""
    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    days = pd.DatetimeIndex(sorted(lab.day.unique()))
    grids = _grids(pares)

    per_tf: dict[str, dict[str, pd.DataFrame]] = {}
    for tf, closes in grids.items():
        lines = css_lines(closes, per=PER, suav=SUAV, box=BOX)
        per_tf[tf] = css_geometry(lines, box=BOX, k_slope=KSLOPE)

    rows = []
    for day in days:
        rec_base = {"day": day}
        snap = {}
        for tf in TFS:
            cut = _cutoff(tf, day)
            g = per_tf[tf]
            idx = g["val"].index
            pos = idx.searchsorted(cut, side="right") - 1
            snap[tf] = None if pos < 0 else pos
        for cur in G8:
            rec = dict(rec_base, currency=cur)
            for tf in TFS:
                pos = snap[tf]
                for feat in GEOFEATS:
                    v = (np.nan if pos is None
                         else per_tf[tf][feat][cur].iloc[pos])
                    rec[f"{tf}_{feat}"] = v
            rows.append(rec)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Regras pré-registradas (ranking diário de (moeda, direção))
# ----------------------------------------------------------------------------

def rule_R1_exaustao_macro(g: pd.DataFrame):
    """Fora da box no D1 com linha esvaziando → operar CONTRA o macro."""
    elig = (g["D1_fora_box"] == 1.0) & (g["D1_dline"] * g["D1_val"] < 0)
    score = g["D1_dline"].abs().where(elig)
    d = -np.sign(g["D1_val"])                      # contra o macro
    gg = g.assign(_dir=d)
    return _rank_by(gg, score, "_dir")


def rule_R2_cascata(g: pd.DataFrame):
    """dline_D1 dá a direção; H4 e H1 confirmam (sinal da linha) → seguir."""
    s = np.sign(g["D1_dline"])
    conf = (np.sign(g["H4_val"]) == s) & (np.sign(g["H1_val"]) == s) & (s != 0)
    score = g["D1_dline"].abs().where(conf)
    gg = g.assign(_dir=s)
    return _rank_by(gg, score, "_dir")


def rule_R3_peso_relativo(g: pd.DataFrame):
    """Mais TFs 'fora da box E abrindo', ponderados por |val|; segue a linha."""
    score = pd.Series(0.0, index=g.index)
    vote = pd.Series(0.0, index=g.index)
    for tf in TFS:
        aberto = (g[f"{tf}_fora_box"] == 1.0) & \
                 (g[f"{tf}_dline"] * g[f"{tf}_val"] > 0)
        w = g[f"{tf}_val"].abs().where(aberto, 0.0).fillna(0.0)
        score = score + w
        vote = vote + np.sign(g[f"{tf}_val"]).where(aberto, 0.0).fillna(0.0) * w
    d = np.sign(vote)
    gg = g.assign(_dir=d)
    return _rank_by(gg, score.where(score > 0), "_dir")


RULES = {"R1_exaustao_macro": rule_R1_exaustao_macro,
         "R2_cascata": rule_R2_cascata,
         "R3_peso_relativo": rule_R3_peso_relativo}


# ----------------------------------------------------------------------------
# Avaliação (aparato do a5: baselines + reality check, dias research)
# ----------------------------------------------------------------------------

def evaluate(df: pd.DataFrame, lines: list[str], n_perm: int = 200,
             perm_block: int = 5, seed: int = 0):
    days = sorted(df.day.unique())
    truth = {d: set() for d in days}
    for r in df[df.labeled].itertuples():
        truth[r.day].add((r.currency, r.direction))
    groups = {d: g.reset_index(drop=True) for d, g in df.groupby("day")}
    all_preds = {name: {d: fn(groups[d]) for d in days}
                 for name, fn in RULES.items()}

    # baselines (mesma definição do a5)
    from cssm_engine import build_indices
    d1 = pd.DataFrame(load_d1_closes()).ffill()
    idx_d1 = build_indices(d1, align="inner")
    dd = idx_d1.diff()
    cont_preds = {}
    for d in days:
        prev = dd[dd.index < d]
        if prev.empty:
            cont_preds[d] = []
            continue
        row = prev.iloc[-1]
        c = row.abs().idxmax()
        cont_preds[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA", float(abs(row[c])))]
    pers_preds = {}
    top_by_day = (df[df.labeled].sort_values("score", ascending=False)
                  .groupby("day").first())
    for i, d in enumerate(days):
        prevs = [x for x in days[:i] if x in top_by_day.index]
        pers_preds[d] = ([(top_by_day.loc[prevs[-1]].currency,
                           top_by_day.loc[prevs[-1]].direction,
                           float(top_by_day.loc[prevs[-1]].score))]
                         if prevs else [])
    rand_top1 = float(np.mean([len(truth[d]) / 16 for d in days]))
    base_evals = {"baseline_continuacao_D1": eval_predictions(cont_preds, truth),
                  "baseline_persistencia": eval_predictions(pers_preds, truth)}

    # reality check
    rng = np.random.default_rng(seed)
    day_arr = np.array(days, dtype="datetime64[ns]")
    maxima = np.empty(n_perm)
    for k in range(n_perm):
        p = block_permute(len(days), perm_block, rng)
        truth_p = {days[i]: truth[pd.Timestamp(day_arr[p[i]])]
                   for i in range(len(days))}
        best = 0.0
        for name in RULES:
            ev = eval_predictions(all_preds[name], truth_p)
            if ev["n"] >= 100 and np.isfinite(ev["top1"]):
                best = max(best, ev["top1"])
        maxima[k] = best
    p95 = reality_check_p95(maxima)

    b_cont = base_evals["baseline_continuacao_D1"]["top1"]
    b_pers = base_evals["baseline_persistencia"]["top1"]
    lines += ["## Regras pré-registradas vs baselines (dias research)", "",
              f"Dias: {len(days)} | acaso pareado: **{100*rand_top1:.1f}%** | "
              f"reality check p95: **{100*p95:.1f}%**", "",
              "| regra | n | top-1 | hit@2 | precision@2 | bate baselines? | > p95? |",
              "|---|---|---|---|---|---|---|"]
    survivors = []
    for name in RULES:
        ev = eval_predictions(all_preds[name], truth)
        if ev["n"] == 0:
            lines.append(f"| {name} | 0 | — | — | — | — | — |")
            continue
        small = " (n<100!)" if ev["n"] < 100 else ""
        beats = ev["top1"] > max(b_cont, b_pers, rand_top1)
        beyond = ev["top1"] > p95
        if beats and beyond and ev["n"] >= 100:
            survivors.append(name)
        lines.append(f"| {name} | {ev['n']}{small} | {100*ev['top1']:.1f}% | "
                     f"{100*ev['hit2']:.1f}% | {100*ev['p2']:.1f}% | "
                     f"{'SIM' if beats else 'não'} | {'SIM' if beyond else 'não'} |")
    for name, ev in base_evals.items():
        lines.append(f"| {name} | {ev['n']} | {100*ev['top1']:.1f}% | "
                     f"{100*ev['hit2']:.1f}% | {100*ev['p2']:.1f}% | — | — |")
    lines.append("")
    if survivors:
        lines.append(f"**Sobreviventes:** {', '.join(survivors)}\n")
    else:
        lines.append("**Nenhuma regra sobreviveu** — nulo reportado "
                     "(regra dura nº 7).\n")
    return survivors


def contrast(df: pd.DataFrame, lines: list[str]):
    """B1: d de Cohen das features geométricas, rotulado vs não."""
    lines.append("## Contraste descritivo (rotulado vs não)")
    rows = []
    for tf in TFS:
        for feat in GEOFEATS:
            c = f"{tf}_{feat}"
            a = df.loc[df.labeled, c].dropna()
            b = df.loc[~df.labeled, c].dropna()
            if len(a) < 30 or len(b) < 30:
                continue
            pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
            d = (a.mean() - b.mean()) / pooled if pooled > 0 else np.nan
            rows.append({"feature": c, "d": d})
    top = (pd.DataFrame(rows).assign(absd=lambda x: x.d.abs())
           .sort_values("absd", ascending=False).head(10))
    lines += ["", "| feature | d de Cohen |", "|---|---|"]
    lines += [f"| {r.feature} | {r.d:+.2f} |" for r in top.itertuples()]
    lines.append("")


def ml_ceiling(df: pd.DataFrame, lines: list[str], gap: int = 5):
    """Teto de ML (purged CV) sobre as features geométricas: prevê 'rotula?'."""
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    fcols = [f"{tf}_{f}" for tf in TFS for f in GEOFEATS]
    d = df.dropna(subset=fcols).reset_index(drop=True)
    days = np.array(sorted(d.day.unique()))
    X, y = d[fcols].to_numpy(), d.labeled.to_numpy()
    aucs = {"logistic": [], "gboost": []}
    for tr_i, te_i in purged_cv_splits(len(days), 5, gap):
        tr_d, te_d = set(days[tr_i]), set(days[te_i])
        tr = d.day.isin(tr_d).to_numpy()
        te = d.day.isin(te_d).to_numpy()
        if y[tr].sum() < 10 or y[te].sum() < 10:
            continue
        sc = StandardScaler().fit(X[tr])
        lo = LogisticRegression(max_iter=1000).fit(sc.transform(X[tr]), y[tr])
        gb = GradientBoostingClassifier(max_depth=2, n_estimators=100,
                                        random_state=0).fit(X[tr], y[tr])
        aucs["logistic"].append(roc_auc_score(y[te], lo.predict_proba(
            sc.transform(X[te]))[:, 1]))
        aucs["gboost"].append(roc_auc_score(y[te], gb.predict_proba(X[te])[:, 1]))
    lines += ["## Teto de ML (purged CV, gap 5 dias) — alvo: rotula?", ""]
    for k, v in aucs.items():
        lines.append(f"- {k}: AUC **{np.mean(v):.3f}** ± {np.std(v):.3f} "
                     f"({len(v)} folds)")
    lines.append("")


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", choices=["usd7", "all28"], default="usd7")
    ap.add_argument("--build-only", action="store_true")
    a = ap.parse_args()

    pares = PARES_USD if a.pares == "usd7" else None
    if pares is None:
        pares = sorted(pd.DataFrame(load_closes()).columns)

    t0 = time.time()
    feat = build_matrix(pares)
    FEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
    suffix = "" if a.pares == "usd7" else "_all28"
    path = FEAT_PATH.with_name(FEAT_PATH.stem + suffix + ".parquet")
    feat.to_parquet(path)
    print(f"matriz {feat.shape} -> {path} ({time.time()-t0:.0f}s)")
    if a.build_only:
        return

    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = set(train) | set(valid)
    df = feat.merge(lab[["day", "currency", "labeled", "direction", "score"]],
                    on=["day", "currency"], how="left")
    df["labeled"] = df["labeled"].fillna(False)
    df = df[df.day.isin(keep)].sort_values(["day", "currency"]).reset_index(drop=True)

    lines = [f"# a12 — Geometria literal do CSS clássico em T0 (pares: {a.pares})",
             "", f"Matriz: {feat.shape[0]} linhas | dias research: {len(keep)} | "
             f"params: per={PER} suav={SUAV} box={BOX} k_slope={KSLOPE}", "",
             "Critérios de sucesso PRÉ-REGISTRADOS no CHANGELOG (2026-07-06) e "
             "no cabeçalho deste script, ANTES da primeira execução.", ""]
    contrast(df, lines)
    survivors = evaluate(df, lines)
    ml_ceiling(df, lines)

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a12")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"pares": a.pares, "per": PER, "suav": SUAV, "box": BOX,
         "k_slope": KSLOPE, "tfs": TFS, "n_dias_research": len(keep)}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md | sobreviventes: {survivors or 'nenhuma'}")


if __name__ == "__main__":
    main()

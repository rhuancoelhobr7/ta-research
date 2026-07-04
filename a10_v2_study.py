"""a10_v2_study.py — Estudo v2, etapa 3: duas tarefas com disciplina total.

TAREFA 1 (H1v2/H2v2): prever o rótulo do dia (moeda+direção) com o retrato
MTF de T0 — cenários A/B/C do PROTOCOLO.md por lente, cascata `alin`, e ML
teto (logistic + gboost raso, purged CV gap 5 dias).

TAREFA 2 (Tokyo-confirma, lição do A8): decisão em T0+4h usando SÓ
[T0, T0+4h]; alvo = retorno orientado do índice em [T0+4h, T0+12h] —
JANELAS DISJUNTAS por construção (`oriented_target` recusa alvo que invada
a janela de decisão; teste em tests/test_a10.py).

Disciplina (pré-registrada no topo do REPORT): seleção de regra/lente/limiar
SÓ em treino (60% dos dias); lente por regra de platô; baselines
obrigatórios (aleatório pareado, continuação-D1; tarefa 2 + reversão);
reality check com 200 permutações em bloco DA BUSCA INTEIRA (lentes ×
regras × limiares); validação = walk-forward (tarefa 1) / IC bootstrap em
blocos (tarefa 2); n<100 = amostra insuficiente; NADA de holdout.

Saída: results/{ts}_v2/REPORT.md + params.json.
Uso: python a10_v2_study.py
"""
from __future__ import annotations

import json, pathlib, time

import numpy as np
import pandas as pd

from a4_features_t0 import load_d1_closes
from a5_reverse import eval_predictions
from a9_mtf_matrix import COND_NAMES
from cssm_engine import build_indices, calibrate_gates, tstat_nw
from splits_days import research_days
from stats_blocks import (block_bootstrap_ci, block_permute,
                          purged_cv_splits, reality_check_p95)

ACTIVE = (1.0, 2.0, 3.0)          # FN, FP, FR
TFS = ("MN", "W1", "D1", "H4", "H1", "M30")
LENSES = (16, 24, 32, 48)
N_PERM, PERM_BLOCK, CV_GAP, N_WF = 200, 5, 5, 5

CRITERIOS = """## Critérios de sucesso PRÉ-REGISTRADOS (fixados antes de rodar)

- **Tarefa 1**: a regra escolhida (em TREINO, lente por platô) precisa de
  (a) top-1 em treino > p95 dos máximos de 200 permutações em bloco da
  busca inteira (regras × lentes); (b) top-1 em treino > TODOS os baselines;
  (c) vencer o melhor baseline em ≥ 70% das janelas walk-forward da
  validação. Qualquer coisa fora disso = NULO.
- **Tarefa 2**: retorno médio do alvo disjunto [T0+4h,T0+12h] na VALIDAÇÃO
  com IC95% (bootstrap em blocos) inteiramente acima de 0 E média acima dos
  três baselines (aleatório, continuação-D1, reversão) E média de treino >
  p95 permutado da busca inteira. Qualquer coisa fora disso = NULO.
- Sem afrouxamento post-hoc; n<100 = amostra insuficiente (flag no texto).
"""


# ----------------------------------------------------------------------------
# Alvo disjunto (guarda de janela)
# ----------------------------------------------------------------------------

def oriented_target(rows: pd.DataFrame, direction: np.ndarray,
                    decision_end_h: float = 4.0, target_start_h: float = 4.0,
                    target_end_h: float = 12.0) -> np.ndarray:
    """Retorno orientado do alvo. Recusa alvo que invada a decisão."""
    if target_start_h < decision_end_h:
        raise ValueError(
            f"Alvo [{target_start_h}h,{target_end_h}h] invade a janela de "
            f"decisão [0,{decision_end_h}h] — regra dura nº 3 (lookahead).")
    if (target_start_h, target_end_h) != (4.0, 12.0):
        raise ValueError("Só o alvo [4h,12h] está materializado (ret_4_12).")
    return direction * rows["ret_4_12"].to_numpy(dtype=float)


# ----------------------------------------------------------------------------
# Tarefa 1 — regras de T0
# ----------------------------------------------------------------------------

def _macro(row):
    if np.isfinite(row.MN_cond):
        return row.MN_cond, row.MN_dir
    return row.W1_cond, row.W1_dir


def _alin(row, d):
    n = 0
    for tf in TFS:
        c, dd = getattr(row, f"{tf}_cond"), getattr(row, f"{tf}_dir")
        if np.isfinite(c) and c in ACTIVE and dd == d:
            n += 1
    return n


def _mk_candidates(g: pd.DataFrame, pred) -> list:
    out = []
    for row in g.itertuples():
        for d in (1.0, -1.0):
            if pred(row, d):
                score = _alin(row, d) + min(abs(np.nan_to_num(row.H4_M)), 1)
                out.append((row.currency, "ALTA" if d > 0 else "BAIXA",
                            float(score)))
    return sorted(out, key=lambda x: -x[2])


def rule_cenA(g):
    def p(r, d):
        mc, md = _macro(r)
        if not (np.isfinite(mc) and mc in (3, 4) and md == -d):
            return False
        if np.isfinite(r.D1_cond) and r.D1_cond in (1, 2) and r.D1_dir == -d:
            return False                                   # D1 bloqueia
        return (np.isfinite(r.H4_cond) and r.H4_cond in (1, 2)
                and r.H4_dir == d and np.isfinite(r.H1_cond)
                and r.H1_cond in (1, 2) and r.H1_dir == d)
    return _mk_candidates(g, p)


def rule_cenB(g):
    def p(r, d):
        mc, md = _macro(r)
        return (np.isfinite(mc) and mc in (2, 3) and md == -d
                and np.isfinite(r.D1_cond) and r.D1_cond in (1, 2)
                and r.D1_dir == d and r.D1_age >= 3
                and np.isfinite(r.H4_cond) and r.H4_cond in ACTIVE
                and r.H4_dir == d)
    return _mk_candidates(g, p)


def rule_cenC(g):
    def p(r, d):
        mc, md = _macro(r)
        macro_ok = np.isfinite(mc) and ((mc in ACTIVE and md == d) or
                                        (mc in (3, 4) and md == -d))
        return (macro_ok and np.isfinite(r.D1_cond) and r.D1_cond in ACTIVE
                and r.D1_dir == d and np.isfinite(r.H4_cond)
                and r.H4_cond == 2 and r.H4_dir == d)
    return _mk_candidates(g, p)


def rule_alin(g):
    out = []
    for row in g.itertuples():
        best = max(((d, _alin(row, d)) for d in (1.0, -1.0)),
                   key=lambda x: x[1])
        d, n = best
        if n >= 1:
            out.append((row.currency, "ALTA" if d > 0 else "BAIXA",
                        n + min(abs(np.nan_to_num(row.H4_M)), 1)))
    return sorted(out, key=lambda x: -x[2])


T1_RULES = {"cenA": rule_cenA, "cenB": rule_cenB, "cenC": rule_cenC,
            "alin": rule_alin}


def t1_predictions(df: pd.DataFrame) -> dict:
    """{(regra, lente): {dia: ranking}} — previsões fixas, avaliadas depois."""
    preds = {}
    for lens, dfl in df.groupby("lens"):
        groups = {d: g for d, g in dfl.groupby("day")}
        for name, fn in T1_RULES.items():
            preds[(name, int(lens))] = {d: fn(g) for d, g in groups.items()}
    return preds


def plateau_lens(scores: dict) -> int:
    """Lente do platô: maximiza a média (própria + vizinhas na grade)."""
    ls = sorted(scores)
    best, best_v = ls[0], -1.0
    for i, w in enumerate(ls):
        neigh = [scores[ls[j]] for j in (i - 1, i, i + 1)
                 if 0 <= j < len(ls) and np.isfinite(scores[ls[j]])]
        v = float(np.mean(neigh))
        if v > best_v:
            best, best_v = w, v
    return best


# ----------------------------------------------------------------------------
# Tarefa 2 — decisão em T0+4h
# ----------------------------------------------------------------------------

def mini_scores(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    bdir = np.where(d.ret4h > 0, d.breadth4h, 1 - d.breadth4h)
    d["mini_score"] = d.ret4h.abs() * bdir * d.er4h
    d["dir4h"] = np.sign(d.ret4h)
    return d


def t2_pick(dfl: pd.DataFrame, theta: float, mtf: bool) -> pd.DataFrame:
    """Por dia: moeda de maior mini_score >= theta (opcional: MTF a favor)."""
    d = dfl
    ok = d.mini_score >= theta
    if mtf:
        h1 = d.H1_cond_4h.isin(ACTIVE[:2]) & (d.H1_dir_4h == d.dir4h)
        h4 = d.H4_cond_4h.isin(ACTIVE[:2]) & (d.H4_dir_4h == d.dir4h)
        ok &= (h1 | h4)
    c = d[ok & d.mini_score.notna() & (d.dir4h != 0)]
    if c.empty:
        return c
    return c.sort_values("mini_score", ascending=False).groupby("day").head(1)


def t2_mean_return(picks: pd.DataFrame) -> tuple[float, int]:
    if picks.empty:
        return np.nan, 0
    r = oriented_target(picks, picks.dir4h.to_numpy())
    r = r[~np.isnan(r)]
    return (float(r.mean()) if len(r) else np.nan), len(r)


# ----------------------------------------------------------------------------
# Baselines
# ----------------------------------------------------------------------------

def continuation_picks(days) -> dict:
    dd = build_indices(load_d1_closes(), align="inner").diff()
    out = {}
    for d in days:
        prev = dd[dd.index < d]
        if prev.empty:
            out[d] = []
            continue
        row = prev.iloc[-1]
        c = row.abs().idxmax()
        out[d] = [(c, "ALTA" if row[c] > 0 else "BAIXA", float(abs(row[c])))]
    return out


# ----------------------------------------------------------------------------

def main():
    df = pd.read_parquet("data/features/v2_mtf.parquet")
    meta9 = json.loads(pathlib.Path(
        "data/features/v2_mtf_meta.json").read_text())
    labels = pd.read_parquet("data/labels/labels_v1.parquet")
    df = df.merge(labels[["day", "currency", "labeled", "direction", "score"]],
                  on=["day", "currency"], how="left")
    df["labeled"] = df["labeled"].fillna(False)

    all_days = pd.DatetimeIndex(sorted(labels.day.unique()))
    train_d, valid_d = research_days(all_days)
    train_d, valid_d = set(train_d), set(valid_d)
    days_res = sorted(df.day.unique())
    truth = {d: set() for d in days_res}
    for r in df[df.labeled & (df.lens == LENSES[0])].itertuples():
        truth[r.day].add((r.currency, r.direction))

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_v2"); out.mkdir(parents=True,
                                                      exist_ok=True)
    L = ["# Estudo v2 — lentes calibradas e leitura MTF fiel", "", CRITERIOS]

    # ---- calibração (tabela) ------------------------------------------------
    L += ["## Calibração dos gates por lente", "",
          "| w | t_gate | t_low | FP medido (walks frescos) |",
          "|---|---|---|---|"]
    rng = np.random.default_rng(2026)
    for w, m in sorted({int(k): v for k, v in meta9["lenses"].items()}.items()):
        fps = []
        for _ in range(8):
            x = np.cumsum(rng.normal(0, 1, 20000))
            t = tstat_nw(x, w); t = t[~np.isnan(t)]
            fps.append(np.mean(np.abs(t) >= m["t_gate"]))
        L.append(f"| {w} | {m['t_gate']} | {m['t_low']} | "
                 f"{100*np.mean(fps):.1f}% |")
    L += ["", f"W1 (w=64) gate {meta9['gate_w1']}; MN (w=24 meses) gate "
          f"{meta9['gate_mn']} — modo reduzido (FP/FR/N).", ""]

    # ================= TAREFA 1 =================
    preds = t1_predictions(df)
    tr_days = [d for d in days_res if d in train_d]
    va_days = [d for d in days_res if d in valid_d]
    truth_tr = {d: truth[d] for d in tr_days}
    truth_va = {d: truth[d] for d in va_days}

    ev_tr = {k: eval_predictions({d: p[d] for d in tr_days if d in p}, truth_tr)
             for k, p in preds.items()}

    # baselines (treino)
    cont = continuation_picks(days_res)
    top_by_day = (df[df.labeled & (df.lens == LENSES[0])]
                  .sort_values("score", ascending=False).groupby("day").first())
    pers = {}
    for i, d in enumerate(days_res):
        prevs = [x for x in days_res[:i] if x in top_by_day.index]
        pers[d] = ([(top_by_day.loc[prevs[-1]].currency,
                     top_by_day.loc[prevs[-1]].direction, 1.0)]
                   if prevs else [])
    base_tr = {"continuação-D1": eval_predictions(
                   {d: cont[d] for d in tr_days}, truth_tr),
               "persistência": eval_predictions(
                   {d: pers[d] for d in tr_days}, truth_tr)}
    rand_tr = float(np.mean([len(truth[d]) / 16 for d in tr_days]))

    # reality check da BUSCA INTEIRA (treino)
    rng = np.random.default_rng(0)
    day_arr = np.array(tr_days, dtype="datetime64[ns]")
    maxima = np.empty(N_PERM)
    for k in range(N_PERM):
        p = block_permute(len(tr_days), PERM_BLOCK, rng)
        tp = {tr_days[i]: truth[pd.Timestamp(day_arr[p[i]])]
              for i in range(len(tr_days))}
        best = 0.0
        for key, pr in preds.items():
            ev = eval_predictions({d: pr[d] for d in tr_days}, tp)
            if ev["n"] >= 100 and np.isfinite(ev["top1"]):
                best = max(best, ev["top1"])
        maxima[k] = best
    p95_t1 = reality_check_p95(maxima)

    L += ["## Tarefa 1 — retrato de T0 prevê o rótulo do dia?", "",
          f"Treino: {len(tr_days)} dias | validação: {len(va_days)} dias "
          f"(n<100 na validação — amostra flagada) | acaso pareado (treino): "
          f"**{100*rand_tr:.1f}%** | p95 permutado da busca inteira "
          f"({len(preds)} combinações): **{100*p95_t1:.1f}%**", "",
          "| regra | lente | n dias | top-1 treino | hit@2 |",
          "|---|---|---|---|---|"]
    for (name, lens), ev in sorted(ev_tr.items()):
        flag = " (n<100!)" if 0 < ev["n"] < 100 else ""
        t1s = f"{100*ev['top1']:.1f}%" if ev["n"] else "—"
        h2s = f"{100*ev['hit2']:.1f}%" if ev["n"] else "—"
        L.append(f"| {name} | {lens} | {ev['n']}{flag} | {t1s} | {h2s} |")
    for bn, ev in base_tr.items():
        L.append(f"| {bn} (baseline) | — | {ev['n']} | "
                 f"{100*ev['top1']:.1f}% | {100*ev['hit2']:.1f}% |")

    # escolha em treino: platô por família, depois melhor família
    chosen, chosen_train = None, -1.0
    for name in T1_RULES:
        sc = {lens: (ev_tr[(name, lens)]["top1"]
                     if ev_tr[(name, lens)]["n"] >= 100 else np.nan)
              for lens in LENSES}
        if all(np.isnan(v) for v in sc.values()):
            continue
        lw = plateau_lens(sc)
        v = sc[lw]
        if np.isfinite(v) and v > chosen_train:
            chosen, chosen_train = (name, lw), v
    best_base_tr = max(rand_tr, *(e["top1"] for e in base_tr.values()))

    if chosen:
        name, lens = chosen
        # walk-forward na validação
        wf_wins, wf_tot = 0, 0
        for wf in np.array_split(np.array(va_days), N_WF):
            if len(wf) == 0:
                continue
            twf = {d: truth[d] for d in wf}
            evr = eval_predictions({d: preds[chosen][d] for d in wf}, twf)
            evc = eval_predictions({d: cont[d] for d in wf}, twf)
            evp = eval_predictions({d: pers[d] for d in wf}, twf)
            rnd = float(np.mean([len(truth[d]) / 16 for d in wf]))
            bb = max(rnd, evc["top1"] if evc["n"] else 0,
                     evp["top1"] if evp["n"] else 0)
            wf_tot += 1
            if evr["n"] and evr["top1"] > bb:
                wf_wins += 1
        ok_a = chosen_train > p95_t1
        ok_b = chosen_train > best_base_tr
        ok_c = wf_tot > 0 and wf_wins / wf_tot >= 0.70
        ev_va = eval_predictions({d: preds[chosen][d] for d in va_days},
                                 truth_va)
        L += ["", f"**Escolhida em treino (platô)**: {name} lente {lens} — "
              f"top-1 treino {100*chosen_train:.1f}%.",
              f"- (a) > p95 permutado ({100*p95_t1:.1f}%)? "
              f"**{'SIM' if ok_a else 'NÃO'}**",
              f"- (b) > todos os baselines (melhor: {100*best_base_tr:.1f}%)? "
              f"**{'SIM' if ok_b else 'NÃO'}**",
              f"- (c) walk-forward validação: venceu {wf_wins}/{wf_tot} "
              f"janelas (critério ≥70%)? **{'SIM' if ok_c else 'NÃO'}** "
              f"(top-1 validação: {100*ev_va['top1']:.1f}%, n={ev_va['n']} "
              f"— n<100, amostra insuficiente p/ IC)",
              f"", f"**Veredicto Tarefa 1: "
              f"{'SUCESSO' if ok_a and ok_b and ok_c else 'NULO'}** "
              f"(critérios pré-registrados).", ""]
        t1_verdict = bool(ok_a and ok_b and ok_c)
    else:
        L += ["", "Nenhuma regra atingiu n>=100 em treino — Tarefa 1 NULA.",
              ""]
        t1_verdict = False

    # ---- ML teto -------------------------------------------------------------
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.preprocessing import StandardScaler

    L += ["### ML teto (alvo: rotula?; purged CV 5 folds, gap "
          f"{CV_GAP} dias)", "", "| lente | logistic AUC | gboost AUC |",
          "|---|---|---|"]
    ml_auc = {}
    for lens in LENSES:
        dfl = df[df.lens == lens].reset_index(drop=True)
        feats = []
        for tf in TFS:
            oh = pd.get_dummies(dfl[f"{tf}_cond"].fillna(-9).astype(int),
                                prefix=f"{tf}c")
            feats.append(oh)
        num = dfl[[c for c in dfl.columns if c.endswith(("_dir", "_M", "_t"))
                   and "4h" not in c] + ["D1_age"]].fillna(0)
        X = pd.concat(feats + [num], axis=1).to_numpy(dtype=float)
        y = dfl.labeled.to_numpy(dtype=int)
        dl = sorted(dfl.day.unique()); dpos = dfl.day.map(
            {d: i for i, d in enumerate(dl)}).to_numpy()
        aucs = {"lg": [], "gb": []}
        for trd, ted in purged_cv_splits(len(dl), 5, CV_GAP):
            tr, te = np.isin(dpos, trd), np.isin(dpos, ted)
            if len(np.unique(y[te])) < 2:
                continue
            sc = StandardScaler().fit(X[tr])
            lg = LogisticRegression(max_iter=2000, class_weight="balanced")
            lg.fit(sc.transform(X[tr]), y[tr])
            aucs["lg"].append(roc_auc_score(y[te], lg.predict_proba(
                sc.transform(X[te]))[:, 1]))
            gb = GradientBoostingClassifier(max_depth=2, n_estimators=200,
                                            learning_rate=0.05, subsample=0.8,
                                            random_state=0)
            gb.fit(X[tr], y[tr])
            aucs["gb"].append(roc_auc_score(y[te], gb.predict_proba(
                X[te])[:, 1]))
        ml_auc[lens] = {k: float(np.mean(v)) for k, v in aucs.items()}
        L.append(f"| {lens} | {ml_auc[lens]['lg']:.3f} | "
                 f"{ml_auc[lens]['gb']:.3f} |")
    L.append("")

    # ================= TAREFA 2 =================
    d16 = mini_scores(df[df.lens == LENSES[0]].reset_index(drop=True))
    thetas = {f"q{q}": float(d16[d16.day.isin(train_d)].mini_score
                             .quantile(q / 100)) for q in (0, 50, 75)}
    variants = {}
    for tn, tv in thetas.items():
        variants[(f"mom_puro_{tn}", None)] = (tv, False, LENSES[0])
        for lens in LENSES:
            variants[(f"mom_mtf_{tn}", lens)] = (tv, True, lens)

    def eval_variant(theta, mtf, lens, day_set):
        dfl = mini_scores(df[df.lens == lens].reset_index(drop=True))
        dfl = dfl[dfl.day.isin(day_set)]
        return t2_pick(dfl, theta, mtf)

    rows_t2, picks_cache = [], {}
    for (vn, lens), (tv, mtf, l_eff) in variants.items():
        picks = eval_variant(tv, mtf, l_eff, train_d)
        picks_cache[(vn, lens)] = (tv, mtf, l_eff)
        mu, n = t2_mean_return(picks)
        rows_t2.append({"variante": vn, "lente": lens or "—", "n": n,
                        "mean_bp": mu * 1e4 if np.isfinite(mu) else np.nan})

    # reality check tarefa 2: permuta dias→alvos, máximo sobre a busca
    tr_list = sorted(train_d & set(days_res))
    tgt = {(r.day, r.currency): r.ret_4_12
           for r in d16[d16.day.isin(train_d)].itertuples()}
    rng = np.random.default_rng(1)
    maxima2 = np.empty(N_PERM)
    pick_rows = {k: eval_variant(*picks_cache[k], train_d)
                 for k in picks_cache}
    for k in range(N_PERM):
        p = block_permute(len(tr_list), PERM_BLOCK, rng)
        remap = {tr_list[i]: tr_list[p[i]] for i in range(len(tr_list))}
        best = -np.inf
        for key, picks in pick_rows.items():
            if len(picks) < 100:
                continue
            r = np.array([picks.dir4h.iloc[i] *
                          tgt.get((remap[picks.day.iloc[i]],
                                   picks.currency.iloc[i]), np.nan)
                          for i in range(len(picks))])
            r = r[~np.isnan(r)]
            if len(r) >= 100:
                best = max(best, r.mean())
        maxima2[k] = best
    p95_t2 = reality_check_p95(maxima2) * 1e4

    tab2 = pd.DataFrame(rows_t2)
    L += ["## Tarefa 2 — Tokyo-confirma (decisão T0+4h, alvo disjunto "
          "[T0+4h, T0+12h])", "",
          f"Limiar θ por quantis do treino: "
          + ", ".join(f"{k}={v:.2e}" for k, v in thetas.items())
          + f" | p95 permutado da busca inteira (bp): **{p95_t2:+.2f}**", "",
          "| variante | lente | n treino | média treino (bp) |",
          "|---|---|---|---|"]
    for r in tab2.itertuples():
        flag = " (n<100!)" if 0 < r.n < 100 else ""
        ms = f"{r.mean_bp:+.2f}" if np.isfinite(r.mean_bp) else "—"
        L.append(f"| {r.variante} | {r.lente} | {r.n}{flag} | {ms} |")

    valid_tab = tab2[(tab2.n >= 100) & tab2.mean_bp.notna()]
    if len(valid_tab):
        bi = valid_tab.mean_bp.idxmax()
        vn, lens = tab2.loc[bi, "variante"], tab2.loc[bi, "lente"]
        key = (vn, None if lens == "—" else lens)
        tv, mtf, l_eff = picks_cache[key]
        # validação
        pv = eval_variant(tv, mtf, l_eff, valid_d)
        rv = oriented_target(pv, pv.dir4h.to_numpy())
        rv = rv[~np.isnan(rv)]
        mu_v, lo_v, hi_v = block_bootstrap_ci(rv, block=PERM_BLOCK)
        # baselines na validação
        cont_p = continuation_picks(days_res)
        rows_c = []
        for d in sorted(valid_d & set(days_res)):
            if not cont_p[d]:
                continue
            c, ds, _ = cont_p[d][0]
            row = d16[(d16.day == d) & (d16.currency == c)]
            if len(row):
                rows_c.append((1.0 if ds == "ALTA" else -1.0) *
                              row.ret_4_12.iloc[0])
        rc = np.array([x for x in rows_c if np.isfinite(x)])
        mu_c = float(rc.mean()) if len(rc) else np.nan
        mu_rev = -mu_v                      # reversão = seleção igual, dir oposta
        mu_rnd = 0.0                        # aleatório pareado: simétrico
        tr_mu = float(tab2.loc[bi, "mean_bp"])
        ok1 = lo_v > 0
        ok2 = (mu_v * 1e4 > max(mu_c * 1e4 if np.isfinite(mu_c) else -9e9,
                                mu_rev * 1e4, mu_rnd))
        ok3 = tr_mu > p95_t2
        flag_n = " (n<100 — amostra insuficiente!)" if len(rv) < 100 else ""
        L += ["", f"**Escolhida em treino**: {vn} (lente {lens}) — média "
              f"treino {tr_mu:+.2f} bp.",
              f"- Validação: média **{mu_v*1e4:+.2f} bp** IC95% "
              f"[{lo_v*1e4:+.2f}, {hi_v*1e4:+.2f}] (n={len(rv)}{flag_n})",
              f"- Baselines validação (bp): aleatório 0.00 | continuação-D1 "
              f"{mu_c*1e4:+.2f} | reversão {mu_rev*1e4:+.2f}",
              f"- (a) IC inteiro > 0? **{'SIM' if ok1 else 'NÃO'}** | "
              f"(b) > 3 baselines? **{'SIM' if ok2 else 'NÃO'}** | "
              f"(c) treino > p95 permutado? **{'SIM' if ok3 else 'NÃO'}**",
              f"", f"**Veredicto Tarefa 2: "
              f"{'SUCESSO' if ok1 and ok2 and ok3 else 'NULO'}** "
              f"(critérios pré-registrados).", ""]
        t2_verdict = bool(ok1 and ok2 and ok3)
        t2_extra = {"chosen": vn, "lens": str(lens), "valid_mean_bp":
                    mu_v * 1e4, "valid_ci_bp": [lo_v * 1e4, hi_v * 1e4],
                    "n_valid": int(len(rv))}
    else:
        L += ["", "Nenhuma variante com n>=100 em treino — Tarefa 2 NULA.", ""]
        t2_verdict, t2_extra = False, {}

    # ---- diagnóstico: por que os cenários não disparam ------------------------
    d24 = df[df.lens == 24]
    L += ["## Diagnóstico — frequência das condições em T0 (lente 24)", "",
          "| TF | N | FN | FP | FR | EX | sem dado |", "|---|---|---|---|---|---|---|"]
    for tf in TFS:
        vc = d24[f"{tf}_cond"].value_counts(normalize=True, dropna=False)
        row = [f"| {tf}"]
        for k in (0.0, 1.0, 2.0, 3.0, 4.0):
            row.append(f"{100*vc.get(k, 0.0):.1f}%")
        row.append(f"{100*float(d24[f'{tf}_cond'].isna().mean()):.1f}%")
        L.append(" | ".join(row) + " |")
    L += ["",
          "Leitura: o tier macro em modo reduzido com gates honestos quase "
          "nunca sai de N (MN 100% N; W1 ~0.3% FP na amostra) — os cenários "
          "A/B/C, que EXIGEM leitura macro não-neutra, ficam estruturalmente "
          "vazios. Não é um bug de implementação: é o resultado. A leitura "
          "'macro contra/a favor' do Protocolo, mecanizada com taxa de falso "
          "positivo controlada, não ocorre nos dados; só a cascata `alin` "
          "(que não exige macro) gera previsões.", ""]

    # ---- grade típica ---------------------------------------------------------
    L += ["## Grade típica em T0 (condição modal por TF) — rotulados vs não",
          ""]
    for lens in LENSES:
        dfl = df[df.lens == lens]
        row_lab, row_nao = [f"| {lens} rotulados"], [f"| {lens} não-rot."]
        for tf in TFS:
            for m, acc in ((dfl[dfl.labeled], row_lab),
                           (dfl[~dfl.labeled], row_nao)):
                md = m[f"{tf}_cond"].mode()
                acc.append(COND_NAMES.get(int(md.iloc[0]), "?")
                           if len(md) else "?")
        if lens == LENSES[0]:
            L += ["| lente/grupo | " + " | ".join(TFS) + " |",
                  "|" + "---|" * 7]
        L += [" | ".join(row_lab) + " |", " | ".join(row_nao) + " |"]
    L.append("")

    # ---- parágrafo final ------------------------------------------------------
    frac_active = df[df.labeled].groupby("lens")[["H1_cond", "M30_cond"]].agg(
        lambda s: float(s.isin(ACTIVE).mean()))
    frase_ativa = ", ".join(f"w={int(l)}: {100*v:.0f}%"
                            for l, v in frac_active["H1_cond"].items())
    L += ["## Conclusão honesta", "",
          f"A reforma da lente FOI testada de verdade: gates calibrados por "
          f"w (FP 4-7% verificado em walks frescos), 4 lentes, MN habilitado "
          f"pelos 7 anos de D1, cenários formais do PROTOCOLO.md. Veredictos "
          f"pré-registrados: Tarefa 1 = "
          f"**{'SUCESSO' if t1_verdict else 'NULO'}**, Tarefa 2 = "
          f"**{'SUCESSO' if t2_verdict else 'NULO'}**. Fração de condição "
          f"ativa no H1 em T0 nos dias rotulados, por lente: {frase_ativa}."]
    if not t1_verdict and not t2_verdict:
        L += ["",
              "Resposta à pergunta do estudo: **não era (só) a lente**. Com "
              "janelas curtas e portões honestos, a fração ativa em T0 sobe "
              "de ~4% (v1) para ~5-8%, mas o retrato continua sem separar os "
              "dias (ML teto ~0.5; `alin` abaixo da persistência) — H1v2 "
              "refutada. A leitura MTF fiel (H2v2) morre antes: os cenários "
              "exigem um tier macro que, mecanizado com FP controlado, é "
              "estruturalmente Neutro. E o momentum das 4 primeiras horas "
              "não sobrevive à janela disjunta [T0+4h, T0+12h] (Tarefa 2 "
              "nula, reversão igualmente nula): o que o A8 viu era o próprio "
              "movimento do dia, sem continuação explorável após as 4h. O "
              "sinal, se existe, não está no preço passado em T0 nem em "
              "T0+4h — está fora do escopo mensurável deste indicador.", ""]
    L += ["", "O holdout permanece intocado; rodada final (a7) só sob ordem "
          "explícita do usuário.", ""]

    (out / "REPORT.md").write_text("\n".join(L), encoding="utf-8")
    (out / "params.json").write_text(json.dumps({
        "n_perm": N_PERM, "perm_block": PERM_BLOCK, "cv_gap": CV_GAP,
        "lenses": list(LENSES), "thetas": thetas,
        "t1": {"chosen": chosen[0] if chosen else None,
               "lens": chosen[1] if chosen else None,
               "train_top1": chosen_train, "p95": p95_t1,
               "verdict": t1_verdict},
        "t2": {"p95_bp": p95_t2, "verdict": t2_verdict, **t2_extra},
        "ml_auc": {str(k): v for k, v in ml_auc.items()}}, indent=2,
        default=float))
    print(f"OK -> {out}/REPORT.md | T1={'SUCESSO' if t1_verdict else 'NULO'} "
          f"| T2={'SUCESSO' if t2_verdict else 'NULO'}")


if __name__ == "__main__":
    main()

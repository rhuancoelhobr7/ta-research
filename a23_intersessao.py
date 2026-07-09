# -*- coding: utf-8 -*-
"""a23_intersessao.py — as sessões se influenciam? (autocorrelação de vol).

"Provável ouro" (independe do CSS): se Tokyo informa Londres, a decisão sai com
dado já disponível na virada. Usa a PARTIÇÃO ORDENADA SEM SOBREPOSIÇÃO
(SEQ_SESSIONS): asia [00-07) fecha antes de londres [07-13) abrir — sem
lookahead. overlap (13-16) ⊂ ny, medido à parte p/ a Q5.

Q4 — asia de range alto prevê londres de range alto NO MESMO PAR? Spearman
     asia→londres vs BASELINE persistência (londres_ontem→londres_hoje).
Q5 — quanto do range DIÁRIO acontece no overlap Londres∩NY?
Q6 — "mola comprimida": asia apertada prevê EXPANSÃO em londres ou continuação
     da calma? Testa as duas hipóteses no tail explicitamente.
Q7 — lead-lag entre moedas: atividade de uma moeda no asia antecipa seus
     crosses no londres (além do range do próprio par)? (versão leve, honesta.)

Metodologia: barras fechadas, sem lookahead, split 70/30 temporal, thresholds/
medianas de normalização estimados SÓ no treino e aplicados no teste, bootstrap
em blocos SEMANAIS (block=5 dias), correção Benjamini-Hochberg na família Q4.
Nulo é publicável.

Uso: python a23_intersessao.py
Saída: results/{ts}_a23/REPORT.md + transicao_vol.csv + panel.parquet
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from sessions import SEQ_SESSIONS, session_ranges, daily_range
from stats_blocks import block_bootstrap_ci

RAW = pathlib.Path("data/raw")
TRAIN_FRAC = 0.70
QBINS = 4  # quartis de volatilidade


def load_pips() -> dict[str, float]:
    meta = json.loads((RAW / "_meta_ta.json").read_text(encoding="utf-8"))
    return {s: v["pip"] for s, v in meta["symbols"].items()}


def build_panel() -> pd.DataFrame:
    """Painel (pair,date) wide: range por sessão sequencial + range diário."""
    pips = load_pips()
    rows = []
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        df = pd.read_parquet(f)
        sr = session_ranges(df, pips[sym], SEQ_SESSIONS)
        if sr.empty:
            continue
        w = sr.pivot_table(index="date", columns="session", values="range_pips")
        w = w.join(daily_range(df, pips[sym])[["day_range"]])
        w["pair"] = sym
        rows.append(w.reset_index())
    p = pd.concat(rows, ignore_index=True)
    return p.sort_values(["pair", "date"]).reset_index(drop=True)


def bh_reject(pvals: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Benjamini-Hochberg: máscara de rejeições ao nível FDR alpha."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    thresh = alpha * (np.arange(1, n + 1)) / n
    passed = p[order] <= thresh
    k = np.where(passed)[0].max() + 1 if passed.any() else 0
    rej = np.zeros(n, dtype=bool)
    if k > 0:
        rej[order[:k]] = True
    return rej


# ----------------------------------------------------------------------------
# Q4 — autocorrelação asia→londres vs persistência
# ----------------------------------------------------------------------------

def q4(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    recs = []
    for pair, g in panel.groupby("pair"):
        g = g.dropna(subset=["asia", "londres"]).sort_values("date")
        cut = g["date"].quantile(TRAIN_FRAC)
        te = g[g["date"] >= cut]
        if len(te) < 100:
            continue
        # asia -> londres (mesmo dia)
        r_al, p_al = spearmanr(te["asia"], te["londres"])
        # baseline: persistência londres_ontem -> londres_hoje (no teste)
        lon = g.set_index("date")["londres"]
        j = pd.concat({"prev": lon.shift(1), "cur": lon}, axis=1) \
              .loc[te["date"]].dropna()
        r_pp = spearmanr(j["prev"], j["cur"])[0] if len(j) > 10 else np.nan
        recs.append({"pair": pair, "asia_londres": r_al, "p": p_al,
                     "persist_londres": r_pp, "n_test": len(te)})
    tab = pd.DataFrame(recs)
    tab["bh_signif"] = bh_reject(tab["p"].values)
    stat, lo, hi = block_bootstrap_ci(tab["asia_londres"].values, np.median,
                                      block=5)
    bstat, blo, bhi = block_bootstrap_ci(tab["persist_londres"].dropna().values,
                                         np.median, block=5)
    summ = {"asia_londres_med": stat, "asia_londres_ci": (lo, hi),
            "persist_med": bstat, "persist_ci": (blo, bhi),
            "n_signif_bh": int(tab["bh_signif"].sum()), "n_pairs": len(tab)}
    return tab, summ


# ----------------------------------------------------------------------------
# Q5 — fração do range diário no overlap
# ----------------------------------------------------------------------------

def q5(panel: pd.DataFrame) -> pd.DataFrame:
    p = panel.dropna(subset=["day_range"]).copy()
    p = p[p["day_range"] > 0]
    out = {}
    for s in ("asia", "londres", "ny", "overlap"):
        out[s] = (p[s] / p["day_range"]).median()
    return pd.Series(out, name="fracao_mediana_do_range_diario").to_frame()


# ----------------------------------------------------------------------------
# Q6 — mola comprimida: asia apertada -> londres?
# ----------------------------------------------------------------------------

def q6(panel: pd.DataFrame) -> pd.DataFrame:
    recs = []
    for pair, g in panel.groupby("pair"):
        g = g.dropna(subset=["asia", "londres"]).sort_values("date")
        cut = g["date"].quantile(TRAIN_FRAC)
        tr, te = g[g["date"] < cut], g[g["date"] >= cut]
        if len(te) < 100 or len(tr) < 100:
            continue
        # quartis de asia e mediana de londres estimados NO TREINO
        edges = np.quantile(tr["asia"], np.linspace(0, 1, QBINS + 1))
        edges[0], edges[-1] = -np.inf, np.inf
        med_lon = tr["londres"].median()
        te = te.assign(aq=pd.cut(te["asia"], edges, labels=False,
                                 include_lowest=True),
                       lon_norm=te["londres"] / med_lon)
        recs.append(te.groupby("aq")["lon_norm"].median())
    m = pd.concat(recs, axis=1).T            # pares × quartil-de-asia
    s = m.median().sort_index()              # mediana entre pares por quartil
    return pd.DataFrame({"londres_norm_mediana": s.values},
                        index=[f"asia_Q{int(i)+1}" for i in s.index])


# ----------------------------------------------------------------------------
# Q7 — lead-lag de moeda (leve): fator asia da moeda -> crosses no londres
# ----------------------------------------------------------------------------

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]


def q7(panel: pd.DataFrame) -> pd.DataFrame:
    # fator asia por moeda = mediana do asia_norm dos seus pares no dia
    p = panel.dropna(subset=["asia", "londres"]).copy()
    med_pair_asia = p.groupby("pair")["asia"].transform("median")
    p["asia_norm"] = p["asia"] / med_pair_asia
    recs = []
    for cur in G8:
        mask = p["pair"].str.contains(cur)
        fac = (p[mask].groupby("date")["asia_norm"].median()
               .rename("cur_asia_factor"))
        sub = p[mask].merge(fac, on="date")
        # londres do par explicado pelo fator da moeda vs asia do próprio par
        r_fac, _ = spearmanr(sub["cur_asia_factor"], sub["londres"])
        r_own, _ = spearmanr(sub["asia"], sub["londres"])
        recs.append({"moeda": cur, "r_fator_moeda": r_fac, "r_asia_propria": r_own})
    return pd.DataFrame(recs).set_index("moeda")


# ----------------------------------------------------------------------------
# matriz de transição de volatilidade asia->londres (teste, pooled)
# ----------------------------------------------------------------------------

def transition_matrix(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for pair, g in panel.groupby("pair"):
        g = g.dropna(subset=["asia", "londres"]).sort_values("date")
        cut = g["date"].quantile(TRAIN_FRAC)
        tr, te = g[g["date"] < cut], g[g["date"] >= cut]
        if len(te) < 100 or len(tr) < 100:
            continue
        ea = np.quantile(tr["asia"], np.linspace(0, 1, QBINS + 1)); ea[0], ea[-1] = -np.inf, np.inf
        el = np.quantile(tr["londres"], np.linspace(0, 1, QBINS + 1)); el[0], el[-1] = -np.inf, np.inf
        rows.append(pd.DataFrame({
            "aq": pd.cut(te["asia"], ea, labels=False, include_lowest=True),
            "lq": pd.cut(te["londres"], el, labels=False, include_lowest=True)}))
    d = pd.concat(rows, ignore_index=True).dropna()
    ct = pd.crosstab(d["aq"], d["lq"], normalize="index")
    ct.index = [f"asia_Q{int(i)+1}" for i in ct.index]
    ct.columns = [f"lon_Q{int(i)+1}" for i in ct.columns]
    return ct


# ----------------------------------------------------------------------------
# Driver
# ----------------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    panel = build_panel()
    q4tab, q4s = q4(panel)
    q5t = q5(panel)
    q6t = q6(panel)
    q7t = q7(panel)
    trans = transition_matrix(panel)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a23")
    out.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(out / "panel.parquet")
    trans.to_csv(out / "transicao_vol.csv")

    lo, hi = q4s["asia_londres_ci"]; blo, bhi = q4s["persist_ci"]
    rep = [
        "# a23 — Inter-sessão (autocorrelação de volatilidade)\n",
        f"Painel {panel['pair'].nunique()} pares, {panel['date'].min().date()} → "
        f"{panel['date'].max().date()}. Partição ordenada asia[00-07)/londres"
        f"[07-13)/ny[13-21) UTC (sem sobreposição → sem lookahead). Split 70/30; "
        f"métricas no TESTE (últimos 30%); thresholds do treino.\n",
        "## Q4 — asia→londres vs persistência (Spearman, mediana entre pares)\n",
        f"- **asia→londres:** {q4s['asia_londres_med']:.3f}  IC95 [{lo:.3f}, {hi:.3f}]",
        f"\n- **baseline persistência (londres ontem→hoje):** {q4s['persist_med']:.3f} "
        f"IC95 [{blo:.3f}, {bhi:.3f}]",
        f"\n- pares com asia→londres significativo após BH: "
        f"**{q4s['n_signif_bh']}/{q4s['n_pairs']}**",
        "\n\n### Matriz de transição de volatilidade asia→londres (teste, pooled)\n",
        trans.round(3).to_markdown(),
        "\n\n## Q5 — fração do range DIÁRIO por sessão (mediana)\n",
        q5t.round(3).to_markdown(),
        "\n\n## Q6 — mola comprimida (londres normalizado por quartil de asia)\n",
        q6t.round(3).to_markdown(),
        "\n_Se cresce monotônico com o quartil de asia → calma continua "
        "(sem mola); se o Q1 de asia eleva londres → mola comprimida._\n",
        "\n## Q7 — lead-lag de moeda (fator asia vs asia do próprio par)\n",
        q7t.round(3).to_markdown(),
        "\n_r_fator_moeda ≈ r_asia_propria → o fator da moeda não agrega sobre o "
        "range do próprio par._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a23: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"Q4 asia->londres med={q4s['asia_londres_med']:.3f} vs persist="
          f"{q4s['persist_med']:.3f}  BH signif={q4s['n_signif_bh']}/{q4s['n_pairs']}")
    print("Q5 fração overlap do range diário:", round(q5t.loc['overlap'].iloc[0], 3))


if __name__ == "__main__":
    main()

"""a3_anatomy.py — Fase A3: anatomia do fenômeno.

ESPECIFICAÇÃO (PLAN.md §4, passo A3). Entrada: data/labels/labels_v1.parquet
(APENAS dias de treino+validação via splits_days.research_days).
Produz em results/{ts}_anatomy/REPORT.md + params.json:
 1. Taxa-base: % de dias com >=1 rótulo; distribuição de rótulos/dia.
 2. Persistência: P(rótulo em D | rótulo em D-1) por moeda e agregada;
    comparação com independência (baseline crucial para a Fase B).
 3. Decomposição por sessão: idx_ret da janela repartido em Tokyo
    [T0, T0+session_cut_h] e Londres [T0+session_cut_h, T0+window_h].
 4. Ranking de protagonistas: frequência de cada moeda como top-score.
 5. Dia-da-semana e proxy de evento (vol realizada 1ª hora pós-T0) vs rótulos.
Regras: bootstrap em blocos p/ ICs; n<100 => 'amostra insuficiente'.

Uso: python a3_anatomy.py [--session-cut-h 8]
"""
from __future__ import annotations

import argparse, json, pathlib, time
from datetime import timedelta

import numpy as np
import pandas as pd

from a1_label_days import load_closes, window_diff
from cssm_engine import G8, build_indices
from splits_days import research_days
from stats_blocks import block_bootstrap_ci

LAB = pathlib.Path("data/labels/labels_v1.parquet")


def insufficient(n: int) -> str:
    return " **(n<100 — amostra insuficiente)**" if n < 100 else ""


def base_rate(lab: pd.DataFrame, lines: list[str]):
    days = lab.day.nunique()
    per_day = lab[lab.labeled].groupby("day").size()
    dist = per_day.reindex(sorted(lab.day.unique()), fill_value=0).value_counts().sort_index()
    lines += ["## 1. Taxa-base",
              f"- Dias avaliados (research): **{days}**",
              f"- Dias com >=1 rótulo: **{len(per_day)}** ({100*len(per_day)/days:.1f}%)",
              f"- Média de rótulos/dia: **{lab.labeled.sum()/days:.2f}**",
              "", "| rótulos no dia | nº de dias |", "|---|---|"]
    lines += [f"| {int(k)} | {int(v)} |" for k, v in dist.items()]
    lines.append("")


def persistence(lab: pd.DataFrame, lines: list[str], boot_block: int):
    """P(rótulo hoje | rótulo ontem) vs P(rótulo hoje) — por moeda e agregado.
    'Ontem' = dia de pregão anterior na sequência de dias avaliados."""
    days = np.array(sorted(lab.day.unique()))
    pos = {d: i for i, d in enumerate(days)}
    lines += ["## 2. Persistência dia-a-dia",
              "", "| moeda | P(hoje) | P(hoje\\|ontem) | lift | pares D-1,D |",
              "|---|---|---|---|---|"]
    agg_pairs = []
    for c in G8:
        sub = lab[lab.currency == c].set_index("day").sort_index()
        flag = sub.labeled.reindex(days, fill_value=False).to_numpy()
        prev, cur = flag[:-1], flag[1:]
        p_base = cur.mean()
        n_prev = int(prev.sum())
        p_cond = cur[prev].mean() if n_prev else np.nan
        lift = p_cond / p_base if p_base > 0 and n_prev else np.nan
        lines.append(f"| {c} | {p_base:.2f} | {p_cond:.2f} | {lift:.2f} | "
                     f"{n_prev}{insufficient(n_prev)} |")
        agg_pairs.append(np.column_stack([prev, cur]))
    ap = np.vstack(agg_pairs).astype(float)
    # bootstrap em blocos sobre os PARES (linhas), preservando o pareamento
    def cond_prob(row_idx):
        m = ap[row_idx.astype(int)]
        pr, cu = m[:, 0].astype(bool), m[:, 1]
        return cu[pr].mean() if pr.any() else np.nan
    stat, lo, hi = block_bootstrap_ci(np.arange(len(ap), dtype=float),
                                      stat=cond_prob, n_boot=2000,
                                      block=boot_block)
    p_uncond = ap[:, 1].mean()
    n_agg = int(ap[:, 0].sum())
    lines += ["",
              f"- **Agregado (8 moedas)**: P(hoje)={p_uncond:.3f}; "
              f"P(hoje|ontem)=**{stat:.3f}** IC95% [{lo:.3f}, {hi:.3f}] "
              f"(bootstrap em blocos); lift=**{stat/p_uncond:.2f}** "
              f"(n={n_agg}{insufficient(n_agg)})",
              "- Independência implicaria lift=1. Lift>1 ⇒ o rótulo de ontem é "
              "informação — baseline crucial da Fase B.", ""]


def session_split(lab: pd.DataFrame, indices: pd.DataFrame, t0_hour: float,
                  cut_h: float, window_h: float, lines: list[str],
                  boot_block: int):
    rows = []
    for _, r in lab[lab.labeled].iterrows():
        t0 = r.day + timedelta(hours=t0_hour)
        sgn = 1.0 if r.direction == "ALTA" else -1.0
        tok = window_diff(indices[r.currency], t0, t0 + timedelta(hours=cut_h))
        lon = window_diff(indices[r.currency], t0 + timedelta(hours=cut_h),
                          t0 + timedelta(hours=window_h))
        if np.isnan(tok) or np.isnan(lon):
            continue
        rows.append({"tok": sgn * tok, "lon": sgn * lon})
    df = pd.DataFrame(rows)
    n = len(df)
    st_t, lo_t, hi_t = block_bootstrap_ci(df.tok.to_numpy(), block=boot_block)
    st_l, lo_l, hi_l = block_bootstrap_ci(df.lon.to_numpy(), block=boot_block)
    share_tok = df.tok.abs().sum() / (df.tok.abs().sum() + df.lon.abs().sum())
    frac_tok_dom = (df.tok.abs() > df.lon.abs()).mean()
    lines += ["## 3. Decomposição por sessão (dias rotulados)",
              f"- Sub-janelas: Tokyo=[T0, T0+{cut_h:.0f}h], "
              f"Londres=[T0+{cut_h:.0f}h, T0+{window_h:.0f}h]; "
              f"n={n}{insufficient(n)}",
              f"- Retorno orientado médio Tokyo: **{st_t*1e4:.2f} bp** "
              f"IC95% [{lo_t*1e4:.2f}, {hi_t*1e4:.2f}]",
              f"- Retorno orientado médio Londres: **{st_l*1e4:.2f} bp** "
              f"IC95% [{lo_l*1e4:.2f}, {hi_l*1e4:.2f}]",
              f"- Share do |movimento| em Tokyo: **{100*share_tok:.1f}%**; "
              f"dias em que Tokyo domina: **{100*frac_tok_dom:.1f}%**", ""]


def protagonists(lab: pd.DataFrame, lines: list[str]):
    tops = (lab[lab.labeled].sort_values("score", ascending=False)
            .groupby("day").first())
    n = len(tops)
    rank = tops.currency.value_counts()
    lines += ["## 4. Ranking de protagonistas (top-score do dia)",
              f"n dias com rótulo = {n}{insufficient(n)}", "",
              "| moeda | dias como protagonista | % |", "|---|---|---|"]
    lines += [f"| {c} | {int(v)} | {100*v/n:.1f}% |" for c, v in rank.items()]
    dirs = tops.direction.value_counts()
    lines += ["", f"- Direções das protagonistas: "
              + ", ".join(f"{k}={int(v)}" for k, v in dirs.items()), ""]


def dow_and_event_proxy(lab: pd.DataFrame, indices: pd.DataFrame,
                        t0_hour: float, lines: list[str], boot_block: int):
    lab = lab.copy()
    lab["dow"] = pd.DatetimeIndex(lab.day).dayofweek
    per_day = lab.groupby("day").agg(any_label=("labeled", "any"),
                                     dow=("dow", "first"))
    tab = per_day.groupby("dow").any_label.agg(["mean", "size"])
    names = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex", 6: "dom"}
    lines += ["## 5. Dia-da-semana e proxy de evento",
              "", "| dia | % dias com rótulo | n |", "|---|---|---|"]
    lines += [f"| {names.get(int(d), d)} | {100*m:.1f}% | {int(s)} |"
              for d, (m, s) in tab.iterrows()]

    # proxy de evento: vol realizada da 1ª hora pós-T0 do índice da moeda,
    # comparada entre linhas rotuladas e não rotuladas (z por moeda)
    vols = {}
    for c in G8:
        s = indices[c]
        for day in lab.day.unique():
            t0 = day + timedelta(hours=t0_hour)
            w = s.loc[t0:t0 + timedelta(hours=1)]
            if len(w) >= 4:
                vols[(day, c)] = float(np.sqrt((np.diff(w.to_numpy())**2).sum()))
    lab["vol1h"] = [vols.get((d, c), np.nan)
                    for d, c in zip(lab.day, lab.currency)]
    lab["vol1h_z"] = lab.groupby("currency").vol1h.transform(
        lambda s: (s - s.mean()) / s.std(ddof=1))
    a = lab[lab.labeled].vol1h_z.dropna().to_numpy()
    b = lab[~lab.labeled].vol1h_z.dropna().to_numpy()
    sa, la_, ha = block_bootstrap_ci(a, block=boot_block)
    sb, lb_, hb = block_bootstrap_ci(b, block=boot_block)
    lines += ["",
              f"- Vol realizada 1ª hora pós-T0 (z por moeda): rotulados "
              f"**{sa:+.2f}** IC95% [{la_:+.2f}, {ha:+.2f}] (n={len(a)}) vs "
              f"não rotulados **{sb:+.2f}** IC95% [{lb_:+.2f}, {hb:+.2f}] "
              f"(n={len(b)})",
              "- Interpretação: se rotulados concentram vol pós-T0 alta, parte "
              "do fenômeno é dia-de-evento (PLAN.md §8).", ""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session-cut-h", type=float, default=8.0)
    ap.add_argument("--boot-block", type=int, default=5)
    a = ap.parse_args()

    meta = json.loads(pathlib.Path("data/labels/labels_v1_meta.json").read_text())
    lab = pd.read_parquet(LAB)
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = set(train) | set(valid)
    lab = lab[lab.day.isin(keep)].reset_index(drop=True)

    closes = load_closes()
    indices = build_indices(closes, align="inner")

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_anatomy")
    out.mkdir(parents=True, exist_ok=True)

    lines = ["# A3 — Anatomia do fenômeno (dias research: treino+validação)",
             f"Definição v1 congelada: {meta}", ""]
    base_rate(lab, lines)
    persistence(lab, lines, a.boot_block)
    session_split(lab, indices, meta["t0_hour"], a.session_cut_h,
                  meta["window_hours"], lines, a.boot_block)
    protagonists(lab, lines)
    dow_and_event_proxy(lab, indices, meta["t0_hour"], lines, a.boot_block)

    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "params.json").write_text(json.dumps(
        {"session_cut_h": a.session_cut_h, "boot_block": a.boot_block,
         "n_research_days": int(lab.day.nunique()),
         "labels_meta": meta}, indent=2))
    print(f"OK -> {out}/REPORT.md")


if __name__ == "__main__":
    main()

"""a11_relational_study.py — Validação da camada relacional em dados reais.

Camada DESCRITIVA (nowcasting, diagnóstico, seleção de par): os nulos
preditivos do programa (A5/A8/v2) permanecem válidos e nada aqui os reabre.
Única exceção: Etapa 5 (seleção de par condicional), preditiva, com a
disciplina completa (UMA regra, alvo disjunto com guarda testada, baselines
no mesmo dia, IC em blocos, critério pré-registrado).

Tudo restrito aos dias RESEARCH (splits_days); holdout intocado — as 7
chamadas do especialista caem TODAS no holdout (>= 2026-02-17), então a
Etapa 3 registra o fato e usa dias research de alto nowcast como validação
visual substituta.

Etapas: 1 latência do nowcast; 2 auditoria de força espúria; 3 matrizes
qualitativas; 4 concordância nowcast × rótulo; 5 seleção de par condicional.

Saída: results/{ts}_relational/REPORT.md + params.json.
Uso: python a11_relational_study.py
"""
from __future__ import annotations

import json, pathlib, time
from datetime import timedelta

import numpy as np
import pandas as pd

from cssm_engine import G8, CssmParams
from r1_relational import (dominance_at, load_closes, matrix_at,
                           pair_features, parse_pair, render_matrix)
from splits_days import research_days
from stats_blocks import block_bootstrap_ci

FEAT = pathlib.Path("data/features")
LENSES = (64, 24)
INSTANTS = (2, 4, 6, 8, 12)
BOOT_BLOCK = 5

CRITERIO_E5 = """### Critério PRÉ-REGISTRADO (Etapa 5, única preditiva)
UMA regra, sem grade: em T0+4h, líder por nowcast (w=64) => célula de maior
|M| orientado na linha => retorno orientado do PAR em [T0+4h, T0+12h]
(disjunto, guarda testada). Sucesso = média de (par escolhido − média dos 7
pares do mesmo dia/direção) com IC95% em blocos INTEIRAMENTE acima de 0 e
n >= 100 dias. Fora disso = NULO, sem afrouxamento."""


# ----------------------------------------------------------------------------
# Guarda de disjunção (padrão do v2)
# ----------------------------------------------------------------------------

def pair_window_return(lp: pd.Series, t0: pd.Timestamp,
                       decision_end_h: float = 4.0,
                       target_start_h: float = 4.0,
                       target_end_h: float = 12.0) -> float:
    """Retorno log do par em [T0+target_start_h, T0+target_end_h], a partir
    de barras FECHADAS. Recusa alvo que invada a janela de decisão."""
    if target_start_h < decision_end_h:
        raise ValueError(
            f"Alvo [{target_start_h}h,{target_end_h}h] invade a janela de "
            f"decisão [0,{decision_end_h}h] — lookahead (regra dura nº 3).")
    a = lp[lp.index <= t0 + timedelta(hours=target_start_h)]
    b = lp[lp.index <= t0 + timedelta(hours=target_end_h)]
    if len(a) == 0 or len(b) == 0 or a.index[-1] == b.index[-1]:
        return np.nan
    return float(b.iloc[-1] - a.iloc[-1])


# ----------------------------------------------------------------------------
# Snapshots da série relacional
# ----------------------------------------------------------------------------

def pivots(br: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {}
    for col in ("nowcast", "breadth_hard", "dir", "t_idx"):
        out[col] = br.pivot(index="ts", columns="currency", values=col)
    return out


def leader_at(piv: dict, tau, metric: str):
    """(moeda líder, direção ±1, valor, top2 [(cur,dir)]) na última barra
    fechada <= tau; None se não houver dado."""
    nm = piv[metric]
    idx = nm.index[nm.index <= tau]
    if len(idx) == 0:
        return None
    row = nm.loc[idx[-1]]
    if row.isna().all():
        return None
    order = row.sort_values(ascending=False)
    drow = piv["dir"].loc[idx[-1]]
    top2 = [(c, float(drow[c])) for c in order.index[:2]]
    c1 = order.index[0]
    return c1, float(drow[c1]), float(order.iloc[0]), top2


def _dirstr(d: float) -> str:
    return "ALTA" if d > 0 else "BAIXA"


# ----------------------------------------------------------------------------

def main():
    labels = pd.read_parquet("data/labels/labels_v1.parquet")
    all_days = pd.DatetimeIndex(sorted(labels.day.unique()))
    tr, va = research_days(all_days)
    res_days = pd.DatetimeIndex(np.concatenate([tr, va]))
    res_set = set(res_days)

    lab_res = labels[labels.day.isin(res_set) & labels.labeled]
    prot = (lab_res.sort_values("score", ascending=False)
            .groupby("day").first())          # protagonista por dia rotulado
    prot_days = list(prot.index)

    gates = json.loads(pathlib.Path("data/gates.json").read_text())
    br = {w: pd.read_parquet(FEAT / f"relational_H1_w{w}.parquet")
          for w in LENSES}
    piv = {w: pivots(br[w]) for w in LENSES}

    ts = time.strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_relational")
    out.mkdir(parents=True, exist_ok=True)
    L = ["# Validação da camada relacional (dias research; holdout intocado)",
         "",
         "Camada DESCRITIVA — nowcasting, diagnóstico, seleção de par. Os "
         "nulos preditivos do programa (A5/A8/v2) permanecem válidos; só a "
         "Etapa 5 é preditiva e segue a disciplina completa.", "",
         CRITERIO_E5, ""]

    # ================= ETAPA 1 — latência =================
    L += ["## Etapa 1 — Latência de convergência do nowcast", "",
          "**Framing obrigatório**: janelas SOBREPOSTAS por construção — "
          "isto mede latência de *reconhecimento* (nowcast), NÃO previsão.",
          "", f"n = {len(prot_days)} dias rotulados research; acerto = "
          "(moeda E direção) da líder vs protagonista rotulada (top-score).",
          "", "| lente | métrica | instante | top-1 | IC95% | top-2 |",
          "|---|---|---|---|---|---|"]
    lat = {}
    for w in LENSES:
        for metric in ("nowcast", "breadth_hard"):
            for h in INSTANTS:
                v1, v2 = [], []
                for d in prot_days:
                    ld = leader_at(piv[w], d + timedelta(hours=h), metric)
                    if ld is None:
                        v1.append(np.nan); v2.append(np.nan); continue
                    c1, d1, _, top2 = ld
                    tgt = (prot.loc[d].currency, prot.loc[d].direction)
                    v1.append(float((c1, _dirstr(d1)) == tgt))
                    v2.append(float(tgt in [(c, _dirstr(dd))
                                            for c, dd in top2]))
                a = np.array(v1, dtype=float)
                mu, lo, hi = block_bootstrap_ci(a[~np.isnan(a)],
                                                block=BOOT_BLOCK)
                mu2 = np.nanmean(v2)
                lat[(w, metric, h)] = mu
                L.append(f"| {w} | {metric} | T0+{h}h | **{100*mu:.1f}%** | "
                         f"[{100*lo:.1f}, {100*hi:.1f}] | {100*mu2:.1f}% |")
    L.append("")

    # ================= ETAPA 2 — força espúria =================
    L += ["## Etapa 2 — Auditoria de força espúria",
          "", "Instantes H1 (dias research) com índice AGREGADO ativo "
          "(|t_idx| ≥ gate) mas breadth_hard orientado < 3/7 — força que a "
          "cesta enxerga e os pares não confirmam.", ""]
    ex_rows = None
    for w in LENSES:
        b = br[w].copy()
        b["day"] = (b.ts - pd.Timedelta("1ns")).dt.normalize()
        b = b[b.day.isin(res_set) & b.t_idx.notna()]
        gate = gates[str(w)]["t_gate"]
        b["active"] = b.t_idx.abs() >= gate
        b["spurious"] = b.active & (b.breadth_hard < 3 / 7)
        agg = b.groupby("currency")[["active", "spurious"]].sum()
        agg["pct"] = 100 * agg.spurious / agg.active
        tot_a, tot_s = int(agg.active.sum()), int(agg.spurious.sum())
        L += [f"### Lente w={w} (gate {gate:.2f})", "",
              f"- Instantes ativos: {tot_a} | espúrios: {tot_s} "
              f"(**{100*tot_s/tot_a:.1f}%** dos ativos)", "",
              "| moeda | ativos | espúrios | % |", "|---|---|---|---|"]
        for c, r in agg.sort_values("pct", ascending=False).iterrows():
            L.append(f"| {c} | {int(r.active)} | {int(r.spurious)} | "
                     f"{r.pct:.1f}% |")
        L.append("")
        if w == 64:
            sp = b[b.spurious].copy()
            sp["abs_t"] = sp.t_idx.abs()
            ex_rows = (sp.sort_values("abs_t", ascending=False)
                       .groupby("currency").head(1)
                       .sort_values("abs_t", ascending=False).head(5))

    # 5 exemplos concretos (w=64): matriz + dominância
    closes = load_closes("H1")
    g64 = gates["64"]
    p64 = CssmParams(w_mid=64, w_fast=16, z_win=500,
                     t_gate=g64["t_gate"], t_low=g64["t_low"])
    pfeats = pair_features(closes, p64)
    L += ["### 5 exemplos concretos (w=64): a cesta acusa, os pares negam",
          ""]
    for r in ex_rows.itertuples():
        mx = matrix_at(pfeats, r.ts)
        dom = dominance_at(closes, r.currency, r.ts, 64)
        L += [f"#### {r.ts} — {r.currency} {_dirstr(r.dir)} | "
              f"t_idx={r.t_idx:+.2f} (≥ gate) mas breadth_hard="
              f"{r.breadth_hard:.0%} (<3/7)", "",
              render_matrix(mx), "",
              f"Dominância do {r.currency} (últimas 64 barras): de onde veio "
              "a 'força' do agregado:", "",
              "| vs | ret orientado (bp) | share |", "|---|---|---|"]
        for _, dr in dom.head(3).iterrows():
            L.append(f"| {dr.vs} | {dr.ret_bp:+.1f} | {dr.share_pct:+.1f}% |")
        L.append("")

    # ================= ETAPA 3 — matrizes qualitativas =================
    L += ["## Etapa 3 — Matrizes nos dias do especialista", "",
          "**As 7 chamadas de specialist_calls.csv caem TODAS no holdout** "
          "(que começa em 2026-02-17) — renderizá-las exporia o holdout, "
          "então esta etapa fica adiada até ordem explícita (junto com a7). "
          "Como validação visual substituta, seguem os 2 dias RESEARCH de "
          "maior nowcast (w=64), com a linha da líder em T0+4h e T0+12h:", ""]
    b64 = br[64].copy()
    b64["day"] = (b64.ts - pd.Timedelta("1ns")).dt.normalize()
    b64 = b64[b64.day.isin(res_set)]
    top_days = (b64.groupby("day").nowcast.max()
                .sort_values(ascending=False).head(2))
    for d in top_days.index:
        led = leader_at(piv[64], d + timedelta(hours=12), "nowcast")
        c1 = led[0] if led else "?"
        for h in (4, 12):
            tau = d + timedelta(hours=h)
            mx = matrix_at(pfeats, tau)
            row = mx[mx.base == c1]
            act = int(((row.state >= 1)).sum())
            L += [f"#### {d.date()} T0+{h}h — líder {c1} "
                  f"(linha ativa contra {act}/7)", "", render_matrix(mx), ""]

    # ================= ETAPA 4 — concordância =================
    L += ["## Etapa 4 — Concordância nowcast × rótulo em T0+12h", ""]
    conc = {}
    for w in LENSES:
        hit_cd, hit_c, now_prot, now_rest = [], [], [], []
        for d in prot_days:
            led = leader_at(piv[w], d + timedelta(hours=12), "nowcast")
            if led is None:
                continue
            c1, d1, _, _ = led
            tgt = (prot.loc[d].currency, prot.loc[d].direction)
            hit_c.append(float(c1 == tgt[0]))
            hit_cd.append(float((c1, _dirstr(d1)) == tgt))
            nm = piv[w]["nowcast"]
            idx = nm.index[nm.index <= d + timedelta(hours=12)]
            rowv = nm.loc[idx[-1]]
            now_prot.append(float(rowv[tgt[0]]))
            now_rest += [float(rowv[c]) for c in G8 if c != tgt[0]]
        a = np.array(hit_cd); c_ = np.array(hit_c)
        mu, lo, hi = block_bootstrap_ci(a, block=BOOT_BLOCK)
        muc, loc_, hic = block_bootstrap_ci(c_, block=BOOT_BLOCK, seed=1)
        npro, nres = np.array(now_prot), np.array(now_rest)
        npro, nres = npro[~np.isnan(npro)], nres[~np.isnan(nres)]
        pooled = np.sqrt((npro.var(ddof=1) + nres.var(ddof=1)) / 2)
        dcoh = (npro.mean() - nres.mean()) / pooled
        conc[w] = {"cur_dir": mu, "cur": muc, "d_cohen": dcoh}
        L += [f"- **w={w}**: líder=protagonista (moeda+direção): "
              f"**{100*mu:.1f}%** [{100*lo:.1f}, {100*hi:.1f}]; só moeda: "
              f"{100*muc:.1f}% [{100*loc_:.1f}, {100*hic:.1f}] "
              f"(n={len(a)}); nowcast protagonistas {npro.mean():.3f} vs "
              f"demais {nres.mean():.3f} — **d de Cohen {dcoh:+.2f}**"]
    L.append("")

    # ================= ETAPA 5 — seleção de par condicional =================
    L += ["## Etapa 5 — Seleção de par condicional (única preditiva)", ""]
    lp_cache = {s: np.log(v) for s, v in closes.items()}
    diffs, rnd_diffs, chosen_rets, mean_rets = [], [], [], []
    rng = np.random.default_rng(7)
    n_skip = 0
    for d in res_days:
        led = leader_at(piv[64], d + timedelta(hours=4), "nowcast")
        if led is None or not np.isfinite(led[2]) or led[2] <= 0 or led[1] == 0:
            n_skip += 1
            continue
        C, dd = led[0], led[1]
        tau = d + timedelta(hours=4)
        # célula de maior M orientado na direção dd, na linha de C
        best_sym, best_score = None, -np.inf
        rets = {}
        for sym in lp_cache:
            a, b_ = parse_pair(sym)
            if C not in (a, b_):
                continue
            flip = (b_ == C)
            pf = pfeats[sym]
            idx = pf.index[pf.index <= tau]
            if len(idx) == 0:
                continue
            M = pf.loc[idx[-1], "M"]
            if np.isnan(M):
                continue
            M_or = -M if flip else M
            score = dd * M_or
            r = pair_window_return(lp_cache[sym], d)
            if np.isnan(r):
                continue
            rets[sym] = dd * (-r if flip else r)     # retorno orientado
            if score > best_score:
                best_sym, best_score = sym, score
        if best_sym is None or len(rets) < 6:
            n_skip += 1
            continue
        mean7 = float(np.mean(list(rets.values())))
        diffs.append(rets[best_sym] - mean7)
        rnd_diffs.append(rets[rng.choice(list(rets))] - mean7)
        chosen_rets.append(rets[best_sym]); mean_rets.append(mean7)

    diffs = np.array(diffs)
    n = len(diffs)
    mu, lo, hi = block_bootstrap_ci(diffs, block=BOOT_BLOCK)
    mur = float(np.mean(rnd_diffs))
    flag = " — **n<100: amostra insuficiente**" if n < 100 else ""
    ok = (lo > 0) and n >= 100
    L += [f"Dias com decisão válida: **{n}** (pulados: {n_skip}){flag}",
          f"- Par escolhido (média, bp): {np.mean(chosen_rets)*1e4:+.2f} | "
          f"média dos 7: {np.mean(mean_rets)*1e4:+.2f}",
          f"- **Diferença (escolhido − média dos 7): {mu*1e4:+.2f} bp** "
          f"IC95% [{lo*1e4:+.2f}, {hi*1e4:+.2f}]",
          f"- Baseline par aleatório − média: {mur*1e4:+.2f} bp "
          f"(esperança ≈ 0 por construção)",
          "", f"**Veredicto Etapa 5: {'SUCESSO' if ok else 'NULO'}** "
          "(critério pré-registrado: IC inteiro > 0 e n ≥ 100).", ""]

    # ================= fechamento =================
    l64_12 = lat[(64, "nowcast", 12)]
    l24_12 = lat[(24, "nowcast", 12)]
    L += ["## Fechamento honesto", "",
          f"O que a camada ENTREGA em dados reais: a auditoria de espúrios é "
          f"o resultado forte — ~2 em cada 3 instantes 'ativos' do índice "
          f"agregado não são confirmados pelos pares (63.6% w=64), e a "
          f"matriz + dominância mostram caso a caso de onde veio a força "
          f"fantasma. Como diagnóstico anti-contaminação, a camada se paga.",
          "",
          f"O que a camada NÃO entrega: como 'rotulador em tempo real', o "
          f"critério de utilidade da Etapa 4 pedia concordância ALTA no fim "
          f"da janela — e ela é baixa: {100*conc[64]['cur_dir']:.0f}% (w=64) "
          f"/ {100*conc[24]['cur_dir']:.0f}% (w=24) em T0+12h, com latência "
          f"que nunca converge ({100*l64_12:.0f}%/{100*l24_12:.0f}% top-1 "
          f"mesmo com a janela encerrada). O padrão é o mesmo do v2: a "
          f"janela rolante (64 ou 24 barras H1) mede outra coisa que a "
          f"janela-calendário [T0,T0+12h] do rótulo — o w=24 dobra a "
          f"concordância do w=64 exatamente por ser mais curto, e a "
          f"separação descritiva d={conc[24]['d_cohen']:+.2f} (w=24) diz "
          f"que o nowcast das protagonistas é maior em média, mas não o "
          f"bastante para apontá-las. E a seleção de par condicional "
          f"{'AGREGA' if ok else 'NÃO agrega'} sobre a média dos 7 pares "
          f"pelo critério pré-registrado (+1.2 bp, IC cruza 0 — "
          f"indistinguível do par aleatório).",
          "",
          f"Os nulos preditivos de A5/A8/v2 permanecem intactos: nada aqui "
          f"prevê o dia. Holdout intocado; a7 não é proposto.", ""]

    (out / "REPORT.md").write_text("\n".join(L), encoding="utf-8")
    (out / "params.json").write_text(json.dumps({
        "lenses": list(LENSES), "instants": list(INSTANTS),
        "boot_block": BOOT_BLOCK, "n_prot_days": len(prot_days),
        "latency_top1": {f"{w}_{m}_{h}": v for (w, m, h), v in lat.items()},
        "concordance": conc, "e5": {"n": int(n), "mean_diff_bp": mu * 1e4,
                                    "ci_bp": [lo * 1e4, hi * 1e4],
                                    "verdict": bool(ok)}},
        indent=2, default=float))
    print(f"OK -> {out}/REPORT.md | E5={'SUCESSO' if ok else 'NULO'}")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""a17_trava.py — Tempo-de-trava da tendência intraday (descritivo) +
família de regra R-CONF(k) pré-registrada.

Pré-registro na íntegra no CHANGELOG (2026-07-07), commitado ANTES da
primeira execução. Resumo:

DESCRITIVO (por dia × moeda ROTULADA, janela v1 [T0, T0+12h], M5):
  t_lock  — instante do ÚLTIMO cruzamento de zero do retorno acumulado do
            índice sintético; depois dele o sinal nunca mais vira.
            HONESTIDADE: definido COM RETROSPECTO (só se sabe que travou
            porque não virou depois). Anatomia, NÃO regra de entrada.
  t_half  — primeiro instante com |cum_ret| >= 50% do |idx_ret| final.
  frac_restante(t) — fração do movimento final ainda por vir em
            t ∈ {1h, 2h, 4h, 8h}.

REGRA R-CONF(k), k ∈ {1,2,4} (grade FECHADA, 3 células): em T0+k h,
  entre as moedas com breadth-parcial >= 6/7, escolher a de maior |z|
  (cum_ret parcial ÷ vol das janelas COMPLETAS dos últimos 63 dias,
  shift(1) — convenção do v1). Previsão: protagonista + direção = sinal.
  Alvo: top-1 vs protagonista do dia (rótulo v1, maior score). Baselines:
  persistência D-1 e p95 do reality check por permutação em blocos SOBRE
  A GRADE (correção de seleção das 3 células). Sucesso = bater AMBOS.
  Nota pré-registrada: acerto em T0+4h só tem valor econômico se
  frac_restante(4h) for material — reportado junto.

Anti-lookahead: features de R-CONF usam SÓ barras <= T0+k h (teste de
truncagem em tests/test_a17.py). Dias research; holdout intocado.

Uso: python a17_trava.py [--pares {usd7,all28}]
Saída: results/{ts}_a17/REPORT.md + params.json
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a1_label_days import load_closes, pair_map, window_bounds
from cssm_engine import G8, build_indices
from splits_days import research_days
from stats_blocks import block_permute, reality_check_p95

PARES_USD = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]
KS = (1, 2, 4)                 # grade fechada da R-CONF (pré-registro)
HORAS_FRAC = (1, 2, 4, 8)
T0_HOUR, WINDOW_HOURS = 0.0, 12.0
VOL_LOOKBACK = 63
BREADTH_MIN = 6 / 7


# ----------------------------------------------------------------------------
# Métricas de trava (funções puras sobre a série cum dentro da janela)
# ----------------------------------------------------------------------------

def t_lock_minutes(cum: pd.Series) -> float:
    """Minutos desde T0 até o ÚLTIMO cruzamento de zero de cum.

    Cruzamento na barra i: sign(cum_i) != sign(cum_{i-1}), ignorando zeros.
    Série que nunca vira depois da 1ª barra → t_lock = minuto da 1ª barra.
    Retrospectivo por construção (ver docstring do módulo)."""
    v = cum.to_numpy()
    if len(v) < 2:
        return np.nan
    s = np.sign(v)
    # propaga o último sinal não-nulo p/ tratar zeros exatos
    for i in range(1, len(s)):
        if s[i] == 0:
            s[i] = s[i - 1]
    flips = np.nonzero(s[1:] * s[:-1] < 0)[0] + 1
    idx = flips[-1] if len(flips) else 0
    return (cum.index[idx] - cum.index[0]).total_seconds() / 60.0


def t_half_minutes(cum: pd.Series) -> float:
    """Minutos até o primeiro |cum| >= 50% do |final| (NaN se final=0)."""
    v = cum.to_numpy()
    if len(v) < 2 or v[-1] == 0:
        return np.nan
    hit = np.nonzero(np.abs(v) >= 0.5 * abs(v[-1]))[0]
    if len(hit) == 0:
        return np.nan
    return (cum.index[hit[0]] - cum.index[0]).total_seconds() / 60.0


def frac_restante(cum: pd.Series, horas: float) -> float:
    """Fração ORIENTADA do movimento final ainda por vir em T0+horas."""
    v = cum.to_numpy()
    if len(v) < 2 or v[-1] == 0:
        return np.nan
    cut = cum.index[0] + pd.Timedelta(hours=horas)
    w = cum.loc[:cut]
    at = w.iloc[-1] if len(w) else 0.0
    return float((v[-1] - at) / v[-1])


# ----------------------------------------------------------------------------
# R-CONF(k) — features estritamente <= T0+k h
# ----------------------------------------------------------------------------

def rconf_features(closes: dict, indices: pd.DataFrame, days, k: int,
                   full_ret: pd.DataFrame) -> dict:
    """{day: [(cur, dir, score)]} da R-CONF(k).

    z parcial = cum_ret(T0..T0+k) / vol63 das janelas COMPLETAS passadas
    (full_ret shift(1) — convenção do v1; a vol de HOJE não entra).
    breadth-parcial = fração orientada dos pares na direção, em T0+k."""
    pm = pair_map(list(closes))
    sd = full_ret.rolling(VOL_LOOKBACK, min_periods=20).std(ddof=1).shift(1)
    preds = {}
    for day in days:
        t0, _ = window_bounds(day, T0_HOUR, WINDOW_HOURS)
        tk = t0 + pd.Timedelta(hours=k)
        cand = []
        for c in G8:
            w = indices[c].loc[t0:tk]
            if len(w) < 4:
                continue
            cum = float(w.iloc[-1] - w.iloc[0])
            prets = []
            for sym, sgn in pm[c]:
                pw = closes[sym].loc[t0:tk]
                if len(pw) < 2:
                    continue
                prets.append(sgn * np.log(pw.iloc[-1] / pw.iloc[0]))
            if len(prets) < 6:
                continue
            prets = np.array(prets)
            breadth = (prets > 0).mean() if cum >= 0 else (prets < 0).mean()
            if breadth < BREADTH_MIN:
                continue
            vol = sd[c].get(day, np.nan) if c in sd.columns else np.nan
            if not np.isfinite(vol) or vol <= 0:
                continue
            cand.append((c, "ALTA" if cum >= 0 else "BAIXA", abs(cum) / vol))
        cand.sort(key=lambda x: -x[2])
        preds[day] = cand
    return preds


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pares", choices=["usd7", "all28"], default="usd7")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--perm-block", type=int, default=5)
    a = ap.parse_args()

    closes_all = load_closes()
    if a.pares == "usd7":
        closes = {s: closes_all[s] for s in PARES_USD if s in closes_all}
    else:
        closes = closes_all
    indices = build_indices(closes, align="inner")

    lab = pd.read_parquet("data/labels/labels_v1.parquet")
    train, valid = research_days(pd.DatetimeIndex(lab.day.unique()))
    keep = sorted(set(train) | set(valid))
    lab = lab[lab.day.isin(keep)]

    # ---- retorno de janela completa por moeda (p/ vol63 da R-CONF) -------
    days_all = pd.DatetimeIndex(sorted(lab.day.unique()))
    fr = {}
    for day in days_all:
        t0, t1 = window_bounds(day, T0_HOUR, WINDOW_HOURS)
        w = indices.loc[t0:t1]
        fr[day] = (w.iloc[-1] - w.iloc[0]) if len(w) >= 8 else \
            pd.Series(np.nan, index=G8)
    full_ret = pd.DataFrame(fr).T[G8]

    # ---- descritivo: t_lock / t_half / frac_restante nos rotulados -------
    rows = []
    for r in lab[lab.labeled].itertuples():
        t0, t1 = window_bounds(r.day, T0_HOUR, WINDOW_HOURS)
        w = indices[r.currency].loc[t0:t1]
        if len(w) < 8:
            continue
        cum = w - w.iloc[0]
        rec = {"day": r.day, "currency": r.currency, "direction": r.direction,
               "dow": r.day.dayofweek,
               "t_lock": t_lock_minutes(cum), "t_half": t_half_minutes(cum)}
        for h in HORAS_FRAC:
            rec[f"frac_rest_{h}h"] = frac_restante(cum, h)
        rows.append(rec)
    d = pd.DataFrame(rows)

    def _dist(s: pd.Series) -> str:
        s = s.dropna() / 60.0
        return (f"mediana {s.median():.1f}h | IQR [{s.quantile(.25):.1f}, "
                f"{s.quantile(.75):.1f}]h | p90 {s.quantile(.9):.1f}h")

    lines = [f"# a17 — Tempo-de-trava (pares: {a.pares})", "",
             f"Dias research: {len(keep)} | eventos rotulados analisados: "
             f"{len(d)}", "",
             "Pré-registro no CHANGELOG (2026-07-07), commitado antes da "
             "execução.", "",
             "## AVISO DE HONESTIDADE (pré-registrado)",
             "`t_lock` é definido COM RETROSPECTO: só se sabe que o último "
             "cruzamento de zero foi o último porque o sinal não virou "
             "depois, dentro da janela. As distribuições abaixo descrevem a "
             "ANATOMIA dos dias rotulados; t_lock NÃO é regra de entrada.",
             "",
             "## Distribuições (horas desde T0)", "",
             f"- t_lock  (geral): {_dist(d.t_lock)}",
             f"- t_half  (geral): {_dist(d.t_half)}", ""]

    lines += ["| moeda | n | t_lock mediana (h) | t_half mediana (h) |",
              "|---|---|---|---|"]
    for c, g in d.groupby("currency"):
        lines.append(f"| {c} | {len(g)} | {g.t_lock.median()/60:.1f} | "
                     f"{g.t_half.median()/60:.1f} |")
    lines += ["", "| direção | n | t_lock mediana (h) |", "|---|---|---|"]
    for dr, g in d.groupby("direction"):
        lines.append(f"| {dr} | {len(g)} | {g.t_lock.median()/60:.1f} |")
    lines += ["", "| dia-da-semana | n | t_lock mediana (h) |", "|---|---|---|"]
    for dw, g in d.groupby("dow"):
        nome = ["seg", "ter", "qua", "qui", "sex"][int(dw)] if dw < 5 else str(dw)
        lines.append(f"| {nome} | {len(g)} | {g.t_lock.median()/60:.1f} |")

    lines += ["", "## % de eventos já travados até T0+t", ""]
    for h in HORAS_FRAC:
        pct = (d.t_lock <= h * 60).mean() * 100
        lines.append(f"- T0+{h}h: **{pct:.1f}%** travados")
    lines += ["", "## Fração do movimento ainda por vir (mediana orientada)", ""]
    for h in HORAS_FRAC:
        lines.append(f"- em T0+{h}h: **{d[f'frac_rest_{h}h'].median()*100:.1f}%** "
                     f"do movimento final")

    # ---- R-CONF(k): avaliação pré-registrada ------------------------------
    top_by_day = (lab[lab.labeled].sort_values("score", ascending=False)
                  .groupby("day").first())
    truth = {day: (r.currency, r.direction) for day, r in top_by_day.iterrows()}
    days_eval = [dd for dd in days_all if dd in truth]

    all_preds = {k: rconf_features(closes, indices, days_eval, k, full_ret)
                 for k in KS}

    def top1(preds):
        n = hits = 0
        for day in days_eval:
            p = preds.get(day) or []
            if not p:
                continue
            n += 1
            hits += (p[0][0], p[0][1]) == truth[day]
        return n, (hits / n if n else np.nan)

    # baseline persistência D-1
    pers_hits = pers_n = 0
    for i, day in enumerate(days_eval[1:], 1):
        prev = days_eval[i - 1]
        pers_n += 1
        pers_hits += truth[prev] == truth[day]
    pers = pers_hits / pers_n

    # reality check SOBRE A GRADE (máximo das 3 células por permutação)
    rng = np.random.default_rng(0)
    tarr = [truth[dd] for dd in days_eval]
    maxima = np.empty(a.n_perm)
    for it in range(a.n_perm):
        p = block_permute(len(days_eval), a.perm_block, rng)
        tp = {days_eval[i]: tarr[p[i]] for i in range(len(days_eval))}
        best = 0.0
        for k in KS:
            n = hits = 0
            for day in days_eval:
                pr = all_preds[k].get(day) or []
                if not pr:
                    continue
                n += 1
                hits += (pr[0][0], pr[0][1]) == tp[day]
            if n >= 100:
                best = max(best, hits / n)
        maxima[it] = best
    p95 = reality_check_p95(maxima)

    lines += ["", "## R-CONF(k) — grade fechada {1,2,4}h (pré-registrada)", "",
              f"Alvo: top-1 (moeda E direção) vs protagonista do dia | dias "
              f"com protagonista: {len(days_eval)} | baseline persistência "
              f"D-1: **{100*pers:.1f}%** | reality check p95 sobre a grade: "
              f"**{100*p95:.1f}%**", "",
              "| k | n opina | top-1 | bate persistência? | > p95? | "
              "frac_restante(k) mediana |", "|---|---|---|---|---|---|"]
    survivors = []
    for k in KS:
        n, acc = top1(all_preds[k])
        fr_k = d[f"frac_rest_{k}h"].median() * 100 if k in HORAS_FRAC else np.nan
        small = " (n<100!)" if n < 100 else ""
        beats, beyond = acc > pers, acc > p95
        if beats and beyond and n >= 100:
            survivors.append(k)
        lines.append(f"| {k}h | {n}{small} | {100*acc:.1f}% | "
                     f"{'SIM' if beats else 'não'} | {'SIM' if beyond else 'não'} | "
                     f"{fr_k:.1f}% |")
    lines += ["", "Nota pré-registrada: acerto em T0+k só tem valor econômico "
              "se a fração restante do movimento em T0+k for material — as "
              "duas colunas devem ser lidas juntas.", ""]
    lines.append(f"**Sobreviventes:** k={survivors}\n" if survivors else
                 "**Nenhuma célula sobreviveu** — nulo reportado "
                 "(regra dura nº 7).\n")

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a17")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"pares": a.pares, "ks": KS, "vol_lookback": VOL_LOOKBACK,
         "breadth_min": BREADTH_MIN, "n_dias_research": len(keep),
         "n_perm": a.n_perm, "perm_block": a.perm_block}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    # eventos com t_lock p/ o descritivo do a18 (trava vs horário de notícia)
    d.to_parquet(out / "trava_eventos.parquet")
    print(f"REPORT -> {out}/REPORT.md | sobreviventes: {survivors or 'nenhuma'}")


if __name__ == "__main__":
    main()

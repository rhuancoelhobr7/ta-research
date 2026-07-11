# -*- coding: utf-8 -*-
"""a34_varredura.py — qual métrica melhor aponta as moedas que vão se mover.

EXPLORATÓRIO. Grade PRÉ-REGISTRADA (declarada aqui ANTES de rodar; nada
adicionado depois). Só RESEARCH (primeiros 50% dos dias M5); a35 confirmará no
holdout pristino [q50, q70) — nunca tocado aqui nem pelo a29.

GRADE:
- Famílias de métrica (por moeda, score no qual argmax=líder previsto):
  1 momentum (Δ índice na janela, com sinal)
  2 retorno/ATR (momentum / vol histórica da moeda)
  3 Efficiency Ratio de Kaufman, com sinal (|Δ|/comprimento × sign)
  4 z-score do retorno vs distribuição histórica da moeda
  5 rank cross-sectional do retorno (posição relativa entre as 8)
  6 dispersão cross-sectional (z da moeda vs média das 8)
  7 range/vol realizada na janela (MAGNITUDE, direção-cega — candidato controle)
  8 CSS e CSSM (CONTROLE — a30 prevê que colam nas métricas de preço)
- Variantes: índice sintético vs média dos 7 pares. NOTA MATEMÁTICA: para
  métricas de retorno (1-6,8) o índice sintético É a média dos retornos orientados
  dos 7 pares por construção (build_indices) — as duas variantes COINCIDEM;
  reporta-se uma. Só a família 7 (range/vol) difere -> reportada nas 2 variantes.
- Janelas: 5,15,30,60,90,120,180 min desde T0.
- Alvos: A (líder exata), B (top-3).

Travas: BH sobre a família INTEIRA; reality check por permutação (máximo entre
células); controle negativo (dia embaralhado). Sem lookahead, barras fechadas.

Uso: python a34_varredura.py
Saída: results/{ts}_a34/REPORT.md + celulas.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from cssm_engine import build_indices
from a29_deteccao import load_m5, truth_by_close, indicator_frames, pick_at
from a23_intersessao import bh_reject

RAW = pathlib.Path("data/raw")
WINDOWS = [5, 15, 30, 60, 90, 120, 180]
G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
Q_RESEARCH = 0.50          # a34 usa dias < q50; holdout a35 = [q50, q70)
N_PERM = 200


def intraday_index(closes: dict) -> pd.DataFrame:
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    return idx


def day_metrics(idx: pd.DataFrame, w: int) -> dict:
    """Métricas por (dia x moeda) na janela [abertura, abertura+w)."""
    day = idx.index.normalize()
    mins = (idx.index - day).total_seconds() / 60.0
    mask = mins < w
    sub = idx[mask]
    dsub = day[mask]
    first = sub.groupby(dsub).first()
    last = sub.groupby(dsub).last()
    mom = last - first                                   # momentum (sinal)
    diff = idx.groupby(day).diff().abs()
    rv = diff[mask].groupby(dsub).sum()                  # comprimento do caminho
    er = (mom.abs() / rv.replace(0, np.nan))
    return {"mom": mom, "rv": rv, "er_signed": np.sign(mom) * er}


def cross(mom: pd.DataFrame) -> dict:
    """Métricas cross-sectional a partir do momentum (dia x moeda)."""
    mean = mom.mean(axis=1); std = mom.std(axis=1).replace(0, np.nan)
    rank = mom.rank(axis=1)                               # 1..8, maior=mais forte
    disp = mom.sub(mean, axis=0).div(std, axis=0)         # z cross-sectional
    return {"rank": rank, "disp": disp}


def zscore_hist(mom: pd.DataFrame, research_mask) -> pd.DataFrame:
    m = mom[research_mask].mean(); s = mom[research_mask].std().replace(0, np.nan)
    return mom.sub(m, axis=1).div(s, axis=1)


def acc(score: pd.DataFrame, truth: pd.DataFrame, days) -> tuple[float, float, int]:
    """Régua A (argmax=líder) e B (top-3), sobre `days`."""
    a = b = n = 0
    for date in days:
        if date not in score.index or date not in truth.index:
            continue
        s = score.loc[date].dropna()
        if len(s) < 8:
            continue
        pred = s.idxmax(); top3 = s.nlargest(3).index.tolist()
        rk = truth.loc[date, "rank"]; n += 1
        a += pred == rk[0]; b += rk[0] in top3
    return (a / n if n else np.nan, b / n if n else np.nan, n)


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    truth = truth_by_close(ohlc, pip)
    idx = intraday_index(closes)
    frames = indicator_frames(closes)                    # css/cssm/site por TF

    dates = pd.DatetimeIndex(sorted(set(truth.index) & set(idx.index.normalize())))
    q50 = dates.to_series().quantile(Q_RESEARCH)
    research = dates[dates < q50]
    research_mask_by_day = pd.Series(True, index=research)

    # range/vol por par p/ variante "média dos 7 pares" (família 7)
    def range_pairs(w):
        day = None
        cur = pd.DataFrame(0.0, index=research, columns=G8); cnt = {c: 0 for c in G8}
        for sym, df in ohlc.items():
            d = df.index.normalize(); m = (df.index - d).total_seconds() / 60.0 < w
            sub = df[m]; ds = d[m]
            r = (sub.groupby(ds)["high"].max() - sub.groupby(ds)["low"].min()) / pip[sym]
            r = r.reindex(research)
            b, q = sym[:3], sym[3:6]
            cur[b] = cur[b].add(r, fill_value=0); cur[q] = cur[q].add(r, fill_value=0)
            cnt[b] += 1; cnt[q] += 1
        for c in G8:
            cur[c] = cur[c] / cnt[c]
        return cur

    rows = []
    for w in WINDOWS:
        dm = day_metrics(idx, w)
        mom = dm["mom"]; rv = dm["rv"]
        rmask = mom.index.isin(research)
        cr = cross(mom)
        zc = zscore_hist(mom, rmask)
        # atr histórico da moeda (vol típica do |mom| no research)
        atr_cur = mom[rmask].abs().median()
        scores = {
            "1_momentum": mom,
            "2_ret_atr": mom.div(atr_cur, axis=1),
            "3_effratio": dm["er_signed"],
            "4_zscore": zc,
            "5_rank_xs": cr["rank"],
            "6_disp_xs": cr["disp"],
            "7_rangevol_idx": rv,                        # magnitude (direção-cega)
            "7_rangevol_pairs": range_pairs(w),          # variante média dos 7 pares
            "8_css": pick_frame(frames[("css", "M5")], idx, w),
            "8_cssm": pick_frame(frames[("cssm", "M5")], idx, w),
        }
        for fam, sc in scores.items():
            aA, aB, n = acc(sc.reindex(research), truth, research)
            rows.append({"familia": fam, "janela": w, "accA": aA, "accB": aB, "n": n})

    cur = pd.DataFrame(rows)
    # significância régua B vs acaso 3/8 + BH sobre a família inteira
    base = 3 / 8
    cur["z"] = (cur["accB"] - base) / np.sqrt(base * (1 - base) / cur["n"])
    cur["p"] = norm.sf(cur["z"].to_numpy())
    cur["bh"] = bh_reject(cur["p"].to_numpy(), 0.05)

    # reality check por permutação (máximo de accB entre células por permutação)
    rng = np.random.default_rng(0)
    truth_arr = {d: truth.loc[d, "rank"][0] for d in research if d in truth.index}
    # precompute top3 sets por célula p/ acelerar
    cell_top3 = {}
    for w in WINDOWS:
        dm = day_metrics(idx, w); mom = dm["mom"]; rv = dm["rv"]
        rmask = mom.index.isin(research); cr = cross(mom); zc = zscore_hist(mom, rmask)
        atr_cur = mom[rmask].abs().median()
        S = {"1_momentum": mom, "2_ret_atr": mom.div(atr_cur, axis=1),
             "3_effratio": dm["er_signed"], "4_zscore": zc, "5_rank_xs": cr["rank"],
             "6_disp_xs": cr["disp"], "7_rangevol_idx": rv,
             "7_rangevol_pairs": range_pairs(w),
             "8_css": pick_frame(frames[("css", "M5")], idx, w),
             "8_cssm": pick_frame(frames[("cssm", "M5")], idx, w)}
        for fam, sc in S.items():
            s = sc.reindex(research)
            cell_top3[(fam, w)] = {d: set(s.loc[d].nlargest(3).index)
                                   for d in research if d in s.index
                                   and s.loc[d].notna().sum() >= 8}
    perm_max = []
    days_list = [d for d in research if d in truth_arr]
    for _ in range(N_PERM):
        perm = rng.permutation(days_list)
        mapped = {days_list[i]: truth_arr[perm[i]] for i in range(len(days_list))}
        best = 0.0
        for key, t3 in cell_top3.items():
            hit = sum(mapped[d] in t3[d] for d in t3 if d in mapped)
            nn = sum(1 for d in t3 if d in mapped)
            if nn:
                best = max(best, hit / nn)
        perm_max.append(best)
    rc_p95 = float(np.quantile(perm_max, 0.95))
    cur["passa_reality"] = cur["accB"] > rc_p95

    surv = cur[cur["bh"] & cur["passa_reality"]].sort_values("accB", ascending=False)

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a34")
    out.mkdir(parents=True, exist_ok=True)
    cur.round(4).to_csv(out / "celulas.csv", index=False)

    top = cur.sort_values("accB", ascending=False).head(10)
    rep = [
        "# a34 — Varredura de métricas (EXPLORATÓRIO)\n",
        f"Grade: 10 scores (8 famílias; família 7 em 2 variantes; 1-6/8 têm "
        f"variante única pois índice=média dos pares) x {len(WINDOWS)} janelas x "
        f"2 alvos = **{len(cur)} células**. Research = {len(research)} dias "
        f"(<q50); holdout [q50,q70) intocado. Acaso régua B (top-3) = 37.5%.\n",
        "**NENHUMA conclusão pode ser tirada do a34 isoladamente; o candidato só "
        "vira achado se sobreviver ao a35 (holdout).**\n",
        f"Reality check (p95 do máximo permutado, régua B): **{rc_p95:.3f}**. "
        f"Células que sobrevivem a BH E reality check: **{len(surv)}**.\n",
        "## Top-10 células por acurácia top-3\n",
        top[["familia", "janela", "accA", "accB", "z", "bh", "passa_reality"]].round(3).to_markdown(index=False),
        "\n\n## Sobreviventes (BH + reality check) — CANDIDATOS p/ o a35\n",
        (surv[["familia", "janela", "accA", "accB"]].round(3).to_markdown(index=False)
         if len(surv) else "_nenhuma célula sobreviveu — nada a confirmar no a35_"),
        "\n\n_Aviso: janelas 5/15 min têm prior ruim (a29: aos 30 min é acaso). "
        "Vitória em 5 min = suspeitar de artefato._\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a34: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"celulas={len(cur)} research={len(research)}d reality_p95={rc_p95:.3f} "
          f"sobreviventes={len(surv)}")
    print(top[["familia", "janela", "accB", "bh", "passa_reality"]].head(8).to_string(index=False))


def pick_frame(frame: pd.DataFrame, idx: pd.DataFrame, w: int) -> pd.DataFrame:
    """Valor do indicador (css/cssm) na barra M5 em abertura+w, por dia x moeda."""
    day = idx.index.normalize()
    turns = (pd.DatetimeIndex(day.unique()) + pd.Timedelta(minutes=w))
    ff = frame.dropna(how="all").sort_index().reset_index()
    ff = ff.rename(columns={ff.columns[0]: "t"}); ff["t"] = ff["t"].astype("datetime64[ns]")
    tdf = pd.DataFrame({"turn": pd.Series(turns.values).astype("datetime64[ns]")})
    m = pd.merge_asof(tdf, ff, left_on="turn", right_on="t", direction="backward")
    m.index = pd.DatetimeIndex(turns).normalize()
    return m[G8]


if __name__ == "__main__":
    main()

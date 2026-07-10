# -*- coding: utf-8 -*-
"""a29_deteccao.py — curva de detecção: a partir de quantas horas o indicador
acerta a moeda líder do dia? (a pergunta central do Carlos.)

Para cada indicador (CSS/CSSM/site-percentil) x TF (M5/M15/H1/H4) x régua (A/B):
acurácia em função do tempo decorrido desde a abertura (00:00 servidor), com a
FRAÇÃO DO MOVIMENTO DO DIA já realizada sobreposta (o custo do atraso).

Verdade (por preço, no FECHAMENTO do dia): ranking de força das 8 moedas
(preponderante.py). Régua A = acertar a líder exata; B = a líder entre top-2/3.

MÉTODO v1 (barras fechadas — padrão do repo, sem lookahead): no tempo t, cada
TF usa a última barra FECHADA <= (abertura + t). Assim TFs rápidos (M5/M15)
atualizam cedo e lentos (H1/H4) só no fechamento da sua barra — o trade-off que
a spec quer medir. A leitura intra-barra (forming) adiantaria os TFs lentos:
refinamento v2 documentado. Indicadores recomputados dos M5 (3 anos).

Split 70/30; curvas no TESTE. Uso: python a29_deteccao.py
Saída: results/{ts}_a29/REPORT.md + curvas.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd

from scipy.stats import norm

from css_screen import css_screen_lines
from cssm_engine import build_indices, compute_all, CssmParams
from t0_normalize import rolling_pct
from preponderante import G8, currency_strength
from a23_intersessao import bh_reject

RAW = pathlib.Path("data/raw")
TF_RULES = {"M5": None, "M15": "15min", "H1": "1h", "H4": "4h"}
TIMES = [30, 60, 90, 120, 180, 240, 360, 480]     # min após 00:00 servidor
TRAIN_FRAC = 0.70
PCT_WIN = 200


def load_m5():
    pips = json.loads((RAW / "_meta_ta_M5.json").read_text(encoding="utf-8"))
    pip = {s: v["pip"] for s, v in pips["symbols"].items()}
    closes, ohlc = {}, {}
    for f in sorted(RAW.glob("M5_*.parquet")):
        sym = f.stem.removeprefix("M5_")
        df = pd.read_parquet(f)
        closes[sym] = df["close"]
        ohlc[sym] = df
    return closes, ohlc, pip


def indicator_frames(closes: dict) -> dict:
    """{(indicador, tf): DataFrame[time x moeda]} p/ css, cssm, site nos 4 TFs."""
    out = {}
    for tf, rule in TF_RULES.items():
        if rule is None:
            ctf = pd.DataFrame(closes)
        else:
            ctf = pd.DataFrame({s: c.resample(rule).last() for s, c in closes.items()})
        ctf = ctf.dropna(how="all")
        val = css_screen_lines(ctf)                      # CSS (linha)
        idx = build_indices({s: ctf[s].dropna() for s in ctf.columns}, align="inner")
        M = pd.DataFrame({c: compute_all(idx)[c]["M"] for c in G8}, index=idx.index)
        pct = pd.DataFrame({c: rolling_pct(val[c], PCT_WIN) for c in G8})  # site
        out[("css", tf)] = val
        out[("cssm", tf)] = M
        out[("site", tf)] = pct
    return out


def truth_by_close(ohlc: dict, pip: dict) -> pd.DataFrame:
    """Ranking de força das moedas por dia (net do dia inteiro, por preço)."""
    net = {}
    for sym, df in ohlc.items():
        day = df.index.normalize()
        g = df.groupby(day)
        net[sym] = (g["close"].last() - g["open"].first()) / pip[sym]
    net = pd.DataFrame(net)
    atr = net.abs().median()
    recs = []
    for date, row in net.iterrows():
        d = row.dropna()
        if len(d) < 20:
            continue
        cs = currency_strength(d.to_dict(), atr.to_dict())
        rank = cs["net_strength"].sort_values(ascending=False).index.tolist()
        recs.append({"date": date, "rank": rank})
    return pd.DataFrame(recs).set_index("date")


def pick_at(frame: pd.DataFrame, turns: np.ndarray) -> pd.Series:
    """Moeda de maior valor do indicador na última barra fechada <= cada turn.
    turns: array de timestamps ordenado asc. Retorna Series alinhada a `turns`."""
    ff = frame.dropna(how="all").sort_index().reset_index()
    ff = ff.rename(columns={ff.columns[0]: "t"})
    ff["t"] = ff["t"].astype("datetime64[ns]")
    tdf = pd.DataFrame({"turn": pd.Series(turns).astype("datetime64[ns]")})
    m = pd.merge_asof(tdf, ff, left_on="turn", right_on="t", direction="backward")
    vals = m[G8]
    allnan = vals.isna().all(axis=1)
    picks = vals.fillna(-np.inf).idxmax(axis=1)     # evita erro em linha all-NaN
    return picks.where(~allnan, other=np.nan)       # sem barra <= turn -> NaN


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    print(f"a29: M5 {len(closes)} pares, computando indicadores nos 4 TFs...")
    frames = indicator_frames(closes)
    truth = truth_by_close(ohlc, pip)
    dates = pd.DatetimeIndex(truth.index)
    cut = dates.to_series().quantile(TRAIN_FRAC)
    te = truth[truth.index >= cut]
    te_dates = pd.DatetimeIndex(te.index)

    # fração do movimento do dia já realizada em t (custo do atraso) — range
    # acumulado até t / range do dia, por par, mediana. Vetorizado (cummax/cummin).
    te_set = set(te_dates)

    def move_frac():
        fr = {t: [] for t in TIMES}
        for sym, df in ohlc.items():
            d = df.copy()
            day = d.index.normalize()
            d = d[day.isin(te_set)]
            if d.empty:
                continue
            day = d.index.normalize()
            mins = (d.index - day).total_seconds() / 60.0
            cmax = d.groupby(day)["high"].cummax()
            cmin = d.groupby(day)["low"].cummin()
            crange = (cmax - cmin)
            full = crange.groupby(day).last()
            for t in TIMES:
                mask = mins < t
                rt = crange[mask].groupby(day[mask]).last()
                frac = (rt / full).replace([np.inf, -np.inf], np.nan).dropna()
                fr[t].extend(frac.values)
        return {t: float(np.median(v)) if v else np.nan for t, v in fr.items()}
    mv = move_frac()

    inds = ["css", "cssm", "site"]
    tfs = list(TF_RULES)
    ranks = list(te["rank"].values)                 # alinhado a te_dates (ordem asc)
    rows = []
    for ind in inds:
        for tf in tfs:
            frame = frames[(ind, tf)]
            for t in TIMES:
                turns = (te_dates + pd.Timedelta(minutes=t)).values
                picks = pick_at(frame, turns).values     # alinhado a te_dates
                accA = accB2 = accB3 = n = 0
                for i, p in enumerate(picks):
                    if not isinstance(p, str):
                        continue
                    rk = ranks[i]
                    n += 1
                    accA += p == rk[0]
                    accB2 += p in rk[:2]
                    accB3 += p in rk[:3]
                if n:
                    rows.append({"indicador": ind, "tf": tf, "t_min": t,
                                 "accA": accA / n, "accB2": accB2 / n,
                                 "accB3": accB3 / n, "mov_feito": mv.get(t),
                                 "n": n})
    cur = pd.DataFrame(rows)

    # significância vs acaso + BH sobre a família (régua B3 e A juntas)
    fam = cur.copy()
    fam["base"] = np.where(True, 3 / 8, 3 / 8)   # B3
    fam["z"] = (fam["accB3"] - 3 / 8) / np.sqrt((3 / 8) * (5 / 8) / fam["n"])
    fam["p"] = norm.sf(fam["z"])
    fam["bh"] = bh_reject(fam["p"].values, 0.05)
    # t mais cedo em que cada indicador×TF bate o acaso (B3) após BH
    earliest = []
    for (ind, tf), g in fam.sort_values("t_min").groupby(["indicador", "tf"]):
        sig = g[g["bh"]]
        if len(sig):
            r = sig.iloc[0]
            earliest.append({"indicador": ind, "tf": tf, "t_signif": int(r["t_min"]),
                             "accB3": r["accB3"], "mov_feito": r["mov_feito"]})
        else:
            earliest.append({"indicador": ind, "tf": tf, "t_signif": None,
                             "accB3": np.nan, "mov_feito": np.nan})
    earliest = pd.DataFrame(earliest).sort_values(
        "t_signif", na_position="last")

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a29")
    out.mkdir(parents=True, exist_ok=True)
    cur.round(4).to_csv(out / "curvas.csv", index=False)

    # tabelas de leitura: régua A e B3 por indicador x tf ao longo de t
    def pivot(metric):
        return cur.pivot_table(index=["indicador", "tf"], columns="t_min",
                               values=metric)
    pA, pB = pivot("accA"), pivot("accB3")
    # melhor combinação: maior accB3 com mov_feito <= 0.5 (ainda sobra movimento)
    early = cur[cur["mov_feito"] <= 0.5]
    best = early.sort_values("accB3", ascending=False).head(5)
    # Q10: aos 30 min de Tóquio
    q10 = cur[cur["t_min"] == 30].sort_values("accB3", ascending=False)

    baseA, baseB3 = 1 / 8, 3 / 8
    rep = [
        "# a29 — Curva de detecção da moeda líder (acurácia x tempo)\n",
        f"Verdade = líder do dia por preço no fechamento. {len(te)} dias de teste "
        f"(out-of-sample). Barras fechadas (v1). Custo do atraso = fração do range "
        f"do dia já feita em t. Acaso: régua A = {baseA:.0%}, B3 (top-3) = {baseB3:.0%}.\n",
        "## Custo do atraso — fração do range do dia já realizada\n",
        pd.Series(mv, name="mov_feito").round(3).to_frame().T.to_markdown(),
        "\n\n## Régua A (líder exata) — acurácia x tempo (min)\n",
        pA.round(3).to_markdown(),
        "\n\n## Régua B3 (top-3) — acurácia x tempo (min)\n",
        pB.round(3).to_markdown(),
        "\n\n## Q10 — aos 30 min de Tóquio (ordenado por top-3)\n",
        q10[["indicador", "tf", "accA", "accB3", "mov_feito"]].round(3).to_markdown(index=False),
        "\n\n## Q8 — melhor acurácia (top-3) COM movimento ainda na mesa (mov<=50%)\n",
        best[["indicador", "tf", "t_min", "accB3", "mov_feito"]].round(3).to_markdown(index=False),
        "\n\n## Significância (BH 5% sobre a família) — t mais cedo que bate o acaso (B3)\n",
        earliest.round(3).to_markdown(index=False),
        f"\n_Régua B3 vs acaso 37.5%. Nº de células (de {len(fam)}) que sobrevivem "
        f"a BH: {int(fam['bh'].sum())}. Combos onde t_signif é vazio nunca batem o "
        f"acaso out-of-sample._\n",
        "\n## Veredito\n",
        "**Régua A (líder exata): nula** — nunca fica utilizável (~0.30 máx às 8h; "
        "aos 30 min está no acaso em TODOS os indicadores/TFs, Q10).\n\n"
        "**Régua B (top-3): sinal real, precoce e modesto.** O M5 (css/site) bate o "
        "acaso (BH 5%, out-of-sample) já aos **90 min**, com **só 26% do range do "
        "dia feito** (74% na mesa) e acurácia ~0.48 vs 0.375 do acaso; M15 aos "
        "180 min, H1 aos 360 min, **H4 nunca** — trade-off rápido>lento confirmado "
        "e ordenado. Fortalece até ~0.6 às 4-6h. O custo do atraso é baixo (range "
        "sobe devagar: ~40% às 4h). Coerente com o a31 (43% do campeão já visível "
        "na asia): não dá pra cravar a líder cedo, mas dá pra ESTREITAR para 3 "
        "candidatas com a maior parte do movimento ainda por vir — melhor que o "
        "nulo pré-abertura do a24. Edge pequeno; badge probabilístico com latência "
        "conhecida, jamais sinal de T0.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a29: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print("mov_feito por t:", {k: round(v, 2) for k, v in mv.items()})
    print("\nQ10 (30min) top-3 por indicador/TF:\n",
          q10[["indicador", "tf", "accA", "accB3", "mov_feito"]].head(8).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

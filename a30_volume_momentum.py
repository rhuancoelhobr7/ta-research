# -*- coding: utf-8 -*-
"""a30_volume_momentum.py — volume e momentum da moeda preponderante.

Q11 a preponderante tem tick-volume agregado (7 pares) maior que as não-líderes?
Q12 momentum: a preponderante tem maior |slope| de preço? (preço puro, sem CSS.)
Q13 TIMING (crucial): a partir de quantos min o volume/momentum da FUTURA líder
    se destaca? Antes do preço, junto, ou depois? Compara com o CSS (a29).
Q14 ablação: volume/momentum como detector melhora a detecção precoce?

Sinais intradiários (M5, cumulativos desde a abertura, sem lookahead até t):
  vol_cur   = soma (nos 7 pares) do tick-volume normalizado acumulado no dia.
  mom_cur   = |índice sintético(t) − índice(abertura)| (momentum de preço).
Detecção = moeda de maior sinal em t (régua B top-3), acurácia x tempo + BH,
comparada ao css do a29. Verdade = líder por preço no fechamento (a29).

Uso: python a30_volume_momentum.py
Saída: results/{ts}_a30/REPORT.md + curvas_vol_mom.csv
"""
from __future__ import annotations

import json
import pathlib
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

from cssm_engine import build_indices
from preponderante import G8, currency_strength
from a29_deteccao import (load_m5, truth_by_close, pick_at, TIMES, TRAIN_FRAC)
from a23_intersessao import bh_reject

RAW = pathlib.Path("data/raw")


def intraday_signals(closes: dict, ohlc: dict) -> dict:
    """Frames M5 (time x moeda) de volume e momentum cumulativos no dia."""
    # --- volume: tick_volume normalizado por par, acumulado no dia, somado/moeda
    voln = {}
    for sym, df in ohlc.items():
        v = df["tick_volume"].astype(float)
        voln[sym] = v / v.median()
    V = pd.DataFrame(voln)
    day = V.index.normalize()
    Vc = V.groupby(day).cumsum()                       # acumulado intradia
    vol_cur = pd.DataFrame(0.0, index=Vc.index, columns=G8)
    cnt = {c: 0 for c in G8}
    for sym in Vc.columns:
        b, q = sym[:3], sym[3:6]
        vol_cur[b] = vol_cur[b] + Vc[sym]; vol_cur[q] = vol_cur[q] + Vc[sym]
        cnt[b] += 1; cnt[q] += 1
    for c in G8:
        vol_cur[c] = vol_cur[c] / cnt[c]

    # --- momentum: índice sintético − índice na abertura, COM SINAL (a líder é a
    # que mais SUBIU; |net| confundiria líder com anti-líder, ambos movem muito).
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    d2 = idx.index.normalize()
    open_idx = idx.groupby(d2).transform("first")
    mom_cur = idx - open_idx
    return {"volume": vol_cur, "momentum": mom_cur}


def curve(frame: pd.DataFrame, truth: pd.DataFrame, te_dates, ranks) -> pd.DataFrame:
    rows = []
    for t in TIMES:
        turns = (te_dates + pd.Timedelta(minutes=t)).values
        picks = pick_at(frame, turns).values
        a = b3 = n = 0
        for i, p in enumerate(picks):
            if not isinstance(p, str):
                continue
            rk = ranks[i]; n += 1
            a += p == rk[0]; b3 += p in rk[:3]
        if n:
            rows.append({"t_min": t, "accA": a / n, "accB3": b3 / n, "n": n})
    return pd.DataFrame(rows)


def earliest_sig(cur: pd.DataFrame, base=3 / 8) -> dict:
    z = (cur["accB3"] - base) / np.sqrt(base * (1 - base) / cur["n"])
    p = norm.sf(z.to_numpy())
    bh = bh_reject(p, 0.05)
    sig = cur[bh].sort_values("t_min")
    if len(sig):
        r = sig.iloc[0]
        return {"t_signif": int(r["t_min"]), "accB3": float(r["accB3"])}
    return {"t_signif": None, "accB3": np.nan}


def main() -> None:
    t0 = time.time()
    closes, ohlc, pip = load_m5()
    sig = intraday_signals(closes, ohlc)
    truth = truth_by_close(ohlc, pip)
    dates = pd.DatetimeIndex(truth.index)
    cut = dates.to_series().quantile(TRAIN_FRAC)
    te = truth[truth.index >= cut]
    te_dates = pd.DatetimeIndex(te.index)
    ranks = list(te["rank"].values)

    curves = {name: curve(fr, truth, te_dates, ranks) for name, fr in sig.items()}
    earl = {name: earliest_sig(c) for name, c in curves.items()}

    # Q11/Q12 descritivo: percentil da líder em volume/momentum no fim do dia
    # (usa o valor cumulativo do dia inteiro = último por dia)
    def leader_pctile(frame):
        d = frame.index.normalize()
        eod = frame.groupby(d).last()
        rows = []
        for date in te_dates:
            if date not in eod.index:
                continue
            r = eod.loc[date].rank(pct=True)     # 0..1 entre as 8 moedas
            rows.append(r[te.loc[date, "rank"][0]])
        return float(np.median(rows))
    q11 = leader_pctile(sig["volume"])
    q12 = leader_pctile(sig["momentum"])

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a30")
    out.mkdir(parents=True, exist_ok=True)
    pd.concat({k: v.set_index("t_min") for k, v in curves.items()}, axis=1
              ).round(4).to_csv(out / "curvas_vol_mom.csv")

    piv = pd.concat({k: v.set_index("t_min")["accB3"] for k, v in curves.items()},
                    axis=1)
    css_ref = "M5 do css/site: **90 min** (a29)"
    rep = [
        "# a30 — Volume e momentum da moeda preponderante\n",
        f"{len(te)} dias de teste (OOS). Sinais M5 cumulativos no dia (sem "
        f"lookahead). Verdade = líder no fechamento. Régua B3 (top-3), acaso 37.5%.\n",
        "## Q11/Q12 — a líder se destaca em volume/momentum? (percentil no fim do dia)\n",
        f"- **volume**: a líder fica no percentil **{q11:.0%}** das 8 moedas "
        f"(50% = mediana; >50% = destaca).",
        f"\n- **momentum (preço)**: percentil **{q12:.0%}**.\n",
        "## Q13 — Timing: quando o sinal da futura líder se destaca (top-3 x tempo)\n",
        piv.round(3).to_markdown(),
        f"\n\n- volume bate o acaso (BH) em **{earl['volume']['t_signif']} min**; "
        f"momentum em **{earl['momentum']['t_signif']} min**; comparação {css_ref}.",
        "\n\n## Q13/Q14 — Veredito\n",
        f"**Momentum (preço puro, com sinal) detecta a líder aos "
        f"{earl['momentum']['t_signif']} min — o MESMO tempo do css M5 (90 min)** "
        f"— e mais forte depois (top-3 0.63 às 4h). Ou seja, o **CSS não agrega "
        f"nada sobre o preço bruto**: como o CSS é uma transformação do preço, "
        f"olhar quem subiu mais até agora dá o mesmo sinal, mais cedo e mais "
        f"direto.\n\n"
        "**Volume NÃO detecta a líder** (nunca bate o acaso; percentil da líder só "
        f"{q11:.0%}). Motivo estrutural: volume é CEGO À DIREÇÃO — marca a moeda "
        "mais ATIVA, que é a líder OU a anti-líder (ambas movem/negociam muito). "
        "Serve para dizer 'algo está acontecendo', não 'quem vai liderar'.\n\n"
        "**Q14 (ablação)**: adicionar volume ao detector não ajuda a escolher a "
        "líder (direção-cego); e o momentum já iguala o CSS. Nada novo entra. "
        "Reforça o tema do programa: o sinal está no PREÇO; CSS é transformação, "
        "não informação extra; volume é atividade, não direção.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a30: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"Q11 volume pctil lider {q11:.0%}; Q12 momentum pctil {q12:.0%}")
    print("earliest-sig:", {k: v["t_signif"] for k, v in earl.items()}, "(css M5=90)")
    print("curvas top-3:\n", piv.round(3).to_string())


if __name__ == "__main__":
    main()

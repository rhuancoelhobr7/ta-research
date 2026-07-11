# -*- coding: utf-8 -*-
"""a37_vol_pareado.py — fecha o caveat do a26b: controle PAREADO por volatilidade.

O a26b achou que sob alinhamento do CSS o movimento persiste (MFE 1.45× o
controle), mas o controle era barras não-alinhadas SEM parear volatilidade —
parte do 1.45× pode ser puro clustering de volatilidade. Aqui, cada evento de
alinhamento é pareado a um controle NÃO-alinhado com volatilidade PRÉVIA
semelhante (matching por decil de range das barras anteriores, por par).

Pergunta: sobra incremento do CSS depois do pareamento? Se sumir, o "badge de
confirmação concorrente" cai e o CSS fica APENAS descritivo.

Uso: python a37_vol_pareado.py [--thr 70] [--win 16]
Saída: results/{ts}_a37/REPORT.md
"""
from __future__ import annotations

import argparse
import pathlib
import time

import numpy as np
import pandas as pd

from sessions import server_to_utc
from a26b_persistencia import load_pips, load_pct
from stats_blocks import block_bootstrap_ci

RAW = pathlib.Path("data/raw")
G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
NBINS = 10


def pair_events(sym, pip, pct15, pctH1, thr, win):
    """Devolve (aligned, nonaligned) como listas de (prior_vol, mfe)."""
    ohlc = pd.read_parquet(RAW / f"M15_{sym}.parquet")
    b, q = sym[:3], sym[3:6]
    df = ohlc.join(pct15[[b, q]].rename(columns={b: "pb15", q: "pq15"}), how="inner")
    h1 = pctH1[[b, q]].rename(columns={b: "pbH1", q: "pqH1"}).reindex(df.index, method="pad")
    df = df.join(h1).dropna(subset=["pb15", "pq15", "pbH1", "pqH1"])
    sep15 = (df["pb15"] - df["pq15"]).to_numpy()
    sepH1 = (df["pbH1"] - df["pqH1"]).to_numpy()
    aligned = (np.abs(sep15) >= thr) & (np.abs(sepH1) >= thr) & \
              (np.sign(sep15) == np.sign(sepH1))
    onset = aligned & ~np.r_[False, aligned[:-1]]
    direction = np.sign(sep15)
    close = df["close"].to_numpy(); high = df["high"].to_numpy(); low = df["low"].to_numpy()
    # volatilidade PRÉVIA: range das `win` barras anteriores (causal), em pips
    hi_prev = pd.Series(high).rolling(win).max().shift(1).to_numpy()
    lo_prev = pd.Series(low).rolling(win).min().shift(1).to_numpy()
    prior_vol = (hi_prev - lo_prev) / pip

    def mfe(t):
        d = direction[t]
        if d == 0:
            return np.nan
        if d > 0:
            return (high[t + 1:t + 1 + win].max() - close[t]) / pip
        return (close[t] - low[t + 1:t + 1 + win].min()) / pip

    al, non = [], []
    N = len(close)
    for t in range(win, N - win):
        if np.isnan(prior_vol[t]):
            continue
        m = mfe(t)
        if np.isnan(m):
            continue
        if onset[t]:
            al.append((prior_vol[t], m))
        elif not aligned[t] and t % 7 == 0:      # subamostra o pool de controle
            non.append((prior_vol[t], m))
    return al, non


def match_control(al: pd.DataFrame, non: pd.DataFrame, seed: int = 0) -> np.ndarray:
    """Controle pareado: p/ cada evento alinhado, amostra um mfe de controle do
    MESMO bin de volatilidade prévia (`bin` já atribuído)."""
    rng = np.random.default_rng(seed)
    matched = []
    for bn, g in al.groupby("bin"):
        pool = non[non["bin"] == bn]["mfe"].to_numpy()
        if len(pool):
            matched.append(rng.choice(pool, size=len(g), replace=True))
    return np.concatenate(matched) if matched else np.array([])


def main(thr, win):
    t0 = time.time()
    pips = load_pips()
    pct15, pctH1 = load_pct("M15"), load_pct("H1")
    AL, NON = [], []
    for f in sorted(RAW.glob("M15_*.parquet")):
        sym = f.stem.removeprefix("M15_")
        al, non = pair_events(sym, pips[sym], pct15, pctH1, thr, win)
        AL += al; NON += non
    al = pd.DataFrame(AL, columns=["vol", "mfe"])
    non = pd.DataFrame(NON, columns=["vol", "mfe"])

    # bins de volatilidade prévia (quantis do pool alinhado)
    edges = np.quantile(al["vol"], np.linspace(0, 1, NBINS + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    al["bin"] = pd.cut(al["vol"], edges, labels=False)
    non["bin"] = pd.cut(non["vol"], edges, labels=False)

    # controle NÃO pareado (média simples) e PAREADO (por decil de vol)
    ctrl_unmatched = non["mfe"].median()
    ctrl_matched = match_control(al, non, seed=0)

    al_mfe = al["mfe"].to_numpy()
    s_al, lo_al, hi_al = block_bootstrap_ci(al_mfe, np.median, block=5, n_boot=3000)
    s_cm, lo_cm, hi_cm = block_bootstrap_ci(ctrl_matched, np.median, block=5, n_boot=3000)
    ratio_unmatched = s_al / ctrl_unmatched
    ratio_matched = s_al / s_cm
    # médias de vol p/ mostrar o pareamento
    vol_al = al["vol"].median(); vol_non = non["vol"].median()

    survives = ratio_matched > 1.15

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_a37")
    out.mkdir(parents=True, exist_ok=True)

    rep = [
        "# a37 — a26b com controle PAREADO por volatilidade\n",
        f"Alinhamento |pct_base−pct_quote|>=%d em M15 E H1; janela %d barras. "
        f"{len(al):,} eventos alinhados, {len(non):,} controles (subamostrados). "
        f"Pareamento por decil de range das %d barras anteriores.\n" % (thr, win, win),
        "## Volatilidade prévia (mediana de range das barras anteriores, pips)\n",
        f"- alinhados: **{vol_al:.1f}** vs controle bruto: **{vol_non:.1f}** — "
        f"{'alinhamento OCORRE em regime mais volátil (o pareamento importa)' if vol_al > 1.1*vol_non else 'vol parecida'}.\n",
        "## MFE (excursão favorável, pips) e razão\n",
        f"- alinhado: **{s_al:.1f}** IC[{lo_al:.1f}, {hi_al:.1f}]",
        f"\n- controle NÃO pareado: {ctrl_unmatched:.1f} → razão **{ratio_unmatched:.2f}×** (o número do a26b)",
        f"\n- controle PAREADO por vol: **{s_cm:.1f}** IC[{lo_cm:.1f}, {hi_cm:.1f}] → "
        f"razão **{ratio_matched:.2f}×**\n",
        "## Veredito\n",
        (f"O incremento do CSS **SOBREVIVE** ao pareamento (razão {ratio_matched:.2f}× "
         f"> 1.15): o alinhamento agrega além do clustering de volatilidade. Badge "
         f"de confirmação concorrente MANTIDO (probabilístico).\n" if survives else
         f"O incremento do CSS **SOME** após parear por volatilidade (razão "
         f"{ratio_matched:.2f}× vs {ratio_unmatched:.2f}× não pareado). O 1.45× do "
         f"a26b era sobretudo CLUSTERING DE VOLATILIDADE, não valor do CSS. O badge "
         f"de 'confirmação concorrente' CAI — o CSS fica APENAS descritivo. "
         f"Atualizar INDICATOR_CHANGELOG e a proposta de badge.\n"),
    ]
    (out / "REPORT.md").write_text("\n".join(rep), encoding="utf-8")
    print(f"a37: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    print(f"vol alinhado={vol_al:.1f} vs controle={vol_non:.1f}")
    print(f"MFE alinhado={s_al:.1f} | ctrl bruto={ctrl_unmatched:.1f} ({ratio_unmatched:.2f}x) "
          f"| ctrl PAREADO={s_cm:.1f} ({ratio_matched:.2f}x)")
    print("VEREDITO:", "incremento SOBREVIVE" if survives else "incremento SOME (CSS so descritivo)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--thr", type=float, default=70)
    ap.add_argument("--win", type=int, default=16)
    a = ap.parse_args()
    main(a.thr, a.win)

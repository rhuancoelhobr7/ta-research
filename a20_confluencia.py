# -*- coding: utf-8 -*-
"""a20_confluencia.py — Confluência multi-timeframe do CSS (MN/W1/D1/H4/H1).

Pré-registro no CHANGELOG (2026-07-08). Lente causal (css_screen).

CAVEAT MECÂNICO (registrado antes de tudo): a soma das 8 forças ≈ 0 por
construção — confluência "X forte em tudo, Y fraca em tudo" tem parte
tautológica. Baseline OBRIGATÓRIO: block-shuffle (blocos = dias) dos
estados vs alvos; só é padrão o que exceder o p95 embaralhado.

ESTADOS por barra FECHADA de H1, para a moeda MAIS FORTE no ranking D1
(orientação = sinal do val_D1; fases do ciclo espelho quando negativo):
  alinh_sinal  — nº de TFs (0–5) com sinal de val == sinal do D1
  alinh_box    — nº de TFs com |val| >= box E sinal == sinal do D1
  cascata      — (D1 ou W1 em FORÇA) E (H1 ou H4 em EXPANSÃO) orientadas
  divergencia  — D1 em FORÇA E H1 em EXAUSTÃO/FRAQUEZA orientadas

ALVO (definido AGORA): par = mais forte vs mais fraca no ranking D1 em t;
movimento = |log-retorno| do par em 24h e 72h ÷ vol H1 (média móvel de
|Δlog| em 100 barras, shift(1)); GRANDE = quartil superior, calculado SÓ
no split de exploração (primeiros 70% dos dias). Métrica: lift =
P(grande | estado) / P(grande).

Q7 monotonia do lift por alinhamento; Q8 cascata vs alinhamento; Q9
lead-lag de EXPANSÃO H1→H4/D1; Q10 contagem de eventos W1/MN (honestidade
sobre poder); Q11 tudo com breadth>=3/7. Validação 70/30 temporal.

GATE: só executar após paridade MQ5×Python (p2_css_parity) confirmada.

Uso: python a20_confluencia.py
Saída: results/{ts}_a20/REPORT.md + params.json
"""
from __future__ import annotations

import argparse, json, pathlib, time

import numpy as np
import pandas as pd

from a19_fases import (TF_RULES, breadth_hard, classify_phases,
                       grid_tf, load_h1_closes)
from css_classic import G8
from css_screen import BOX, css_screen_lines

TFS = ["H1", "H4", "D1", "W1", "MN"]
TF_HOURS = {"H1": 1, "H4": 4, "D1": 24, "W1": 168, "MN": 720}
HORIZONS_H = (24, 72)
VOL_WIN = 100
N_SHUFFLE = 200


def align_closed(df: pd.DataFrame, tf: str, h1_idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Valor do último bar do TF FECHADO até o fim da barra H1 t.

    Barra do TF carimbada s fecha em s+dur; conhecida na barra H1 t
    (que fecha em t+1h) sse s+dur <= t+1h. Reindexação por asof do índice
    deslocado."""
    dur = pd.Timedelta(hours=TF_HOURS[tf])
    shifted = df.copy()
    shifted.index = shifted.index + dur - pd.Timedelta(hours=1)
    return shifted.reindex(h1_idx, method="ffill")


def oriented_phase(ph_buy: pd.DataFrame, ph_sell: pd.DataFrame,
                   sign_ref: pd.DataFrame) -> pd.DataFrame:
    """Fase orientada: ciclo comprador se sinal_ref>0, espelho se <0."""
    return ph_buy.where(sign_ref > 0, ph_sell)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-shuffle", type=int, default=N_SHUFFLE)
    a = ap.parse_args()
    rng = np.random.default_rng(0)

    h1 = load_h1_closes()
    h1_idx = h1.index

    # ---- linhas, fases (buy+sell) e breadth por TF, alinhadas ao H1 ------
    val, phb, phs, brd = {}, {}, {}, {}
    for tf in TFS:
        g = grid_tf(h1, tf)
        lines = css_screen_lines(g)
        val[tf] = align_closed(lines, tf, h1_idx)
        phb[tf] = align_closed(classify_phases(lines), tf, h1_idx)
        phs[tf] = align_closed(classify_phases(lines, mirror=True), tf, h1_idx)
        brd[tf] = align_closed(breadth_hard(g, lines), tf, h1_idx)

    d1v = val["D1"]
    strongest = d1v.idxmax(axis=1)
    weakest = d1v.idxmin(axis=1)
    sgn = np.sign(d1v)

    # fases orientadas pela direção do D1 da própria moeda
    pho = {tf: oriented_phase(phb[tf], phs[tf], sgn) for tf in TFS}

    # ---- features de confluência da moeda mais forte ----------------------
    rows = {}
    stack_val = {tf: val[tf].stack() for tf in TFS}
    idx_pairs = list(zip(h1_idx, strongest))
    for name in ("alinh_sinal", "alinh_box", "cascata", "diverg", "brd_ok"):
        rows[name] = np.zeros(len(h1_idx))
    sref = np.array([d1v.at[t, c] if pd.notna(c) else np.nan
                     for t, c in idx_pairs])
    for i, (t, c) in enumerate(idx_pairs):
        if pd.isna(c) or not np.isfinite(sref[i]) or sref[i] == 0:
            rows["alinh_sinal"][i] = np.nan
            continue
        s = np.sign(sref[i])
        vs = [val[tf].at[t, c] for tf in TFS]
        rows["alinh_sinal"][i] = sum(np.sign(v) == s for v in vs
                                     if np.isfinite(v))
        rows["alinh_box"][i] = sum((abs(v) >= BOX) and (np.sign(v) == s)
                                   for v in vs if np.isfinite(v))
        f = {tf: pho[tf].at[t, c] for tf in TFS}
        rows["cascata"][i] = float(
            (f["D1"] == "FORCA" or f["W1"] == "FORCA") and
            (f["H1"] == "EXPANSAO" or f["H4"] == "EXPANSAO"))
        rows["diverg"][i] = float(
            f["D1"] == "FORCA" and f["H1"] in ("EXAUSTAO", "FRAQUEZA"))
        rows["brd_ok"][i] = float(brd["H1"].at[t, c] >= 3)
    F = pd.DataFrame(rows, index=h1_idx)

    # ---- alvo --------------------------------------------------------------
    logs = np.log(h1)
    dvol = logs.diff().abs().rolling(VOL_WIN).mean().shift(1)
    tgt = {}
    for H in HORIZONS_H:
        mv = np.full(len(h1_idx), np.nan)
        for i, (t, cs) in enumerate(idx_pairs):
            cw = weakest.iloc[i]
            if pd.isna(cs) or pd.isna(cw):
                continue
            sym = cs + cw if cs + cw in h1.columns else \
                (cw + cs if cw + cs in h1.columns else None)
            if sym is None:
                continue
            j = i + H
            if j >= len(h1_idx):
                continue
            v = dvol[sym].iloc[i]
            if not np.isfinite(v) or v <= 0:
                continue
            mv[i] = abs(logs[sym].iloc[j] - logs[sym].iloc[i]) / (v * np.sqrt(H))
        tgt[H] = pd.Series(mv, index=h1_idx)

    # ---- split temporal 70/30 ----------------------------------------------
    days = pd.DatetimeIndex(sorted(set(h1_idx.normalize())))
    cut = days[int(len(days) * 0.7)]
    explo = h1_idx.normalize() < cut
    confirm = ~explo

    lines_rep = [f"# a20 — Confluência MTF (H1 10a, 28 pares; "
                 f"split 70/30 em {cut.date()})", "",
                 "Caveat mecânico e baseline por block-shuffle: ver "
                 "pré-registro (CHANGELOG 2026-07-08).", ""]

    day_keys = h1_idx.normalize()

    def lift_table(mask_state: pd.Series, H: int, sample: np.ndarray) -> tuple:
        y = tgt[H][sample]
        thr = np.nanquantile(tgt[H][explo], 0.75)   # quartil SÓ na exploração
        big = y >= thr
        base = big.mean()
        st = mask_state[sample]
        sel = big[st == 1]
        if len(sel) < 50 or base == 0:
            return np.nan, len(sel), base
        return sel.mean() / base, len(sel), base

    def shuffle_p95(mask_state: pd.Series, H: int, sample: np.ndarray) -> float:
        """Lift p95 sob block-shuffle por dia (estado embaralhado vs alvo)."""
        y = tgt[H][sample]
        thr = np.nanquantile(tgt[H][explo], 0.75)
        big = (y >= thr).to_numpy()
        st = mask_state[sample].to_numpy()
        dk = day_keys[sample]
        udays = dk.unique()
        pos_by_day = {d: np.nonzero(dk == d)[0] for d in udays}
        lifts = []
        base = np.nanmean(big)
        for _ in range(a.n_shuffle):
            perm = rng.permutation(len(udays))
            st_sh = np.empty_like(st)
            for orig, new in zip(range(len(udays)), perm):
                src, dst = pos_by_day[udays[new]], pos_by_day[udays[orig]]
                m = min(len(src), len(dst))
                st_sh[dst[:m]] = st[src[:m]]
                if len(dst) > m:
                    st_sh[dst[m:]] = st[src[-1]] if len(src) else 0
            sel = big[st_sh == 1]
            if len(sel) >= 50 and base > 0:
                lifts.append(np.nanmean(sel) / base)
        return float(np.percentile(lifts, 95)) if lifts else np.nan

    # ---- Q7/Q8/Q11 ----------------------------------------------------------
    for filtro, fmask in (("sem filtro", pd.Series(1.0, index=h1_idx)),
                          ("breadth>=3/7 (Q11)", F.brd_ok)):
        lines_rep += [f"## Lifts — {filtro}", "",
                      "| estado | H | lift explo | lift CONFIRM (30%) | "
                      "p95 shuffle (confirm) | n confirm | padrão? |",
                      "|---|---|---|---|---|---|---|"]
        estados = [(f"alinh_sinal={k}", (F.alinh_sinal == k) * fmask)
                   for k in (3, 4, 5)]
        estados += [(f"alinh_box>={k}", (F.alinh_box >= k) * fmask)
                    for k in (2, 3)]
        estados += [("cascata", F.cascata * fmask),
                    ("divergencia", F.diverg * fmask)]
        for nome, st in estados:
            for H in HORIZONS_H:
                le, ne, _ = lift_table(st, H, explo.nonzero()[0])
                lc, nc, _ = lift_table(st, H, confirm.nonzero()[0])
                p95 = shuffle_p95(st, H, confirm.nonzero()[0])
                ok = np.isfinite(lc) and np.isfinite(p95) and lc > p95 \
                    and le > 1.0 and lc > 1.0
                lines_rep.append(
                    f"| {nome} | {H}h | "
                    f"{le:.2f} | {lc:.2f} | {p95:.2f} | {nc} | "
                    f"{'**SIM**' if ok else 'não'} |")
        lines_rep.append("")

    # ---- Q9 lead-lag ---------------------------------------------------------
    lines_rep += ["## Q9 — lead-lag de EXPANSÃO (onsets, orientados)", ""]
    for tf_hi in ("H4", "D1"):
        leads = []
        for c in G8:
            hi_on = (pho[tf_hi][c] == "EXPANSAO") & \
                    (pho[tf_hi][c].shift(1) != "EXPANSAO")
            lo_on = (pho["H1"][c] == "EXPANSAO") & \
                    (pho["H1"][c].shift(1) != "EXPANSAO")
            lo_idx = np.nonzero(lo_on.to_numpy())[0]
            for i in np.nonzero(hi_on.to_numpy())[0]:
                prev = lo_idx[(lo_idx >= i - TF_HOURS[tf_hi]) & (lo_idx < i)]
                leads.append(len(prev) > 0)
        if leads:
            lines_rep.append(
                f"- {tf_hi}: {np.mean(leads):.1%} dos onsets de EXPANSÃO "
                f"foram precedidos por EXPANSÃO no H1 dentro de 1 barra do "
                f"{tf_hi} (n={len(leads)})")
    lines_rep.append("")

    # ---- Q10 poder em W1/MN ----------------------------------------------
    lines_rep += ["## Q10 — poder estatístico em W1/MN", ""]
    for tf in ("W1", "MN"):
        g = grid_tf(h1, tf)
        lines_rep.append(f"- {tf}: {len(g)} barras no histórico; eventos "
                         f"independentes de fase por moeda ~ dezenas "
                         f"({'INCONCLUSIVO por construção' if tf=='MN' else 'usar só como filtro binário'})")
    lines_rep.append("")

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a20")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"tfs": TFS, "horizons_h": HORIZONS_H, "vol_win": VOL_WIN,
         "n_shuffle": a.n_shuffle, "split": str(cut.date()),
         "quartil_alvo": 0.75}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines_rep), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md")


if __name__ == "__main__":
    main()

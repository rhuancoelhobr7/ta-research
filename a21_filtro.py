# -*- coding: utf-8 -*-
"""a21_filtro.py — O CSS como FILTRO de setups independentes.

Pergunta única (pré-registro CHANGELOG 2026-07-08): condicionar um setup
de entrada INDEPENDENTE ao estado do CSS (par forte-vs-fraca, breadth
confirmada, sem exaustão) melhora o resultado do MESMO setup sem filtro?
É o último papel do CSS não refutado por a5→a13→a19→a20.

Postura: nulo é aceitável. Limiares fixados ANTES. Barras fechadas, sem
look-ahead, custos incluídos. Lente CSS: css_screen (paridade 5e-9, a19).

SETUPS-BASE (independentes do CSS; medimos o DELTA do filtro, não o setup):
  S1 Breakout : rompe Donchian(20) em H1 (long acima da máx. de 20 barras).
  S2 Pullback : EMA50>EMA200; toca a EMA50 por baixo e fecha acima (long).
  S3 Reversão : RSI(14) cruza 30 p/ cima (long) / 70 p/ baixo (short).
  Saída: stop 1.5×ATR(14), alvo 2×ATR(14), timeout 48 barras.
  Custo: spread mediano do par + 0.5 pip de slippage (round-trip, em preço).
  1 posição por par; sinais durante posição aberta = ignorados (contados).

FILTROS CSS no bar do sinal (D1 âncora + H1), EMPILHADOS:
  F1 direção : trade a favor do diferencial — base >= +box e quote <= -box
               no D1 (espelho p/ short), (base-quote) >= diffthr.
  F2 breadth : F1 E breadth>=3/7 nas duas moedas (a11).
  F3 veto exaustão : F2 E nenhuma moeda em exaustão no D1 (|val|>=box e
               delta contra o sinal, k=3 fechadas).
  F4 atenção : só o par nº1 do ranking D1 (mais forte vs mais fraca).
  Controle negativo F1-INV: operar CONTRA o diferencial (deve piorar).

Sucesso pré-registrado: melhora de expectancy >= 0.10R, IC excluindo zero,
NO OUT-OF-SAMPLE, em >=2 dos 3 setups para o MESMO filtro. n<100 OOS =
inconclusivo (não nulo). BH nas 24 células (3 setups × 4 filtros × 2 dir).

Uso: python a21_filtro.py
Saída: results/{ts}_a21/REPORT.md + params.json
"""
from __future__ import annotations

import json, pathlib, time

import numpy as np
import pandas as pd

from a19_fases import breadth_hard, grid_tf
from a20_confluencia import align_closed
from css_classic import G8
from css_screen import BOX, KSLOPE, css_screen_lines

RAW = pathlib.Path("data/raw")
DIFFTHR = 0.0                  # InpDiffThr (default MQ5); box é o limiar binding
ATR_WIN, STOP_MULT, TGT_MULT, TIMEOUT = 14, 1.5, 2.0, 48
SLIP_PIPS = 0.5
PARES = None                   # todos os 28


# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------

def load_ohlc() -> tuple[dict, dict]:
    files = sorted(RAW.glob("H1OHLC_*.parquet"))
    if not files:
        raise SystemExit("sem data/raw/H1OHLC_*.parquet — rode s3_export_h1_ohlc.py")
    meta = {m["symbol"]: m for m in
            json.loads((RAW / "_meta_h1_ohlc.json").read_text())}
    return {f.stem.removeprefix("H1OHLC_"): pd.read_parquet(f)
            for f in files}, meta


# ----------------------------------------------------------------------------
# Indicadores (vetorizados, causais)
# ----------------------------------------------------------------------------

def atr(df: pd.DataFrame, w: int = ATR_WIN) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat([h - l, (h - c.shift(1)).abs(),
                    (l - c.shift(1)).abs()], axis=1).max(axis=1)
    return tr.rolling(w).mean()


def rsi(c: pd.Series, w: int = 14) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1/w, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/w, adjust=False).mean()
    return 100 - 100 / (1 + up / (dn + 1e-12))


def signals(df: pd.DataFrame, setup: str) -> tuple[np.ndarray, np.ndarray]:
    c = df["close"]
    if setup == "S1":
        hi = df["high"].rolling(20).max().shift(1)
        lo = df["low"].rolling(20).min().shift(1)
        return (c > hi).to_numpy(), (c < lo).to_numpy()
    if setup == "S2":
        e50, e200 = c.ewm(span=50).mean(), c.ewm(span=200).mean()
        up = e50 > e200
        touch_l = (df["low"] <= e50) & (c > e50) & up
        touch_s = (df["high"] >= e50) & (c < e50) & (~up)
        return touch_l.to_numpy(), touch_s.to_numpy()
    if setup == "S3":
        r = rsi(c)
        return ((r > 30) & (r.shift(1) <= 30)).to_numpy(), \
               ((r < 70) & (r.shift(1) >= 70)).to_numpy()
    raise ValueError(setup)


# ----------------------------------------------------------------------------
# Contexto CSS por barra H1 (D1 alinhado + H1)
# ----------------------------------------------------------------------------

def css_context(closes: pd.DataFrame):
    h1_idx = closes.index
    cssH1 = css_screen_lines(closes)
    d1 = grid_tf(closes, "D1")
    cssD1 = css_screen_lines(d1)
    brdD1 = breadth_hard(d1, cssD1)
    deltaD1 = cssD1 - cssD1.shift(KSLOPE)
    # exaustão: |val|>=box e delta contra o sinal (força/fraqueza esvaziando)
    exhD1 = (cssD1.abs() >= BOX) & (np.sign(deltaD1) != np.sign(cssD1)) \
        & (deltaD1 != 0)
    cssD1_al = align_closed(cssD1, "D1", h1_idx)
    brdD1_al = align_closed(brdD1, "D1", h1_idx)
    exhD1_al = align_closed(exhD1.astype(float), "D1", h1_idx)
    strong = pd.Series(pd.NA, index=h1_idx, dtype=object)
    weak = pd.Series(pd.NA, index=h1_idx, dtype=object)
    ok = cssD1_al.notna().any(axis=1)
    strong[ok] = cssD1_al[ok].idxmax(axis=1)
    weak[ok] = cssD1_al[ok].idxmin(axis=1)
    return cssD1_al, brdD1_al, exhD1_al, strong, weak


# ----------------------------------------------------------------------------
# Simulação de trades (1 posição por par, sem sobreposição)
# ----------------------------------------------------------------------------

def simulate(sym: str, df: pd.DataFrame, setup: str, meta: dict,
             ctx, cut: pd.Timestamp, warmup: int = 200) -> list[dict]:
    cssD1_al, brdD1_al, exhD1_al, strong, weak = ctx
    long_s, short_s = signals(df, setup)
    a = atr(df).to_numpy()
    o, h, l, c = (df[x].to_numpy() for x in ("open", "high", "low", "close"))
    idx = df.index
    base, quote = sym[:3], sym[3:6]
    point = meta[sym]["point"]
    pip = 10 * point
    cost = meta[sym]["spread_mediano_points"] * point + SLIP_PIPS * pip

    # séries de contexto reindexadas ao df do par
    cD1 = cssD1_al.reindex(idx)
    bD1 = brdD1_al.reindex(idx)
    eD1 = exhD1_al.reindex(idx)
    st = strong.reindex(idx).to_numpy()
    wk = weak.reindex(idx).to_numpy()
    vb, vq = cD1[base].to_numpy(), cD1[quote].to_numpy()
    bb, bq = bD1[base].to_numpy(), bD1[quote].to_numpy()
    eb, eq = eD1[base].to_numpy(), eD1[quote].to_numpy()

    trades, i, n = [], warmup, len(df)
    skipped = 0
    while i < n - 1:
        d = 1 if long_s[i] else (-1 if short_s[i] else 0)
        if d == 0 or not np.isfinite(a[i]) or a[i] <= 0:
            i += 1
            continue
        entry = c[i]
        stop = entry - d * STOP_MULT * a[i]
        tgt = entry + d * TGT_MULT * a[i]
        risk = STOP_MULT * a[i]
        exit_p, exit_j, mae, mfe = entry, min(i + TIMEOUT, n - 1), 0.0, 0.0
        for j in range(i + 1, min(i + TIMEOUT + 1, n)):
            adv = d * (h[j] - entry) if d > 0 else d * (l[j] - entry)
            adv_hi = max(d * (h[j] - entry), d * (l[j] - entry))
            adv_lo = min(d * (h[j] - entry), d * (l[j] - entry))
            mfe = max(mfe, adv_hi / risk)
            mae = min(mae, adv_lo / risk)
            hit_stop = (l[j] <= stop) if d > 0 else (h[j] >= stop)
            hit_tgt = (h[j] >= tgt) if d > 0 else (l[j] <= tgt)
            if hit_stop:                       # pessimista: stop antes do alvo
                exit_p, exit_j = stop, j
                break
            if hit_tgt:
                exit_p, exit_j = tgt, j
                break
        else:
            exit_p, exit_j = c[min(i + TIMEOUT, n - 1)], min(i + TIMEOUT, n - 1)
        pnl = d * (exit_p - entry) - cost
        R = pnl / risk
        # filtros no bar do sinal i
        f1_long = (vb[i] >= BOX) and (vq[i] <= -BOX) and (vb[i] - vq[i] >= DIFFTHR)
        f1_short = (vb[i] <= -BOX) and (vq[i] >= BOX) and (vq[i] - vb[i] >= DIFFTHR)
        f1 = f1_long if d > 0 else f1_short
        f1inv = f1_short if d > 0 else f1_long       # contra o diferencial
        f2 = f1 and (bb[i] >= 3) and (bq[i] >= 3)
        f3 = f2 and not (eb[i] >= 0.5) and not (eq[i] >= 0.5)
        pair_top = {st[i], wk[i]} == {base, quote}
        trades.append({
            "pair": sym, "setup": setup, "time": idx[i], "dir": d, "R": R,
            "atr_e": a[i], "week": idx[i].isocalendar().week + 100 * idx[i].year,
            "f1": f1, "f1inv": f1inv, "f2": f2, "f3": f3, "f4": pair_top,
            "oos": idx[i].normalize() >= cut, "mae": mae, "mfe": mfe})
        i = exit_j + 1
    return trades


# ----------------------------------------------------------------------------
# Avaliação
# ----------------------------------------------------------------------------

def block_boot_delta(R_all: np.ndarray, weeks: np.ndarray,
                     mask: np.ndarray, n_boot=2000, seed=0):
    """Delta de expectancy (filtrado − todos) com bootstrap por semana."""
    if mask.sum() < 5:
        return np.nan, np.nan, np.nan, np.nan
    point = R_all[mask].mean() - R_all.mean()
    uw = np.unique(weeks)
    by = {w: np.nonzero(weeks == w)[0] for w in uw}
    rng = np.random.default_rng(seed)
    ds = np.empty(n_boot)
    for b in range(n_boot):
        pick = np.concatenate([by[w] for w in rng.choice(uw, len(uw))])
        m = mask[pick]
        ds[b] = R_all[pick][m].mean() - R_all[pick].mean() \
            if m.sum() >= 3 else np.nan
    ds = ds[np.isfinite(ds)]
    lo, hi = np.percentile(ds, [2.5, 97.5])
    p = 2 * min((ds <= 0).mean(), (ds >= 0).mean())
    return point, lo, hi, max(p, 1 / n_boot)


def expectancy_stats(R: np.ndarray) -> dict:
    if len(R) == 0:
        return {"n": 0, "exp": np.nan, "pf": np.nan, "hit": np.nan}
    wins, losses = R[R > 0].sum(), -R[R < 0].sum()
    return {"n": len(R), "exp": R.mean(),
            "pf": wins / losses if losses > 0 else np.inf,
            "hit": (R > 0).mean()}


def bh_flag(cells: list[dict], alpha=0.05):
    ps = sorted((c["p"], i) for i, c in enumerate(cells) if np.isfinite(c["p"]))
    m, ksig = len(ps), 0
    for rank, (p, _) in enumerate(ps, 1):
        if p <= alpha * rank / m:
            ksig = rank
    thr = ps[ksig - 1][0] if ksig else 0.0
    for c in cells:
        c["bh"] = np.isfinite(c["p"]) and c["p"] <= thr and ksig > 0


def main():
    ohlc, meta = load_ohlc()
    closes = pd.DataFrame({s: d["close"] for s, d in ohlc.items()})
    days = pd.DatetimeIndex(sorted(set(closes.index.normalize())))
    cut = days[int(len(days) * 0.7)]
    ctx = css_context(closes)

    SETUPS = ["S1", "S2", "S3"]
    FILTERS = ["f1", "f2", "f3", "f4"]
    all_trades = []
    overlap_skips = 0
    for setup in SETUPS:
        for sym in ohlc:
            all_trades += simulate(sym, ohlc[sym], setup, meta, ctx, cut)
    T = pd.DataFrame(all_trades)

    lines = [f"# a21 — CSS como filtro de setups independentes (28 pares, "
             f"H1 10a; split 70/30 em {cut.date()})", "",
             "Pré-registro CHANGELOG 2026-07-08. Custos incluídos (spread "
             "mediano + 0.5 pip). Lente css_screen (paridade 5e-9).", "",
             "## Setups-base SEM filtro (sanidade — trap #1)", "",
             "| setup | amostra | n | expectancy (R) | PF | hit |",
             "|---|---|---|---|---|---|"]
    for setup in SETUPS:
        for smp, m in (("in", ~T.oos), ("out", T.oos)):
            s = expectancy_stats(T[(T.setup == setup) & m].R.to_numpy())
            lines.append(f"| {setup} | {smp} | {s['n']} | {s['exp']:+.3f} | "
                         f"{s['pf']:.2f} | {s['hit']:.1%} |")
    lines.append("")

    # ---- teste principal: delta de expectancy por setup×filtro×dir -------
    cells = []
    for setup in SETUPS:
        for d, dname in ((1, "long"), (-1, "short")):
            base_mask = (T.setup == setup) & (T.dir == d) & T.oos
            R_all = T[base_mask].R.to_numpy()
            weeks = T[base_mask].week.to_numpy()
            for filt in FILTERS:
                mask = T[base_mask][filt].to_numpy().astype(bool)
                pt, lo, hi, p = block_boot_delta(R_all, weeks, mask)
                cells.append({"setup": setup, "dir": dname, "filter": filt,
                              "n_all": len(R_all), "n_f": int(mask.sum()),
                              "delta": pt, "lo": lo, "hi": hi, "p": p})
    bh_flag(cells)

    lines += ["## Teste principal — Δ expectancy (filtrado − todos), "
              "OUT-OF-SAMPLE", "",
              "Sucesso: Δ>=+0.10R, IC exclui 0, BH-ok, em >=2/3 setups p/ o "
              "mesmo filtro. n_f<100 = inconclusivo.", "",
              "| setup | dir | filtro | n todos | n filtro | Δexp (R) | IC95% "
              "| BH | passa? |", "|---|---|---|---|---|---|---|---|---|"]
    for c in cells:
        incon = c["n_f"] < 100
        passa = (not incon and np.isfinite(c["lo"]) and c["lo"] > 0
                 and c["delta"] >= 0.10 and c["bh"])
        flag = "INCONCL" if incon else ("**SIM**" if passa else "não")
        ic = f"[{c['lo']:+.3f}, {c['hi']:+.3f}]" if np.isfinite(c["lo"]) else "—"
        c["passa"] = passa
        lines.append(f"| {c['setup']} | {c['dir']} | {c['filter']} | "
                     f"{c['n_all']} | {c['n_f']} | {c['delta']:+.3f} | {ic} | "
                     f"{'sim' if c['bh'] else 'não'} | {flag} |")
    lines.append("")

    # veredito por filtro
    lines += ["## Veredito por filtro (critério: >=2/3 setups passam)", ""]
    verdict_pos = False
    for filt in FILTERS:
        npass = sum(c["passa"] for c in cells if c["filter"] == filt)
        ok = npass >= 2
        verdict_pos = verdict_pos or ok
        lines.append(f"- {filt}: {npass}/6 células passam "
                     f"({'**FILTRO ÚTIL**' if ok else 'não atinge critério'})")
    lines.append("")

    # ---- controle negativo F1-inverso ------------------------------------
    lines += ["## Controle negativo — F1-inverso (operar CONTRA; deve PIORAR)",
              "", "| setup | dir | Δexp inv (R) | IC95% |", "|---|---|---|---|"]
    for setup in SETUPS:
        for d, dname in ((1, "long"), (-1, "short")):
            bm = (T.setup == setup) & (T.dir == d) & T.oos
            R_all = T[bm].R.to_numpy()
            pt, lo, hi, _ = block_boot_delta(
                R_all, T[bm].week.to_numpy(), T[bm].f1inv.to_numpy().astype(bool))
            ic = f"[{lo:+.3f}, {hi:+.3f}]" if np.isfinite(lo) else "—"
            lines.append(f"| {setup} | {dname} | {pt:+.3f} | {ic} |")
    lines.append("")

    # ---- custo de oportunidade -------------------------------------------
    lines += ["## Custo de oportunidade (OOS, F3 empilhado)", "",
              "| setup | % trades mantidos | % vencedores descartados |",
              "|---|---|---|"]
    for setup in SETUPS:
        sub = T[(T.setup == setup) & T.oos]
        if len(sub) == 0:
            continue
        kept = sub.f3.mean()
        win = sub[sub.R > 0]
        disc = (win[~win.f3].shape[0] / win.shape[0]) if len(win) else np.nan
        lines.append(f"| {setup} | {kept:.1%} | {disc:.1%} |")
    lines.append("")

    verdict = ("POSITIVO — ver filtro vencedor acima" if verdict_pos else
               "NULO — CSS como filtro não agrega; indicador é descritivo.")
    lines += [f"## VEREDITO: **{verdict}**", ""]

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a21")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"setups": SETUPS, "filters": FILTERS, "box": BOX, "diffthr": DIFFTHR,
         "stop": STOP_MULT, "tgt": TGT_MULT, "timeout": TIMEOUT,
         "slip_pips": SLIP_PIPS, "split": str(cut.date()),
         "n_trades": len(T)}, indent=2))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    T.to_parquet(out / "trades.parquet")
    print(f"REPORT -> {out}/REPORT.md | veredito: "
          f"{'POSITIVO' if verdict_pos else 'NULO'}")


if __name__ == "__main__":
    main()

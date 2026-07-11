# -*- coding: utf-8 -*-
"""a39_prospective.py — scaffold de validação PROSPECTIVA (a única honesta).

O holdout está esgotado (a35/a35-bis) e o a38 mostrou os dois sinais confirmados
como economicamente inúteis no retrospecto. A ÚNICA forma legítima de testar
qualquer coisa daqui em diante é PROSPECTIVA: registrar as previsões das regras
CONGELADAS ANTES de saber o resultado, e pontuar depois — acumulando uma amostra
genuinamente out-of-sample com o tempo.

Regras congeladas (idênticas ao a35/a35-bis/a38, ZERO parâmetros livres):
  A (z-score@180): z = (mom@180 − média_research)/desvio_research (params
    congelados em frozen_params.json); long top-1 vs bottom-1, fecha 15h.
  B (persistência@240): direção = sinal do mov acumulado até 4h; long a moeda de
    maior |mov| vs a mais oposta, fecha 15h.

Integridade (append-only, à prova de adulteração):
  data/prospective/frozen_params.json — params do z-score, congelados (versionado).
  data/prospective/predictions.csv    — 1 linha por (dia, sinal), escrita ANTES
    do desfecho; nunca reescrita.
  data/prospective/outcomes.csv        — pontuação, escrita só após a janela fechar.
FREEZE_DATE: só dias ESTRITAMENTE POSTERIORES entram (o resto o projeto já viu).

Uso operacional (após exportar/ingerir M5 novo):
  python a39_prospective.py --freeze    # 1x, cria frozen_params.json
  python a39_prospective.py --record     # registra previsões de dias novos
  python a39_prospective.py --score      # pontua previsões cuja janela fechou
  python a39_prospective.py --report      # estatística acumulada OOS
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
import pandas as pd

from cssm_engine import build_indices
from a29_deteccao import load_m5
from a34_varredura import day_metrics
from a31_par_campeao import pair_of
from a38_economic import price_at, side_for, A_ENTRY, B_ENTRY, EXIT
from costs import default_costs
from stats_blocks import block_bootstrap_ci
from preponderante import G8

FREEZE_DATE = pd.Timestamp("2026-07-10")     # último dia já analisado pelo projeto
PDIR = pathlib.Path("data/prospective")
PARAMS = PDIR / "frozen_params.json"
PRED = PDIR / "predictions.csv"
OUT = PDIR / "outcomes.csv"
PRED_COLS = ["pred_id", "logged_at", "target_date", "signal", "leader", "counter",
             "direction", "pair", "side", "entry_min", "exit_min", "entry_price"]
OUT_COLS = ["pred_id", "scored_at", "par_gross_pips", "par_net_pips",
            "par_dir_correct", "cesta_net_pips", "cesta_dir_correct", "n_legs"]


def _append(path: pathlib.Path, rows: list[dict], cols: list[str]) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows)[cols]
    header = not path.exists()
    df.to_csv(path, mode="a", header=header, index=False, encoding="utf-8")
    return len(df)


def _existing_ids(path: pathlib.Path) -> set:
    if not path.exists():
        return set()
    return set(pd.read_csv(path)["pred_id"].astype(str))


def _now() -> str:
    return pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- freeze
def cmd_freeze():
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    days = pd.DatetimeIndex(sorted(idx.index.normalize().unique()))
    q50 = days.to_series().quantile(0.50)
    mom = day_metrics(idx, A_ENTRY)["mom"]
    rm = mom[mom.index < q50]
    PDIR.mkdir(parents=True, exist_ok=True)
    params = {"signal_A_zscore180": {"mean": rm.mean().round(8).to_dict(),
                                     "std": rm.std().round(8).to_dict()},
              "research_ate": str(q50.date()), "freeze_date": str(FREEZE_DATE.date()),
              "entradas": {"A": A_ENTRY, "B": B_ENTRY, "exit": EXIT}}
    PARAMS.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"freeze: {PARAMS} criado (research até {q50.date()}, freeze {FREEZE_DATE.date()})")


def _load_params():
    p = json.loads(PARAMS.read_text(encoding="utf-8"))["signal_A_zscore180"]
    return pd.Series(p["mean"]), pd.Series(p["std"])


def predict(mom_row: pd.Series, signal: str, mean: pd.Series, std: pd.Series,
            cols: set) -> dict | None:
    """Regra CONGELADA -> decisão de trade (líder/anti/par/lado). Pura, testável."""
    v = mom_row.dropna()
    if len(v) < 8:
        return None
    if signal == "A":
        z = ((v - mean.reindex(v.index)) / std.reindex(v.index)).dropna()
        if len(z) < 8:
            return None
        leader, counter = z.idxmax(), z.idxmin()
        sign = int(np.sign(z[leader])) or 1
    else:
        leader = v.abs().idxmax()
        sign = int(np.sign(v[leader])) or 1
        counter = (sign * v).idxmin()
    pair = pair_of(leader, counter, cols)
    if not pair:
        return None
    return {"leader": leader, "counter": counter, "direction": sign,
            "pair": pair, "side": side_for(leader, pair, sign)}


# ---------------------------------------------------------------- record
def cmd_record():
    if not PARAMS.exists():
        raise SystemExit("rode --freeze primeiro (frozen_params.json ausente)")
    mean, std = _load_params()
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    days = pd.DatetimeIndex(sorted(idx.index.normalize().unique()))
    prosp = days[days > FREEZE_DATE]
    momA = day_metrics(idx, A_ENTRY)["mom"]
    momB = day_metrics(idx, B_ENTRY)["mom"]
    peA, peB = price_at(ohlc, A_ENTRY), price_at(ohlc, B_ENTRY)
    cols = set(ohlc.keys())
    done = _existing_ids(PRED)
    rows = []
    for d in prosp:
        for sig, mom, pe, ent in [("A", momA, peA, A_ENTRY), ("B", momB, peB, B_ENTRY)]:
            pid = f"{d.date()}|{sig}"
            if pid in done or d not in mom.index or d not in pe.index:
                continue
            dec = predict(mom.loc[d], sig, mean, std, cols)
            if dec is None or not np.isfinite(pe.loc[d, dec["pair"]]):
                continue
            rows.append({"pred_id": pid, "logged_at": _now(),
                         "target_date": str(d.date()), "signal": sig,
                         "leader": dec["leader"], "counter": dec["counter"],
                         "direction": dec["direction"], "pair": dec["pair"],
                         "side": dec["side"], "entry_min": ent, "exit_min": EXIT,
                         "entry_price": round(float(pe.loc[d, dec["pair"]]), 6)})
    n = _append(PRED, rows, PRED_COLS)
    print(f"record: {n} previsões novas registradas ({len(prosp)} dias prospectivos "
          f"disponíveis; {len(prosp)==0 and 'nenhum dia após o freeze ainda' or 'ok'})")


# ---------------------------------------------------------------- score
def cmd_score():
    if not PRED.exists():
        print("score: sem predictions.csv"); return
    preds = pd.read_csv(PRED)
    closes, ohlc, pip = load_m5()
    idx = build_indices({s: closes[s].dropna() for s in closes}, align="inner")
    costs = default_costs()
    px = price_at(ohlc, EXIT)
    peA, peB = price_at(ohlc, A_ENTRY), price_at(ohlc, B_ENTRY)
    cols = set(ohlc.keys())
    scored = _existing_ids(OUT)
    rows = []
    for _, p in preds.iterrows():
        if p["pred_id"] in scored:
            continue
        d = pd.Timestamp(p["target_date"])
        if d not in px.index or not np.isfinite(px.loc[d, p["pair"]]):
            continue                                   # janela ainda não fechou
        # par-único
        r = costs.net_pnl(p["entry_price"], px.loc[d, p["pair"]], int(p["side"]), p["pair"])
        # cesta: 7 pares da moeda líder na direção do sinal
        pe = peA if p["signal"] == "A" else peB
        legs = [c for c in cols if p["leader"] in (c[:3], c[3:6])]
        net, gross, nlegs = [], [], 0
        for lp in legs:
            if d in pe.index and np.isfinite(pe.loc[d, lp]) and np.isfinite(px.loc[d, lp]):
                s = side_for(p["leader"], lp, int(p["direction"]))
                rr = costs.net_pnl(pe.loc[d, lp], px.loc[d, lp], s, lp)
                net.append(rr["net_pips"]); gross.append(rr["gross_pips"]); nlegs += 1
        rows.append({"pred_id": p["pred_id"], "scored_at": _now(),
                     "par_gross_pips": round(r["gross_pips"], 3),
                     "par_net_pips": round(r["net_pips"], 3),
                     "par_dir_correct": int(r["gross_pips"] > 0),
                     "cesta_net_pips": round(float(np.mean(net)), 3) if net else np.nan,
                     "cesta_dir_correct": int(np.mean(gross) > 0) if gross else np.nan,
                     "n_legs": nlegs})
    n = _append(OUT, rows, OUT_COLS)
    print(f"score: {n} previsões pontuadas ({len(preds)-len(scored)-n} ainda pendentes)")


# ---------------------------------------------------------------- report
def cmd_report():
    if not PRED.exists() or not OUT.exists():
        print("report: ainda não há previsões pontuadas. Acumule prospectivamente "
              "(--record / --score) conforme dias novos chegam.")
        if PRED.exists():
            print(f"  ({len(pd.read_csv(PRED))} previsões registradas, 0 pontuadas)")
        return
    m = pd.read_csv(PRED).merge(pd.read_csv(OUT), on="pred_id")
    print(f"=== Validação prospectiva acumulada ({len(m)} trades pontuados) ===")
    print(f"período: {m['target_date'].min()} → {m['target_date'].max()}")
    for sig in ["A", "B"]:
        s = m[m["signal"] == sig]
        if s.empty:
            continue
        net = s["par_net_pips"].to_numpy()
        exp, lo, hi = block_bootstrap_ci(net, np.mean, block=5,
                                         n_boot=2000) if len(net) >= 10 else (net.mean(), np.nan, np.nan)
        print(f"  sinal {sig} (par): n={len(s)} acc_dir={s['par_dir_correct'].mean():.1%} "
              f"exp_net={exp:+.2f}p IC[{lo:+.2f},{hi:+.2f}]")
    print("Comparar com o retrospecto do a38 (acc ~49-51%, exp<0): se a amostra "
          "prospectiva divergir muito, investigar; se confirmar, veredito robusto.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.freeze: cmd_freeze()
    if a.record: cmd_record()
    if a.score: cmd_score()
    if a.report: cmd_report()
    if not any([a.freeze, a.record, a.score, a.report]):
        ap.print_help()


if __name__ == "__main__":
    main()

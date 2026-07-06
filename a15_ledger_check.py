# -*- coding: utf-8 -*-
"""a15_ledger_check.py — Autenticação do ledger dos prints contra o M5.

O QUE ISTO É (e o que não é):
- O ledger (specialist_ledger.csv) NÃO mede hit rate preditivo: são trades
  encerrados e publicados ex-post — vencedores por construção (viés de
  seleção). Hit rate é papel exclusivo do a14 (prospectivo).
- O que este script responde: (1) os preços/lucros dos prints são
  consistentes com o mercado real (autenticidade)? (2) qual a cobertura de
  dias e há dias de perda publicados? (3) registro estruturado p/ uso futuro.
- "Consistente com preços reais" NÃO prova conta real nem skill: uma conta
  DEMO usa os mesmos preços; a seleção ex-post permanece.

RESTRIÇÃO DE HOLDOUT (regra dura 2; precedente: a11 Etapa 3): os dias do
ledger (19/06–06/07/2026) caem na região de holdout do split. Este script
NÃO importa splits_days, NÃO lê data/labels/*, NÃO calcula índice
sintético, feature ou regra nesses dias — lê APENAS closes M5 brutos de
data/raw/{SYMBOL}.parquet para conferir preços de prints. Qualquer análise
preditiva desses dias fica adiada junto com o a7.

Checagens por perna:
  1. price_out vs mercado: M5 close mais próximo de close_date+close_time
     (janela ±15 min) a ≤ --tol-price-bp (bp relativos) de price_out.
  2. price_in plausível: dentro de [min,max] (± tol) dos closes M5 da
     janela de abertura possível (00:00 do dia, ou D−2 dias úteis p/
     span_days=2, até close_time). Limitação: o print só tem horário de
     FECHAMENTO — a entrada exata é desconhecida.
  3. profit reconstruído: (out−in) × dir × lots × 100000 × (QUOTE→USD no
     carimbo do fechamento) vs profit_usd, a ≤ --tol-profit-pct.
  4. consistência interna: soma das pernas do dia == total_print (±0.02).
  5. continuidade: gap quando o mesmo símbolo fecha num print e reabre no
     seguinte (descritivo, sem PASS/FAIL).

Uso: python a15_ledger_check.py [--csv specialist_ledger.csv]
     [--tol-price-bp 15] [--tol-profit-pct 3]
Saída: results/{ts}_a15/REPORT.md + params.json
"""
from __future__ import annotations

import argparse, json, pathlib, re, time

import numpy as np
import pandas as pd

RAW = pathlib.Path("data/raw")
CONTRACT = 100_000
LEDGER_COLS = ["close_date", "symbol", "side", "lots", "price_in",
               "price_out", "close_time", "profit_usd", "portfolio_currency",
               "portfolio_direction", "span_days", "source", "notes"]


# ----------------------------------------------------------------------------
# Carga e validação
# ----------------------------------------------------------------------------

def load_ledger(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"close_time": str}, keep_default_na=False)
    missing = [c for c in LEDGER_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"colunas ausentes no ledger: {missing}")
    bad_side = set(df.side.unique()) - {"buy", "sell"}
    if bad_side:
        raise ValueError(f"side inválido: {bad_side}")
    df["close_date"] = pd.to_datetime(df["close_date"], format="%Y-%m-%d")
    if not df.close_time.str.match(r"^\d{2}:\d{2}:\d{2}$").all():
        raise ValueError("close_time deve ser HH:MM:SS")
    df["close_ts"] = df.close_date + pd.to_timedelta(df.close_time)
    for c in ("lots", "price_in", "price_out", "profit_usd", "span_days"):
        df[c] = pd.to_numeric(df[c])
    return df


def load_m5(symbol: str) -> pd.Series | None:
    p = RAW / f"{symbol}.parquet"
    return pd.read_parquet(p)["close"] if p.exists() else None


# ----------------------------------------------------------------------------
# Checagens (funções puras: recebem a série M5, testáveis com sintético)
# ----------------------------------------------------------------------------

def nearest_close(m5: pd.Series, ts: pd.Timestamp,
                  window_min: int = 15) -> tuple[float, float] | None:
    """(close M5 mais próximo de ts, distância em min) na janela ±window_min."""
    w = m5.loc[ts - pd.Timedelta(minutes=window_min):
               ts + pd.Timedelta(minutes=window_min)]
    if w.empty:
        return None
    d = (w.index - ts).total_seconds() / 60.0
    i = int(np.abs(d).argmin())
    return float(w.iloc[i]), float(d[i])


def check_price_out(leg, m5: pd.Series, tol_bp: float) -> dict:
    r = nearest_close(m5, leg.close_ts)
    if r is None:
        return {"ok": False, "dev_bp": np.nan, "obs": "sem M5 na janela ±15min"}
    px, dmin = r
    dev_bp = abs(leg.price_out - px) / px * 1e4
    return {"ok": dev_bp <= tol_bp, "dev_bp": dev_bp,
            "obs": f"M5@{dmin:+.0f}min"}


def open_window_start(leg) -> pd.Timestamp:
    """Início da janela de abertura possível (00:00; D−2 úteis p/ span=2)."""
    if leg.span_days >= 2:
        return (leg.close_date - pd.offsets.BDay(int(leg.span_days))).normalize()
    return leg.close_date.normalize()


def check_price_in(leg, m5: pd.Series, tol_bp: float) -> dict:
    w = m5.loc[open_window_start(leg):leg.close_ts]
    if w.empty:
        return {"ok": False, "dev_bp": np.nan, "obs": "sem M5 na janela de abertura"}
    lo, hi = w.min(), w.max()
    marg_lo, marg_hi = lo * tol_bp / 1e4, hi * tol_bp / 1e4
    inside = (lo - marg_lo) <= leg.price_in <= (hi + marg_hi)
    dev = 0.0 if lo <= leg.price_in <= hi else \
        min(abs(leg.price_in - lo) / lo, abs(leg.price_in - hi) / hi) * 1e4
    return {"ok": inside, "dev_bp": dev,
            "obs": f"range=[{lo:.5f},{hi:.5f}]"}


def quote_to_usd(quote: str, ts: pd.Timestamp,
                 m5_map: dict[str, pd.Series]) -> float | None:
    """Fator QUOTE→USD no carimbo ts (M5 mais próximo, ±15min)."""
    if quote == "USD":
        return 1.0
    if quote in ("JPY", "CHF", "CAD"):
        r = nearest_close(m5_map.get("USD" + quote, pd.Series(dtype=float)), ts) \
            if "USD" + quote in m5_map else None
        return 1.0 / r[0] if r else None
    if quote in ("GBP", "AUD", "NZD", "EUR"):
        sym = quote + "USD"
        r = nearest_close(m5_map.get(sym, pd.Series(dtype=float)), ts) \
            if sym in m5_map else None
        return r[0] if r else None
    return None


def reconstruct_profit(leg, m5_map: dict[str, pd.Series]) -> float | None:
    """(out−in) × dir × lots × contrato × QUOTE→USD."""
    quote = leg.symbol[3:6]
    fx = quote_to_usd(quote, leg.close_ts, m5_map)
    if fx is None:
        return None
    direc = 1.0 if leg.side == "buy" else -1.0
    return (leg.price_out - leg.price_in) * direc * leg.lots * CONTRACT * fx


def check_profit(leg, m5_map: dict[str, pd.Series], tol_pct: float) -> dict:
    est = reconstruct_profit(leg, m5_map)
    if est is None:
        return {"ok": False, "err_pct": np.nan, "obs": "sem par de conversão"}
    if leg.profit_usd == 0:
        return {"ok": abs(est) < 1.0, "err_pct": np.nan, "obs": "profit 0"}
    err = abs(est - leg.profit_usd) / abs(leg.profit_usd) * 100
    return {"ok": err <= tol_pct, "err_pct": err, "obs": f"recon={est:,.2f}"}


def scan_clock_offset(leg, m5: pd.Series,
                      hours=range(-6, 7)) -> tuple[int, float] | None:
    """Diagnóstico p/ pernas que falham price_out: qual deslocamento fixo de
    relógio (em horas) minimiza o desvio? NÃO altera a checagem nem o CSV —
    relógios de prints podem estar em outro fuso (ex.: UTC vs servidor)."""
    best = None
    for h in hours:
        r = nearest_close(m5, leg.close_ts + pd.Timedelta(hours=h))
        if r is None:
            continue
        dev = abs(leg.price_out - r[0]) / r[0] * 1e4
        if best is None or dev < best[1]:
            best = (h, dev)
    return best


def parse_total_print(notes: str) -> float | None:
    m = re.search(r"total_print=([\d.]+)", str(notes))
    return float(m.group(1)) if m else None


def check_day_sums(df: pd.DataFrame, tol: float = 0.02) -> list[dict]:
    out = []
    for day, g in df.groupby("close_date"):
        tot = parse_total_print("; ".join(g.notes.astype(str)))
        s = g.profit_usd.sum()
        out.append({"day": day, "n_legs": len(g), "sum": s, "total_print": tot,
                    "ok": (tot is not None) and abs(s - tot) <= tol,
                    "losing_legs": int((g.profit_usd < 0).sum())})
    return out


def continuity_gaps(df: pd.DataFrame) -> list[dict]:
    """Gap descritivo: mesmo símbolo fecha num print e reabre no seguinte."""
    out = []
    days = sorted(df.close_date.unique())
    for a, b in zip(days, days[1:]):
        ga = df[df.close_date == a].set_index("symbol")
        gb = df[df.close_date == b].set_index("symbol")
        for sym in ga.index.intersection(gb.index):
            gap = gb.loc[sym, "price_in"] - ga.loc[sym, "price_out"]
            out.append({"symbol": sym, "de": a, "para": b,
                        "gap_bp": gap / ga.loc[sym, "price_out"] * 1e4})
    return out


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="specialist_ledger.csv")
    ap.add_argument("--tol-price-bp", type=float, default=15.0)
    ap.add_argument("--tol-profit-pct", type=float, default=3.0)
    a = ap.parse_args()

    df = load_ledger(a.csv)
    syms = sorted(set(df.symbol) |
                  {"USDJPY", "USDCHF", "USDCAD", "GBPUSD", "AUDUSD",
                   "NZDUSD", "EURUSD"})
    m5_map = {s: m5 for s in syms if (m5 := load_m5(s)) is not None}

    rows, fails = [], []
    for leg in df.itertuples():
        m5 = m5_map.get(leg.symbol)
        if m5 is None:
            rows.append({"leg": f"{leg.close_date.date()} {leg.symbol}",
                         "out": "—", "in": "—", "profit": "—",
                         "obs": "SEM PARQUET"})
            fails.append(f"{leg.close_date.date()} {leg.symbol}: sem parquet")
            continue
        c1 = check_price_out(leg, m5, a.tol_price_bp)
        c2 = check_price_in(leg, m5, a.tol_price_bp)
        c3 = check_profit(leg, m5_map, a.tol_profit_pct)
        rows.append({
            "leg": f"{leg.close_date.date()} {leg.symbol} {leg.side}",
            "out": f"{'PASS' if c1['ok'] else 'FAIL'} ({c1['dev_bp']:.1f}bp)",
            "in": f"{'PASS' if c2['ok'] else 'FAIL'} ({c2['dev_bp']:.1f}bp)",
            "profit": f"{'PASS' if c3['ok'] else 'FAIL'}"
                      + (f" ({c3['err_pct']:.2f}%)"
                         if np.isfinite(c3.get("err_pct", np.nan)) else ""),
            "obs": "; ".join(x["obs"] for x in (c1, c2, c3)),
        })
        for nm, c in (("price_out", c1), ("price_in", c2), ("profit", c3)):
            if not c["ok"]:
                extra = ""
                if nm == "price_out":
                    b = scan_clock_offset(leg, m5)
                    if b:
                        extra = (f" | diagnóstico: melhor offset de relógio "
                                 f"{b[0]:+d}h → {b[1]:.1f}bp")
                fails.append(f"{leg.close_date.date()} {leg.symbol} {nm}: "
                             f"desvio {c['dev_bp']:.1f}bp ({c['obs']}){extra}")

    day_sums = check_day_sums(df)
    gaps = continuity_gaps(df)

    # cobertura: dias úteis do span do ledger
    d0, d1 = df.close_date.min(), df.close_date.max()
    bdays = pd.bdate_range(d0, d1)
    have = set(df.close_date.dt.normalize())
    coverage = [(d, d in have) for d in bdays]

    n_pass = {k: sum(k_ok in r[k] for r in rows if r[k] != "—"
                     for k_ok in ["PASS"]) for k in ("out", "in", "profit")}
    n_legs = len(df)

    lines = ["# a15 — Autenticação do ledger dos prints contra o M5", "",
             f"Ledger: {a.csv} | {n_legs} pernas, {df.close_date.nunique()} "
             f"dias ({d0.date()} → {d1.date()}) | tol preço "
             f"{a.tol_price_bp}bp, tol lucro {a.tol_profit_pct}%", "",
             "**Enquadramento honesto**: trades encerrados publicados "
             "ex-post — vencedores por construção. Este relatório atesta "
             "apenas CONSISTÊNCIA COM PREÇOS REAIS, que NÃO prova conta "
             "real nem skill (demo usa os mesmos preços; a seleção "
             "ex-post permanece). Hit rate preditivo = papel do a14.", "",
             "**Holdout**: dias do ledger caem na região de holdout. Este "
             "script leu APENAS closes M5 brutos (sem labels, splits, "
             "índices ou regras) — precedente da Etapa 3 do a11.", "",
             "**Limitação**: o print só tem horário de FECHAMENTO; a "
             "checagem de price_in é de plausibilidade (range do dia), "
             "não de carimbo exato.", "",
             f"## Resumo: price_out {n_pass['out']}/{n_legs} | "
             f"price_in {n_pass['in']}/{n_legs} | "
             f"profit {n_pass['profit']}/{n_legs}", ""]

    if fails:
        lines += ["## ⚠ FALHAS (sem edição do CSV — achado, não conserto)", ""]
        lines += [f"- {f}" for f in fails]
        lines.append("")

    lines += ["## Por perna", "", "| perna | price_out | price_in | profit | obs |",
              "|---|---|---|---|---|"]
    lines += [f"| {r['leg']} | {r['out']} | {r['in']} | {r['profit']} | "
              f"{r['obs']} |" for r in rows]

    lines += ["", "## Por dia", "",
              "| dia | moeda | dir | pernas | soma | total_print | bate? | perdedoras |",
              "|---|---|---|---|---|---|---|---|"]
    for d in day_sums:
        g = df[df.close_date == d["day"]].iloc[0]
        tp = f"{d['total_print']:,.2f}" if d["total_print"] else "—"
        lines.append(f"| {d['day'].date()} | {g.portfolio_currency} | "
                     f"{g.portfolio_direction} | {d['n_legs']} | "
                     f"{d['sum']:,.2f} | {tp} | "
                     f"{'PASS' if d['ok'] else 'FAIL'} | {d['losing_legs']} |")

    lines += ["", "## Cobertura (dias úteis do intervalo)", "",
              "| dia útil | print? |", "|---|---|"]
    lines += [f"| {d.date()} | {'sim' if h else '**NÃO**'} |"
              for d, h in coverage]

    lines += ["", "## Continuidade entre prints (descritivo)", "",
              "| símbolo | de | para | gap (bp) |", "|---|---|---|---|"]
    lines += [f"| {g['symbol']} | {g['de'].date()} | {g['para'].date()} | "
              f"{g['gap_bp']:+.1f} |" for g in gaps]

    lines += ["", "## Veredito", "",
              "Preços consistentes com o mercado real = prints AUTÊNTICOS "
              "quanto a preços. Isso não diferencia conta real de demo e "
              "não corrige o viés de seleção dos dias publicados; a taxa "
              "de acerto real segue sendo medida exclusivamente pelo a14 "
              "(prospectivo).", ""]

    out = pathlib.Path(f"results/{time.strftime('%Y%m%d_%H%M%S')}_a15")
    out.mkdir(parents=True, exist_ok=True)
    (out / "params.json").write_text(json.dumps(
        {"csv": a.csv, "tol_price_bp": a.tol_price_bp,
         "tol_profit_pct": a.tol_profit_pct, "n_legs": n_legs,
         "pass": n_pass}, indent=2, default=str))
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"REPORT -> {out}/REPORT.md | out {n_pass['out']}/{n_legs} "
          f"in {n_pass['in']}/{n_legs} profit {n_pass['profit']}/{n_legs}")


if __name__ == "__main__":
    main()

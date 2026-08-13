# -*- coding: utf-8 -*-
"""export_ta_py.py — gêmeo Python do export_ta.mq5 (elimina o passo manual no MT5).

Puxa OHLC + tick_volume + spread dos 28 pares G8 via o pacote MetaTrader5 e
escreve os MESMOS arquivos que o export_ta.mq5 produz, na mesma pasta ta_export/:
  {SYMBOL}_M15.csv  (time epoch de SERVIDOR, open/high/low/close/tick_volume/spread)
  broker_info.csv   (scope,key,value — global + por-símbolo)
…de modo que o s4_ingest_ta.py roda sem NENHUMA mudança em seguida.

Paridade verificada (2026-07-17): sobre a janela sobreposta ao golden do MQL5,
OHLCV bate bit a bit (max|Δ| = 0.0). O pacote devolve `time` já no relógio do
servidor (mesma convenção do MQL5), então o índice casa com data/raw/*.parquet.

⚠ Requisitos: Windows + terminal MT5 aberto e LOGADO na conta do a25
(TenTrade-Server). Sem isso, sai com erro (exit≠0) e não escreve nada.

Uso:
  python export_ta_py.py                 # M15, 10 anos, na pasta ta_export do terminal
  python export_ta_py.py --m5-years 3    # também exporta M5 (para costs/a29/a30)
  python export_ta_py.py --dst <pasta>   # destino alternativo (ex.: teste de paridade)
  python export_ta_py.py --years 10 --min-bars-m15 30000
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import sys
import time

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    sys.exit("MetaTrader5 indisponível (Windows-only). Abra o MT5 e instale o pacote.")

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]

# pasta ta_export do terminal desta máquina (mesma que o s4_ingest lê por default)
DEFAULT_DST = pathlib.Path(
    r"C:\Users\Léo Lzr7\AppData\Roaming\MetaQuotes\Terminal"
    r"\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\ta_export")

TF_MAP = {"M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "M5": mt5.TIMEFRAME_M5}


def resolve_symbol(a: str, b: str) -> str | None:
    """Acha o símbolo real do broker (XY ou YX) e o seleciona no Market Watch."""
    for cand in (a + b, b + a):
        if mt5.symbol_select(cand, True):
            return cand
    return None


def export_pair(sym: str, tf: str, since: dt.datetime, dst: pathlib.Path) -> dict | None:
    """Escreve {sym}_{tf}.csv (descarta a barra em formação). Retorna meta ou None."""
    rates = mt5.copy_rates_range(sym, TF_MAP[tf], since, dt.datetime.now())
    if rates is None or len(rates) <= 1:
        return None
    d = pd.DataFrame(rates)[["time", "open", "high", "low", "close",
                             "tick_volume", "spread"]]
    d = d.iloc[:-1]                         # descarta a última (em formação), como o MQL5
    if d.empty:
        return None
    info = mt5.symbol_info(sym)
    dg = int(info.digits)
    out = pd.DataFrame({
        "time": d["time"].astype("int64"),
        "open": d["open"].map(lambda v: f"{v:.{dg}f}"),
        "high": d["high"].map(lambda v: f"{v:.{dg}f}"),
        "low": d["low"].map(lambda v: f"{v:.{dg}f}"),
        "close": d["close"].map(lambda v: f"{v:.{dg}f}"),
        "tick_volume": d["tick_volume"].astype("int64"),
        "spread": d["spread"].astype("int64"),
    })
    dst.mkdir(parents=True, exist_ok=True)
    out.to_csv(dst / f"{sym}_{tf}.csv", index=False, encoding="utf-8")
    return {
        "tf": tf, "bars": len(out),
        "first_epoch": int(out["time"].iloc[0]),
        "last_epoch": int(out["time"].iloc[-1]),
        "point": info.point, "tick_size": info.trade_tick_size, "digits": dg,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dst", type=pathlib.Path, default=DEFAULT_DST)
    ap.add_argument("--years", type=int, default=10)
    ap.add_argument("--m5-years", type=int, default=0, help=">0 exporta M5 também")
    ap.add_argument("--min-bars-m15", type=int, default=30000)
    args = ap.parse_args(argv)

    if not mt5.initialize():
        print(f"MT5 não conectou: {mt5.last_error()} — abra o terminal e logue.")
        return 1
    acc = mt5.account_info()
    if acc is None:
        print("Sem conta logada no MT5.")
        return 1
    print(f"export_ta_py: {acc.company} / {acc.server} (conta {acc.login})")

    now = dt.datetime.now()
    since = now - dt.timedelta(days=args.years * 365)
    since_m5 = now - dt.timedelta(days=args.m5_years * 365) if args.m5_years > 0 else None

    meta_rows: list[tuple[str, str, str]] = []

    def g(key, value):
        meta_rows.append(("global", key, str(value)))

    # offset servidor↔GMT (para o s4 casar UTC/sessões) — server_now − utc_now
    tick = mt5.symbol_info_tick("EURUSD")
    utc_now = dt.datetime.now(dt.timezone.utc).timestamp()
    # arredonda ao minuto: mata o jitter de amostragem (sessões são horárias)
    off = int(round((tick.time - utc_now) / 60.0)) * 60 if tick else 0
    g("broker", acc.company)
    g("server", acc.server)
    g("time_current_epoch", int(tick.time) if tick else 0)
    g("time_gmt_epoch", int(utc_now))
    g("server_gmt_offset_sec", off)
    g("export_years", args.years)

    ok_m15 = ok_m5 = missing = 0
    t0 = time.time()
    for i in range(8):
        for j in range(i + 1, 8):
            sym = resolve_symbol(G8[i], G8[j])
            if sym is None:
                print(f"  par ausente {G8[i]}{G8[j]}")
                missing += 1
                continue
            m = export_pair(sym, "M15", since, args.dst)
            if m and m["bars"] >= args.min_bars_m15:
                ok_m15 += 1
                for k in ("tf", "bars", "first_epoch", "last_epoch",
                          "point", "tick_size", "digits"):
                    meta_rows.append((sym, k, str(m[k])))
            elif m:
                print(f"  {sym} M15 raso ({m['bars']} barras) — mantido, sem fallback")
                ok_m15 += 1
                for k in ("tf", "bars", "first_epoch", "last_epoch",
                          "point", "tick_size", "digits"):
                    meta_rows.append((sym, k, str(m[k])))
            else:
                print(f"  {sym} sem M15 utilizável")
                missing += 1
                continue
            if since_m5 is not None:
                m5 = export_pair(sym, "M5", since_m5, args.dst)
                if m5:
                    ok_m5 += 1

    g("pairs_m15", ok_m15)
    g("pairs_m5", ok_m5)
    g("pairs_missing", missing)

    args.dst.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(meta_rows, columns=["scope", "key", "value"]).to_csv(
        args.dst / "broker_info.csv", index=False, encoding="utf-8")

    print(f"export_ta_py: DONE  M15={ok_m15} M5={ok_m5} ausentes={missing} "
          f"em {time.time()-t0:.0f}s -> {args.dst}")
    return 0 if missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

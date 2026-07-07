"""s0_export_ohlc.py — OHLC D1 + H1, 4 anos, 7 pares do USD (estudo v3).

REQUISITOS: Windows, terminal MT5 logado, `pip install MetaTrader5`.
Saída: v3_usd_casocontrole/data/{TF}_{PAR}.parquet (open/high/low/close/
tick_volume, índice = horário de ABERTURA da barra, fuso do servidor) e
data/_meta.json. 4 anos é o piso duro do programa — não pedir mais.
"""
from __future__ import annotations

import json
import sys

import pandas as pd

from comum import DATA, config


def dump(mt5, sym: str, tf, anos: int, nome_tf: str, par: str) -> int | None:
    desde = (pd.Timestamp.now() - pd.DateOffset(years=anos)).to_pydatetime()
    r = mt5.copy_rates_range(sym, tf, desde, pd.Timestamp.now().to_pydatetime())
    if r is None or len(r) < 500:
        return None
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = (df.set_index("time")[["open", "high", "low", "close", "tick_volume"]]
            .astype("float64"))
    df = df[~df.index.duplicated()].sort_index().iloc[:-1]   # barra em formação fora
    df.to_parquet(DATA / f"{nome_tf}_{par}.parquet")
    return len(df)


def main():
    cfg = config()
    try:
        import MetaTrader5 as mt5
    except ImportError:
        sys.exit("MetaTrader5 indisponível (Windows-only).")
    if not mt5.initialize():
        sys.exit(f"Terminal MT5 não conectou: {mt5.last_error()}")
    DATA.mkdir(exist_ok=True)
    tfs = {"H1": mt5.TIMEFRAME_H1, "D1": mt5.TIMEFRAME_D1}
    meta = {"anos": cfg["dados"]["anos"], "exportado_em": str(pd.Timestamp.now()),
            "server_tz": "herdado do programa: UTC+2 (inverno NA) / UTC+3 (verao NA), "
                         "DST dos EUA; meia-noite do servidor = 17:00 NY (_meta.json raiz, "
                         "verificado pelo usuario)",
            "pares": {}}
    for par in cfg["dados"]["pares"]:
        sym = None
        for cand in (par, par + ".m"):
            if mt5.symbol_select(cand, True):
                sym = cand
                break
        if sym is None:
            sys.exit(f"par {par} não disponível no terminal")
        ns = {nome: dump(mt5, sym, tf, cfg["dados"]["anos"], nome, par)
              for nome, tf in tfs.items()}
        if not all(ns.values()):
            sys.exit(f"export incompleto p/ {par}: {ns}")
        meta["pares"][par] = ns
        print(par, ns)
    (DATA / "_meta.json").write_text(json.dumps(meta, indent=2))
    mt5.shutdown()
    print("export OK ->", DATA)


if __name__ == "__main__":
    main()

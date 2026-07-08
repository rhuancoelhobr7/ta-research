"""s3_export_h1_ohlc.py — H1 OHLC + spread (10 anos, 28 pares) p/ o a21.

Setups do a21 precisam de high/low (Donchian, ATR) e de spread por par
(custos). Contrato: data/raw/H1OHLC_{SYMBOL}.parquet com colunas
open/high/low/close/spread (spread em points da barra), índice servidor,
barra em formação descartada. Requer Windows + MT5 logado."""
import itertools, json, pathlib
import pandas as pd

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
RAW = pathlib.Path("data/raw")


def main(years: int = 10):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"MT5 não conectou: {mt5.last_error()}")
    now = pd.Timestamp.now()
    meta = []
    for x, y in itertools.combinations(G8, 2):
        for sym in (x + y, y + x):
            if not mt5.symbol_select(sym, True):
                continue
            r = mt5.copy_rates_range(
                sym, mt5.TIMEFRAME_H1,
                (now - pd.DateOffset(years=years)).to_pydatetime(),
                now.to_pydatetime())
            if r is None or len(r) < 5000:
                continue
            df = pd.DataFrame(r)
            df["time"] = pd.to_datetime(df["time"], unit="s")
            df = (df.set_index("time")
                    [["open", "high", "low", "close", "spread"]]
                    .astype("float64"))
            df = df[~df.index.duplicated()].sort_index().iloc[:-1]
            df.to_parquet(RAW / f"H1OHLC_{sym}.parquet")
            info = mt5.symbol_info(sym)
            meta.append({"symbol": sym, "bars": len(df),
                         "point": info.point, "digits": info.digits,
                         "spread_mediano_points": float(df["spread"].median())})
            break
    (RAW / "_meta_h1_ohlc.json").write_text(json.dumps(meta, indent=2))
    print(f"{len(meta)} pares OHLC exportados")
    mt5.shutdown()


if __name__ == "__main__":
    main()

"""s2_export_h1.py — Exporta H1 (10 anos) dos 28 pares G8 p/ a19/a20.

Mesmo contrato do s0 (close, DatetimeIndex servidor, barra em formação
descartada). Saída: data/raw/H1_{SYMBOL}.parquet + _meta_h1.json.
Requer Windows + terminal MT5 logado."""
import itertools, json, pathlib
import pandas as pd

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
RAW = pathlib.Path("data/raw")


def main(years: int = 10):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f"MT5 não conectou: {mt5.last_error()}")
    now = pd.Timestamp.now()
    exported = []
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
            s = df.set_index("time")["close"].astype("float64")
            s = s[~s.index.duplicated()].sort_index().iloc[:-1]
            s.to_frame().to_parquet(RAW / f"H1_{sym}.parquet")
            exported.append({"symbol": sym, "h1_bars": len(s),
                             "desde": str(s.index[0])})
            break
    (RAW / "_meta_h1.json").write_text(json.dumps(exported, indent=2))
    print(f"{len(exported)} pares H1 exportados")
    mt5.shutdown()


if __name__ == "__main__":
    main()

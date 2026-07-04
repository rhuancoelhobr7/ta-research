"""s0_export_mt5.py — Exporta M5 (2 anos) + D1 (4 anos) dos 28 pares G8.

REQUISITOS: Windows, terminal MT5 logado, `pip install MetaTrader5`.
Fora disso: falha cedo; usuário fornece os dados conforme CLAUDE.md.

Uso: python s0_export_mt5.py [--suffix .m] [--m5-years 2] [--d1-years 15]
Saída: data/raw/{SYMBOL}.parquet (M5) e data/raw/D1_{SYMBOL}.parquet (D1),
       data/raw/_meta.json (server_tz — VERIFICAR MANUALMENTE, PLAN.md §3).
"""
import argparse, itertools, json, pathlib, sys
import pandas as pd

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
RAW = pathlib.Path("data/raw")


def dump(mt5, sym, tf, since, prefix=""):
    r = mt5.copy_rates_range(sym, tf, since.to_pydatetime(),
                             pd.Timestamp.now().to_pydatetime())
    if r is None or len(r) < 500:
        return None
    df = pd.DataFrame(r); df["time"] = pd.to_datetime(df["time"], unit="s")
    s = df.set_index("time")["close"].astype("float64")
    s = s[~s.index.duplicated()].sort_index().iloc[:-1]
    s.to_frame().to_parquet(RAW / f"{prefix}{sym}.parquet")
    return len(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="")
    ap.add_argument("--m5-years", type=int, default=2)
    ap.add_argument("--d1-years", type=int, default=4)
    a = ap.parse_args()
    try:
        import MetaTrader5 as mt5
    except ImportError:
        sys.exit("MetaTrader5 indisponível (Windows-only). Ver CLAUDE.md.")
    if not mt5.initialize():
        sys.exit(f"Terminal MT5 não conectou: {mt5.last_error()}")
    RAW.mkdir(parents=True, exist_ok=True)
    now = pd.Timestamp.now()
    exported = []
    for x, y in itertools.combinations(G8, 2):
        for sym in (x + y + a.suffix, y + x + a.suffix):
            if not mt5.symbol_select(sym, True):
                continue
            clean = sym.replace(a.suffix, "")
            n5 = dump(mt5, sym, mt5.TIMEFRAME_M5, now - pd.DateOffset(years=a.m5_years))
            nd = dump(mt5, sym, mt5.TIMEFRAME_D1, now - pd.DateOffset(years=a.d1_years),
                      prefix="D1_")
            if n5:
                exported.append({"symbol": clean, "m5_bars": n5, "d1_bars": nd})
                break
    (RAW / "_meta.json").write_text(json.dumps(
        {"server_tz": "VERIFICAR_MANUALMENTE",  # PLAN.md §3 — obrigatório
         "exported": exported}, indent=2))
    print(f"{len(exported)} pares. ATENÇÃO: preencha server_tz em _meta.json "
          f"e valide T0 contra o gráfico antes de rodar a1.")
    mt5.shutdown()


if __name__ == "__main__":
    main()

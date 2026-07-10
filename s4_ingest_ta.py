# -*- coding: utf-8 -*-
"""s4_ingest_ta.py — ingere a pasta ta_export/ (export_ta.mq5) no contrato do repo.

Le os CSVs {SYMBOL}_M15.csv + broker_info.csv gerados por export_ta.mq5 e grava:
  data/raw/M15_{SYMBOL}.parquet  — open/high/low/close/tick_volume/spread,
                                    indice DatetimeIndex 'time' em TEMPO DO
                                    SERVIDOR (naive), barras unicas e ordenadas.
  data/raw/_meta_ta.json         — broker, offset servidor<->GMT, pip/point/
                                    digits por par, cobertura (barras, 1a/ult).

Convencao temporal (igual s3_export_h1_ohlc.py e _meta.json): o campo `time`
do MT5 e o CALENDARIO DO SERVIDOR codificado como epoch; pd.to_datetime(unit=s)
devolve o relogio do servidor direto. UTC = indice - server_gmt_offset_sec.
A conversao p/ UTC/sessoes acontece no a22, nao aqui — aqui mantemos o tempo
de servidor p/ casar com a paridade MQ5 (css_parity_*.csv) e com a19/a20.

Pip: pip = point * 10 (JPY digits=3 -> 0.01; nao-JPY digits=5 -> 0.0001).

Uso:
  python s4_ingest_ta.py [--src <pasta ta_export>]
O default de --src aponta p/ a pasta Files do terminal MT5 desta maquina.
"""
from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

RAW = pathlib.Path("data/raw")
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread"]

# terminal desta maquina (fallback; sobreponha com --src)
DEFAULT_SRC = pathlib.Path(
    r"C:\Users\Léo Lzr7\AppData\Roaming\MetaQuotes\Terminal"
    r"\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Files\ta_export")


def pip_from_point(point: float, digits: int) -> float:
    """pip = point * 10 (fracional-pip do broker de 5/3 digitos)."""
    return round(point * 10.0, 10)


def parse_broker_info(path: pathlib.Path) -> tuple[dict, dict]:
    """Le broker_info.csv (long-format scope,key,value).

    Retorna (global_meta, {symbol: {tf,bars,point,tick_size,digits,...}}).
    """
    df = pd.read_csv(path)
    g = dict(zip(df.loc[df.scope == "global", "key"],
                 df.loc[df.scope == "global", "value"]))
    per: dict[str, dict] = {}
    for _, r in df[df.scope != "global"].iterrows():
        per.setdefault(r["scope"], {})[r["key"]] = r["value"]
    return g, per


def csv_to_df(path: pathlib.Path) -> pd.DataFrame:
    """CSV de barras -> DataFrame OHLCV, indice 'time' (servidor), unico/ordenado."""
    d = pd.read_csv(path)
    d["time"] = pd.to_datetime(d["time"], unit="s")   # relogio do servidor
    d = (d.set_index("time")[OHLCV]
           .astype({"open": "float64", "high": "float64", "low": "float64",
                    "close": "float64", "tick_volume": "int64", "spread": "int64"}))
    d = d[~d.index.duplicated(keep="first")].sort_index()
    return d


def main(src: pathlib.Path, tf: str = "M15") -> None:
    src = pathlib.Path(src)
    if not (src / "broker_info.csv").exists():
        raise SystemExit(f"broker_info.csv nao encontrado em {src}")
    RAW.mkdir(parents=True, exist_ok=True)

    gmeta, per = parse_broker_info(src / "broker_info.csv")
    off = int(gmeta["server_gmt_offset_sec"])

    symbols_meta: dict[str, dict] = {}
    for csv in sorted(src.glob(f"*_{tf}.csv")):
        sym = csv.stem.removesuffix(f"_{tf}")
        df = csv_to_df(csv)
        if df.empty:
            print(f"s4: {sym} vazio, pulado"); continue
        df.to_parquet(RAW / f"{tf}_{sym}.parquet")

        info = per.get(sym, {})
        point = float(info.get("point", "nan"))
        digits = int(float(info.get("digits", "0")))
        symbols_meta[sym] = {
            "bars": int(len(df)),
            "first_server": df.index[0].strftime("%Y-%m-%d %H:%M:%S"),
            "last_server": df.index[-1].strftime("%Y-%m-%d %H:%M:%S"),
            "point": point,
            "tick_size": float(info.get("tick_size", "nan")),
            "digits": digits,
            "pip": pip_from_point(point, digits),
            "m15_fallback": info.get("m15_fallback", ""),
        }
        print(f"s4: {sym}  {len(df)} barras  {symbols_meta[sym]['first_server']}"
              f" -> {symbols_meta[sym]['last_server']}")

    meta = {
        "source": "export_ta.mq5",
        "broker": gmeta.get("broker", ""),
        "server": gmeta.get("server", ""),
        "tz_index": "server (naive); UTC = index - server_gmt_offset_sec",
        "server_gmt_offset_sec": off,
        "export_years": int(gmeta.get("export_years", "0")),
        "n_symbols": len(symbols_meta),
        "symbols": symbols_meta,
    }
    # M15 e o meta canonico (_meta_ta.json, lido por a25/a28...); outros TFs
    # gravam meta proprio (pips sao symbol-level, iguais entre TFs).
    meta_name = "_meta_ta.json" if tf == "M15" else f"_meta_ta_{tf}.json"
    (RAW / meta_name).write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                 encoding="utf-8")
    print(f"s4: {len(symbols_meta)} pares -> data/raw/{tf}_*.parquet + {meta_name}"
          f"  (offset servidor {off}s)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(DEFAULT_SRC),
                    help="pasta ta_export/ do MT5")
    ap.add_argument("--tf", default="M15", help="timeframe a ingerir (M15, M5)")
    a = ap.parse_args()
    main(a.src, a.tf)

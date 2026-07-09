# -*- coding: utf-8 -*-
"""Testes da ingestao ta_export (s4_ingest_ta): conversao de tempo, pip,
dedup/ordenacao e parse do broker_info long-format."""
import pandas as pd

from s4_ingest_ta import csv_to_df, pip_from_point, parse_broker_info


def test_pip_from_point():
    assert pip_from_point(0.00001, 5) == 0.0001    # nao-JPY
    assert pip_from_point(0.001, 3) == 0.01         # JPY


def test_csv_to_df_time_dedup_sort(tmp_path):
    # epoch de servidor: 1468254600 = 2016-07-11 16:30:00 (relogio do servidor)
    p = tmp_path / "EURUSD_M15.csv"
    p.write_text(
        "time,open,high,low,close,tick_volume,spread\n"
        "1468255500,1.1,1.2,1.0,1.15,10,7\n"   # fora de ordem de proposito
        "1468254600,1.0,1.1,0.9,1.05,20,7\n"
        "1468254600,1.0,1.1,0.9,1.05,20,7\n",  # duplicata
    )
    d = csv_to_df(p)
    assert list(d.index) == [pd.Timestamp("2016-07-11 16:30:00"),
                             pd.Timestamp("2016-07-11 16:45:00")]
    assert d.index.is_monotonic_increasing and d.index.is_unique
    assert list(d.columns) == ["open", "high", "low", "close",
                               "tick_volume", "spread"]
    assert d["tick_volume"].dtype == "int64"


def test_parse_broker_info(tmp_path):
    p = tmp_path / "broker_info.csv"
    p.write_text(
        "scope,key,value\n"
        "global,broker,Foo Ltd\n"
        "global,server_gmt_offset_sec,10800\n"
        "EURUSD,digits,5\n"
        "EURUSD,point,0.00001\n"
        "USDJPY,digits,3\n"
        "USDJPY,point,0.001\n",
    )
    g, per = parse_broker_info(p)
    assert g["broker"] == "Foo Ltd"
    assert int(g["server_gmt_offset_sec"]) == 10800
    assert per["EURUSD"]["digits"] == "5"
    assert per["USDJPY"]["point"] == "0.001"

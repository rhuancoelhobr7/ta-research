# -*- coding: utf-8 -*-
"""Testes do a18 — parser do CSV, mapeamento, junção evento×dia e a trava
de que H-A18-3 não acessa actual/forecast."""
import ast
import inspect

import numpy as np
import pandas as pd
import pytest

import a18_calendar as m

HDR = "event_id,time_server,country,currency,name,importance,actual,forecast,previous"
ROWS = [
    "1001,2026-03-03 15:30:00,United States,USD,CPI m/m,HIGH,0.3,0.2,0.4",
    "1002,2026-03-03 10:00:00,Germany,EUR,Ifo Business Climate,MODERATE,,,",
    "1003,2026-03-03 02:30:00,Japan,JPY,BoJ Rate,HIGH,0.5,,0.5",
    "1004,2026-03-04 15:30:00,United States,USD,CPI y/y,HIGH,2.9,2.8,3.0",
]


def _write(tmp_path, encoding="utf-8", extra=()):
    p = tmp_path / "calendar_mt5.csv"
    p.write_text("\n".join([HDR, *ROWS, *extra]) + "\n", encoding=encoding)
    return p


def test_parser_utf8_e_utf16(tmp_path):
    for enc in ("utf-8", "utf-16"):
        df = m.load_calendar(_write(tmp_path, encoding=enc))
        assert len(df) == 4
        assert df.time_server.dtype.kind == "M"


def test_parser_arquivo_ausente(tmp_path):
    with pytest.raises(SystemExit, match="rode s1"):
        m.load_calendar(tmp_path / "nao_existe.csv")


def test_descarta_moeda_fora_do_g8(tmp_path):
    p = _write(tmp_path, extra=[
        "1005,2026-03-03 12:00:00,Norway,NOK,Rate Decision,HIGH,,,"])
    df = m.load_calendar(p)
    assert "NOK" not in set(df.currency)
    assert len(df) == 4


def test_juncao_evento_dia(tmp_path):
    """Evento às 15:30 do dia D entra na janela [T0, T0+12h) de D; o das
    02:30 também; nada vaza para o dia seguinte."""
    df = m.load_calendar(_write(tmp_path))
    days = pd.DatetimeIndex([pd.Timestamp("2026-03-03"),
                             pd.Timestamp("2026-03-04"),
                             pd.Timestamp("2026-03-05")])
    hbd = m.high_events_by_day(df, days)
    g = hbd.set_index(["day", "currency"]).n_high
    assert g[(pd.Timestamp("2026-03-03"), "USD")] == 0  # 15:30 > T0+12h!
    assert g[(pd.Timestamp("2026-03-03"), "JPY")] == 1  # 02:30 dentro
    assert g[(pd.Timestamp("2026-03-05"), "USD")] == 0


def test_verify_tz_para_com_fuso_errado(tmp_path):
    """CPI dos EUA fora de 15:30 → SystemExit (pré-registro: PARAR)."""
    rows = [f"20{i:02d},2026-0{1+i%6}-10 14:30:00,United States,USD,"
            f"CPI m/m,HIGH,,," for i in range(8)]
    df = m.load_calendar(_write(tmp_path, extra=rows))
    with pytest.raises(SystemExit, match="fuso FALHOU"):
        m.verify_tz(df)


def test_verify_tz_ok(tmp_path):
    """Fixture no fuso REAL do calendário (UTC+3 fixo): 16:30 no inverno
    dos EUA, 15:30 no verão — a normalização leva tudo p/ 15:30 servidor."""
    rows = []
    for i in range(8):
        mes = 1 + i % 6
        hora = "16:30" if mes in (1, 2) else "15:30"   # jan/fev = inverno
        rows.append(f"21{i:02d},2026-{mes:02d}-10 {hora}:00,United States,"
                    f"USD,Consumer Price Index,HIGH,,,")
    df = m.load_calendar(_write(tmp_path, extra=rows))
    ev = m.verify_tz(df)
    assert ev["horario_modal_server"] == "15:30"


def test_h3_nao_acessa_actual_forecast():
    """A regra H-A18-3 (ex-ante) não pode tocar actual/forecast/previous.

    Trava via AST do main(): dentro do bloco H-A18-3 (da construção de
    `agenda` até `p95`), nenhum acesso a colunas proibidas. Como o bloco
    usa só `hbd` (que nasce de importance/currency/time), verificamos que
    a função high_events_by_day não seleciona colunas proibidas e que o
    main não referencia `actual`/`forecast`/`previous` fora do ingest.
    """
    proibidas = {"actual", "forecast", "previous"}
    for fn in (m.high_events_by_day,):
        tree = ast.parse(inspect.getsource(fn))
        names = {n.value for n in ast.walk(tree)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        attrs = {n.attr for n in ast.walk(tree)
                 if isinstance(n, ast.Attribute)}
        assert not (proibidas & names) and not (proibidas & attrs)
    # main(): actual/forecast só podem aparecer em strings de texto do
    # relatório/meta, nunca como coluna acessada (atributo ou subscrito)
    tree = ast.parse(inspect.getsource(m.main))
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    subs = {n.slice.value for n in ast.walk(tree)
            if isinstance(n, ast.Subscript)
            and isinstance(n.slice, ast.Constant)
            and isinstance(n.slice.value, str)}
    assert not (proibidas & attrs)
    assert not (proibidas & subs)

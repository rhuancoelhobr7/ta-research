# -*- coding: utf-8 -*-
"""Testes do a15 — parser, reconstrução de lucro, checagens (sintético)."""
import inspect
import pathlib

import numpy as np
import pandas as pd
import pytest

import a15_ledger_check as m


# ----------------------------------------------------------------------------
# Parser / validação do CSV
# ----------------------------------------------------------------------------

def _csv(tmp_path, body: str) -> str:
    p = tmp_path / "ledger.csv"
    p.write_text(",".join(m.LEDGER_COLS) + "\n" + body, encoding="utf-8")
    return str(p)


def test_load_ledger_ok(tmp_path):
    p = _csv(tmp_path, "2026-06-19,NZDUSD,sell,60,0.57555,0.57405,10:48:30,"
                       "9000.00,NZD,BAIXA,1,story,total_print=9000.00\n")
    df = m.load_ledger(p)
    assert len(df) == 1
    assert df.close_ts.iloc[0] == pd.Timestamp("2026-06-19 10:48:30")


def test_load_ledger_side_invalido(tmp_path):
    p = _csv(tmp_path, "2026-06-19,NZDUSD,hold,60,0.5,0.5,10:00:00,"
                       "0,NZD,BAIXA,1,story,\n")
    with pytest.raises(ValueError, match="side"):
        m.load_ledger(p)


def test_load_ledger_coluna_faltando(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("close_date,symbol\n2026-06-19,NZDUSD\n", encoding="utf-8")
    with pytest.raises(ValueError, match="colunas"):
        m.load_ledger(str(p))


# ----------------------------------------------------------------------------
# Reconstrução de lucro (quote USD, JPY via 1/USDJPY, GBP via GBPUSD)
# ----------------------------------------------------------------------------

def _leg(**kw):
    base = dict(symbol="NZDUSD", side="sell", lots=60.0, price_in=0.57555,
                price_out=0.57405, profit_usd=9000.0,
                close_ts=pd.Timestamp("2026-06-19 10:48:30"), span_days=1,
                close_date=pd.Timestamp("2026-06-19"))
    base.update(kw)
    return pd.Series(base)


def _m5(sym_px: dict, ts="2026-06-19 10:45") -> dict:
    idx = pd.date_range("2026-06-19 00:00", "2026-06-19 12:00", freq="5min")
    return {s: pd.Series(px, index=idx) for s, px in sym_px.items()}


def test_profit_quote_usd_sell():
    """NZDUSD sell: (0.57555−0.57405)×60×100k = 9000 USD exatos."""
    est = m.reconstruct_profit(_leg(), _m5({"NZDUSD": 0.574}))
    assert np.isclose(est, 9000.0)


def test_profit_quote_jpy_perdedora():
    """USDJPY sell PERDEDORA: out>in → lucro negativo, convertido por 1/fx."""
    leg = _leg(symbol="USDJPY", side="sell", price_in=161.580,
               price_out=161.724, profit_usd=-5342.44)
    est = m.reconstruct_profit(leg, _m5({"USDJPY": 161.724}))
    esperado = (161.724 - 161.580) * -1 * 60 * 100_000 / 161.724
    assert np.isclose(est, esperado)
    assert est < 0
    assert abs(est - leg.profit_usd) / abs(leg.profit_usd) < 0.01


def test_profit_quote_gbp_buy():
    """EURGBP sell com quote GBP: converte via GBPUSD."""
    leg = _leg(symbol="EURGBP", side="sell", price_in=0.86790,
               price_out=0.86562, profit_usd=18109.86)
    est = m.reconstruct_profit(leg, _m5({"EURGBP": 0.866, "GBPUSD": 1.3238}))
    esperado = (0.86562 - 0.86790) * -1 * 60 * 100_000 * 1.3238
    assert np.isclose(est, esperado)
    assert abs(est - leg.profit_usd) / leg.profit_usd < 0.01


def test_check_profit_tolerancia():
    ok = m.check_profit(_leg(), _m5({"NZDUSD": 0.574}), tol_pct=3.0)
    assert ok["ok"]
    ruim = m.check_profit(_leg(profit_usd=12000.0), _m5({"NZDUSD": 0.574}), 3.0)
    assert not ruim["ok"]


# ----------------------------------------------------------------------------
# price_out / price_in contra série M5 sintética
# ----------------------------------------------------------------------------

def test_price_out_pass_e_fail():
    m5 = _m5({"X": 0.57410})["X"]
    leg = _leg(price_out=0.57405)
    assert m.check_price_out(leg, m5, tol_bp=15.0)["ok"]          # ~0.9bp
    leg2 = _leg(price_out=0.58000)                                # ~103bp
    r = m.check_price_out(leg2, m5, tol_bp=15.0)
    assert not r["ok"] and r["dev_bp"] > 15


def test_price_out_sem_dados():
    m5 = pd.Series([1.0], index=[pd.Timestamp("2026-01-01")])
    assert not m.check_price_out(_leg(), m5, 15.0)["ok"]


def test_price_in_range():
    idx = pd.date_range("2026-06-19 00:00", "2026-06-19 12:00", freq="5min")
    m5 = pd.Series(np.linspace(0.570, 0.576, len(idx)), index=idx)
    assert m.check_price_in(_leg(price_in=0.5735), m5, 15.0)["ok"]
    assert not m.check_price_in(_leg(price_in=0.590), m5, 15.0)["ok"]


def test_open_window_span2():
    """span_days=2 (quinta): janela começa 2 dias úteis antes (terça)."""
    leg = _leg(close_date=pd.Timestamp("2026-07-02"), span_days=2)
    assert m.open_window_start(leg) == pd.Timestamp("2026-06-30")


# ----------------------------------------------------------------------------
# Soma do dia vs total_print
# ----------------------------------------------------------------------------

def test_day_sums():
    df = pd.DataFrame({
        "close_date": [pd.Timestamp("2026-06-19")] * 2,
        "profit_usd": [5000.0, 4000.0],
        "notes": ["", "total_print=9000.00"],
    })
    d = m.check_day_sums(df)[0]
    assert d["ok"] and d["losing_legs"] == 0
    df.loc[0, "profit_usd"] = 5100.0
    assert not m.check_day_sums(df)[0]["ok"]


# ----------------------------------------------------------------------------
# Restrição de holdout: sem splits_days, sem data/labels
# ----------------------------------------------------------------------------

def test_nao_importa_splits_nem_labels():
    """Analisa a AST: nenhum import proibido e nenhum literal de caminho de
    labels no CÓDIGO (docstrings/comentários documentando a restrição são
    permitidos)."""
    import ast
    tree = ast.parse(inspect.getsource(m))
    imports = [n.names[0].name for n in ast.walk(tree)
               if isinstance(n, ast.Import)] + \
              [n.module for n in ast.walk(tree)
               if isinstance(n, ast.ImportFrom) and n.module]
    assert "splits_days" not in imports
    assert not any("label" in i for i in imports)
    # literais de string usados em código (fora de docstring de módulo/fn)
    docstrings = {ast.get_docstring(n, clean=False)
                  for n in ast.walk(tree)
                  if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef))}
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value not in docstrings]
    assert not any("data/labels" in s or "labels_v1" in s for s in literals)
    assert not hasattr(m, "holdout_days")

"""comum.py — carregamento, orientação USD e grade de T0 (estudo v3).

Convenções do estudo (CLAUDE.md do v3):
- Parquets em data/ têm índice = horário de ABERTURA da barra (cru do MT5,
  fuso do servidor). Os loaders convertem para horário de FECHAMENTO
  (abertura + duração da barra) — a regra de vazamento (ts <= T0) é sempre
  sobre fechamentos.
- Orientação USD: séries por par viram "log-preço do USD" — log(close)
  para USDxxx, -log(close) para xxxUSD. Subiu = USD fortaleceu.
- T0 do dia D = meia-noite do servidor de D (fechamento da última barra
  H1 do dia anterior), ~2-3h antes da abertura de Tóquio.
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
import yaml

V3 = pathlib.Path(__file__).resolve().parents[1]
RAIZ = V3.parent                      # repo ta-research (cssm_engine etc.)
DATA = V3 / "data"
RES = V3 / "resultados"
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))     # imports do programa (cssm_engine, stats_blocks)


def config() -> dict:
    return yaml.safe_load((V3 / "config.yaml").read_text(encoding="utf-8"))


def carregar_ohlc(tf: str, cfg: dict | None = None) -> dict[str, pd.DataFrame]:
    """{par: OHLC} com índice = FECHAMENTO da barra (abertura + duração)."""
    cfg = cfg or config()
    dur = {"H1": pd.Timedelta(hours=1), "D1": pd.Timedelta(days=1)}[tf]
    out = {}
    for par in cfg["dados"]["pares"]:
        f = DATA / f"{tf}_{par}.parquet"
        if not f.exists():
            raise FileNotFoundError(f"{f} — rode src/s0_export_ohlc.py (dados fora do git)")
        df = pd.read_parquet(f)
        df.index = df.index + dur
        out[par] = df
    return out


def eh_usd_base(par: str, cfg: dict) -> bool:
    return par in cfg["dados"]["usd_base"]


def orientar(valor, par: str, cfg: dict):
    """Orienta um retorno/movimento ao USD: positivo = USD fortaleceu."""
    return valor if eh_usd_base(par, cfg) else -valor


def log_usd(close: pd.Series, par: str, cfg: dict) -> pd.Series:
    """Log-preço orientado ao USD (sobe = USD forte)."""
    lp = np.log(close.astype(float))
    return lp if eh_usd_base(par, cfg) else -lp


def t0_do_dia(dia: pd.Timestamp) -> pd.Timestamp:
    """T0 do dia D = meia-noite do servidor de D (timestamp de fechamento)."""
    return pd.Timestamp(dia).normalize()


def gate_fase0():
    """Aborta se a Fase 0 não passou (gate obrigatório)."""
    ok = DATA / "fase0_ok.json"
    if not ok.exists():
        raise SystemExit("FASE 0 não validada — rode src/fase0_validacao.py primeiro.")

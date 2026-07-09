# -*- coding: utf-8 -*-
"""sessions.py — framework de sessões FX (Tokyo/Londres/NY/overlap) reutilizável
por a22–a26.

CONVERSÃO SERVIDOR→UTC (DST-aware). O feed do MT5 grava o CALENDÁRIO DO
SERVIDOR (naive). Este broker (TenTrade) segue o horário do leste dos EUA:
  hora do servidor = ET + 7h  ("meia-noite do servidor = 17:00 NY", estável nos
  dois lados do DST — registrado na Fase 0 e no CHANGELOG).
Logo o offset servidor↔UTC é +3h no verão dos EUA e +2h no inverno. Reverter
com um offset FIXO desloca metade do ano em 1h e joga barras na sessão errada.
Aqui reconstruímos o instante real: naive_ET = servidor − 7h, localiza em
US/Eastern (resolve o DST), converte p/ UTC. As poucas barras nas transições
(hora ambígua/inexistente) viram NaT e são descartadas.

SESSÕES (janelas fixas em UTC — convenção padrão; o "wobble" de ±1h do DST
próprio de cada praça é pequeno vs a duração da sessão e fica documentado).
Todas dentro do mesmo dia-UTC (sem cruzar meia-noite):
  tokyo    00:00–09:00 UTC   (JST 09–18)
  londres  07:00–16:00 UTC
  ny       12:00–21:00 UTC
  overlap  13:00–16:00 UTC   (Londres∩NY — onde o range costuma concentrar)
NOTA: a pré-Tokyo/Sydney (~21:00–00:00 UTC, o "abertura Tokyo ~20:20 UTC" dos
casos-âncora) NÃO tem bucket aqui; é uma limitação consciente do v1, ajustável.
"""
from __future__ import annotations

import pandas as pd

# janelas de sessão em HORA UTC [ini, fim)  — fim exclusivo
SESSIONS: dict[str, tuple[int, int]] = {
    "tokyo":   (0, 9),
    "londres": (7, 16),
    "ny":      (12, 21),
    "overlap": (13, 16),
}
SERVER_MINUS_ET_HOURS = 7   # hora do servidor = ET + 7h


def server_to_utc(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Converte índice de tempo de SERVIDOR (naive) p/ UTC (naive), DST-aware.

    servidor = ET + 7h  ->  ET = servidor − 7h  ->  localiza US/Eastern -> UTC.
    Barras em transição de DST (ambíguas/inexistentes) viram NaT.
    """
    et_naive = index - pd.Timedelta(hours=SERVER_MINUS_ET_HOURS)
    et = et_naive.tz_localize("US/Eastern", ambiguous="NaT", nonexistent="NaT")
    return et.tz_convert("UTC").tz_localize(None)


def add_utc(df: pd.DataFrame) -> pd.DataFrame:
    """Devolve cópia com coluna 'utc' (do índice servidor) e sem as barras NaT."""
    out = df.copy()
    out["utc"] = server_to_utc(df.index)
    return out[out["utc"].notna()]


def session_of(utc: pd.Series) -> pd.DataFrame:
    """Máscara booleana por sessão (uma coluna por sessão; overlap ⊂ londres∩ny).

    Uma barra pode pertencer a mais de uma sessão (ex.: 14:00 UTC está em
    londres, ny E overlap) — cada sessão é medida independentemente."""
    h = utc.dt.hour
    return pd.DataFrame({s: (h >= a) & (h < b) for s, (a, b) in SESSIONS.items()},
                        index=utc.index)


def session_ranges(df: pd.DataFrame, pip: float) -> pd.DataFrame:
    """Agrega range/movimento por (dia-UTC, sessão) p/ UM par.

    df: OHLC(V) indexado por tempo de SERVIDOR. Retorna DataFrame long com
    colunas: date (dia-UTC), session, range_pips, net_pips, traj (|net|/range),
    n_bars, tick_vol. range = (max high − min low)/pip; net = (close_last −
    open_first)/pip; traj = |net|/range (1=limpo, ~0.5=choppy — métrica do P9).
    """
    d = add_utc(df)
    if d.empty:
        return pd.DataFrame()
    day = d["utc"].dt.normalize()
    masks = session_of(d["utc"])
    rows = []
    for s in SESSIONS:
        sub = d[masks[s]]
        if sub.empty:
            continue
        g = sub.groupby(day[masks[s]])
        rng = (g["high"].max() - g["low"].min()) / pip
        net = (g["close"].last() - g["open"].first()) / pip
        agg = pd.DataFrame({
            "range_pips": rng,
            "net_pips": net,
            "traj": (net.abs() / rng.replace(0.0, pd.NA)),
            "n_bars": g.size(),
            "tick_vol": g["tick_volume"].sum(),
        })
        agg["session"] = s
        agg.index.name = "date"
        rows.append(agg.reset_index())
    return (pd.concat(rows, ignore_index=True)
            if rows else pd.DataFrame())

# -*- coding: utf-8 -*-
"""preponderante.py — definições compartilhadas da bateria a28-a32.

A "moeda preponderante" (a dos ~88%) é definida por PREÇO REAL, não pelo
indicador: a moeda que num dia/sessão se move na MESMA direção contra (quase)
todos os seus 7 pares.

Para cada moeda C e cada um dos seus 7 pares:
  dirmove(C, par) = movimento normalizado de C nesse par
                  = +net/ATR se C é base;  −net/ATR se C é cotada.
Daí, por moeda:
  net_strength = média dos 7 dirmove (com sinal; + = fortaleceu no conjunto)
  up / dn      = nº de pares em que C fortaleceu / enfraqueceu
  consist      = max(up, dn)  (a "consistência direcional" 0-7 da spec)
  dir          = +1 se up>=dn senão −1  (lidera por FORÇA ou por FRAQUEZA)
  forca        = média |dirmove|  (força_preponderante da spec, normalizada)

Derivados por janela (dia/sessão):
  leader      = moeda de maior net_strength (a mais forte)
  anti_leader = moeda de menor net_strength (a mais fraca)
  preponderante = a de maior consist (o polo de destaque); dir diz o lado.

Réguas de acerto (a29/a31): A = apontar a líder EXATA do fechamento; B = apontar
uma no top-2/top-3 de força. Funções em `regua_acerto`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

G8 = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]


def currency_strength(net: dict[str, float],
                      norm: dict[str, float]) -> pd.DataFrame:
    """Perfil de força das 8 moedas numa janela, a partir dos net-moves dos pares.

    net  : {par: movimento líquido com sinal (close−open), em pips}
    norm : {par: normalizador (ATR/range típico do par, mesmas unidades)}
    Retorna DataFrame index=G8 com net_strength, up, dn, consist, dir, forca, n.
    """
    acc = {c: {"s": 0.0, "a": 0.0, "up": 0, "dn": 0, "n": 0} for c in G8}
    for pair, nv in net.items():
        if nv is None or (isinstance(nv, float) and np.isnan(nv)):
            continue
        b, q = pair[:3], pair[3:6]
        if b not in G8 or q not in G8:
            continue
        d = norm.get(pair, np.nan)
        contrib = nv / d if (d and not np.isnan(d)) else np.nan
        if np.isnan(contrib):
            continue
        for cur, sign in ((b, 1.0), (q, -1.0)):
            dm = sign * contrib                 # dirmove de `cur` nesse par
            acc[cur]["s"] += dm
            acc[cur]["a"] += abs(dm)
            acc[cur]["n"] += 1
            if dm > 0:
                acc[cur]["up"] += 1
            elif dm < 0:
                acc[cur]["dn"] += 1
    rows = {}
    for c in G8:
        n = acc[c]["n"]
        rows[c] = {
            "net_strength": acc[c]["s"] / n if n else np.nan,
            "up": acc[c]["up"], "dn": acc[c]["dn"],
            "consist": max(acc[c]["up"], acc[c]["dn"]),
            "dir": 1 if acc[c]["up"] >= acc[c]["dn"] else -1,
            "forca": acc[c]["a"] / n if n else np.nan,
            "n": n,
        }
    return pd.DataFrame(rows).T


def leaders(cs: pd.DataFrame) -> dict:
    """Extrai líder/anti-líder/preponderante de um perfil de força (currency_strength)."""
    valid = cs.dropna(subset=["net_strength"])
    if valid.empty:
        return {"leader": None, "anti_leader": None, "prep": None,
                "prep_consist": 0, "prep_dir": 0, "prep_forca": np.nan}
    leader = valid["net_strength"].idxmax()
    anti = valid["net_strength"].idxmin()
    prep = valid["consist"].idxmax()            # polo de maior consistência
    return {"leader": leader, "anti_leader": anti, "prep": prep,
            "prep_consist": int(valid.loc[prep, "consist"]),
            "prep_dir": int(valid.loc[prep, "dir"]),
            "prep_forca": float(valid.loc[prep, "forca"]),
            # consistência dos POLOS (a métrica útil da spec): quantos dos 7
            # a líder bateu (up) / a anti perdeu (dn).
            "leader_consist": int(valid.loc[leader, "up"]),
            "anti_consist": int(valid.loc[anti, "dn"]),
            "leader_forca": float(valid.loc[leader, "forca"])}


def regua_acerto(previsto: str, ranking_final: list[str]) -> dict:
    """A/B: previsto bate a líder exata (A) e/ou está no top-2/top-3 (B)?

    ranking_final: moedas ordenadas por força no fechamento (mais forte primeiro).
    """
    if previsto is None or not ranking_final:
        return {"A": False, "B2": False, "B3": False}
    return {"A": previsto == ranking_final[0],
            "B2": previsto in ranking_final[:2],
            "B3": previsto in ranking_final[:3]}

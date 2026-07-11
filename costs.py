# -*- coding: utf-8 -*-
"""costs.py — camada de custo realista para o a38 (teste econômico).

Custo determinístico aplicado a trades. Componentes:
- spread mediano por par (dado REAL do M5: coluna spread em pontos; pips =
  pontos/10, tanto p/ 5 dígitos quanto p/ JPY 3 dígitos).
- slippage por PONTA (parâmetro explícito; default conservador 0.1 pip/ponta).
- swap/overnight: ZERO — as janelas do a38 são intradiárias (entra T0+Xh, fecha
  T0+15h no MESMO dia), não cruzam o horário de swap. Registrado como 0 e
  justificado aqui.
- comissão: parametrizável; default 0 (o broker embute no spread).

Custo total sempre disponível em PIPS e em % do movimento bruto. Conversão p/ $
usa um valor de pip APROXIMADO ($10/pip/lote padrão) — o número honesto é PIPS;
o $ é aproximação documentada (o valor de pip real varia ~$7-13 entre pares G8).
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field

import pandas as pd

RAW = pathlib.Path("data/raw")
PIP_VALUE_USD = 10.0        # aprox., lote padrão 100k — DOCUMENTADO como aproximação


def pip_size_from_digits(digits: int) -> float:
    return 0.01 if digits == 3 else 0.0001


def build_spread_pips(meta_path="data/raw/_meta_ta_M5.json",
                      glob="M5_*.parquet", floor=0.1) -> dict[str, float]:
    """Spread mediano por par em pips (pontos/10, piso `floor`), do M5 real."""
    out = {}
    for f in sorted(RAW.glob(glob)):
        sym = f.stem.split("_", 1)[1]
        d = pd.read_parquet(f, columns=["spread"])
        out[sym] = max(float(d["spread"].median()) / 10.0, floor)
    return out


def load_pip_sizes(meta_path="data/raw/_meta_ta_M5.json") -> dict[str, float]:
    m = json.loads(pathlib.Path(meta_path).read_text(encoding="utf-8"))["symbols"]
    return {s: pip_size_from_digits(int(v["digits"])) for s, v in m.items()}


@dataclass(frozen=True)
class Costs:
    spread_pips: dict[str, float]
    pip_size: dict[str, float]
    slippage_pips: float = 0.1          # por PONTA (conservador)
    commission_pips: float = 0.0
    swap_pips: float = 0.0              # intradiário -> 0 (justificado)
    pip_value_usd: float = PIP_VALUE_USD

    def roundtrip_cost_pips(self, symbol: str) -> float:
        return (self.spread_pips[symbol] + 2 * self.slippage_pips
                + self.commission_pips + self.swap_pips)

    def net_pnl(self, entry: float, exit: float, side: int, symbol: str,
                lots: float = 1.0) -> dict:
        """PnL líquido de um trade. side +1 compra, -1 venda. Retorna pips/$/%."""
        pip = self.pip_size[symbol]
        gross = side * (exit - entry) / pip
        cost = self.roundtrip_cost_pips(symbol)
        net = gross - cost
        return {
            "gross_pips": gross, "cost_pips": cost, "net_pips": net,
            "net_usd": net * self.pip_value_usd * lots,
            "cost_pct_gross": (cost / abs(gross) * 100) if gross != 0 else float("inf"),
        }


def default_costs(slippage_pips: float = 0.1, commission_pips: float = 0.0,
                  spread_mult: float = 1.0) -> Costs:
    """Costs padrão do repo (spread real x `spread_mult` p/ sensibilidade)."""
    sp = {s: v * spread_mult for s, v in build_spread_pips().items()}
    return Costs(spread_pips=sp, pip_size=load_pip_sizes(),
                 slippage_pips=slippage_pips, commission_pips=commission_pips)

# -*- coding: utf-8 -*-
"""diag_microestrutura.py — DIAGNÓSTICO (não é estudo, sem hipótese, sem veredito).

Inventário do que existe em data/raw e do que faltaria para um futuro a42 de
microestrutura (tick/spread). NÃO gera entrada de estudo no CHANGELOG (infra).

Ressalva honesta: tick volume em forex é proxy FRACO de fluxo (não há bolsa
centralizada; o volume é do broker). O a30 já matou volume simples como seletor
de direção. Desequilíbrio direcional de tick é mecanismo DISTINTO e não testado,
mas o prior é modesto.

Uso: python diag_microestrutura.py
Saída: results/{ts}_diag/REPORT.md
"""
from __future__ import annotations

import json
import pathlib
import time

import pandas as pd

RAW = pathlib.Path("data/raw")

MQL5_SNIPPET = r"""
// --- Exportar TICKS reais (para desequilíbrio direcional) ---
MqlTick ticks[];
int n = CopyTicks(_Symbol, ticks, COPY_TICKS_ALL, from_msc, 0);
for(int i=0;i<n;i++){
   // ticks[i].flags: TICK_FLAG_BID/ASK/LAST/VOLUME/BUY/SELL
   bool up   = (ticks[i].flags & TICK_FLAG_BUY)  != 0;  // agressor comprador
   bool down = (ticks[i].flags & TICK_FLAG_SELL) != 0;  // agressor vendedor
   // gravar: time_msc, bid, ask, last, volume, flags
}
// --- Spread por barra (já disponível em MqlRates, mas confirmar) ---
MqlRates r[];
CopyRates(_Symbol, PERIOD_M1, 0, N, r);
// r[i].spread  (em points)  |  r[i].real_volume (0 em muitos brokers de FX)
""".strip()


def inspect(path: pathlib.Path) -> dict:
    df = pd.read_parquet(path)
    return {"arquivo": path.name, "linhas": len(df), "colunas": list(df.columns),
            "inicio": str(df.index.min()), "fim": str(df.index.max()),
            "tem_tick_volume": "tick_volume" in df.columns,
            "tem_real_volume": "real_volume" in df.columns,
            "tem_spread": "spread" in df.columns}


def main():
    t0 = time.time()
    inv = []
    for tf in ["M5", "M15"]:
        files = sorted(RAW.glob(f"{tf}_*.parquet"))
        if files:
            inv.append((tf, len(files), inspect(files[0])))

    ts = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    out = pathlib.Path(f"results/{ts}_diag")
    out.mkdir(parents=True, exist_ok=True)

    lines = ["# Diagnóstico de microestrutura (inventário, NÃO é estudo)\n"]
    for tf, npairs, meta in inv:
        lines.append(f"## {tf} — {npairs} pares")
        lines.append(f"- colunas: `{meta['colunas']}`")
        lines.append(f"- período: {meta['inicio'][:10]} → {meta['fim'][:10]}, "
                     f"{meta['linhas']:,} barras/par (amostra: {meta['arquivo']})")
        lines.append(f"- tick_volume: {'SIM' if meta['tem_tick_volume'] else 'não'} · "
                     f"real_volume: {'SIM' if meta['tem_real_volume'] else 'NÃO'} · "
                     f"spread/barra: {'SIM' if meta['tem_spread'] else 'não'}\n")

    can_imbalance = any(m["tem_real_volume"] for _, _, m in inv)
    lines += [
        "## Dá para construir DESEQUILÍBRIO DIRECIONAL de tick com o que existe?\n",
        f"**{'SIM' if can_imbalance else 'NÃO'}.** Os parquets têm OHLC + "
        "`tick_volume` (contagem de ticks, SEM direção) + `spread` por barra. "
        "**Não há** o número de ticks de ALTA vs de BAIXA por barra, nem "
        "bid/ask/last por tick, nem flags de agressor. Logo o desequilíbrio "
        "direcional (compradores vs vendedores agressores) **não é reconstruível** "
        "do dado atual — `tick_volume` é só a contagem total.\n",
        "## O que o dono precisaria re-exportar do MT5 para um a42\n",
        "- **Ticks reais** via `CopyTicks(..., COPY_TICKS_ALL, ...)`: por tick, "
        "`time_msc`, `bid`, `ask`, `last`, `volume` e **`flags`** "
        "(`MqlTick.flags`: `TICK_FLAG_BUY`/`TICK_FLAG_SELL` distinguem o agressor). "
        "Sem os flags, não há direção de tick.\n"
        "- **Spread por barra** já vem em `MqlRates.spread` (points) — confirmar; "
        "`real_volume` costuma ser 0 em FX (broker sem feed de bolsa).\n\n"
        "```mql5\n" + MQL5_SNIPPET + "\n```\n",
        "## Ressalva (prior modesto)\n",
        "Tick volume em forex é proxy FRACO de fluxo (mercado descentralizado; o "
        "volume é do broker). O **a30 já matou volume simples** como seletor de "
        "direção (é cego à direção). Desequilíbrio direcional é mecanismo distinto "
        "e NÃO testado — mas, dado o histórico do projeto (o sinal está no preço; "
        "microestrutura de FX de varejo é ruidosa), o prior de sucesso é **modesto**. "
        "Este diagnóstico só diz o que É POSSÍVEL medir, não que valha a pena.\n",
    ]
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"diag: {out}/REPORT.md ({time.time()-t0:.1f}s)")
    for tf, npairs, meta in inv:
        print(f"{tf}: {npairs} pares, cols={meta['colunas']}, real_volume="
              f"{meta['tem_real_volume']}")
    print(f"desequilibrio direcional reconstruivel? {'SIM' if can_imbalance else 'NAO'} "
          f"(so tick_volume total, sem direcao)")


if __name__ == "__main__":
    main()

# Diagnóstico de microestrutura (inventário, NÃO é estudo)

## M5 — 28 pares
- colunas: `['open', 'high', 'low', 'close', 'tick_volume', 'spread']`
- período: 2023-07-11 → 2026-07-10, 223,379 barras/par (amostra: M5_AUDCAD.parquet)
- tick_volume: SIM · real_volume: NÃO · spread/barra: SIM

## M15 — 28 pares
- colunas: `['open', 'high', 'low', 'close', 'tick_volume', 'spread']`
- período: 2016-07-11 → 2026-07-09, 248,292 barras/par (amostra: M15_AUDCAD.parquet)
- tick_volume: SIM · real_volume: NÃO · spread/barra: SIM

## Dá para construir DESEQUILÍBRIO DIRECIONAL de tick com o que existe?

**NÃO.** Os parquets têm OHLC + `tick_volume` (contagem de ticks, SEM direção) + `spread` por barra. **Não há** o número de ticks de ALTA vs de BAIXA por barra, nem bid/ask/last por tick, nem flags de agressor. Logo o desequilíbrio direcional (compradores vs vendedores agressores) **não é reconstruível** do dado atual — `tick_volume` é só a contagem total.

## O que o dono precisaria re-exportar do MT5 para um a42

- **Ticks reais** via `CopyTicks(..., COPY_TICKS_ALL, ...)`: por tick, `time_msc`, `bid`, `ask`, `last`, `volume` e **`flags`** (`MqlTick.flags`: `TICK_FLAG_BUY`/`TICK_FLAG_SELL` distinguem o agressor). Sem os flags, não há direção de tick.
- **Spread por barra** já vem em `MqlRates.spread` (points) — confirmar; `real_volume` costuma ser 0 em FX (broker sem feed de bolsa).

```mql5
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
```

## Ressalva (prior modesto)

Tick volume em forex é proxy FRACO de fluxo (mercado descentralizado; o volume é do broker). O **a30 já matou volume simples** como seletor de direção (é cego à direção). Desequilíbrio direcional é mecanismo distinto e NÃO testado — mas, dado o histórico do projeto (o sinal está no preço; microestrutura de FX de varejo é ruidosa), o prior de sucesso é **modesto**. Este diagnóstico só diz o que É POSSÍVEL medir, não que valha a pena.

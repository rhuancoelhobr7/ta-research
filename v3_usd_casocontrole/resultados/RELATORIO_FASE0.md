# RELATÓRIO FASE 0 — validação de dados


## H1

| par | barras | de | até | cobertura (dias) | gaps % | OHLC inválido | vol=0 | preço<=0 |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 24818 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.82 | 0 | 0 | 0 |
| GBPUSD | 24817 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.82 | 0 | 0 | 0 |
| AUDUSD | 24828 | 2022-07-07 16:00:00 | 2026-07-07 14:00:00 | 1460 | 0.81 | 0 | 0 | 0 |
| NZDUSD | 24825 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.79 | 0 | 0 | 0 |
| USDJPY | 24819 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.81 | 0 | 0 | 0 |
| USDCHF | 24818 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.82 | 0 | 0 | 0 |
| USDCAD | 24818 | 2022-07-07 16:00:00 | 2026-07-07 05:00:00 | 1460 | 0.82 | 0 | 0 | 0 |

## D1

| par | barras | de | até | cobertura (dias) | gaps % | OHLC inválido | vol=0 | preço<=0 |
|---|---|---|---|---|---|---|---|---|
| EURUSD | 1038 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.38 | 0 | 0 | 0 |
| GBPUSD | 1038 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.38 | 0 | 0 | 0 |
| AUDUSD | 1039 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.29 | 0 | 0 | 0 |
| NZDUSD | 1038 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.38 | 0 | 0 | 0 |
| USDJPY | 1039 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.29 | 0 | 0 | 0 |
| USDCHF | 1038 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.38 | 0 | 0 | 0 |
| USDCAD | 1038 | 2022-07-08 00:00:00 | 2026-07-06 00:00:00 | 1459 | 0.38 | 0 | 0 | 0 |

## Timezone

- Servidor (herdado do programa, `data/raw/_meta.json` verificado pelo usuário): **UTC+2 (inverno NA) / UTC+3 (verão NA)**, DST dos EUA; meia-noite do servidor = 17:00 NY.
- Abertura de Tóquio (09:00 JST = 00:00 UTC) = **02:00/03:00 do servidor** → T0 (meia-noite do servidor) precede Tóquio por 2-3h.
- Evidência empírica: 206/208 segundas-feiras com primeira barra H1 às 00:00 do servidor.

## Veredito

Todas as validações passaram. Estudo liberado.
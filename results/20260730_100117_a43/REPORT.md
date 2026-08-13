# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2334 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2333 |                79.2  |              135.36 |                  0.25 |       0.8  |           17.8  |
| EFICIÊNCIA (z-ATR)  |     2083 |                49.04 |              159.6  |                  0.06 |       0.51 |            1.9  |
| estático (ref)      |     2334 |                75.28 |               97.14 |                  0.22 |       0.77 |           17.8  |
| aleatório (ref)     |     2334 |                44.9  |              132.05 |                  0.04 |     nan    |           12.03 |


- Modo AMPLITUDE: **79.2 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 25% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (49.0) mas **160 de razão range/spread** vs 135 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   75.4 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   64.1 |
|   2022 |   94   |
|   2023 |   72   |
|   2024 |   83.5 |
|   2025 |   78.9 |
|   2026 |   66.2 |


## Escolha operável — último dia disponível (2026-07-29)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPNZD |          93.95 |           0.8 |               117.44 |
| GBPCAD |          85.8  |           0.5 |               171.6  |
| EURNZD |          77.7  |           0.7 |               111    |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| AUDNZD |           54   |           0.6 |                 90   |
| GBPCAD |           85.8 |           0.5 |                171.6 |
| NZDCAD |           47.6 |           0.4 |                119   |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

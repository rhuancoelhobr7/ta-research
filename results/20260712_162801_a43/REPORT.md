# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2335 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2334 |                79.27 |              135.55 |                  0.25 |       0.8  |           10.1  |
| EFICIÊNCIA (z-ATR)  |     2084 |                49.16 |              159.7  |                  0.06 |       0.51 |            1.9  |
| estático (ref)      |     2335 |                75.34 |               97.23 |                  0.22 |       0.77 |           13.1  |
| aleatório (ref)     |     2335 |                45    |              132.36 |                  0.04 |     nan    |            5.26 |


- Modo AMPLITUDE: **79.3 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 25% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (49.2) mas **160 de razão range/spread** vs 136 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   75.7 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   64.1 |
|   2022 |   94   |
|   2023 |   72   |
|   2024 |   83.5 |
|   2025 |   78.9 |
|   2026 |   66.1 |


## Escolha operável — último dia disponível (2026-07-09)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPJPY |         107.05 |           0.6 |               178.42 |
| GBPNZD |         102.8  |           0.8 |               128.5  |
| CHFJPY |          99.6  |           1.1 |                90.55 |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPJPY |         107.05 |           0.6 |               178.42 |
| EURJPY |          87.25 |           0.2 |               436.25 |
| AUDNZD |          39.7  |           0.6 |                66.17 |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

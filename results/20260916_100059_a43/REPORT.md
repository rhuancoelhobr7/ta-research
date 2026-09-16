# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2333 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2333 |                79.11 |              138.1  |                  0.26 |       0.8  |           17.8  |
| EFICIÊNCIA (z-ATR)  |     2333 |                47.9  |              160.01 |                  0.05 |       0.51 |            1.9  |
| estático (ref)      |     2333 |                75.11 |               97.42 |                  0.22 |       0.77 |           17.8  |
| aleatório (ref)     |     2333 |                44.69 |              131.49 |                  0.04 |     nan    |           12.03 |


- Modo AMPLITUDE: **79.1 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 26% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (47.9) mas **160 de razão range/spread** vs 138 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   82.2 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   63.1 |
|   2022 |   93.2 |
|   2023 |   71.2 |
|   2024 |   84.9 |
|   2025 |   80.7 |
|   2026 |   63.1 |


## Escolha operável — último dia disponível (2026-09-15)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPNZD |          95.9  |           0.8 |               119.88 |
| GBPJPY |          82.55 |           0.6 |               137.58 |
| CHFJPY |          82.35 |           1.1 |                74.86 |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| USDCAD |          54.85 |           0.2 |               274.25 |
| NZDCAD |          49.9  |           0.4 |               124.75 |
| USDJPY |          76.5  |           0.1 |               765    |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

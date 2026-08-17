# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2333 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2333 |                79.22 |              138.27 |                  0.26 |       0.8  |           17.8  |
| EFICIÊNCIA (z-ATR)  |     2333 |                48.06 |              160.31 |                  0.05 |       0.51 |            1.9  |
| estático (ref)      |     2333 |                75.22 |               97.56 |                  0.22 |       0.77 |           17.8  |
| aleatório (ref)     |     2333 |                44.86 |              131.96 |                  0.04 |     nan    |           12.03 |


- Modo AMPLITUDE: **79.2 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 26% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (48.1) mas **160 de razão range/spread** vs 138 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   77.6 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   63.1 |
|   2022 |   93.2 |
|   2023 |   71.2 |
|   2024 |   84.9 |
|   2025 |   80.7 |
|   2026 |   64.8 |


## Escolha operável — último dia disponível (2026-08-13)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPJPY |          103.4 |           0.6 |               172.33 |
| GBPNZD |           94.3 |           0.8 |               117.87 |
| CHFJPY |           90.6 |           1.1 |                82.36 |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| AUDNZD |          55.05 |           0.6 |                91.75 |
| CADJPY |          60.35 |           0.4 |               150.87 |
| USDJPY |          77.6  |           0.1 |               776    |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

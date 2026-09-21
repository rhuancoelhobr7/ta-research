# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2332 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2332 |                79.08 |              138.06 |                  0.26 |       0.8  |           17.8  |
| EFICIÊNCIA (z-ATR)  |     2332 |                47.89 |              160.51 |                  0.05 |       0.51 |            1.9  |
| estático (ref)      |     2332 |                75.02 |               97.31 |                  0.22 |       0.77 |           17.8  |
| aleatório (ref)     |     2332 |                44.67 |              131.45 |                  0.04 |     nan    |           12.03 |


- Modo AMPLITUDE: **79.1 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 26% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (47.9) mas **161 de razão range/spread** vs 138 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   82.6 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   63.1 |
|   2022 |   93.2 |
|   2023 |   71.2 |
|   2024 |   84.9 |
|   2025 |   80.7 |
|   2026 |   62.9 |


## Escolha operável — último dia disponível (2026-09-18)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPNZD |         108.1  |           0.8 |               135.12 |
| GBPJPY |          99.35 |           0.6 |               165.58 |
| USDJPY |          98.45 |           0.1 |               984.5  |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| USDJPY |          98.45 |           0.1 |               984.5  |
| USDCAD |          54.85 |           0.2 |               274.25 |
| NZDCAD |          51.75 |           0.4 |               129.37 |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

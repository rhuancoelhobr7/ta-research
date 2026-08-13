# a43 — O produto a25, empacotado (seletor de AMPLITUDE)

**Seleciona AMPLITUDE (qual par anda mais / com mais eficiência de spread), NÃO direção nem lucro.** A 'amplitude líquida' abaixo é o TETO capturável (se a direção acertar), não P&L. Direção e gestão são do trader. 2332 dias.

## Backtest — amplitude líquida capturável por modo (pips)

| modo                |   n_dias |   amp_liq_media_pips |   efic_range/spread |   P(top1=maior_range) |   pct_teto |   menor_amp_dia |
|:--------------------|---------:|---------------------:|--------------------:|----------------------:|-----------:|----------------:|
| AMPLITUDE (a25/ATR) |     2332 |                79.27 |              138.32 |                  0.26 |       0.8  |           17.8  |
| EFICIÊNCIA (z-ATR)  |     2332 |                48.13 |              160.59 |                  0.05 |       0.51 |            1.9  |
| estático (ref)      |     2332 |                75.26 |               97.6  |                  0.22 |       0.77 |           17.8  |
| aleatório (ref)     |     2332 |                44.9  |              132.07 |                  0.04 |     nan    |           12.03 |


- Modo AMPLITUDE: **79.3 pips líq/dia** (80% do teto do dia), acerta o par de maior range em 26% vs 3.6% do acaso.

- Modo EFICIÊNCIA: menos pips (48.1) mas **161 de razão range/spread** vs 138 do amplitude — mais movimento por custo.

## Estabilidade por ano (amplitude líq. média/dia, modo AMPLITUDE)

|   date |   pips |
|-------:|-------:|
|   2017 |   77.2 |
|   2018 |   76   |
|   2019 |   79.7 |
|   2020 |   94.4 |
|   2021 |   63.1 |
|   2022 |   93.2 |
|   2023 |   71.2 |
|   2024 |   84.9 |
|   2025 |   80.7 |
|   2026 |   65.5 |


## Escolha operável — último dia disponível (2026-08-07)

**Modo AMPLITUDE (maior movimento):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| GBPJPY |          103.4 |           0.6 |               172.33 |
| GBPNZD |           96.4 |           0.8 |               120.5  |
| EURNZD |           88.9 |           0.7 |               127    |


**Modo EFICIÊNCIA (mais movimento por spread):**

|        |   atr_est_pips |   spread_pips |   folga_range/spread |
|:-------|---------------:|--------------:|---------------------:|
| AUDNZD |           57.2 |           0.6 |                95.33 |
| USDCAD |           48.9 |           0.2 |               244.5  |
| AUDCAD |           52.6 |           0.3 |               175.33 |


_Rankings completos em pick_hoje_*.csv. Rodar diariamente após ingerir M5 novo. Card do produto em PRODUTO_a25.md.

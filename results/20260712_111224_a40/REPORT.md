# a40 — Valor econômico do ranqueador de amplitude ATR (a25)

## 1.1 (DESTAQUE) — O spread escala com o ATR?

- spread como % do ATR: **TOP-8 ATR = 0.5%** vs BOT-8 ATR = 1.0%.

- correlação ATR×spread(pips) = 0.25; ATR×spread(%ATR) = -0.42.


**VANTAGEM ESTRUTURAL: o spread é proporcionalmente MENOR nos pares de maior ATR.**

## 1.2 — Captura líquida (pips, por dia)

| par | range bruto | range líquido | folga (líq/spread) |
|---|---|---|---|
| **TOP-1 (a25)** | 81.3 | **80.5** | 91x |
| TOP-3 (cesta) | 76.8 | 76.0 | |
| aleatório | 45.9 | 45.2 | |
| menor ATR | 24.8 | 24.2 | |


- TOP-1 − aleatório (range líq./dia): **+35.2 pips** IC95 [+33.3, +37.3] — significativo.

## 1.3 (NÚCLEO) — Curva de breakeven direcional

_Sem assumir sinal. Expectativa líq./trade = (2p−1)·range − custo._

| acurácia p | TOP-1 | aleatório | TOP-3 |
|---|---|---|---|
| 0.50 | -0.9 | -0.9 | -0.9 |
| 0.52 | +2.4 | +1.0 | +2.2 |
| 0.55 | +7.3 | +3.7 | +6.8 |
| 0.58 | +12.1 | +6.5 | +11.4 |
| 0.60 | +15.4 | +8.3 | +14.5 |
| 0.65 | +23.5 | +12.9 | +22.1 |


- **p de breakeven (expectativa > 0)**: TOP-1 = **0.505**, aleatório = 0.510, TOP-3 = 0.506.

- **Reframe do problema**: o breakeven do TOP-1 é BAIXÍSSIMO (0.505) — a amplitude é tão grande vs o spread (folga 91x) que basta uma acurácia MARGINAL acima de 0.505 para pagar. CAVEAT HONESTO (lição do a38): o 0.506 do a35 era sobre o estado JÁ FORMADO, NÃO o capturável (o a38 mediu ~0.50 no capturável). Logo a barra é baixa (0.505) mas ainda NÃO foi cruzada: falta um sinal marginal (>0.505) sobre o CAPTURÁVEL — exatamente o que o a41 caça. O a40 não prova que paga; prova que o alvo é MODESTO.

## 1.4 — Robustez por ano (range líquido/dia)

|   ano |   t1_net |   rand_net |
|------:|---------:|-----------:|
|  2016 |     98.4 |       54.7 |
|  2017 |     76.9 |       46   |
|  2018 |     76.4 |       45.2 |
|  2019 |     80.3 |       39.3 |
|  2020 |     94.9 |       50   |
|  2021 |     64.6 |       41.7 |
|  2022 |     94.4 |       55.2 |
|  2023 |     72.4 |       48.3 |
|  2024 |     84   |       38.2 |
|  2025 |     79.4 |       42.2 |
|  2026 |     66.6 |       38.8 |


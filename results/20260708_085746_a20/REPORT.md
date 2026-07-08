# a20 — Confluência MTF (H1 10a, 28 pares; split 70/30 em 2023-07-17)

Caveat mecânico e baseline por block-shuffle: ver pré-registro (CHANGELOG 2026-07-08).

## Lifts — sem filtro

| estado | H | lift explo | lift CONFIRM (30%) | p95 shuffle (confirm) | n confirm | padrão? |
|---|---|---|---|---|---|---|
| alinh_sinal=3 | 24h | 0.98 | 1.01 | 1.07 | 6285 | não |
| alinh_sinal=3 | 72h | 1.02 | 1.10 | 1.09 | 6285 | **SIM** |
| alinh_sinal=4 | 24h | 1.09 | 0.92 | 1.11 | 5028 | não |
| alinh_sinal=4 | 72h | 1.04 | 0.95 | 1.10 | 5028 | não |
| alinh_sinal=5 | 24h | 1.30 | 1.04 | 1.19 | 1901 | não |
| alinh_sinal=5 | 72h | 0.91 | 0.92 | 1.20 | 1901 | não |
| alinh_box>=2 | 24h | 1.04 | 1.00 | 1.03 | 14038 | não |
| alinh_box>=2 | 72h | 0.96 | 1.01 | 1.04 | 14038 | não |
| alinh_box>=3 | 24h | 1.11 | 1.08 | 1.08 | 7033 | não |
| alinh_box>=3 | 72h | 0.97 | 1.06 | 1.09 | 7033 | não |
| cascata | 24h | 1.00 | 1.04 | 1.07 | 6412 | não |
| cascata | 72h | 0.97 | 1.10 | 1.08 | 6412 | não |
| divergencia | 24h | 1.02 | 0.97 | 1.06 | 6097 | não |
| divergencia | 72h | 0.98 | 1.06 | 1.08 | 6097 | não |

## Lifts — breadth>=3/7 (Q11)

| estado | H | lift explo | lift CONFIRM (30%) | p95 shuffle (confirm) | n confirm | padrão? |
|---|---|---|---|---|---|---|
| alinh_sinal=3 | 24h | 0.99 | 1.02 | 1.06 | 6199 | não |
| alinh_sinal=3 | 72h | 1.03 | 1.11 | 1.07 | 6199 | **SIM** |
| alinh_sinal=4 | 24h | 1.09 | 0.93 | 1.09 | 4917 | não |
| alinh_sinal=4 | 72h | 1.04 | 0.96 | 1.11 | 4917 | não |
| alinh_sinal=5 | 24h | 1.29 | 1.05 | 1.17 | 1859 | não |
| alinh_sinal=5 | 72h | 0.90 | 0.94 | 1.18 | 1859 | não |
| alinh_box>=2 | 24h | 1.04 | 1.00 | 1.03 | 13823 | não |
| alinh_box>=2 | 72h | 0.96 | 1.02 | 1.04 | 13823 | não |
| alinh_box>=3 | 24h | 1.11 | 1.09 | 1.08 | 6907 | **SIM** |
| alinh_box>=3 | 72h | 0.97 | 1.07 | 1.08 | 6907 | não |
| cascata | 24h | 1.01 | 1.04 | 1.07 | 6286 | não |
| cascata | 72h | 0.97 | 1.11 | 1.08 | 6286 | não |
| divergencia | 24h | 1.03 | 0.97 | 1.07 | 5994 | não |
| divergencia | 72h | 0.99 | 1.06 | 1.07 | 5994 | não |

## Q9 — lead-lag de EXPANSÃO (onsets, orientados)

- H4: 32.8% dos onsets de EXPANSÃO foram precedidos por EXPANSÃO no H1 dentro de 1 barra do H4 (n=7271)
- D1: 82.8% dos onsets de EXPANSÃO foram precedidos por EXPANSÃO no H1 dentro de 1 barra do D1 (n=1514)

## Q10 — poder estatístico em W1/MN

- W1: 523 barras no histórico; eventos independentes de fase por moeda ~ dezenas (usar só como filtro binário)
- MN: 121 barras no histórico; eventos independentes de fase por moeda ~ dezenas (INCONCLUSIVO por construção)

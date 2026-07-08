# a19 — Ciclo de fases do CSS (H1,H4,D1,W1,MN; H1 10a, 28 pares)

Pré-registro CHANGELOG 2026-07-08. Lente causal (css_screen, leitura ao vivo). Nulo é resultado.

## H1 — Q1: matriz de transição (linhas→colunas, normalizada; ciclo comprador + espelho é simétrico)

| USD      |   FORCA |   EXAUSTAO |   FRAQUEZA |   EXPANSAO |
|:---------|--------:|-----------:|-----------:|-----------:|
| FORCA    |   0     |      0.8   |      0.119 |      0.082 |
| EXAUSTAO |   0.398 |      0     |      0.598 |      0.004 |
| FRAQUEZA |   0.04  |      0.02  |      0     |      0.94  |
| EXPANSAO |   0.28  |      0.002 |      0.718 |      0     |

Rotação completa: **2082/15178 (13.7%)** das saídas de FORÇA percorrem o ciclo na ordem.

Prob. média da transição canônica: **0.655** (H0 uniforme = 0.333)

Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana 0.168, IQR [0.143, 0.186]; fração em [0.4,0.6]: 0.0% (nível 0.50 parece decoração)

### H1 — Q2: dwell (mediana de barras por fase)

| fase | n runs | mediana | p90 |
|---|---|---|---|
| FORCA | 15179 | 4 | 10 |
| EXAUSTAO | 12854 | 3 | 9 |
| FRAQUEZA | 31994 | 4 | 14 |
| EXPANSAO | 31371 | 4 | 13 |

Hazard de sair do topo (prob. de a fase acabar na barra n dado que durou n): n=1: 0.23, n=2: 0.15, n=3: 0.19, n=5: 0.19, n=8: 0.27, n=13: 0.38

Q4 — whipsaw (reversão à box em ≤2 barras): **21.7%** das saídas (21575 saídas)

Q5 — |val|: 0.20 = p47; 0.50 = p86 (mediana |val| = 0.214)

## H4 — Q1: matriz de transição (linhas→colunas, normalizada; ciclo comprador + espelho é simétrico)

| USD      |   FORCA |   EXAUSTAO |   FRAQUEZA |   EXPANSAO |
|:---------|--------:|-----------:|-----------:|-----------:|
| FORCA    |   0     |      0.808 |      0.119 |      0.072 |
| EXAUSTAO |   0.402 |      0     |      0.594 |      0.004 |
| FRAQUEZA |   0.04  |      0.025 |      0     |      0.935 |
| EXPANSAO |   0.292 |      0.002 |      0.706 |      0     |

Rotação completa: **550/3952 (13.9%)** das saídas de FORÇA percorrem o ciclo na ordem.

Prob. média da transição canônica: **0.657** (H0 uniforme = 0.333)

Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana 0.167, IQR [0.140, 0.185]; fração em [0.4,0.6]: 0.0% (nível 0.50 parece decoração)

### H4 — Q2: dwell (mediana de barras por fase)

| fase | n runs | mediana | p90 |
|---|---|---|---|
| FORCA | 3954 | 4 | 10 |
| EXAUSTAO | 3408 | 3 | 8 |
| FRAQUEZA | 7965 | 5 | 13 |
| EXPANSAO | 7743 | 4 | 12 |

Hazard de sair do topo (prob. de a fase acabar na barra n dado que durou n): n=1: 0.23, n=2: 0.16, n=3: 0.19, n=5: 0.22, n=8: 0.25, n=13: 0.33

Q4 — whipsaw (reversão à box em ≤2 barras): **21.5%** das saídas (5514 saídas)

Q5 — |val|: 0.20 = p46; 0.50 = p86 (mediana |val| = 0.220)

## D1 — Q1: matriz de transição (linhas→colunas, normalizada; ciclo comprador + espelho é simétrico)

| USD      |   FORCA |   EXAUSTAO |   FRAQUEZA |   EXPANSAO |
|:---------|--------:|-----------:|-----------:|-----------:|
| FORCA    |   0     |      0.806 |      0.116 |      0.079 |
| EXAUSTAO |   0.397 |      0     |      0.596 |      0.007 |
| FRAQUEZA |   0.028 |      0.025 |      0     |      0.948 |
| EXPANSAO |   0.294 |      0.003 |      0.702 |      0     |

Rotação completa: **95/649 (14.6%)** das saídas de FORÇA percorrem o ciclo na ordem.

Prob. média da transição canônica: **0.661** (H0 uniforme = 0.333)

Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana 0.169, IQR [0.150, 0.185]; fração em [0.4,0.6]: 0.0% (nível 0.50 parece decoração)

### D1 — Q2: dwell (mediana de barras por fase)

| fase | n runs | mediana | p90 |
|---|---|---|---|
| FORCA | 650 | 4 | 10 |
| EXAUSTAO | 560 | 3 | 8 |
| FRAQUEZA | 1340 | 5 | 14 |
| EXPANSAO | 1324 | 4 | 12 |

Hazard de sair do topo (prob. de a fase acabar na barra n dado que durou n): n=1: 0.25, n=2: 0.16, n=3: 0.24, n=5: 0.21, n=8: 0.25, n=13: 0.34

Q4 — whipsaw (reversão à box em ≤2 barras): **22.8%** das saídas (928 saídas)

Q5 — |val|: 0.20 = p49; 0.50 = p88 (mediana |val| = 0.205)

## W1 — Q1: matriz de transição (linhas→colunas, normalizada; ciclo comprador + espelho é simétrico)

| USD      |   FORCA |   EXAUSTAO |   FRAQUEZA |   EXPANSAO |
|:---------|--------:|-----------:|-----------:|-----------:|
| FORCA    |   0     |      0.793 |      0.124 |      0.083 |
| EXAUSTAO |   0.375 |      0     |      0.625 |      0     |
| FRAQUEZA |   0.019 |      0.022 |      0     |      0.959 |
| EXPANSAO |   0.291 |      0.007 |      0.701 |      0     |

Rotação completa: **16/121 (13.2%)** das saídas de FORÇA percorrem o ciclo na ordem.

Prob. média da transição canônica: **0.667** (H0 uniforme = 0.333)

Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana 0.171, IQR [0.150, 0.189]; fração em [0.4,0.6]: 0.0% (nível 0.50 parece decoração)

### W1 — Q2: dwell (mediana de barras por fase)

| fase | n runs | mediana | p90 |
|---|---|---|---|
| FORCA | 123 | 4 | 9 |
| EXAUSTAO | 104 | 2 | 8 |
| FRAQUEZA | 272 | 5 | 13 |
| EXPANSAO | 271 | 4 | 10 |

Hazard de sair do topo (prob. de a fase acabar na barra n dado que durou n): n=1: 0.24, n=2: 0.21, n=3: 0.14, n=5: 0.24, n=8: 0.32, n=13: 0.50

Q4 — whipsaw (reversão à box em ≤2 barras): **21.8%** das saídas (182 saídas)

Q5 — |val|: 0.20 = p52; 0.50 = p91 (mediana |val| = 0.190)

## MN — Q1: matriz de transição (linhas→colunas, normalizada; ciclo comprador + espelho é simétrico)

| USD      |   FORCA |   EXAUSTAO |   FRAQUEZA |   EXPANSAO |
|:---------|--------:|-----------:|-----------:|-----------:|
| FORCA    |   0     |       0.81 |      0.143 |      0.048 |
| EXAUSTAO |   0.444 |       0    |      0.556 |      0     |
| FRAQUEZA |   0.02  |       0    |      0     |      0.98  |
| EXPANSAO |   0.255 |       0.02 |      0.725 |      0     |

Rotação completa: **2/21 (9.5%)** das saídas de FORÇA percorrem o ciclo na ordem.

Prob. média da transição canônica: **0.650** (H0 uniforme = 0.333)

Q1b — val na transição EXAUSTÃO→FRAQUEZA: mediana 0.172, IQR [0.147, 0.180]; fração em [0.4,0.6]: 0.0% (nível 0.50 parece decoração)

### MN — Q2: dwell (mediana de barras por fase)

| fase | n runs | mediana | p90 |
|---|---|---|---|
| FORCA | 22 | 5 | 10 |
| EXAUSTAO | 20 | 3 | 6 |
| FRAQUEZA | 53 | 5 | 13 |
| EXPANSAO | 54 | 4 | 10 |

Hazard de sair do topo (prob. de a fase acabar na barra n dado que durou n): n=1: 0.19, n=2: 0.15, n=3: 0.17, n=5: 0.18, n=8: 0.33, n=13: 0.00

Q4 — whipsaw (reversão à box em ≤2 barras): **17.3%** das saídas (37 saídas)

Q5 — |val|: 0.20 = p52; 0.50 = p92 (mediana |val| = 0.190)

## Q3 — retorno futuro condicionado à fase (sem filtro): 492 células, **54 sobrevivem a Benjamini-Hochberg (5%)**

| tf | moeda | fase | h | n | média (bps) | IC95% |
|---|---|---|---|---|---|---|
| H1 | CHF | FRAQUEZA | 1 | 23821 | +0.14 | [+0.05, +0.23] |
| H1 | CHF | FRAQUEZA | 3 | 23821 | +0.35 | [+0.10, +0.58] |
| H4 | CHF | FRAQUEZA | 10 | 6044 | +4.32 | [+2.33, +6.49] |
| H4 | NZD | FORCA | 3 | 2489 | -2.64 | [-4.24, -0.86] |
| D1 | USD | EXAUSTAO | 10 | 314 | +21.18 | [+8.75, +36.15] |
| D1 | EUR | FRAQUEZA | 10 | 1053 | +10.49 | [+5.64, +15.15] |
| D1 | GBP | EXPANSAO | 10 | 831 | +14.65 | [+6.88, +22.62] |
| D1 | JPY | FRAQUEZA | 3 | 1041 | -9.22 | [-13.69, -4.06] |
| D1 | JPY | FRAQUEZA | 5 | 1039 | -15.89 | [-21.98, -9.07] |
| D1 | JPY | EXAUSTAO | 10 | 232 | -44.68 | [-62.75, -25.72] |
| D1 | JPY | FRAQUEZA | 10 | 1037 | -22.11 | [-31.54, -13.09] |
| D1 | CHF | EXPANSAO | 3 | 846 | +7.34 | [+3.67, +10.72] |
| D1 | CHF | EXPANSAO | 5 | 844 | +11.04 | [+7.00, +15.31] |
| D1 | CHF | FRAQUEZA | 10 | 1005 | +17.12 | [+11.36, +24.24] |
| D1 | CHF | EXPANSAO | 10 | 839 | +16.61 | [+9.86, +23.46] |
| D1 | AUD | EXAUSTAO | 3 | 293 | +10.01 | [+2.39, +18.35] |
| D1 | NZD | EXAUSTAO | 10 | 225 | -21.93 | [-35.83, -7.72] |
| D1 | NZD | FRAQUEZA | 10 | 1034 | -11.93 | [-18.51, -4.65] |
| W1 | USD | FORCA | 5 | 83 | -78.67 | [-121.07, -32.66] |
| W1 | EUR | EXAUSTAO | 3 | 69 | +38.10 | [+22.11, +53.07] |
| W1 | EUR | FRAQUEZA | 3 | 196 | +24.07 | [+12.12, +38.24] |
| W1 | EUR | EXPANSAO | 3 | 161 | -26.26 | [-42.37, -10.16] |
| W1 | EUR | EXAUSTAO | 5 | 69 | +66.34 | [+47.16, +87.32] |
| W1 | EUR | FORCA | 10 | 66 | +76.02 | [+47.34, +108.60] |
| W1 | EUR | EXAUSTAO | 10 | 69 | +111.35 | [+88.20, +133.44] |

## Q3 — retorno futuro condicionado à fase (breadth>=3/7 (Q6)): 491 células, **59 sobrevivem a Benjamini-Hochberg (5%)**

| tf | moeda | fase | h | n | média (bps) | IC95% |
|---|---|---|---|---|---|---|
| H1 | CHF | FRAQUEZA | 3 | 23293 | +0.34 | [+0.09, +0.59] |
| H1 | CHF | FRAQUEZA | 5 | 23292 | +0.50 | [+0.14, +0.83] |
| H1 | AUD | FORCA | 1 | 10156 | -0.23 | [-0.40, -0.07] |
| H4 | CHF | FRAQUEZA | 10 | 5952 | +4.21 | [+2.37, +6.23] |
| H4 | NZD | FORCA | 5 | 2474 | -3.63 | [-6.07, -1.42] |
| D1 | USD | EXAUSTAO | 10 | 314 | +21.18 | [+8.75, +36.15] |
| D1 | EUR | FRAQUEZA | 10 | 1033 | +9.91 | [+5.34, +14.29] |
| D1 | GBP | EXPANSAO | 10 | 805 | +15.83 | [+8.03, +24.41] |
| D1 | JPY | FRAQUEZA | 3 | 1035 | -9.12 | [-13.41, -4.43] |
| D1 | JPY | FRAQUEZA | 5 | 1033 | -15.97 | [-21.93, -9.60] |
| D1 | JPY | EXAUSTAO | 10 | 232 | -44.68 | [-62.75, -25.72] |
| D1 | JPY | FRAQUEZA | 10 | 1031 | -21.92 | [-31.16, -12.73] |
| D1 | CHF | EXPANSAO | 3 | 834 | +7.24 | [+3.37, +10.77] |
| D1 | CHF | EXPANSAO | 5 | 832 | +10.75 | [+5.69, +15.59] |
| D1 | CHF | FRAQUEZA | 10 | 995 | +16.61 | [+10.15, +22.93] |
| D1 | CHF | EXPANSAO | 10 | 827 | +15.94 | [+8.88, +22.71] |
| D1 | AUD | EXAUSTAO | 3 | 293 | +10.01 | [+2.39, +18.35] |
| D1 | NZD | EXAUSTAO | 10 | 225 | -21.93 | [-35.83, -7.72] |
| D1 | NZD | FRAQUEZA | 10 | 1020 | -12.58 | [-19.66, -6.10] |
| W1 | USD | FORCA | 5 | 83 | -78.67 | [-121.07, -32.66] |
| W1 | EUR | EXAUSTAO | 3 | 69 | +38.10 | [+22.11, +53.07] |
| W1 | EUR | FRAQUEZA | 3 | 196 | +24.07 | [+12.12, +38.24] |
| W1 | EUR | EXPANSAO | 3 | 159 | -26.09 | [-41.70, -9.71] |
| W1 | EUR | EXAUSTAO | 5 | 69 | +66.34 | [+47.16, +87.32] |
| W1 | EUR | FORCA | 10 | 66 | +76.02 | [+47.34, +108.60] |

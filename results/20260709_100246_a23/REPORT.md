# a23 — Inter-sessão (autocorrelação de volatilidade)

Painel 28 pares, 2016-07-11 → 2026-07-09. Partição ordenada asia[00-07)/londres[07-13)/ny[13-21) UTC (sem sobreposição → sem lookahead). Split 70/30; métricas no TESTE (últimos 30%); thresholds do treino.

## Q4 — asia→londres vs persistência (Spearman, mediana entre pares)

- **asia→londres:** 0.342  IC95 [0.316, 0.367]

- **baseline persistência (londres ontem→hoje):** 0.267 IC95 [0.233, 0.292]

- pares com asia→londres significativo após BH: **28/28**


### Matriz de transição de volatilidade asia→londres (teste, pooled)

|         |   lon_Q1 |   lon_Q2 |   lon_Q3 |   lon_Q4 |
|:--------|---------:|---------:|---------:|---------:|
| asia_Q1 |    0.631 |    0.198 |    0.108 |    0.063 |
| asia_Q2 |    0.472 |    0.256 |    0.165 |    0.107 |
| asia_Q3 |    0.334 |    0.254 |    0.234 |    0.178 |
| asia_Q4 |    0.171 |    0.194 |    0.254 |    0.38  |


## Q5 — fração do range DIÁRIO por sessão (mediana)

|         |   fracao_mediana_do_range_diario |
|:--------|---------------------------------:|
| asia    |                            0.452 |
| londres |                            0.589 |
| ny      |                            0.631 |
| overlap |                            0.493 |


## Q6 — mola comprimida (londres normalizado por quartil de asia)

|         |   londres_norm_mediana |
|:--------|-----------------------:|
| asia_Q1 |                  0.701 |
| asia_Q2 |                  0.785 |
| asia_Q3 |                  0.883 |
| asia_Q4 |                  1.027 |

_Se cresce monotônico com o quartil de asia → calma continua (sem mola); se o Q1 de asia eleva londres → mola comprimida._


## Q7 — lead-lag de moeda (fator asia vs asia do próprio par)

| moeda   |   r_fator_moeda |   r_asia_propria |
|:--------|----------------:|-----------------:|
| USD     |           0.33  |            0.395 |
| EUR     |           0.299 |            0.623 |
| GBP     |           0.299 |            0.582 |
| JPY     |           0.434 |            0.532 |
| CHF     |           0.313 |            0.483 |
| CAD     |           0.305 |            0.437 |
| AUD     |           0.236 |            0.61  |
| NZD     |           0.194 |            0.637 |

_r_fator_moeda ≈ r_asia_propria → o fator da moeda não agrega sobre o range do próprio par._

# a29 — Curva de detecção da moeda líder (acurácia x tempo)

Verdade = líder do dia por preço no fechamento. 237 dias de teste (out-of-sample). Barras fechadas (v1). Custo do atraso = fração do range do dia já feita em t. Acaso: régua A = 12%, B3 (top-3) = 38%.

## Custo do atraso — fração do range do dia já realizada

|           |    30 |    60 |   90 |   120 |   180 |   240 |   360 |   480 |
|:----------|------:|------:|-----:|------:|------:|------:|------:|------:|
| mov_feito | 0.178 | 0.217 | 0.26 |  0.28 | 0.333 | 0.392 | 0.479 | 0.534 |


## Régua A (líder exata) — acurácia x tempo (min)

|                 |    30 |    60 |    90 |   120 |   180 |   240 |   360 |   480 |
|:----------------|------:|------:|------:|------:|------:|------:|------:|------:|
| ('css', 'H1')   | 0.152 | 0.16  | 0.16  | 0.152 | 0.169 | 0.198 | 0.232 | 0.3   |
| ('css', 'H4')   | 0.152 | 0.152 | 0.152 | 0.152 | 0.152 | 0.16  | 0.16  | 0.165 |
| ('css', 'M15')  | 0.11  | 0.118 | 0.148 | 0.156 | 0.203 | 0.249 | 0.342 | 0.321 |
| ('css', 'M5')   | 0.101 | 0.11  | 0.177 | 0.181 | 0.245 | 0.249 | 0.215 | 0.207 |
| ('cssm', 'H1')  | 0.127 | 0.131 | 0.131 | 0.118 | 0.148 | 0.148 | 0.173 | 0.173 |
| ('cssm', 'H4')  | 0.118 | 0.118 | 0.118 | 0.118 | 0.118 | 0.139 | 0.139 | 0.16  |
| ('cssm', 'M15') | 0.135 | 0.105 | 0.122 | 0.131 | 0.181 | 0.181 | 0.211 | 0.253 |
| ('cssm', 'M5')  | 0.089 | 0.11  | 0.127 | 0.156 | 0.207 | 0.266 | 0.291 | 0.312 |
| ('site', 'H1')  | 0.165 | 0.156 | 0.156 | 0.16  | 0.16  | 0.198 | 0.241 | 0.253 |
| ('site', 'H4')  | 0.135 | 0.135 | 0.135 | 0.135 | 0.135 | 0.143 | 0.143 | 0.156 |
| ('site', 'M15') | 0.101 | 0.097 | 0.101 | 0.131 | 0.165 | 0.232 | 0.308 | 0.232 |
| ('site', 'M5')  | 0.076 | 0.089 | 0.173 | 0.181 | 0.245 | 0.236 | 0.181 | 0.127 |


## Régua B3 (top-3) — acurácia x tempo (min)

|                 |    30 |    60 |    90 |   120 |   180 |   240 |   360 |   480 |
|:----------------|------:|------:|------:|------:|------:|------:|------:|------:|
| ('css', 'H1')   | 0.38  | 0.38  | 0.38  | 0.38  | 0.388 | 0.422 | 0.473 | 0.549 |
| ('css', 'H4')   | 0.384 | 0.384 | 0.384 | 0.384 | 0.384 | 0.388 | 0.388 | 0.426 |
| ('css', 'M15')  | 0.342 | 0.359 | 0.388 | 0.422 | 0.473 | 0.574 | 0.637 | 0.637 |
| ('css', 'M5')   | 0.312 | 0.354 | 0.477 | 0.511 | 0.502 | 0.549 | 0.46  | 0.536 |
| ('cssm', 'H1')  | 0.342 | 0.354 | 0.354 | 0.359 | 0.371 | 0.384 | 0.414 | 0.401 |
| ('cssm', 'H4')  | 0.367 | 0.367 | 0.367 | 0.367 | 0.367 | 0.401 | 0.401 | 0.414 |
| ('cssm', 'M15') | 0.376 | 0.338 | 0.359 | 0.342 | 0.418 | 0.422 | 0.451 | 0.549 |
| ('cssm', 'M5')  | 0.388 | 0.401 | 0.384 | 0.401 | 0.456 | 0.557 | 0.616 | 0.646 |
| ('site', 'H1')  | 0.397 | 0.401 | 0.401 | 0.392 | 0.371 | 0.414 | 0.464 | 0.523 |
| ('site', 'H4')  | 0.338 | 0.338 | 0.338 | 0.338 | 0.338 | 0.35  | 0.35  | 0.409 |
| ('site', 'M15') | 0.333 | 0.321 | 0.312 | 0.371 | 0.485 | 0.565 | 0.62  | 0.561 |
| ('site', 'M5')  | 0.295 | 0.3   | 0.494 | 0.511 | 0.527 | 0.586 | 0.392 | 0.46  |


## Q10 — aos 30 min de Tóquio (ordenado por top-3)

| indicador   | tf   |   accA |   accB3 |   mov_feito |
|:------------|:-----|-------:|--------:|------------:|
| site        | H1   |  0.165 |   0.397 |       0.178 |
| cssm        | M5   |  0.089 |   0.388 |       0.178 |
| css         | H4   |  0.152 |   0.384 |       0.178 |
| css         | H1   |  0.152 |   0.38  |       0.178 |
| cssm        | M15  |  0.135 |   0.376 |       0.178 |
| cssm        | H4   |  0.118 |   0.367 |       0.178 |
| cssm        | H1   |  0.127 |   0.342 |       0.178 |
| css         | M15  |  0.11  |   0.342 |       0.178 |
| site        | H4   |  0.135 |   0.338 |       0.178 |
| site        | M15  |  0.101 |   0.333 |       0.178 |
| css         | M5   |  0.101 |   0.312 |       0.178 |
| site        | M5   |  0.076 |   0.295 |       0.178 |


## Q8 — melhor acurácia (top-3) COM movimento ainda na mesa (mov<=50%)

| indicador   | tf   |   t_min |   accB3 |   mov_feito |
|:------------|:-----|--------:|--------:|------------:|
| css         | M15  |     360 |   0.637 |       0.479 |
| site        | M15  |     360 |   0.62  |       0.479 |
| cssm        | M5   |     360 |   0.616 |       0.479 |
| site        | M5   |     240 |   0.586 |       0.392 |
| css         | M15  |     240 |   0.574 |       0.392 |


## Significância (BH 5% sobre a família) — t mais cedo que bate o acaso (B3)

| indicador   | tf   |   t_signif |   accB3 |   mov_feito |
|:------------|:-----|-----------:|--------:|------------:|
| css         | M5   |         90 |   0.477 |       0.26  |
| site        | M5   |         90 |   0.494 |       0.26  |
| cssm        | M5   |        180 |   0.456 |       0.333 |
| css         | M15  |        180 |   0.473 |       0.333 |
| site        | M15  |        180 |   0.485 |       0.333 |
| css         | H1   |        360 |   0.473 |       0.479 |
| cssm        | M15  |        360 |   0.451 |       0.479 |
| site        | H1   |        360 |   0.464 |       0.479 |
| css         | H4   |        nan | nan     |     nan     |
| cssm        | H1   |        nan | nan     |     nan     |
| cssm        | H4   |        nan | nan     |     nan     |
| site        | H4   |        nan | nan     |     nan     |

_Régua B3 vs acaso 37.5%. Nº de células (de 96) que sobrevivem a BH: 29. Combos onde t_signif é vazio nunca batem o acaso out-of-sample._


## Veredito

**Régua A (líder exata): nula** — nunca fica utilizável (~0.30 máx às 8h; aos 30 min está no acaso em TODOS os indicadores/TFs, Q10).

**Régua B (top-3): sinal real, precoce e modesto.** O M5 (css/site) bate o acaso (BH 5%, out-of-sample) já aos **90 min**, com **só 26% do range do dia feito** (74% na mesa) e acurácia ~0.48 vs 0.375 do acaso; M15 aos 180 min, H1 aos 360 min, **H4 nunca** — trade-off rápido>lento confirmado e ordenado. Fortalece até ~0.6 às 4-6h. O custo do atraso é baixo (range sobe devagar: ~40% às 4h). Coerente com o a31 (43% do campeão já visível na asia): não dá pra cravar a líder cedo, mas dá pra ESTREITAR para 3 candidatas com a maior parte do movimento ainda por vir — melhor que o nulo pré-abertura do a24. Edge pequeno; badge probabilístico com latência conhecida, jamais sinal de T0.

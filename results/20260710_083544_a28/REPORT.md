# a28 — Comportamento da moeda preponderante (descritivo, por preço)

3116 dias, 2016-07-11 -> 2026-07-09. Preponderante por consistência direcional (0-7) dos 7 pares da moeda; força normalizada pelo range típico do par.

## Q1 — Frequência da preponderante (consistência da moeda líder)

|         |   n_dias |   lider>=6/7 |   lider=7/7 |   7/7 E forca>=0.5 |
|:--------|---------:|-------------:|------------:|-------------------:|
| asia    |     2592 |        0.976 |       0.838 |              0.645 |
| londres |     2593 |        0.994 |       0.911 |              0.709 |
| ny      |     2611 |        0.988 |       0.874 |              0.65  |
| dia     |     3116 |        0.975 |       0.848 |              0.616 |

_No DIA, a líder bate >=6/7 em 98% e 7/7 em 85%. Consistência sozinha é quase universal — o '~88%' útil da tese aparece só com MAGNITUDE: 7/7 E forca>=0.5 ATR = 62%._

## Q2 — Direção e viés por moeda

- lidera por FORÇA (moeda forte) em 50% vs por FRAQUEZA em 50% dos dias.

- viés de fraqueza por moeda (vezes anti-líder / (líder+anti)):

|     |   vezes_lider |   vezes_anti |   vies_fraqueza |
|:----|--------------:|-------------:|----------------:|
| JPY |           406 |          643 |           0.613 |
| CHF |           321 |          413 |           0.563 |
| CAD |           328 |          355 |           0.52  |
| USD |           424 |          380 |           0.473 |
| NZD |           415 |          370 |           0.471 |
| EUR |           323 |          272 |           0.457 |
| GBP |           433 |          338 |           0.438 |
| AUD |           466 |          345 |           0.425 |


## Q3 — Continuidade da liderança entre sessões

|               |   P(mesma líder) |
|:--------------|-----------------:|
| asia->londres |            0.135 |
| londres->ny   |            0.133 |
| asia->ny      |            0.135 |
| acaso (1/8)   |            0.125 |

_Londres cria líder novo em 86% dos dias; NY em 87%. Acima do acaso (7/8=88%) = herda; perto = cria._

## Q4 — Persistência / meia-vida da liderança

- líder do dia = líder do dia anterior em **14%** (acaso 12.5%).

- líder do dia coincide com a líder de cada sessão: asia 32%, londres 41%, ny 39%.


## Q5 — Limpo (7/7) vs sujo (6/7, 5/7): força da líder por consistência

|   leader_consist |   forca_mediana |
|-----------------:|----------------:|
|                4 |           0.241 |
|                5 |           0.286 |
|                6 |           0.458 |
|                7 |           0.736 |

_Se a força cresce forte com a consistência, o 'quão preponderante' importa muito — o 7/7 limpo é um dia materialmente maior._

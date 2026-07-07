# a17 — Tempo-de-trava (pares: usd7)

Dias research: 395 | eventos rotulados analisados: 784

Pré-registro no CHANGELOG (2026-07-07), commitado antes da execução.

## AVISO DE HONESTIDADE (pré-registrado)
`t_lock` é definido COM RETROSPECTO: só se sabe que o último cruzamento de zero foi o último porque o sinal não virou depois, dentro da janela. As distribuições abaixo descrevem a ANATOMIA dos dias rotulados; t_lock NÃO é regra de entrada.

## Distribuições (horas desde T0)

- t_lock  (geral): mediana 3.3h | IQR [1.0, 9.0]h | p90 11.0h
- t_half  (geral): mediana 3.8h | IQR [1.8, 6.9]h | p90 9.3h

| moeda | n | t_lock mediana (h) | t_half mediana (h) |
|---|---|---|---|
| AUD | 88 | 2.5 | 3.8 |
| CAD | 71 | 7.6 | 1.9 |
| CHF | 110 | 3.5 | 3.1 |
| EUR | 105 | 5.8 | 3.2 |
| GBP | 104 | 8.7 | 3.8 |
| JPY | 119 | 2.9 | 3.8 |
| NZD | 96 | 2.4 | 4.1 |
| USD | 91 | 2.8 | 5.7 |

| direção | n | t_lock mediana (h) |
|---|---|---|
| ALTA | 404 | 3.4 |
| BAIXA | 380 | 3.3 |

| dia-da-semana | n | t_lock mediana (h) |
|---|---|---|
| seg | 167 | 2.8 |
| ter | 138 | 4.1 |
| qua | 153 | 3.2 |
| qui | 165 | 3.7 |
| sex | 161 | 3.3 |

## % de eventos já travados até T0+t

- T0+1h: **27.3%** travados
- T0+2h: **35.1%** travados
- T0+4h: **55.4%** travados
- T0+8h: **71.7%** travados

## Fração do movimento ainda por vir (mediana orientada)

- em T0+1h: **94.0%** do movimento final
- em T0+2h: **90.8%** do movimento final
- em T0+4h: **73.7%** do movimento final
- em T0+8h: **49.8%** do movimento final

## R-CONF(k) — grade fechada {1,2,4}h (pré-registrada)

Alvo: top-1 (moeda E direção) vs protagonista do dia | dias com protagonista: 346 | baseline persistência D-1: **8.1%** | reality check p95 sobre a grade: **8.9%**

| k | n opina | top-1 | bate persistência? | > p95? | frac_restante(k) mediana |
|---|---|---|---|---|---|
| 1h | 86 (n<100!) | 10.5% | SIM | SIM | 94.0% |
| 2h | 112 | 8.0% | não | não | 90.8% |
| 4h | 173 | 12.1% | SIM | SIM | 73.7% |

Nota pré-registrada: acerto em T0+k só tem valor econômico se a fração restante do movimento em T0+k for material — as duas colunas devem ser lidas juntas.

**Sobreviventes:** k=[4]

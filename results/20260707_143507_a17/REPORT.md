# a17 — Tempo-de-trava (pares: all28)

Dias research: 395 | eventos rotulados analisados: 784

Pré-registro no CHANGELOG (2026-07-07), commitado antes da execução.

## AVISO DE HONESTIDADE (pré-registrado)
`t_lock` é definido COM RETROSPECTO: só se sabe que o último cruzamento de zero foi o último porque o sinal não virou depois, dentro da janela. As distribuições abaixo descrevem a ANATOMIA dos dias rotulados; t_lock NÃO é regra de entrada.

## Distribuições (horas desde T0)

- t_lock  (geral): mediana 2.4h | IQR [0.5, 5.4]h | p90 8.9h
- t_half  (geral): mediana 4.9h | IQR [3.0, 8.2]h | p90 9.8h

| moeda | n | t_lock mediana (h) | t_half mediana (h) |
|---|---|---|---|
| AUD | 88 | 2.0 | 4.3 |
| CAD | 71 | 1.9 | 4.8 |
| CHF | 110 | 1.5 | 4.9 |
| EUR | 105 | 3.2 | 6.0 |
| GBP | 104 | 5.1 | 8.4 |
| JPY | 119 | 2.0 | 4.0 |
| NZD | 96 | 2.2 | 4.4 |
| USD | 91 | 2.4 | 5.5 |

| direção | n | t_lock mediana (h) |
|---|---|---|
| ALTA | 404 | 2.7 |
| BAIXA | 380 | 2.1 |

| dia-da-semana | n | t_lock mediana (h) |
|---|---|---|
| seg | 167 | 2.1 |
| ter | 138 | 2.9 |
| qua | 153 | 2.1 |
| qui | 165 | 2.4 |
| sex | 161 | 2.6 |

## % de eventos já travados até T0+t

- T0+1h: **35.2%** travados
- T0+2h: **45.9%** travados
- T0+4h: **66.5%** travados
- T0+8h: **84.6%** travados

## Fração do movimento ainda por vir (mediana orientada)

- em T0+1h: **95.4%** do movimento final
- em T0+2h: **89.4%** do movimento final
- em T0+4h: **73.1%** do movimento final
- em T0+8h: **47.0%** do movimento final

## R-CONF(k) — grade fechada {1,2,4}h (pré-registrada)

Alvo: top-1 (moeda E direção) vs protagonista do dia | dias com protagonista: 346 | baseline persistência D-1: **8.1%** | reality check p95 sobre a grade: **12.8%**

| k | n opina | top-1 | bate persistência? | > p95? | frac_restante(k) mediana |
|---|---|---|---|---|---|
| 1h | 187 | 11.2% | SIM | não | 95.4% |
| 2h | 326 | 14.4% | SIM | SIM | 89.4% |
| 4h | 329 | 21.0% | SIM | SIM | 73.1% |

Nota pré-registrada: acerto em T0+k só tem valor econômico se a fração restante do movimento em T0+k for material — as duas colunas devem ser lidas juntas.

**Sobreviventes:** k=[2, 4]

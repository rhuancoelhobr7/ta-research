# a30 — Volume e momentum da moeda preponderante

237 dias de teste (OOS). Sinais M5 cumulativos no dia (sem lookahead). Verdade = líder no fechamento. Régua B3 (top-3), acaso 37.5%.

## Q11/Q12 — a líder se destaca em volume/momentum? (percentil no fim do dia)

- **volume**: a líder fica no percentil **62%** das 8 moedas (50% = mediana; >50% = destaca).

- **momentum (preço)**: percentil **100%**.

## Q13 — Timing: quando o sinal da futura líder se destaca (top-3 x tempo)

|   t_min |   volume |   momentum |
|--------:|---------:|-----------:|
|      30 |    0.367 |      0.401 |
|      60 |    0.376 |      0.418 |
|      90 |    0.388 |      0.477 |
|     120 |    0.371 |      0.498 |
|     180 |    0.35  |      0.523 |
|     240 |    0.359 |      0.633 |
|     360 |    0.409 |      0.633 |
|     480 |    0.418 |      0.679 |


- volume bate o acaso (BH) em **None min**; momentum em **90 min**; comparação M5 do css/site: **90 min** (a29).


## Q13/Q14 — Veredito

**Momentum (preço puro, com sinal) detecta a líder aos 90 min — o MESMO tempo do css M5 (90 min)** — e mais forte depois (top-3 0.63 às 4h). Ou seja, o **CSS não agrega nada sobre o preço bruto**: como o CSS é uma transformação do preço, olhar quem subiu mais até agora dá o mesmo sinal, mais cedo e mais direto.

**Volume NÃO detecta a líder** (nunca bate o acaso; percentil da líder só 62%). Motivo estrutural: volume é CEGO À DIREÇÃO — marca a moeda mais ATIVA, que é a líder OU a anti-líder (ambas movem/negociam muito). Serve para dizer 'algo está acontecendo', não 'quem vai liderar'.

**Q14 (ablação)**: adicionar volume ao detector não ajuda a escolher a líder (direção-cego); e o momentum já iguala o CSS. Nada novo entra. Reforça o tema do programa: o sinal está no PREÇO; CSS é transformação, não informação extra; volume é atividade, não direção.

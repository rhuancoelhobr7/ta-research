# a25 — Ranqueador de par operável (CSS-free)

Virada NY, alvo range [13,17) UTC. Modelo logístico interpretável em log(base_atr)+asia_norm. Split 70/30; backtest no teste (775 dias). CSS excluído (não passou no a24).

## Q8 — Modelo (coeficientes padronizados, interpretáveis)

|           |   coef |
|:----------|-------:|
| log_atr   |  1.518 |
| asia_norm |  0.006 |

_log_atr = largura estrutural do par; asia_norm = atividade de hoje vs a norma do par (Tokyo→Londres do a23)._


## Q9 — Backtest: range médio capturado (pips/dia) no top-1

|                     |   modelo |   so_base_atr |
|:--------------------|---------:|--------------:|
| top1_modelo         |     77.7 |          77.5 |
| top3_modelo         |     71.2 |          71.2 |
| sempre_mais_volatil |     77.5 |          77.5 |
| aleatorio           |     43   |          43   |
| teto_do_dia         |     97.7 |          97.7 |

- **lift do top-1 vs aleatório: 1.81×**  ·  captura 80% do teto possível do dia.

- modelo top-1 (77.7) vs sempre-o-mais-volátil (77.5): ganho marginal do sinal de hoje.


## Q10 — Estabilidade do top-1

- top-1 igual ao dia anterior: **84%** (troca de instrumento no resto dos dias).

- pares distintos que já foram top-1 no teste: 8.


## Nota honesta

Ranqueia por MOVIMENTO ESPERADO, não por lucro. Movimento é condição necessária, não suficiente — direção e gestão ficam com o trader. O CSS não entra: o produto é ATR-de-sessão + inclinação Tokyo→Londres.

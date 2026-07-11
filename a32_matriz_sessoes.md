# a32 — ATR/volatilidade entre todas as sessões (matriz completa)

Deliverable da bateria a28–a32. Fecha o a23 (que só olhou Tóquio→Londres→NY).
Sequência cronológica asia→londres→ny→asia(dia+1); matriz 3×3 "de sessão X para
a PRÓXIMA ocorrência de Y" (inclui wrap-around NY→Tóquio do dia seguinte).
Spearman por par, out-of-sample, IC bootstrap em blocos. `results/*_a32/`.

## Achados

**Q20/Q21 — Matriz completa (Spearman mediano entre 28 pares).**

| de \ para | asia | londres | ny |
|---|---|---|---|
| **asia** | 0.311 | **0.341** | 0.269 |
| **londres** | 0.265 | 0.261 | **0.337** |
| **ny** | 0.273 | 0.263 | 0.281 |

**Todas as 9 células são positivas e significativas** (0.26-0.34, IC não cruza
0): a volatilidade gruda em QUALQUER transição de sessão, não só Tóquio→Londres.
As adjacentes são as mais fortes e iguais entre si: asia→londres 0.341 ≈
londres→ny 0.337.

**Q22 — NY → Tóquio (dia seguinte), com %.** Spearman **0.273** (IC [0.247,
0.301]) = **7.4%** da variância de rank compartilhada. A volatilidade de NY VAZA
para a abertura asiática seguinte — efeito real, porém menor que o adjacente
intradia.

**Q23 — Decaimento por distância.** NÃO é monotônico: dist 1 (adjacente) = 0.337
> dist 3 (mesma sessão no dia seguinte) = 0.281 > dist 2 = 0.265. O **salto no
dist 3** (ex.: asia→asia 0.311) acima do dist 2 revela **sazonalidade de
sessão** — cada sessão correlaciona com ela mesma no dia seguinte mais do que
com a sessão 2 slots à frente.

## Leitura
Consolida o achado transversal da bateria: **RANGE/volatilidade tem memória forte
e pervasiva** (a23 + a32), o que sustenta o ranqueador por ATR de sessão do a25.
A DIREÇÃO/liderança, ao contrário, não tem memória (a28). Para escolher par por
AMPLITUDE, a estrutura de sessões é uma âncora robusta.

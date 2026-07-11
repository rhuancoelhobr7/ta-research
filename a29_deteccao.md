# a29 — Curva de detecção: a partir de quantas horas o indicador acerta?

**A pergunta central do Carlos.** Se CSS/CSSM/site não preveem em T0, quando
começam a acertar? Deliverable da bateria a28–a32. Verdade = líder do dia por
PREÇO no fechamento; 237 dias de teste out-of-sample; indicadores recomputados
dos M5 (3 anos). Tabelas completas em `results/*_a29/REPORT.md`.

**Método v1 (barras fechadas).** No tempo *t*, cada TF usa a última barra
FECHADA ≤ abertura+*t* — logo TFs rápidos (M5/M15) atualizam cedo e lentos
(H1/H4) só no fechamento da sua barra. Isso capta o trade-off central. A leitura
intra-barra (forming) adiantaria os TFs lentos: refinamento v2 documentado.

**Réguas.** A = apontar a líder EXATA do fechamento (acaso 12.5%). B = apontar
uma no top-3 de força (acaso 37.5%).

## Achados

**Q10 — Aos 30 min de Tóquio: ACASO.** Todos os indicadores × TFs ficam no acaso
(top-3 ~0.38; régua A ~0.13). *A intuição dos "30 minutos" não se sustenta.*

**Custo do atraso (fração do range do dia já feita).** Sobe devagar: 18% aos
30 min, 26% aos 90 min, 40% às 4h, 53% às 8h. → *Sobra movimento mesmo detectando
tarde* — o atraso não é fatal.

**Régua A (líder exata): NULA.** Nunca fica utilizável (~0.30 no máximo às 8h).

**Régua B (top-3): sinal real, precoce e MODESTO.** Trade-off ordenado (BH 5%,
out-of-sample), t mais cedo em que cada TF bate o acaso:

| TF | t significativo | acurácia top-3 | range já feito |
|---|---|---|---|
| **M5** (css/site) | **90 min** | 0.48 | 26% |
| M15 | 180 min | 0.47 | 33% |
| H1 | 360 min | 0.47 | 48% |
| H4 | **nunca** | — | — |

Fortalece a ~0.6 às 4-6h. **29/96 células** sobrevivem a BH.

## Veredito
Não dá pra **cravar a líder** cedo (régua A nula), mas dá pra **estreitar para
3 candidatas** já aos ~90 min via TF rápido (M5), com **74% do movimento ainda
por vir**. É melhor que o nulo pré-abertura do a24 e coerente com o a31 (43% do
par campeão já visível na asia). O edge é pequeno — serve como **badge
probabilístico com latência conhecida, nunca sinal de T0**.

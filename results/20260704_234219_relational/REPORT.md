# Validação da camada relacional (dias research; holdout intocado)

Camada DESCRITIVA — nowcasting, diagnóstico, seleção de par. Os nulos preditivos do programa (A5/A8/v2) permanecem válidos; só a Etapa 5 é preditiva e segue a disciplina completa.

### Critério PRÉ-REGISTRADO (Etapa 5, única preditiva)
UMA regra, sem grade: em T0+4h, líder por nowcast (w=64) => célula de maior
|M| orientado na linha => retorno orientado do PAR em [T0+4h, T0+12h]
(disjunto, guarda testada). Sucesso = média de (par escolhido − média dos 7
pares do mesmo dia/direção) com IC95% em blocos INTEIRAMENTE acima de 0 e
n >= 100 dias. Fora disso = NULO, sem afrouxamento.

## Etapa 1 — Latência de convergência do nowcast

**Framing obrigatório**: janelas SOBREPOSTAS por construção — isto mede latência de *reconhecimento* (nowcast), NÃO previsão.

n = 346 dias rotulados research; acerto = (moeda E direção) da líder vs protagonista rotulada (top-score).

| lente | métrica | instante | top-1 | IC95% | top-2 |
|---|---|---|---|---|---|
| 64 | nowcast | T0+2h | **4.9%** | [2.9, 7.2] | 13.3% |
| 64 | nowcast | T0+4h | **8.4%** | [5.5, 11.6] | 15.0% |
| 64 | nowcast | T0+6h | **9.3%** | [6.4, 12.2] | 18.3% |
| 64 | nowcast | T0+8h | **10.1%** | [7.5, 13.0] | 18.8% |
| 64 | nowcast | T0+12h | **16.2%** | [12.2, 20.3] | 30.1% |
| 64 | breadth_hard | T0+2h | **4.6%** | [2.6, 6.9] | 8.7% |
| 64 | breadth_hard | T0+4h | **6.9%** | [4.6, 9.2] | 11.6% |
| 64 | breadth_hard | T0+6h | **8.4%** | [5.8, 11.3] | 13.0% |
| 64 | breadth_hard | T0+8h | **7.8%** | [5.5, 10.4] | 15.3% |
| 64 | breadth_hard | T0+12h | **11.6%** | [8.1, 15.3] | 20.2% |
| 24 | nowcast | T0+2h | **6.4%** | [3.8, 9.0] | 12.1% |
| 24 | nowcast | T0+4h | **9.0%** | [6.1, 11.8] | 16.8% |
| 24 | nowcast | T0+6h | **11.3%** | [7.8, 15.1] | 21.7% |
| 24 | nowcast | T0+8h | **12.8%** | [9.3, 16.2] | 24.1% |
| 24 | nowcast | T0+12h | **27.8%** | [23.5, 32.5] | 46.4% |
| 24 | breadth_hard | T0+2h | **4.6%** | [2.6, 6.9] | 10.4% |
| 24 | breadth_hard | T0+4h | **7.8%** | [5.2, 10.7] | 14.5% |
| 24 | breadth_hard | T0+6h | **8.7%** | [6.1, 11.6] | 15.9% |
| 24 | breadth_hard | T0+8h | **11.3%** | [8.7, 13.9] | 19.1% |
| 24 | breadth_hard | T0+12h | **13.0%** | [10.1, 16.2] | 27.5% |

## Etapa 2 — Auditoria de força espúria

Instantes H1 (dias research) com índice AGREGADO ativo (|t_idx| ≥ gate) mas breadth_hard orientado < 3/7 — força que a cesta enxerga e os pares não confirmam.

### Lente w=64 (gate 2.14)

- Instantes ativos: 2088 | espúrios: 1328 (**63.6%** dos ativos)

| moeda | ativos | espúrios | % |
|---|---|---|---|
| CAD | 273 | 239 | 87.5% |
| EUR | 194 | 157 | 80.9% |
| GBP | 199 | 157 | 78.9% |
| USD | 531 | 327 | 61.6% |
| AUD | 193 | 117 | 60.6% |
| CHF | 195 | 117 | 60.0% |
| NZD | 225 | 130 | 57.8% |
| JPY | 278 | 84 | 30.2% |

### Lente w=24 (gate 2.47)

- Instantes ativos: 2189 | espúrios: 1366 (**62.4%** dos ativos)

| moeda | ativos | espúrios | % |
|---|---|---|---|
| CAD | 286 | 249 | 87.1% |
| GBP | 177 | 153 | 86.4% |
| EUR | 198 | 147 | 74.2% |
| CHF | 213 | 137 | 64.3% |
| AUD | 234 | 143 | 61.1% |
| USD | 355 | 213 | 60.0% |
| NZD | 383 | 191 | 49.9% |
| JPY | 343 | 133 | 38.8% |

### 5 exemplos concretos (w=64): a cesta acusa, os pares negam

#### 2024-10-03 19:00:00 — USD ALTA | t_idx=+3.59 (≥ gate) mas breadth_hard=29% (<3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |  X↑ |   · |   · |   · |   · |   · |  M↑ |
|  EUR |  X↓ |   — |   · |   · |   · |   · |   · |   · |
|  GBP |   · |   · |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |   · |
|  CAD |   · |   · |   · |   · |   · |   — |   · |  M↑ |
|  AUD |   · |   · |   · |   · |   · |   · |   — |   · |
|  NZD |  M↓ |   · |   · |   · |   · |  M↓ |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

Dominância do USD (últimas 64 barras): de onde veio a 'força' do agregado:

| vs | ret orientado (bp) | share |
|---|---|---|
| JPY | +212.2 | +22.7% |
| NZD | +207.0 | +22.1% |
| GBP | +195.8 | +21.0% |

#### 2024-10-07 22:00:00 — NZD BAIXA | t_idx=-3.28 (≥ gate) mas breadth_hard=29% (<3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |   · |   · |   · |   · |   · |   · |  M↑ |
|  EUR |   · |   — |   · |   · |   · |   · |   · |  M↑ |
|  GBP |   · |   · |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |  E↑ |
|  CAD |   · |   · |   · |   · |   · |   — |   · |   · |
|  AUD |   · |   · |   · |   · |   · |   · |   — |   · |
|  NZD |  M↓ |  M↓ |   · |   · |  E↓ |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

Dominância do NZD (últimas 64 barras): de onde veio a 'força' do agregado:

| vs | ret orientado (bp) | share |
|---|---|---|
| AUD | -33.1 | -3.9% |
| GBP | -70.1 | -8.3% |
| JPY | -118.8 | -14.0% |

#### 2024-08-16 13:00:00 — GBP ALTA | t_idx=+3.05 (≥ gate) mas breadth_hard=0% (<3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |   · |   · |   · |   · |   · |   · |   · |
|  EUR |   · |   — |   · |   · |   · |   · |   · |   · |
|  GBP |   · |   · |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |   · |
|  CAD |   · |   · |   · |   · |   · |   — |   · |   · |
|  AUD |   · |   · |   · |   · |   · |   · |   — |   · |
|  NZD |   · |   · |   · |   · |   · |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

Dominância do GBP (últimas 64 barras): de onde veio a 'força' do agregado:

| vs | ret orientado (bp) | share |
|---|---|---|
| JPY | +154.1 | +33.8% |
| NZD | +103.7 | +22.7% |
| CHF | +75.4 | +16.5% |

#### 2024-10-03 04:00:00 — CAD ALTA | t_idx=+3.04 (≥ gate) mas breadth_hard=29% (<3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |  X↑ |   · |  M↑ |   · |   · |   · |   · |
|  EUR |  X↓ |   — |   · |   · |   · |  X↓ |   · |   · |
|  GBP |   · |   · |   — |  E↑ |   · |   · |   · |   · |
|  JPY |  M↓ |   · |  E↓ |   — |  M↓ |  M↓ |   · |   · |
|  CHF |   · |   · |   · |  M↑ |   — |   · |   · |   · |
|  CAD |   · |  X↑ |   · |  M↑ |   · |   — |   · |   · |
|  AUD |   · |   · |   · |   · |   · |   · |   — |   · |
|  NZD |   · |   · |   · |   · |   · |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

Dominância do CAD (últimas 64 barras): de onde veio a 'força' do agregado:

| vs | ret orientado (bp) | share |
|---|---|---|
| JPY | +323.4 | +33.6% |
| NZD | +185.4 | +19.3% |
| EUR | +153.9 | +16.0% |

#### 2025-02-13 09:00:00 — EUR ALTA | t_idx=+3.00 (≥ gate) mas breadth_hard=29% (<3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |   · |   · |  E↑ |   · |   · |   · |   · |
|  EUR |   · |   — |   · |  M↑ |  M↑ |   · |   · |   · |
|  GBP |   · |   · |   — |  M↑ |   · |   · |   · |   · |
|  JPY |  E↓ |  M↓ |  M↓ |   — |   · |  M↓ |   · |   · |
|  CHF |   · |  M↓ |   · |   · |   — |   · |   · |   · |
|  CAD |   · |   · |   · |  M↑ |   · |   — |   · |   · |
|  AUD |   · |   · |   · |   · |   · |   · |   — |   · |
|  NZD |   · |   · |   · |   · |   · |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

Dominância do EUR (últimas 64 barras): de onde veio a 'força' do agregado:

| vs | ret orientado (bp) | share |
|---|---|---|
| JPY | +270.3 | +34.0% |
| CHF | +124.9 | +15.7% |
| NZD | +115.0 | +14.5% |

## Etapa 3 — Matrizes nos dias do especialista

**As 7 chamadas de specialist_calls.csv caem TODAS no holdout** (que começa em 2026-02-17) — renderizá-las exporia o holdout, então esta etapa fica adiada até ordem explícita (junto com a7). Como validação visual substituta, seguem os 2 dias RESEARCH de maior nowcast (w=64), com a linha da líder em T0+4h e T0+12h:

#### 2024-08-20 T0+4h — líder USD (linha ativa contra 3/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |   · |  M↓ |   · |   · |   · |  M↓ |  M↓ |
|  EUR |   · |   — |   · |   · |   · |   · |   · |  M↓ |
|  GBP |  M↑ |   · |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |   · |
|  CAD |   · |   · |   · |   · |   · |   — |  M↓ |  M↓ |
|  AUD |  M↑ |   · |   · |   · |   · |  M↑ |   — |   · |
|  NZD |  M↑ |  M↑ |   · |   · |   · |  M↑ |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

#### 2024-08-20 T0+12h — líder USD (linha ativa contra 6/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |  M↓ |  X↓ |   · |  M↓ |  M↓ |  M↓ |  M↓ |
|  EUR |  M↑ |   — |   · |   · |   · |   · |   · |  M↓ |
|  GBP |  X↑ |   · |   — |   · |   · |   · |   · |  M↓ |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |  M↑ |   · |   · |   · |   — |   · |   · |   · |
|  CAD |  M↑ |   · |   · |   · |   · |   — |  M↓ |  M↓ |
|  AUD |  M↑ |   · |   · |   · |   · |  M↑ |   — |   · |
|  NZD |  M↑ |  M↑ |  M↑ |   · |   · |  M↑ |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

#### 2025-03-06 T0+4h — líder EUR (linha ativa contra 5/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |  M↓ |  M↓ |   · |   · |   · |   · |   · |
|  EUR |  M↑ |   — |  M↑ |   · |   · |  M↑ |  M↑ |  E↑ |
|  GBP |  M↑ |  M↓ |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |   · |
|  CAD |   · |  M↓ |   · |   · |   · |   — |   · |   · |
|  AUD |   · |  M↓ |   · |   · |   · |   · |   — |   · |
|  NZD |   · |  E↓ |   · |   · |   · |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

#### 2025-03-06 T0+12h — líder EUR (linha ativa contra 4/7)

|      | USD | EUR | GBP | JPY | CHF | CAD | AUD | NZD |
|---|---|---|---|---|---|---|---|---|
|  USD |   — |  M↓ |  E↓ |   · |   · |   · |   · |   · |
|  EUR |  M↑ |   — |  M↑ |   · |   · |   · |  E↑ |  E↑ |
|  GBP |  E↑ |  M↓ |   — |   · |   · |   · |   · |   · |
|  JPY |   · |   · |   · |   — |   · |   · |   · |   · |
|  CHF |   · |   · |   · |   · |   — |   · |   · |   · |
|  CAD |   · |   · |   · |   · |   · |   — |   · |   · |
|  AUD |   · |  E↓ |   · |   · |   · |   · |   — |   · |
|  NZD |   · |  E↓ |   · |   · |   · |   · |   · |   — |

Legenda: M=Madura E=Emergindo X=Exausta ·=Ruído; seta = direção da LINHA vs coluna.

## Etapa 4 — Concordância nowcast × rótulo em T0+12h

- **w=64**: líder=protagonista (moeda+direção): **16.2%** [12.2, 20.3]; só moeda: 17.4% [13.6, 21.4] (n=345); nowcast protagonistas 0.082 vs demais 0.058 — **d de Cohen +0.25**
- **w=24**: líder=protagonista (moeda+direção): **27.8%** [23.5, 32.5]; só moeda: 28.7% [24.3, 32.8] (n=345); nowcast protagonistas 0.174 vs demais 0.086 — **d de Cohen +0.57**

## Etapa 5 — Seleção de par condicional (única preditiva)

Dias com decisão válida: **394** (pulados: 1)
- Par escolhido (média, bp): -0.46 | média dos 7: -1.64
- **Diferença (escolhido − média dos 7): +1.18 bp** IC95% [-0.65, +3.00]
- Baseline par aleatório − média: +1.38 bp (esperança ≈ 0 por construção)

**Veredicto Etapa 5: NULO** (critério pré-registrado: IC inteiro > 0 e n ≥ 100).

## Fechamento honesto

O que a camada ENTREGA em dados reais: a auditoria de espúrios é o resultado forte — ~2 em cada 3 instantes 'ativos' do índice agregado não são confirmados pelos pares (63.6% w=64), e a matriz + dominância mostram caso a caso de onde veio a força fantasma. Como diagnóstico anti-contaminação, a camada se paga.

O que a camada NÃO entrega: como 'rotulador em tempo real', o critério de utilidade da Etapa 4 pedia concordância ALTA no fim da janela — e ela é baixa: 16% (w=64) / 28% (w=24) em T0+12h, com latência que nunca converge (16%/28% top-1 mesmo com a janela encerrada). O padrão é o mesmo do v2: a janela rolante (64 ou 24 barras H1) mede outra coisa que a janela-calendário [T0,T0+12h] do rótulo — o w=24 dobra a concordância do w=64 exatamente por ser mais curto, e a separação descritiva d=+0.57 (w=24) diz que o nowcast das protagonistas é maior em média, mas não o bastante para apontá-las. E a seleção de par condicional NÃO agrega sobre a média dos 7 pares pelo critério pré-registrado (+1.2 bp, IC cruza 0 — indistinguível do par aleatório).

Os nulos preditivos de A5/A8/v2 permanecem intactos: nada aqui prevê o dia. Holdout intocado; a7 não é proposto.

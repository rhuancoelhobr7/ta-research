# a21 — CSS como filtro de setups independentes (28 pares, H1 10a; split 70/30 em 2023-07-17)

Pré-registro CHANGELOG 2026-07-08. Custos incluídos (spread mediano + 0.5 pip). Lente css_screen (paridade 5e-9).

## Setups-base SEM filtro (sanidade — trap #1)

| setup | amostra | n | expectancy (R) | PF | hit |
|---|---|---|---|---|---|
| S1 | in | 59202 | -0.069 | 0.89 | 41.9% |
| S1 | out | 25441 | -0.122 | 0.81 | 39.9% |
| S2 | in | 39290 | -0.061 | 0.90 | 42.2% |
| S2 | out | 17531 | -0.086 | 0.86 | 41.5% |
| S3 | in | 29714 | -0.075 | 0.88 | 41.6% |
| S3 | out | 12270 | -0.037 | 0.94 | 43.4% |

## Teste principal — Δ expectancy (filtrado − todos), OUT-OF-SAMPLE

Sucesso: Δ>=+0.10R, IC exclui 0, BH-ok, em >=2/3 setups p/ o mesmo filtro. n_f<100 = inconclusivo.

| setup | dir | filtro | n todos | n filtro | Δexp (R) | IC95% | BH | passa? |
|---|---|---|---|---|---|---|---|---|
| S1 | long | f1 | 13458 | 1260 | +0.018 | [-0.052, +0.089] | não | não |
| S1 | long | f2 | 13458 | 1260 | +0.018 | [-0.052, +0.089] | não | não |
| S1 | long | f3 | 13458 | 540 | +0.028 | [-0.069, +0.112] | não | não |
| S1 | long | f4 | 13458 | 484 | -0.006 | [-0.109, +0.092] | não | não |
| S1 | short | f1 | 11983 | 839 | +0.013 | [-0.091, +0.103] | não | não |
| S1 | short | f2 | 11983 | 839 | +0.013 | [-0.091, +0.103] | não | não |
| S1 | short | f3 | 11983 | 342 | +0.073 | [-0.102, +0.222] | não | não |
| S1 | short | f4 | 11983 | 418 | +0.038 | [-0.064, +0.146] | não | não |
| S2 | long | f1 | 9289 | 1436 | -0.030 | [-0.091, +0.034] | não | não |
| S2 | long | f2 | 9289 | 1436 | -0.030 | [-0.091, +0.034] | não | não |
| S2 | long | f3 | 9289 | 607 | -0.004 | [-0.091, +0.081] | não | não |
| S2 | long | f4 | 9289 | 333 | +0.065 | [-0.054, +0.185] | não | não |
| S2 | short | f1 | 8242 | 1023 | -0.054 | [-0.139, +0.027] | não | não |
| S2 | short | f2 | 8242 | 1023 | -0.054 | [-0.139, +0.027] | não | não |
| S2 | short | f3 | 8242 | 452 | -0.052 | [-0.169, +0.074] | não | não |
| S2 | short | f4 | 8242 | 260 | +0.041 | [-0.103, +0.190] | não | não |
| S3 | long | f1 | 5937 | 486 | -0.007 | [-0.107, +0.100] | não | não |
| S3 | long | f2 | 5937 | 486 | -0.007 | [-0.107, +0.100] | não | não |
| S3 | long | f3 | 5937 | 163 | -0.122 | [-0.313, +0.076] | não | não |
| S3 | long | f4 | 5937 | 195 | +0.071 | [-0.079, +0.232] | não | não |
| S3 | short | f1 | 6333 | 369 | +0.040 | [-0.085, +0.172] | não | não |
| S3 | short | f2 | 6333 | 369 | +0.040 | [-0.085, +0.172] | não | não |
| S3 | short | f3 | 6333 | 119 | +0.040 | [-0.165, +0.272] | não | não |
| S3 | short | f4 | 6333 | 263 | +0.105 | [-0.023, +0.242] | não | não |

## Veredito por filtro (critério: >=2/3 setups passam)

- f1: 0/6 células passam (não atinge critério)
- f2: 0/6 células passam (não atinge critério)
- f3: 0/6 células passam (não atinge critério)
- f4: 0/6 células passam (não atinge critério)

## Controle negativo — F1-inverso (operar CONTRA; deve PIORAR)

| setup | dir | Δexp inv (R) | IC95% |
|---|---|---|---|
| S1 | long | -0.025 | [-0.098, +0.049] |
| S1 | short | -0.004 | [-0.081, +0.076] |
| S2 | long | +0.019 | [-0.190, +0.224] |
| S2 | short | +0.313 | [+0.105, +0.511] |
| S3 | long | +0.002 | [-0.107, +0.132] |
| S3 | short | +0.027 | [-0.069, +0.127] |

## Custo de oportunidade (OOS, F3 empilhado)

| setup | % trades mantidos | % vencedores descartados |
|---|---|---|
| S1 | 3.5% | 96.4% |
| S2 | 6.0% | 94.2% |
| S3 | 2.3% | 97.8% |

## VEREDITO: **NULO — CSS como filtro não agrega; indicador é descritivo.**

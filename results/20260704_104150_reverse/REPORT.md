# A5 — Engenharia reversa em T0 (dias research)

## B1 — Contraste descritivo (rotulado vs não)

Maiores separações (d de Cohen):

| feature | d | média rot. | média não |
|---|---|---|---|
| W1_pers | -0.10 | +0.516 | +0.521 |
| D1_er | -0.08 | +0.104 | +0.110 |
| H1_dir | -0.07 | -0.041 | +0.032 |
| H4_er | -0.06 | +0.115 | +0.120 |
| W1_t | +0.05 | +0.044 | -0.001 |
| H4_pers | -0.05 | +0.530 | +0.533 |
| D1_dir | -0.05 | -0.061 | -0.012 |
| M30_dir | -0.05 | -0.046 | +0.003 |
| W1_M | +0.05 | +0.008 | +0.004 |
| H4_t | -0.04 | -0.010 | +0.030 |
| H4_M | -0.04 | +0.001 | +0.005 |
| M30_t | -0.04 | -0.022 | +0.015 |

Alinhamento do `dir` de cada TF com a direção rotulada (dias rotulados):

| TF | % alinhado | estado modal |
|---|---|---|
| M30 | 45.7% | Ruído |
| H1 | 46.2% | Ruído |
| H4 | 50.1% | Ruído |
| D1 | 53.6% | Ruído |
| W1 | 51.3% | Ruído |

## B2/B3 — Regras candidatas vs baselines

Dias research: 395 | acaso pareado (top-1 esperado): **12.4%** | reality check p95 dos máximos permutados (200 perm., blocos de 5): **17.5%**

| regra | n dias c/ previsão | top-1 | hit@2 | precision@2 | bate 3 baselines? | > p95 perm.? |
|---|---|---|---|---|---|---|
| maior_|M|_H4 | 395 | 10.9% | 20.5% | 11.4% | não | não |
| maior_|M|_D1 | 395 | 14.2% | 24.1% | 13.4% | não | não |
| maior_|M|_M30 | 395 | 10.1% | 19.5% | 11.0% | não | não |
| alinhamento_D1_H4_H1 | 395 | 13.4% | 22.0% | 12.0% | não | não |
| estado_D1xH4 | 3 (n<100!) | 0.0% | 0.0% | 0.0% | não | não |
| macro_W1_D1 | 395 | 12.4% | 21.0% | 11.9% | não | não |
| protoA_aprox | 1 (n<100!) | 0.0% | 0.0% | 0.0% | não | não |
| protoB_aprox | 183 | 13.7% | 16.4% | 8.5% | não | não |
| protoC_aprox | 12 (n<100!) | 0.0% | 0.0% | 0.0% | não | não |
| baseline_continuacao_D1 | 395 | 12.9% | 12.9% | 6.5% | — | — |
| baseline_persistencia | 394 | 14.5% | 14.5% | 7.2% | — | — |

Cenários P_A/P_B/P_C são APROXIMAÇÕES (documento do Protocolo ausente do repositório).

**Nenhuma regra sobreviveu** aos baselines + reality check — resultado nulo reportado (regra dura nº 7).

## B4 — Teto com ML honesto (alvo: rotula?)
Purged CV 5 folds, gap 5 dias; imputação por mediana do treino; AUC média ± dp entre folds.

### logistic: AUC = **0.487 ± 0.024**
Top features: D1_t (0.332), W1_t (0.269), H4_t (0.237), D1_M (0.201), W1_M (0.175), D1_dir (0.169), H4_M (0.157), M30_t (0.139)

### gboost_raso: AUC = **0.480 ± 0.016**
Top features: H1_conv_z (0.076), H4_er (0.063), D1_er (0.060), D1_acc_z (0.056), H4_acc_z (0.055), D1_conv_z (0.051), M30_t (0.045), M30_acc_z (0.045)

### direção (logistic, só rotulados): AUC = **0.588 ± 0.085** (5 folds válidos)

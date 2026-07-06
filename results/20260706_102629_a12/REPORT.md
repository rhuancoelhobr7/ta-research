# a12 — Geometria literal do CSS clássico em T0 (pares: usd7)

Matriz: 3952 linhas | dias research: 395 | params: per=14 suav=3 box=0.2 k_slope=3

Critérios de sucesso PRÉ-REGISTRADOS no CHANGELOG (2026-07-06) e no cabeçalho deste script, ANTES da primeira execução.

## Contraste descritivo (rotulado vs não)

| feature | d de Cohen |
|---|---|
| MN_dist_box | +0.10 |
| MN_dist_zero | +0.10 |
| MN_dline | +0.10 |
| W1_dist_zero | +0.08 |
| W1_dist_box | +0.08 |
| MN_fora_box | +0.07 |
| W1_fora_box | +0.07 |
| W1_val | +0.07 |
| H4_val | -0.06 |
| W1_dline | -0.06 |

## Regras pré-registradas vs baselines (dias research)

Dias: 395 | acaso pareado: **12.4%** | reality check p95: **16.4%**

| regra | n | top-1 | hit@2 | precision@2 | bate baselines? | > p95? |
|---|---|---|---|---|---|---|
| R1_exaustao_macro | 237 | 10.1% | 16.0% | 8.9% | não | não |
| R2_cascata | 317 | 13.9% | 18.0% | 9.8% | não | não |
| R3_peso_relativo | 395 | 10.6% | 23.0% | 12.7% | não | não |
| baseline_continuacao_D1 | 395 | 12.4% | 12.4% | 6.2% | — | — |
| baseline_persistencia | 394 | 14.5% | 14.5% | 7.2% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: rotula?

- logistic: AUC **0.515** ± 0.024 (5 folds)
- gboost: AUC **0.503** ± 0.020 (5 folds)

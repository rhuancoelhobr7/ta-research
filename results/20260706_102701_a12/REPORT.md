# a12 — Geometria literal do CSS clássico em T0 (pares: all28)

Matriz: 3952 linhas | dias research: 395 | params: per=14 suav=3 box=0.2 k_slope=3

Critérios de sucesso PRÉ-REGISTRADOS no CHANGELOG (2026-07-06) e no cabeçalho deste script, ANTES da primeira execução.

## Contraste descritivo (rotulado vs não)

| feature | d de Cohen |
|---|---|
| W1_dline | -0.09 |
| MN_dline | +0.08 |
| MN_dist_box | +0.08 |
| MN_dist_zero | +0.08 |
| D1_dist_box | -0.07 |
| D1_dist_zero | -0.07 |
| D1_fora_box | -0.07 |
| H1_dline | +0.07 |
| MN_val | +0.05 |
| W1_val | +0.04 |

## Regras pré-registradas vs baselines (dias research)

Dias: 395 | acaso pareado: **12.4%** | reality check p95: **15.7%**

| regra | n | top-1 | hit@2 | precision@2 | bate baselines? | > p95? |
|---|---|---|---|---|---|---|
| R1_exaustao_macro | 255 | 11.8% | 14.1% | 7.3% | não | não |
| R2_cascata | 348 | 14.9% | 19.8% | 10.8% | SIM | não |
| R3_peso_relativo | 395 | 10.9% | 18.5% | 10.5% | não | não |
| baseline_continuacao_D1 | 395 | 12.4% | 12.4% | 6.2% | — | — |
| baseline_persistencia | 394 | 14.5% | 14.5% | 7.2% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: rotula?

- logistic: AUC **0.509** ± 0.020 (5 folds)
- gboost: AUC **0.518** ± 0.021 (5 folds)

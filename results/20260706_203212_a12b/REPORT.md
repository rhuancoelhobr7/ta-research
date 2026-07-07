# a12b — Geometria do CSS DA TELA em T0 (pares: usd7)

Matriz: 3952 linhas | dias research: 395 | lente: css_screen (v2.20, escala fixa) | k_slope=3

Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; exceção única autorizada pelo dono). Regras, alvo, baselines e critérios IDÊNTICOS ao a12 — só a fonte das linhas muda.

## Contraste descritivo (rotulado vs não)

| feature | d de Cohen |
|---|---|
| D1_dist_box | -0.12 |
| D1_dist_zero | -0.12 |
| W1_dline | -0.10 |
| H4_fora_box | -0.09 |
| D1_val | -0.08 |
| D1_fora_box | -0.07 |
| H4_dist_zero | -0.07 |
| H4_dist_box | -0.07 |
| D1_dline | -0.07 |
| MN_val | +0.07 |

## Regras pré-registradas vs baselines (dias research)

Dias: 395 | acaso pareado: **12.4%** | reality check p95: **15.8%**

| regra | n | top-1 | hit@2 | precision@2 | bate baselines? | > p95? |
|---|---|---|---|---|---|---|
| R1_exaustao_macro | 272 | 10.3% | 16.9% | 9.0% | não | não |
| R2_cascata | 371 | 11.3% | 21.0% | 10.9% | não | não |
| R3_peso_relativo | 395 | 12.2% | 23.3% | 12.0% | não | não |
| baseline_continuacao_D1 | 395 | 12.4% | 12.4% | 6.2% | — | — |
| baseline_persistencia | 394 | 14.5% | 14.5% | 7.2% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: rotula?

- logistic: AUC **0.509** ± 0.024 (5 folds)
- gboost: AUC **0.502** ± 0.037 (5 folds)

# a12b — Geometria do CSS DA TELA em T0 (pares: all28)

Matriz: 3952 linhas | dias research: 395 | lente: css_screen (v2.20, escala fixa) | k_slope=3

Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; exceção única autorizada pelo dono). Regras, alvo, baselines e critérios IDÊNTICOS ao a12 — só a fonte das linhas muda.

## Contraste descritivo (rotulado vs não)

| feature | d de Cohen |
|---|---|
| D1_fora_box | -0.09 |
| D1_dist_box | -0.09 |
| D1_dist_zero | -0.09 |
| MN_val | +0.07 |
| W1_fora_box | -0.07 |
| W1_dist_zero | -0.05 |
| W1_dist_box | -0.05 |
| W1_dline | -0.04 |
| H1_dist_box | +0.03 |
| H1_dist_zero | +0.03 |

## Regras pré-registradas vs baselines (dias research)

Dias: 395 | acaso pareado: **12.4%** | reality check p95: **15.4%**

| regra | n | top-1 | hit@2 | precision@2 | bate baselines? | > p95? |
|---|---|---|---|---|---|---|
| R1_exaustao_macro | 301 | 10.3% | 14.0% | 8.0% | não | não |
| R2_cascata | 390 | 12.1% | 21.0% | 11.4% | não | não |
| R3_peso_relativo | 395 | 9.4% | 20.3% | 10.5% | não | não |
| baseline_continuacao_D1 | 395 | 12.4% | 12.4% | 6.2% | — | — |
| baseline_persistencia | 394 | 14.5% | 14.5% | 7.2% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: rotula?

- logistic: AUC **0.493** ± 0.021 (5 folds)
- gboost: AUC **0.478** ± 0.012 (5 folds)

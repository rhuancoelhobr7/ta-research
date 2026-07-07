# a13b — Peso do CSS DA TELA em T0 → sinal Tokyo→NY (pares: usd7, janela: 15h)

Matriz: 3952 linhas | dias research: 395 | lente: css_screen (v2.20, escala fixa) | k=3

Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; exceção única autorizada pelo dono). Regras, alvo, baselines e critérios IDÊNTICOS ao a13 — só a fonte das linhas muda. Rótulo v1 e holdout intocados.

## Regras pré-registradas vs baselines (sinal do alvo, research)

Dias: 395 | acaso pareado: **50.0%** | reality check p95: **57.1%**

| regra | n | top-1 | bate baselines? | > p95? |
|---|---|---|---|---|
| RA_exaustao_contra | 251 | 47.8% | não | não |
| RB_transferencia_H4 | 177 | 50.3% | SIM | não |
| RC_amparo_D1 | 93 (n<100!) | 38.7% | não | não |
| baseline_continuacao_D1 | 395 | 44.8% | — | — |
| baseline_persistencia_y | 394 | 45.7% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: sinal Tokyo→NY

- logistic: AUC **0.520** ± 0.020 (5 folds)
- gboost: AUC **0.530** ± 0.018 (5 folds)

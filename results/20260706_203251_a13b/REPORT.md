# a13b — Peso do CSS DA TELA em T0 → sinal Tokyo→NY (pares: all28, janela: 15h)

Matriz: 3952 linhas | dias research: 395 | lente: css_screen (v2.20, escala fixa) | k=3

Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; exceção única autorizada pelo dono). Regras, alvo, baselines e critérios IDÊNTICOS ao a13 — só a fonte das linhas muda. Rótulo v1 e holdout intocados.

## Regras pré-registradas vs baselines (sinal do alvo, research)

Dias: 395 | acaso pareado: **50.0%** | reality check p95: **56.1%**

| regra | n | top-1 | bate baselines? | > p95? |
|---|---|---|---|---|
| RA_exaustao_contra | 242 | 43.8% | não | não |
| RB_transferencia_H4 | 228 | 45.6% | não | não |
| RC_amparo_D1 | 95 (n<100!) | 43.2% | não | não |
| baseline_continuacao_D1 | 395 | 44.8% | — | — |
| baseline_persistencia_y | 394 | 45.7% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: sinal Tokyo→NY

- logistic: AUC **0.538** ± 0.016 (5 folds)
- gboost: AUC **0.523** ± 0.014 (5 folds)

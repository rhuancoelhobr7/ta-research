# a13b — Peso do CSS DA TELA em T0 → sinal Tokyo→NY (pares: usd7, janela: 12h — SENSIBILIDADE)

Matriz: 3952 linhas | dias research: 395 | lente: css_screen (v2.20, escala fixa) | k=3

Re-execução de fidelidade PRÉ-REGISTRADA (CHANGELOG 2026-07-06; exceção única autorizada pelo dono). Regras, alvo, baselines e critérios IDÊNTICOS ao a13 — só a fonte das linhas muda. Rótulo v1 e holdout intocados.

## Regras pré-registradas vs baselines (sinal do alvo, research)

Dias: 395 | acaso pareado: **50.0%** | reality check p95: **56.0%**

| regra | n | top-1 | bate baselines? | > p95? |
|---|---|---|---|---|
| RA_exaustao_contra | 251 | 46.2% | não | não |
| RB_transferencia_H4 | 177 | 49.2% | não | não |
| RC_amparo_D1 | 93 (n<100!) | 39.8% | não | não |
| baseline_continuacao_D1 | 395 | 44.1% | — | — |
| baseline_persistencia_y | 394 | 50.8% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: sinal Tokyo→NY

- logistic: AUC **0.517** ± 0.018 (5 folds)
- gboost: AUC **0.497** ± 0.018 (5 folds)

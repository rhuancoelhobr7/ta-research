# a13 — Peso (derivada do CSS) em T0 → sinal Tokyo→NY (pares: usd7, janela: 15h)

Matriz: 3952 linhas | dias research: 395 | params: per=14 suav=3 box=0.2 k=3

Hipóteses e critérios PRÉ-REGISTRADOS no CHANGELOG (2026-07-06) e no cabeçalho deste script, ANTES da primeira execução. Rótulo v1 e holdout intocados.

## Regras pré-registradas vs baselines (sinal do alvo, research)

Dias: 395 | acaso pareado: **50.0%** | reality check p95: **57.7%**

| regra | n | top-1 | bate baselines? | > p95? |
|---|---|---|---|---|
| RA_exaustao_contra | 115 | 48.7% | não | não |
| RB_transferencia_H4 | 163 | 50.9% | SIM | não |
| RC_amparo_D1 | 59 (n<100!) | 47.5% | não | não |
| baseline_continuacao_D1 | 395 | 44.8% | — | — |
| baseline_persistencia_y | 394 | 45.7% | — | — |

**Nenhuma regra sobreviveu** — nulo reportado (regra dura nº 7).

## Teto de ML (purged CV, gap 5 dias) — alvo: sinal Tokyo→NY

- logistic: AUC **0.508** ± 0.012 (5 folds)
- gboost: AUC **0.516** ± 0.004 (5 folds)

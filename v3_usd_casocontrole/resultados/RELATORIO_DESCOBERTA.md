# RELATÓRIO DE DESCOBERTA — v3 USD caso-controle

## Sumário executivo

Na descoberta (683 dias), o melhor modelo com as features relacionais brutas (F1-F3, família logit) atinge AUC out-of-fold de **0.595**; o benchmark CSSM v1.41 (F4, família gbm) atinge **0.520** (H3: F1-F3 supera F4 neste dataset).
AUC ~0.5 = indistinguível de moeda ao ar. O teste que DECIDE é a confirmação (única, modelo congelado) — este relatório não autoriza conclusão preditiva.

Modelos congelados: primário F1-F3 (logit) e benchmark F4 (gbm), treinados na descoberta inteira, salvos em resultados/modelo_congelado.pkl.

## Janela e classes

- Descoberta: 2022-10-04 → 2025-05-19 (683 dias); buffer de 10 dias úteis descartado; confirmação começa em 2025-06-03 (intocada).
- Taxa-base pooled: **26.9%** (up 11.6%, down 15.4%).

## Modelos pooled (AUC out-of-fold, CV purgada 5 folds gap 10)

| conjunto | família | AUC OOF | p@k OOF |
|---|---|---|---|
| F1-F3 | logit | 0.5947 | 0.315 |
| F1-F3 | gbm | 0.5230 | 0.299 |
| F4 | logit | 0.5069 | 0.255 |
| F4 | gbm | 0.5196 | 0.310 |

## Baselines na descoberta

| baseline | AUC | p@k |
|---|---|---|
| taxa_base | 0.5000 | 0.269 |
| persistencia | 0.5341 | 0.319 |
| reversao | 0.4659 | 0.251 |

## H2 — precursores de alta vs baixa (exploratório, só descoberta)

| alvo | família | AUC OOF |
|---|---|---|
| USD up | logit | 0.4564 |
| USD up | gbm | 0.5441 |
| USD down | logit | 0.5997 |
| USD down | gbm | 0.5659 |

Maiores divergências de coeficiente (up − down):

| feature | coef up | coef down |
|---|---|---|
| f1_mag_24 | -0.097 | +0.517 |
| f1_breadth_48 | -0.295 | +0.224 |
| f2_dist_hi5 | +0.299 | -0.180 |
| f2_close_pos | +0.173 | -0.290 |
| f1_mag_48 | +0.268 | -0.156 |
| f2_run_len | -0.335 | +0.040 |
| f2_dist_lo20 | -0.057 | -0.335 |
| f2_dist_lo5 | -0.030 | +0.219 |

## Limitações

- Tudo acima é DESCOBERTA: números OOF, sem garantia fora dela.
- Lista de features fechada (CLAUDE.md regra 3); ideias novas em IDEIAS_FUTURAS.md.
- Ver trilha de calibração do rótulo em CLAUDE.md (leitura C).
# a24 — CSS como preditor de range (P8/P9/P10 vs baseline)

Virada NY 13:00 UTC, alvo range [13,17) UTC. Estado na barra fechada anterior (sem lookahead). Split 70/30, teste = 775 dias. pct200. Baseline a bater: **base_atr** (o par estruturalmente mais largo). Controle negativo: **P8_shuf**.

## (A) ABSOLUTO — top-3 range pós-abertura (pips) — pergunta do trader

| pred         | target    |   top3_mean |   ci_lo |   ci_hi |   lift |   spearman |   n_days |
|:-------------|:----------|------------:|--------:|--------:|-------:|-----------:|---------:|
| base_atr     | tgt_range |      71.158 |  67.83  |  74.895 |  1.649 |      0.794 |      775 |
| base_asia    | tgt_range |      68.955 |  65.198 |  73.263 |  1.588 |      0.625 |      775 |
| P8_mag       | tgt_range |      46.915 |  44.114 |  49.878 |  1.076 |      0.054 |      775 |
| P8_intra     | tgt_range |      45.407 |  43.189 |  47.773 |  1.055 |      0.044 |      775 |
| P8_long      | tgt_range |      47.545 |  44.289 |  51.341 |  1.081 |      0.061 |      775 |
| P10_brd      | tgt_range |      44.268 |  42.082 |  46.595 |  1.027 |      0.055 |      775 |
| stack_atr_P8 | tgt_range |      64.446 |  61.107 |  68.226 |  1.484 |      0.574 |      775 |
| P8_shuf      | tgt_range |      43.637 |  41.568 |  45.898 |  1.013 |      0.005 |      775 |

_Se P8/P10/stack não superam base_atr aqui, o CSS não ajuda a escolher o par de maior amplitude além da largura estrutural._


## (B) RELATIVO — alvo = range/ATR-do-próprio-par — o CSS tem info?

| pred         | target   |   top3_mean |   ci_lo |   ci_hi |   lift |   spearman |   n_days |
|:-------------|:---------|------------:|--------:|--------:|-------:|-----------:|---------:|
| base_atr     | tgt_norm |       0.57  |   0.547 |   0.592 |  0.901 |     -0.09  |      775 |
| base_asia    | tgt_norm |       0.62  |   0.592 |   0.65  |  0.977 |     -0.069 |      775 |
| P8_mag       | tgt_norm |       0.66  |   0.63  |   0.695 |  1.032 |      0.035 |      775 |
| P8_intra     | tgt_norm |       0.655 |   0.628 |   0.682 |  1.027 |      0.036 |      775 |
| P8_long      | tgt_norm |       0.644 |   0.616 |   0.674 |  1.01  |      0.027 |      775 |
| P10_brd      | tgt_norm |       0.638 |   0.608 |   0.671 |  0.996 |      0.003 |      775 |
| stack_atr_P8 | tgt_norm |       0.61  |   0.584 |   0.637 |  0.959 |     -0.039 |      775 |
| P8_shuf      | tgt_norm |       0.638 |   0.612 |   0.666 |  1.002 |     -0.002 |      775 |

_lift>1 e spearman>0 acima do controle P8_shuf = o CSS prevê o par que excede a PRÓPRIA norma. É o teste limpo de conteúdo informativo.


## P9 — par limpo × conflitado (trajetória da janela-alvo)

- traj mediana com moeda fraca LIMPA (P9_diverg baixo): **0.454**

- traj mediana com moeda fraca CONFLITADA (alto): **0.441**


_traj mais alta = movimento mais limpo (menos choppy). Limpo > conflitado, na direção do P9._

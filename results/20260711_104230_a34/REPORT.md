# a34 — Varredura de métricas (EXPLORATÓRIO)

Grade: 10 scores (8 famílias; família 7 em 2 variantes; 1-6/8 têm variante única pois índice=média dos pares) x 7 janelas x 2 alvos = **70 células**. Research = 393 dias (<q50); holdout [q50,q70) intocado. Acaso régua B (top-3) = 37.5%.

**NENHUMA conclusão pode ser tirada do a34 isoladamente; o candidato só vira achado se sobreviver ao a35 (holdout).**

Reality check (p95 do máximo permutado, régua B): **0.461**. Células que sobrevivem a BH E reality check: **13**.

## Top-10 células por acurácia top-3

| familia    |   janela |   accA |   accB |     z | bh   | passa_reality   |
|:-----------|---------:|-------:|-------:|------:|:-----|:----------------|
| 4_zscore   |      180 |  0.194 |  0.508 | 5.388 | True | True            |
| 8_css      |      180 |  0.204 |  0.487 | 4.59  | True | True            |
| 8_cssm     |      180 |  0.191 |  0.485 | 4.486 | True | True            |
| 3_effratio |      180 |  0.212 |  0.482 | 4.337 | True | True            |
| 5_rank_xs  |      180 |  0.236 |  0.482 | 4.337 | True | True            |
| 1_momentum |      180 |  0.236 |  0.482 | 4.337 | True | True            |
| 6_disp_xs  |      180 |  0.236 |  0.482 | 4.337 | True | True            |
| 2_ret_atr  |      180 |  0.199 |  0.474 | 4.021 | True | True            |
| 6_disp_xs  |      120 |  0.189 |  0.469 | 3.811 | True | True            |
| 5_rank_xs  |      120 |  0.189 |  0.469 | 3.811 | True | True            |


## Sobreviventes (BH + reality check) — CANDIDATOS p/ o a35

| familia    |   janela |   accA |   accB |
|:-----------|---------:|-------:|-------:|
| 4_zscore   |      180 |  0.194 |  0.508 |
| 8_css      |      180 |  0.204 |  0.487 |
| 8_cssm     |      180 |  0.191 |  0.485 |
| 1_momentum |      180 |  0.236 |  0.482 |
| 6_disp_xs  |      180 |  0.236 |  0.482 |
| 5_rank_xs  |      180 |  0.236 |  0.482 |
| 3_effratio |      180 |  0.212 |  0.482 |
| 2_ret_atr  |      180 |  0.199 |  0.474 |
| 1_momentum |      120 |  0.189 |  0.469 |
| 2_ret_atr  |      120 |  0.184 |  0.469 |
| 6_disp_xs  |      120 |  0.189 |  0.469 |
| 5_rank_xs  |      120 |  0.189 |  0.469 |
| 8_css      |       90 |  0.214 |  0.467 |


_Aviso: janelas 5/15 min têm prior ruim (a29: aos 30 min é acaso). Vitória em 5 min = suspeitar de artefato._

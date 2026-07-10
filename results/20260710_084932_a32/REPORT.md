# a32 — Matriz completa de autocorrelação de range entre sessões

28 pares. Sequência asia->londres->ny->asia(dia+1). Célula (de->para) = range da sessão `de` prevê a PRÓXIMA `para`. Spearman mediano entre pares, out-of-sample (30% finais), IC bootstrap em blocos.

## Q20/Q21 — Matriz 3x3 (Spearman mediano; linha=de, coluna=para)

| de      |   asia |   londres |    ny |
|:--------|-------:|----------:|------:|
| asia    |  0.311 |     0.341 | 0.269 |
| londres |  0.265 |     0.261 | 0.337 |
| ny      |  0.273 |     0.263 | 0.281 |


### Detalhe por célula (com distância, IC e rho^2)

| de      | para    | dia+1   |   dist |   spearman |   ic_lo |   ic_hi |   rho2_% |   n_pares |
|:--------|:--------|:--------|-------:|-----------:|--------:|--------:|---------:|----------:|
| asia    | londres | False   |      1 |      0.341 |   0.314 |   0.366 |   11.653 |        28 |
| londres | ny      | False   |      1 |      0.337 |   0.303 |   0.365 |   11.35  |        28 |
| ny      | asia    | True    |      1 |      0.273 |   0.247 |   0.301 |    7.448 |        28 |
| asia    | ny      | False   |      2 |      0.269 |   0.235 |   0.306 |    7.218 |        28 |
| ny      | londres | True    |      2 |      0.263 |   0.247 |   0.29  |    6.894 |        28 |
| londres | asia    | True    |      2 |      0.265 |   0.243 |   0.288 |    7.035 |        28 |
| asia    | asia    | True    |      3 |      0.311 |   0.285 |   0.329 |    9.652 |        28 |
| londres | londres | True    |      3 |      0.261 |   0.225 |   0.289 |    6.787 |        28 |
| ny      | ny      | True    |      3 |      0.281 |   0.248 |   0.342 |    7.908 |        28 |


## Q22 — NY -> Tóquio (dia+1)

- Spearman **0.273** IC95 [0.247, 0.301]; **7.4%** da variância de rank compartilhada. A volatilidade de NY VAZA para a abertura asiática seguinte (efeito real).

## Q23 — Decaimento por distância entre sessões

|   dist |   spearman_mediano |
|-------:|-------------------:|
|      1 |              0.337 |
|      2 |              0.265 |
|      3 |              0.281 |

_dist 1 = adjacente; 3 = mesma sessão no dia seguinte. Monotônico = vol decai com o tempo; salto no 3 = sazonalidade de sessão._

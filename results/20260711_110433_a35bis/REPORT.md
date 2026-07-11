# a35-bis — Confirmação OOS da persistência-de-preço direcional (a36)

Regra (ZERO parâmetros livres, do a17): sinal do Δíndice de C em T0+240min sustenta até 900min. Acaso 0.50. O holdout formal foi consumido no a35 — aqui: robustez + estabilidade + cauda recente [q70,fim).

## (1)+(3) Research [<q70] vs cauda recente [>=q70]

- research: **0.640** IC[0.624, 0.654] (n=4,320)

- **cauda OOS: 0.646** IC[0.622, 0.668] (n=1,888)

- edge mantido: **104%**; IC OOS exclui 0.5? **sim**

## (2) Estabilidade por bloco (4 períodos consecutivos)

|   bloco | ini        | fim        |   acc |   ic_lo |    n |
|--------:|:-----------|:-----------|------:|--------:|-----:|
|       1 | 2023-07-11 | 2024-04-08 | 0.63  |   0.605 | 1528 |
|       2 | 2024-04-09 | 2025-01-09 | 0.651 |   0.624 | 1568 |
|       3 | 2025-01-10 | 2025-10-07 | 0.64  |   0.615 | 1544 |
|       4 | 2025-10-08 | 2026-07-10 | 0.645 |   0.621 | 1568 |


_>0.5 em todos os blocos? **SIM**._

## (4) Magnitude residual — sobra movimento após T0+4h?

- residual direcional mediano (normalizado pelo move típico do dia) na cauda OOS: **+0.02** — pouco/nada sobra (sinal chega tarde).

## (5) Robustez ao par (k, fim)

|   k |   fim |   acc |   resid_norm_med |
|----:|------:|------:|-----------------:|
| 120 |   720 | 0.575 |           -0.035 |
| 180 |   780 | 0.619 |            0.014 |
| 240 |   900 | 0.642 |           -0.015 |


## Veredito

**CONFIRMA o SINAL, com caveat de magnitude.** A persistência-de-preço direcional é robusta e estável OOS (cauda 0.646, IC exclui 0.5, edge 104%, estável nos 4 blocos). MAS a magnitude residual é minúscula (+0.02 do move típico) — por 4h quase todo o movimento LÍQUIDO do dia já foi. Leitura honesta: é um sinal de CONFIRMAÇÃO/MANUTENÇÃO (a direção raramente inverte até o fim), NÃO um edge de ENTRADA tardia às 4h (sobra pouco a capturar). Útil para segurar/não-reverter uma posição já aberta, não para abrir às 4h. Coerente com o tema: o sinal está no preço, mas chega quando o grosso já passou.


_Escopo honesto: entrada às 4h (tardia); alvo é o SINAL às 15h, não a magnitude garantida; é momentum intradiário persistente, não previsão em T0._

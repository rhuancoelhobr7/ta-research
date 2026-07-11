# a35 — Confirmação no HOLDOUT (uma vez só)

Holdout PRISTINO [q50,q70) = 157 dias (2025-01-09 → 2025-08-12). Células pré-declaradas do a34, regra congelada, z-score com stats do research. Acaso régua B = 37.5%.

## Resultado (régua B top-3)

| celula      |   accB_holdout |   ic_lo |   ic_hi |   accB_research |   edge_mantido | confirma   |   n |
|:------------|---------------:|--------:|--------:|----------------:|---------------:|:-----------|----:|
| z-score@180 |          0.506 |   0.422 |   0.591 |           0.508 |          0.989 | True       | 154 |
| css@180     |          0.433 |   0.35  |   0.516 |           0.487 |          0.519 | False      | 157 |
| cssm@180    |          0.439 |   0.357 |   0.522 |           0.485 |          0.586 | False      | 157 |


## Veredito pré-registrado
Critério: accB IC95 lo > 0.375 E manter >=75% do edge do research.

- **top-1 (z-score@180): CONFIRMA** (holdout 0.506, IC[0.422, 0.591], edge mantido 99%).

- alguma das top-3 confirma? **SIM**.


### → PRIMEIRO PREDITOR CONFIRMADO OOS do projeto.


## Estado do holdout (irreversível)

Consumida a fatia [q50,q70) do M5 (157 dias). Resta o holdout final [q70, fim) (~30% mais recente) — que o a29/a30 já tocaram e portanto NÃO é pristino; e todo o research <q50. Esta confirmação NÃO se repete.

# RELATÓRIO DE CONFIRMAÇÃO — v3 USD caso-controle

Janela: 2025-06-03 → 2026-07-06 (283 dias; descoberta congelada em 2025-05-19; buffer 10 dias úteis descartado).

Taxa-base na confirmação: **25.1%** (71/283 dias protagonista).


## primario_f13 (logit, 20 features)

| métrica | valor |
|---|---|
| AUC | 0.5267 (p-perm = 0.2507) |
| precision@k (k=71) | 0.366 |
| Brier | 0.1896 |
| p@k baseline `taxa_base` | 0.251 |
| p@k baseline `persistencia` | 0.347 |
| p@k baseline `reversao` | 0.218 |
| **lift vs melhor baseline (`persistencia`)** | **+0.019** IC95% [-0.091, +0.137] |

## benchmark_f4 (gbm, 20 features)

| métrica | valor |
|---|---|
| AUC | 0.4733 (p-perm = 0.7502) |
| precision@k (k=71) | 0.239 |
| Brier | 0.2056 |
| p@k baseline `taxa_base` | 0.251 |
| p@k baseline `persistencia` | 0.347 |
| p@k baseline `reversao` | 0.218 |
| **lift vs melhor baseline (`persistencia`)** | **-0.108** IC95% [-0.219, +0.018] |

## Veredito (critérios pré-registrados)

**NULO**: o critério positivo não foi atingido. Com estas features, o USD protagonista **não é previsível em T0**.

F1–F3 e F4 ambos nulos: a evidência aponta que o fenômeno é primariamente **identificável em retrospecto**, não previsível em T0 — resposta direta à questão aberta do programa.

## Interpretação

Este teste foi executado UMA única vez sobre o modelo congelado da descoberta, como pré-registrado. O que este resultado muda na decisão de trading: um resultado NULO significa que nenhuma das leituras disponíveis à meia-noite do servidor (véspera da abertura de Tóquio) — nem as relacionais brutas, nem o CSSM — antecipa o dia de tendência absoluta do USD melhor que regras triviais; qualquer uso operacional do fenômeno continua sendo REAÇÃO (reconhecimento em curso), não antecipação.

## Limitações

- Amostra de confirmação limitada (~9-10 meses de dias úteis).
- Rótulo calibrado na leitura C da magnitude (ver CLAUDE.md).
- F3 'qualquer moeda' usa proxy contínuo (7 pares apenas).
- F4 exclui a lente D1 estrutural (aquecimento > metade da amostra).
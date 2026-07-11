# a33 — A cadeia composta, ponta a ponta, líquida de custo

CONFIRMATÓRIO, uma execução. 631 dias de RESEARCH (primeiros 80% do M5; holdout intocado). Pipeline: momentum T0+90min → líder×anti → par.

## P(par candidato = par de MAIOR range do dia)

| fonte | P(=max) |
|---|---|
| **cadeia (candidato)** | **4.1%** |
| baseline maior-ATR (a25) | 29.8% |
| baseline persistência | 23.8% |
| aleatório (1/28) | 3.6% |
| referência a31 (conhecendo a líder) | 14% |


## Decomposição — o custo do erro de detecção

- acerta a líder estimada = a verdadeira em **15.7%** dos dias.

- P(candidato=max | líder correta) = **10.1%** vs P(candidato=max | líder errada) = **3.0%**.

- → a queda do 14%(a31) para 4.1% vem sobretudo de NÃO conhecer a líder (16% de acerto).

## Range capturado e custo (spread real por par, mediana do M5)

- range mediano do candidato: **72.7 pips**; líquido de spread: **72.3 pips**; **178.0× o spread** do par.

- excesso de ATR do candidato vs média dos 28: mediana -0.08 ATR (a31 achou +0.67 conhecendo a líder).

- comparador maior-ATR (a25): range mediano 143.0 pips.

## Veredito pré-registrado

- bate TODOS os baselines em P(=max)? **NÃO** (cand 4.1% vs ATR 29.8%, persist 23.8%, aleat 3.6%).

- range líquido > 2× spread? **SIM** (178.0× spread).


### → A cadeia NÃO se sustenta (critério pré-registrado).

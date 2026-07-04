# Estudo v2 — lentes calibradas e leitura MTF fiel

## Critérios de sucesso PRÉ-REGISTRADOS (fixados antes de rodar)

- **Tarefa 1**: a regra escolhida (em TREINO, lente por platô) precisa de
  (a) top-1 em treino > p95 dos máximos de 200 permutações em bloco da
  busca inteira (regras × lentes); (b) top-1 em treino > TODOS os baselines;
  (c) vencer o melhor baseline em ≥ 70% das janelas walk-forward da
  validação. Qualquer coisa fora disso = NULO.
- **Tarefa 2**: retorno médio do alvo disjunto [T0+4h,T0+12h] na VALIDAÇÃO
  com IC95% (bootstrap em blocos) inteiramente acima de 0 E média acima dos
  três baselines (aleatório, continuação-D1, reversão) E média de treino >
  p95 permutado da busca inteira. Qualquer coisa fora disso = NULO.
- Sem afrouxamento post-hoc; n<100 = amostra insuficiente (flag no texto).

## Calibração dos gates por lente

| w | t_gate | t_low | FP medido (walks frescos) |
|---|---|---|---|
| 16 | 2.896 | 1.692 | 5.1% |
| 24 | 2.511 | 1.527 | 5.0% |
| 32 | 2.35 | 1.46 | 4.9% |
| 48 | 2.205 | 1.397 | 4.9% |

W1 (w=64) gate 2.134; MN (w=24 meses) gate 2.511 — modo reduzido (FP/FR/N).

## Tarefa 1 — retrato de T0 prevê o rótulo do dia?

Treino: 296 dias | validação: 99 dias (n<100 na validação — amostra flagada) | acaso pareado (treino): **12.6%** | p95 permutado da busca inteira (16 combinações): **18.2%**

| regra | lente | n dias | top-1 treino | hit@2 |
|---|---|---|---|---|
| alin | 16 | 256 | 14.1% | 20.7% |
| alin | 24 | 252 | 15.1% | 21.4% |
| alin | 32 | 253 | 11.9% | 19.0% |
| alin | 48 | 245 | 11.8% | 18.0% |
| cenA | 16 | 0 | — | — |
| cenA | 24 | 0 | — | — |
| cenA | 32 | 0 | — | — |
| cenA | 48 | 0 | — | — |
| cenB | 16 | 0 | — | — |
| cenB | 24 | 0 | — | — |
| cenB | 32 | 0 | — | — |
| cenB | 48 | 0 | — | — |
| cenC | 16 | 0 | — | — |
| cenC | 24 | 0 | — | — |
| cenC | 32 | 0 | — | — |
| cenC | 48 | 0 | — | — |
| continuação-D1 (baseline) | — | 296 | 13.9% | 13.9% |
| persistência (baseline) | — | 295 | 15.9% | 15.9% |

**Escolhida em treino (platô)**: alin lente 16 — top-1 treino 14.1%.
- (a) > p95 permutado (18.2%)? **NÃO**
- (b) > todos os baselines (melhor: 15.9%)? **NÃO**
- (c) walk-forward validação: venceu 3/5 janelas (critério ≥70%)? **NÃO** (top-1 validação: 20.3%, n=79 — n<100, amostra insuficiente p/ IC)

**Veredicto Tarefa 1: NULO** (critérios pré-registrados).

### ML teto (alvo: rotula?; purged CV 5 folds, gap 5 dias)

| lente | logistic AUC | gboost AUC |
|---|---|---|
| 16 | 0.515 | 0.497 |
| 24 | 0.478 | 0.498 |
| 32 | 0.493 | 0.498 |
| 48 | 0.510 | 0.489 |

## Tarefa 2 — Tokyo-confirma (decisão T0+4h, alvo disjunto [T0+4h, T0+12h])

Limiar θ por quantis do treino: q0=0.00e+00, q50=9.22e-05, q75=2.90e-04 | p95 permutado da busca inteira (bp): **+3.27**

| variante | lente | n treino | média treino (bp) |
|---|---|---|---|
| mom_puro_q0 | — | 295 | -1.03 |
| mom_mtf_q0 | 16 | 54 (n<100!) | +1.70 |
| mom_mtf_q0 | 24 | 56 (n<100!) | -3.03 |
| mom_mtf_q0 | 32 | 57 (n<100!) | -3.39 |
| mom_mtf_q0 | 48 | 55 (n<100!) | +1.48 |
| mom_puro_q50 | — | 289 | -1.16 |
| mom_mtf_q50 | 16 | 32 (n<100!) | +3.89 |
| mom_mtf_q50 | 24 | 31 (n<100!) | -2.86 |
| mom_mtf_q50 | 32 | 38 (n<100!) | -4.71 |
| mom_mtf_q50 | 48 | 28 (n<100!) | +1.44 |
| mom_puro_q75 | — | 245 | -2.47 |
| mom_mtf_q75 | 16 | 15 (n<100!) | +0.52 |
| mom_mtf_q75 | 24 | 15 (n<100!) | +1.43 |
| mom_mtf_q75 | 32 | 22 (n<100!) | -8.75 |
| mom_mtf_q75 | 48 | 9 (n<100!) | -4.07 |

**Escolhida em treino**: mom_puro_q0 (lente —) — média treino -1.03 bp.
- Validação: média **-0.27 bp** IC95% [-3.43, +2.91] (n=99 (n<100 — amostra insuficiente!))
- Baselines validação (bp): aleatório 0.00 | continuação-D1 -0.56 | reversão +0.27
- (a) IC inteiro > 0? **NÃO** | (b) > 3 baselines? **NÃO** | (c) treino > p95 permutado? **NÃO**

**Veredicto Tarefa 2: NULO** (critérios pré-registrados).

## Diagnóstico — frequência das condições em T0 (lente 24)

| TF | N | FN | FP | FR | EX | sem dado |
|---|---|---|---|---|---|---|
| MN | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| W1 | 99.7% | 0.0% | 0.3% | 0.0% | 0.0% | 0.0% |
| D1 | 92.6% | 6.0% | 0.0% | 1.4% | 0.1% | 0.0% |
| H4 | 90.4% | 2.3% | 0.3% | 2.5% | 0.1% | 4.3% |
| H1 | 94.2% | 3.1% | 0.3% | 2.1% | 0.3% | 0.0% |
| M30 | 93.5% | 3.8% | 0.3% | 1.7% | 0.7% | 0.0% |

Leitura: o tier macro em modo reduzido com gates honestos quase nunca sai de N (MN 100% N; W1 ~0.3% FP na amostra) — os cenários A/B/C, que EXIGEM leitura macro não-neutra, ficam estruturalmente vazios. Não é um bug de implementação: é o resultado. A leitura 'macro contra/a favor' do Protocolo, mecanizada com taxa de falso positivo controlada, não ocorre nos dados; só a cascata `alin` (que não exige macro) gera previsões.

## Grade típica em T0 (condição modal por TF) — rotulados vs não

| lente/grupo | MN | W1 | D1 | H4 | H1 | M30 |
|---|---|---|---|---|---|---|
| 16 rotulados | N | N | N | N | N | N |
| 16 não-rot. | N | N | N | N | N | N |
| 24 rotulados | N | N | N | N | N | N |
| 24 não-rot. | N | N | N | N | N | N |
| 32 rotulados | N | N | N | N | N | N |
| 32 não-rot. | N | N | N | N | N | N |
| 48 rotulados | N | N | N | N | N | N |
| 48 não-rot. | N | N | N | N | N | N |

## Conclusão honesta

A reforma da lente FOI testada de verdade: gates calibrados por w (FP 4-7% verificado em walks frescos), 4 lentes, MN habilitado pelos 7 anos de D1, cenários formais do PROTOCOLO.md. Veredictos pré-registrados: Tarefa 1 = **NULO**, Tarefa 2 = **NULO**. Fração de condição ativa no H1 em T0 nos dias rotulados, por lente: w=16: 8%, w=24: 7%, w=32: 7%, w=48: 5%.

Resposta à pergunta do estudo: **não era (só) a lente**. Com janelas curtas e portões honestos, a fração ativa em T0 sobe de ~4% (v1) para ~5-8%, mas o retrato continua sem separar os dias (ML teto ~0.5; `alin` abaixo da persistência) — H1v2 refutada. A leitura MTF fiel (H2v2) morre antes: os cenários exigem um tier macro que, mecanizado com FP controlado, é estruturalmente Neutro. E o momentum das 4 primeiras horas não sobrevive à janela disjunta [T0+4h, T0+12h] (Tarefa 2 nula, reversão igualmente nula): o que o A8 viu era o próprio movimento do dia, sem continuação explorável após as 4h. O sinal, se existe, não está no preço passado em T0 nem em T0+4h — está fora do escopo mensurável deste indicador.


O holdout permanece intocado; rodada final (a7) só sob ordem explícita do usuário.

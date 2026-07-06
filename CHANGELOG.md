# Histórico de decisões e resultados

Registro cronológico das decisões metodológicas — o "porquê" que o código não
conta. Toda IA (ou humano) trabalhando neste repositório deve ler isto antes
de propor mudanças: várias escolhas abaixo são IRREVERSÍVEIS por regra
(CLAUDE.md, "Regras duras").

## 2026-07-04 — Fase 0: dados e fuso

- Exportados 28 pares G8 do MT5 (M5 2 anos + D1 4 anos) via `s0_export_mt5.py`.
- **Fuso do servidor verificado e confirmado pelo usuário**: UTC+2 (inverno
  NA) / UTC+3 (verão NA), DST dos EUA — meia-noite do servidor = 17:00 NY.
  Evidência: todas as 104 segundas-feiras da amostra abrem 00:00 e todas as
  sextas fecham 23:55, inverno e verão (ver `data/raw/_meta.json`).
  Consequência: T0 = 00:00 do servidor ≈ pré-Tokyo, como o PLAN assume.

## 2026-07-04 — Fase A: definição v1 CONGELADA

- Calibração pelos dois critérios do PLAN §2 (âncoras + taxa-base):
  **breadth ≥ 6/7, |z| ≥ 0.8, er ≥ 0.12** → 1.98 rótulos/dia, 88.1% dos dias
  com ≥1 rótulo, **6/7 chamadas do especialista confirmadas** (direção 7/7).
- `er_min=0.12` está ABAIXO da grade de sensibilidade do PLAN (piso 0.15):
  os dias das 7 chamadas tinham er ≈ 0.14 e o piso da grade perdia 3 âncoras
  por 0.004–0.014. Decisão tomada ANTES de qualquer contato com features do
  indicador — separação de fases intacta. Aprovada explicitamente pelo usuário.
- Âncora não reproduzida: NZD 2026-06-17 (z 0.45, er 0.089 — o movimento não
  aparece na janela T0+12h). Registrada como miss honesto.
- A partir daqui, mudar a definição = v2 e reinicia a Fase B do zero.

## 2026-07-04 — Fase A3: anatomia (results/*_anatomy)

- Tokyo carrega 56% do |movimento|; protagonistas mais frequentes: EUR/GBP.
- Hipótese "NZD ilíquido rotula mais" NÃO se sustentou (NZD 9.8%, meio da fila).
- **Persistência dia-a-dia NULA** (lift 0.99, IC [0.216, 0.277] vs base
  0.248) — refuta a suspeita do PLAN de que o edge seria "surfar sequências".
- Proxy de evento (vol 1ª hora pós-T0) e dia-da-semana: nada saliente.

## 2026-07-04 — Fase B: features T0 (a4) e engenharia reversa (a5)

- Matriz 3.952 linhas (494 dias × 8 moedas); M30/H1/H4/D1 completos, W1
  reduzido, MN omitido; teste anti-lookahead em tests/test_features_t0.py.
- **RESULTADO CENTRAL: NULO** (results/*_reverse):
  - B1: maior separação rotulado×não = d de Cohen 0.10 (nada separa);
  - alinhamento direcional dos TFs em T0 ≈ 50% (moeda ao ar);
  - B2/B3: nenhuma das 9 regras bate os 3 baselines nem o reality check
    (p95 dos máximos permutados = 17.5% top-1; melhor regra: 14.2%);
  - B4: ML honesto AUC 0.487 (logistic) / 0.480 (gboost) para "rotula?";
    direção entre rotulados 0.588 ± 0.085 (fraco e instável).
  - Leitura: se o edge do especialista é real, vem de informação FORA do
    indicador (calendário, fluxo, preço) — exatamente o desfecho que o
    PLAN §5-B4 antecipava como resposta válida.
- Cenários A/B/C do "Protocolo" foram APROXIMADOS (documento não está no
  repositório) e estão rotulados como tal no relatório.

## 2026-07-04 — Fase C: portfólio (a6)

- Baselines e melhor regra (referência, não-sobrevivente) ≈ 0 bp/dia líquido
  ou pior; **teto oracle +41 bp/dia (+141% no período)** — o fenômeno vale
  muito SE previsível; o gargalo é a previsão, não o veículo.

## 2026-07-04 — a8: rótulos × estados nas primeiras 4h (descritivo)

- 126 dias research (2025-08-19 a 2026-02-16), holdout intocado.
- Nas primeiras 4h o CSSM quase não sai de Ruído, NEM nos dias rotulados:
  H1 ativo-na-direção em 4.1% (T0+2h) / 3.3% (T0+4h) das rotuladas — menor
  que nas não-rotuladas (6.8% / 6.2%). P(rotulou | H1 Ruído em T0+4h) = 25%
  > P(rotulou | Emergindo) = 16%.
- `align_4h` = 88.9% [85.4, 92.2]: o preço já anda na direção do dia cedo —
  mas é decomposição da própria janela do rótulo, não previsão.
- Única hipótese registrada p/ v2: sinal de preço das primeiras horas como
  confirmação intraday (exigiria v2 + Fase B reiniciada).

## 2026-07-04 — Estudo v2: lentes calibradas + leitura MTF fiel (a9/a10)

Motivação: no v1, w_mid=64 no H1 = janela de 2,7 dias — lente multi-dia
para um fenômeno de 12h. O v2 testou (H1v2) lentes intraday recalibradas
e (H2v2) os cenários formais do Protocolo (agora em `PROTOCOLO.md`).

- Etapa 0: D1 re-exportado com 7 anos → MN habilitado em modo reduzido
  (w=24 meses). `PROTOCOLO.md` criado (5 condições FP/FN/FR/EX/N + 3
  cenários formais — o A5 v1 só tinha aproximações).
- Etapa 1: `calibrate_gates` no engine — gates de |t| calibrados por lente
  em random walks (5%/20% de excedência); lentes curtas têm cauda mais
  pesada (w=16 pede gate 2,90 vs 2,13 no w=64). FP verificado 4,9-5,1%.
- Etapa 2: `a9_mtf_matrix.py` — 12.640 linhas (395 dias research × 8
  moedas × 4 lentes), condições em MN/W1/D1/H4/H1/M30 em T0 e T0+4h,
  realizado 4h + alvo bruto [T0+4h,T0+12h] separado; 2 testes de lookahead.
- Etapa 3: `a10_v2_study.py`, critérios PRÉ-REGISTRADOS no topo do REPORT.
  **Tarefa 1 (T0 prevê o rótulo): NULA** — cenários A/B/C estruturalmente
  vazios (o tier macro mecanizado com FP controlado é ~100% Neutro: MN 100%
  N, W1 0,3% FP — achado, não bug); `alin` 14-15% top-1 < persistência
  15,9% < p95 permutado 18,2%; ML teto AUC ~0,5 em todas as lentes.
  **Tarefa 2 (Tokyo-confirma disjunto): NULA** — momentum das 4h não
  continua em [T0+4h,T0+12h] (validação −0,3 bp, IC [−3,4, +2,9]); a
  reversão também não paga. A lição do A8 fechou: o align_4h de 89% era o
  próprio movimento do dia, sem continuação explorável.
- Conclusão do v2: NÃO era (só) a lente. Fração ativa em T0 sobe de ~4%
  para ~5-8% com lentes curtas, mas segue sem separar os dias. O sinal,
  se existe, não está no preço passado em T0 nem em T0+4h.

## 2026-07-04 — Camada relacional: validação em dados reais (r1/a11)

`r1_relational.py` (fornecido pelo usuário, com testes sintéticos): motor
por par, matriz 8×8 orientada, breadth/nowcast rolante, dominância. Camada
DESCRITIVA — os nulos preditivos (A5/A8/v2) não são reabertos. Validação
em dias research (a11_relational_study.py):

- **Resultado forte (Etapa 2)**: ~2/3 dos instantes "ativos" do índice
  agregado (63.6% w=64; 62.4% w=24) NÃO são confirmados pelos pares
  (breadth_hard < 3/7) — força espúria por contaminação da cesta. CAD é a
  mais afetada (87%), JPY a menos (30%). Como diagnóstico, a camada se paga.
- **Limite honesto (Etapas 1/4)**: como "rotulador em tempo real" a camada
  falha o próprio critério de utilidade — concordância líder×protagonista
  em T0+12h de só 16% (w=64) / 28% (w=24); a latência nunca converge.
  Mesmo padrão do v2: janela rolante ≠ janela-calendário do rótulo.
- **Etapa 3**: as 7 chamadas do especialista caem TODAS no holdout —
  matrizes desses dias ficam adiadas até ordem explícita (junto com a7);
  substituídas por 2 dias research de alto nowcast (a linha da líder acende
  como esperado).
- **Etapa 5 (única preditiva, critério pré-registrado): NULA** — seleção
  de par por |M| orientado dá +1.18 bp sobre a média dos 7, IC [-0.65,
  +3.00] cruza 0, indistinguível de par aleatório (n=394).

## 2026-07-05 — Cssm.mq5 v1.40: camada relacional no indicador MT5

O indicador original (v1.30, importado intocado no commit anterior) ganhou
a camada relacional validada pelo a11 — detalhe mudança-a-mudança com
âncoras de linha em `INDICATOR_CHANGELOG.md`. Em resumo: motor por par
(t NW + ER, mesma disciplina anti-repaint), buffers 24-31/32-39
(breadth_hard/soft × dir p/ EAs), coluna "amp" e marcador ⚠ de força
espúria no painel, aba MATRIZ 8×8 com dominância do líder, alerta opcional
de amplitude ≥ 6/7 (reconhecimento, não previsão — continuação testada e
nula). Gates do par calibrados por w documentados no cabeçalho (64→2.13).
Compilado no MetaEditor: 0 erros, 0 warnings; regressão garantida com
`InpRelational=false` (buffers 0-23 no caminho v1.30 intocado).
`Export_CSSM_Parity.mq5` fecha o critério 6 (execução manual pendente).

## 2026-07-06 — a12 (em andamento): geometria literal do CSS clássico

Motivação: posts públicos do especialista indicam que o "score de inflação/
deflação" seria a GEOMETRIA das linhas do CSS clássico (TMA-slope,
normalizado por barra): dentro/fora da box ±0.2, linha ascendente/
descendente, proximidade do zero — lida em MN/W1/D1/H4/H1. Isso NÃO foi
testado literalmente: o cssm_engine usa features por-moeda (t, ER, M,
acc_z), sem a normalização cross-sectional por barra (ranking relativo)
nem a box literal.

- `css_classic.py` + testes: porte fiel do CurrencySlopeStrength.mq5 do
  usuário (TMA CAUSAL — a TMA centrada repinta e foi rejeitada), slope por
  par, agregação por moeda, normalização por barra (mais forte = ±2*box).
  Anti-lookahead travado em teste (normalização é cross-sectional na
  MESMA barra; não vaza futuro).
- HIPÓTESES PRÉ-REGISTRADAS (traduzidas dos 4 posts do especialista, antes
  de qualquer contato com os dados): R1 exaustão-macro (linha fora da box
  com dline contra = operar CONTRA o macro); R2 cascata (D1 dline contra o
  macro + H4/H1 confirmando = seguir D1); R3 peso-relativo (seguir o TF com
  linha fora da box E ainda abrindo). Avaliação nos moldes do a5/a10:
  3 baselines + reality check por permutação, dias research, holdout
  intocado. Variações pós-hoc serão rotuladas como exploratórias.
- Nota: honestidade sobre o prior — acc_z (primo da inclinação da linha)
  e ML teto AUC ~0.5 já deram nulo; o a12 fecha a última porta fiel à
  tese "só com CSS", não reabre as anteriores.
- Dado bruto: re-export s0 bloqueado por "Máx. barras no gráfico"=100k no
  terminal (copy_rates_range Invalid params; M5 só até 2025-03). Usuário
  subiu o limite; re-export ok (28 pares, M5 2a + D1 7a). Fuso re-verificado
  no novo export: exceções = semanas de DST dos EUA e feriados, nenhum
  deslocamento uniforme — evidência anexada ao `_meta.json`.

## 2026-07-06 — a12 executado: **RESULTADO NULO** (results/*_a12)

Código congelado em commit ANTES da primeira execução. Dois universos:
usd7 (fiel ao indicador do usuário) e all28 (sensibilidade).

- Contraste: maior d de Cohen 0.10 (MN_dist_box/dline) — nada separa
  rotulados de não-rotulados, mesmo padrão do a5.
- Regras pré-registradas (395 dias research): R1 10.1/11.8% top-1,
  R2 13.9/14.9%, R3 10.6/10.9% — nenhuma sobrevive. No all28 a R2 passa
  dos baselines por 0.4pp mas fica ABAIXO do p95 permutado (15.7%) —
  exatamente o tipo de falso positivo que o reality check existe para matar.
- Teto de ML sobre a geometria: AUC 0.503–0.518 — sem sinal.
- Conclusão: a geometria literal do CSS clássico (ranking por barra, box
  ±0.2, inclinação da linha) TAMBÉM não prevê o rótulo em T0. A tese
  "identifica só com o CSS" está agora refutada nas duas formulações
  possíveis (features estatísticas E geometria literal). Restam, como
  hipóteses vivas: informação fora do gráfico (calendário/fundamentos —
  nunca testada) ou decisão em horário ≠ T0.

## Pendente

- `a7_final_test.py` (holdout, últimos ~20% dos dias): NÃO executado. Roda
  UMA vez, só sob ordem explícita do dono do repositório.

## 2026-07-06 — a13 (pré-registro): "peso" (derivada do CSS) → Tokyo→NY

Motivação: 3 posts públicos novos do especialista (CHF/GBP/NZD, jul/2026)
revelam que a leitura dele NÃO é a posição da linha (a12, nulo) e sim a
VARIAÇÃO de intensidade ("fraqueza reduzida", "combustível no fim", "perde
o fôlego", "força bruta", "região de retomada"), aplicada como árvore de
VETO hierárquico (TF maior sem peso → comando passa ao menor). Ele também
declara a janela operacional: abre em Tokyo, fecha ANTES de NY, sem
gain/stop — um alvo diferente do rótulo v1.

Pré-registro (commit ANTES da primeira execução, disciplina do a12):

- ALVO NOVO (rótulo v1 INTOCADO — não é redefinição, é outra variável de
  saída): sinal do Δ índice sintético da moeda em [T0, T0+15h) —
  00:00→15:00 servidor = 17:00→08:00 NY. Sensibilidade secundária: 12h.
- Features derivadas por TF: dpeso = |val|_t − |val|_{t−3}; conv (fora da
  box E esvaziando); retomada (dentro da box, re-expandindo a favor).
- 3 regras traduzidas dos posts: RA exaustão-contra (CHF), RB
  transferência-de-comando ao H4 (GBP), RC amparo-D1 contra o macro (NZD).
  Macro = MN se disponível, senão W1.
- Critério de sucesso idêntico a5/a10/a12: top-1 no sinal do alvo > 3
  baselines (continuação-D1, persistência do alvo, acaso pareado 50%) E >
  p95 de 200 permutações em bloco; n<100 = amostra insuficiente. Dias
  research; holdout intocado; usd7 primário, all28 sensibilidade. Fora
  disso = exploratório.
- Prior honesto: alvo Tokyo→NY nunca foi testado diretamente (a5/a12
  miravam o rótulo; a10 Tarefa 2 mirava [T0+4h,T0+12h]) — mas os nulos
  anteriores tornam um positivo improvável; o valor do a13 é fechar a
  formulação "peso/derivada + veto + janela do especialista".
- 10 testes novos (tests/test_a13.py): causalidade das features (dpeso/
  conv/retomada não veem futuro), lógica das 3 regras, veto do D1, fallback
  MN→W1, janela do alvo exclusiva em T0+15h.

Pendente (fora deste commit): auditoria PROSPECTIVA das chamadas públicas
do especialista (specialist_calls_v2.csv, coleta diária, 60-90 dias) para
medir hit rate real na janela Tokyo→NY antes de gastar mais ciclos de
engenharia reversa — os posts são ex-post e carregam viés de seleção.

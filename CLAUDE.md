# Tendência Absoluta — Instruções do Projeto

Pesquisa em duas fases sobre "tendência absoluta" diária de moedas G8:
(A) rotular a realidade nos últimos 2 anos; (B) engenharia reversa — o que o
CSSM mostrava na abertura de Tokyo (T0) nos dias rotulados. Metodologia
completa em `PLAN.md` — leia antes de qualquer fase.

## Estado atual

- `cssm_engine.py` — PRONTO e validado (porte fiel do indicador MQ5). Não
  alterar matemática sem rodar `pytest` e justificar.
- `a1_label_days.py` — PRONTO. **Definição v1 CONGELADA em 2026-07-04**
  (breadth>=6/7, |z|>=0.8, er>=0.12 — ver labels_v1_meta.json e CHANGELOG.md).
  Qualquer mudança = v2, reinicia a Fase B.
- `a2_audit_specialist.py` — PRONTO: 6/7 chamadas confirmadas, direção 7/7.
- `specialist_calls.csv` — IMUTÁVEL. Dados fornecidos pelo usuário.
- `splits_days.py` — guardião do holdout (por dias).
- `s0_export_mt5.py` — pronto (Windows + MT5; exporta M5 2a + D1 4a).
- Modos por TF (a4): completo M30/H1/H4/D1; reduzido W1 (sem z-features,
  estados Ruído/Madura); MN omitido. Justificativa no PLAN.md §3.
- `stats_blocks.py` — bootstrap em blocos, permutação, purged CV (testados).
- `a3`, `a4`, `a5`, `a6`, `a8` — PRONTOS e executados em 2026-07-04; ver
  results/*/REPORT.md. **Resultado central: NULO** — o fenômeno existe
  (~88% dos dias com >=1 rótulo) mas o CSSM em T0 não o prevê (ML AUC ~0.48;
  nenhuma regra bate baselines + reality check; persistência dia-a-dia nula).
- `a7_final_test.py` — stub DE PROPÓSITO: holdout, só sob ordem explícita.
- `r1_relational.py` — camada relacional (motor por par, matriz 8x8,
  breadth/nowcast, dominância). DESCRITIVA: diagnóstico validado pelo a11
  (~64% dos instantes ativos do índice são força espúria); como preditor,
  NULA (concordância 16-28%; seleção de par nula). Não reabre os nulos.
- `Cssm.mq5` — indicador MT5 de produção, v1.40 (v1.30 + camada relacional
  portada da pesquisa). Ver "Regras do indicador" abaixo e o
  `INDICATOR_CHANGELOG.md` (âncoras de linha de cada mudança).
- Histórico de decisões e resultados: `CHANGELOG.md`.

## Ambiente e dados

- Python >= 3.11; `pip install -r requirements.txt`; `pytest -q` deve passar.
- `MetaTrader5` (pip) só em Windows com terminal logado. Sem isso: usuário
  fornece os dados. NUNCA usar dados sintéticos como substituto de dados
  reais nas fases A2+.
- Contrato: `data/raw/{SYMBOL}.parquet` (M5, 2 anos) e
  `data/raw/D1_{SYMBOL}.parquet` (D1, 4 anos) — índice DatetimeIndex no fuso
  do servidor, coluna única `close`, barras fechadas, sem duplicatas.
  `data/raw/_meta.json` deve ter `server_tz` preenchido e VERIFICADO pelo
  usuário antes de a1 (erro de fuso desloca a janela e invalida tudo).

## Regras duras (não negociáveis)

1. **Separação de fases**: a Fase A (rotulagem) não consulta o indicador; a
   definição v1 é congelada (`--freeze`) ANTES de qualquer feature da Fase B
   ser calculada. Mudança de definição = v2, reinicia a Fase B, reportada
   como segunda tentativa.
2. **Holdout por dias**: últimos 20% dos dias só via
   `splits_days.holdout_days(i_accept_this_is_final=True)`, chamado
   exclusivamente por `a7_final_test.py`, UMA vez, sob ordem explícita.
3. **Sem lookahead**: features em T0 usam só barras FECHADAS antes de T0
   (merge_asof backward; D1 = barra de ontem). Teste obrigatório em tests/.
4. **specialist_calls.csv é âncora de auditoria, nunca de treino**: na Fase B
   os 7 dias são dias comuns, sem peso especial.
5. **Baselines antes de vitória**: nenhuma regra é reportada como boa sem
   bater continuação-D1, persistência-de-rótulo e aleatório pareado.
6. **Bootstrap em blocos** p/ ICs; **n<100 eventos** = amostra insuficiente;
   **reality check** com 200 permutações em bloco para rankings de regras.
7. Relatórios sempre com as métricas do PLAN.md, incluindo resultados nulos.

## Regras do indicador (Cssm.mq5) — valem para QUALQUER mudança no .mq5

1. **Ler o arquivo inteiro e mapear as estruturas antes de editar**
   (`Compute()`, `StateAt()`, `FillBuffers()`, arrays achatados
   `serie[moeda*len+k]`, prefixos de objetos `PFX/PPFX/MPFX`). Não confiar
   de memória.
2. **Compilar antes de entregar**: MetaEditor CLI —
   `MetaEditor64.exe /compile:"Cssm.mq5" /log:"log"` — deve dar
   **0 errors, 0 warnings** (o log sai em UTF-16). O `.ex5` NÃO é
   versionado (.gitignore).
3. **Anti-repaint é sagrado**: todo cálculo usa `CopyClose(...,1,W)` (só
   barras fechadas); a barra em formação (shift 0) recebe só cópia
   cosmética. Nenhuma feature nova pode ler a barra 0.
4. **Contrato de buffers p/ EAs é API pública**: 0-7 M | 8-15 estado |
   16-23 direção | 24-31 breadth_hard*dir | 32-39 breadth_soft*dir, ordem
   USD,EUR,GBP,JPY,CHF,CAD,AUD,NZD, ler com shift>=1. Mudar índice/semântica
   de buffer existente = breaking change: só com ordem explícita do dono.
5. **Matemática = porte fiel**: TStat/EffRatio do .mq5 espelham
   `cssm_engine.py` (validado por testes). Mudou a matemática num lado,
   muda no outro E roda `pytest` — paridade via `Export_CSSM_Parity.mq5`.
6. **Gates por par são calibrados por janela** (random walk, ~5% FP):
   w=16→2.90 | 24→2.51 | 32→2.35 | 48→2.21 | 64→2.13. Mudou `InpWMid`,
   ajuste `InpPairGate` pela tabela (fonte: `calibrate_gates` do engine).
7. **Honestidade no produto**: o indicador NÃO gera sinal de entrada; a
   camada relacional é LEITURA (diagnóstico/nowcast). Os avisos do
   cabeçalho e do rodapé do painel não saem; features novas que insinuem
   previsão precisam de pesquisa antes (e a pesquisa até hoje deu nulo).
8. Toda mudança no indicador entra no `INDICATOR_CHANGELOG.md` (com
   âncoras de linha) ALÉM do CHANGELOG.md padrão, no mesmo commit.

## Convenções

- Séries cronológicas; janelas para trás; funções puras; CLI fino por script;
  cada rodada grava `results/{timestamp}_{fase}/` com params.json + REPORT.md.
- Novos cálculos estatísticos ganham teste em `tests/` antes do uso.

## Fluxo de alterações (git) — OBRIGATÓRIO para IAs e humanos

Este repositório vive no GitHub (`origin` = github.com/rhuancoelhobr7/
ta-research) e é compartilhado: toda modificação DEVE ser registrada no git.

1. **Nunca trabalhe sem commitar**: mudança feita = commit feito. Nada de
   deixar alterações soltas na working tree ao terminar uma tarefa.
2. **Branch + Pull Request** para qualquer mudança de código ou metodologia
   (`git checkout -b <tema>` → commits → `git push -u origin <tema>` →
   `gh pr create`). Push direto no `main` só para correções triviais de
   documentação, e ainda assim commitado e pushado.
3. **`pytest -q` verde ANTES de cada commit** — se quebrar, o commit não
   acontece.
4. **Mensagens de commit explicam o PORQUÊ** (o método, não só o código);
   decisões metodológicas também entram no `CHANGELOG.md` no mesmo commit.
5. **Puxe antes de mexer** (`git pull --rebase origin main`): outras pessoas
   (e outras IAs) trabalham no mesmo repositório.
6. As regras duras acima continuam valendo dentro do git: PR que toque
   holdout (a7, `--include-holdout`), definição v1 congelada ou
   `specialist_calls.csv` não deve ser aberto sem ordem explícita do dono
   do repositório (rhuancoelhobr7).

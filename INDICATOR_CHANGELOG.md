# CSSM_Contexto — changelog do indicador

## v1.40 (2026-07-05) — camada relacional (matriz 8×8, breadth, força espúria)

Motivação (pesquisa a11, H1/2 anos, dias research): o índice sintético, por
ser média da cesta, acusa força espúria em **~64% dos instantes ativos**
(|t_índice| ≥ gate com menos de 3 dos 7 pares confirmando). A camada por
par corrige a LEITURA. Camada **descritiva** — nada aqui é sinal de entrada;
a pesquisa (a11/v2) testou continuação pós-reconhecimento: **nula**.

Âncoras de linha em `Cssm.mq5` (1.385 linhas; v1.30 tinha 912):

| Mudança | Onde | O quê |
|---|---|---|
| Cabeçalho e versão | 1–53 | v1.40, motivação com o nº (~64%), tabela de gates por w, limitação (par sem Exausta), contrato de buffers 0–39, aviso de honestidade estendido à camada |
| Inputs novos | 102–107 | `InpRelational`, `InpPairGate` (2.13, w=64), `InpPairGateLow` (1.28), `InpAlertBreadth`; comentário com a tabela w→gate (16→2.90, 24→2.51, 32→2.35, 48→2.21, 64→2.13) |
| Buffers declarados | 133–134 | `BH0..BH7` (24–31, breadth_hard×dir), `BB0..BB7` (32–39, breadth_soft×dir) |
| Globals da camada | 155–172 | `gLp`, `gPairT/gPairER/gPairLog[p*gLp+k]`, `gPairOk`, `gBrSoft/gBrHard[c*gLs+k]`, flags de perf/alerta, `gMtx`, prefixos `PPFX`/`MPFX` |
| Refactor sem duplicação | 220–248 | `TStatSer`/`EffRatioSer` = núcleos sobre série arbitrária; `TStat`/`EffRatio` viram wrappers **idênticos** ao v1.30 (mesma matemática, teste de regressão pela suíte do repo) |
| Núcleo relacional | 409–541 | `RelActive`, `FindPair`, `PairCellT` (orientação: A+B usa t; B+A inverte — antissimetria exata), `PairStateAbs` (Madura ≥ gate; Emergindo-lite ≥ low; Ruído), `Spurious` (\|t_idx\| ≥ InpTGate e hard < 3/7), `SelfTestAntisym` (3 pares, 1ª barra), `ComputePairs` (CopyClose(...,1,W) — anti-repaint idêntico ao Compute; t+ER por par; breadth soft/hard orientado ao sinal do t do índice; cronômetro `GetMicrosecondCount`, log no Journal na 1ª barra, auto-desliga > 200 ms com aviso no painel) |
| Alerta de amplitude | 543–566 | `CheckBreadthAlerts`: transição para hard ≥ 6/7, barra fechada, anti-spam do padrão existente; comentário: reconhecimento, não previsão |
| Buffers 24–39 | 693–702, 717–744, 1167–1176, 1305–1318 | `SetBr`, preenchimento no `FillBuffers` (histórico + cópia cosmética na barra 0), registro no `OnInit`, init/cosmética no `OnCalculate`; com `InpRelational=false` recebem `EMPTY_VALUE` e os buffers 0–23 não mudam |
| Botão MTX | 815–845, 1366–1383 | mesma infraestrutura do FOCO; clique alterna painel ⇄ matriz; estado persiste como o FOCO persiste |
| Painel: coluna amp | 927, 979–987 | após o estado; hard como número principal (`3/7`, verde/vermelho pela direção), soft apagado (`•5`); layout desloca 48 px só quando a camada está ativa (`InpRelational=false` ⇒ layout v1.30) |
| Painel: marcador ⚠ | 955–961, 1024–1031 | linha da moeda com força espúria ganha ⚠ laranja e M em cinza (rótulo do M separado p/ colorir só ele); legenda no rodapé; aviso alternativo quando a camada auto-desliga por perf |
| Aba MATRIZ | 1040–1132 | 8×8 na ordem G8, célula = fundo na cor do estado do par orientado + `M↑/M↓/E↑/E↓/·`, diagonal `—`, cabeçalhos nas cores das moedas; rodapé = líder por breadth_hard + dominância top-3 (bp e % do total, últimas InpWMid barras); redesenho só visível+barra fechada (`gMtxDirty`) |
| Integração | 1260–1289 | `ComputePairs` roda no bloco de barra nova, ANTES do `FillBuffers`; alternância painel/matriz com limpeza de grupo por prefixo |

### Critérios de aceite

1. **Compilação**: MetaEditor 5 CLI — `0 errors, 0 warnings` (Cssm.mq5 e
   Export_CSSM_Parity.mq5).
2. **Antissimetria**: `SelfTestAntisym()` roda na 1ª barra calculada com
   dados reais (3 pares, tolerância 1e-12) e loga no Journal; estrutural-
   mente exata (célula espelhada = mesmo t armazenado com sinal trocado).
3. **Anti-repaint**: todo cálculo novo usa `CopyClose(...,1,W)` (só barras
   fechadas); buffers 24–39 na barra 0 são cópia cosmética, como os 0–23.
4. **Sem regressão**: `InpRelational=false` ⇒ `ComputePairs` nunca roda,
   buffers 0–23 seguem o caminho de código v1.30 intocado (wrappers de
   TStat/EffRatio são identidade), painel volta ao layout v1.30.
5. **Performance**: tempo de `ComputePairs()` logado no Journal na 1ª
   barra; guarda auto-desliga a camada acima de 200 ms com aviso no painel.
   (28 pares × 300 barras × TStat w=64 — mesma ordem do Compute atual.)
6. **Paridade com a pesquisa**: `Export_CSSM_Parity.mq5` exporta breadth
   hard/soft (buffers 24/32+c) de 1 moeda × 50 barras p/ CSV; comparação
   com `data/features/relational_H1_w64.parquet` documentada no próprio
   script (usar `InpPairGate=2.137276`, o gate exato da pesquisa).
   PENDENTE de execução manual no terminal — o t NW em si é o porte já
   validado pela suíte (tests/test_engine.py + test_relational.py).

## CurrencySlopeStrength v2.30 (2026-07-06) — camada de "peso" (leitura, NÃO sinal)

Arquivo novo `indicators/CurrencySlopeStrength_v2_30.mq5`; o
`CurrencySlopeStrength_v2_20.mq5` fica INTOCADO como referência histórica
(é a matemática exata testada no a12b/a13b).

- Painel MTF: símbolo de peso por moeda × TF, k=3 barras FECHADAS do TF
  (pré-registro do a13): `+` dpeso>0 (enchendo), `-` dpeso<0 (esvaziando),
  `!` conv (fora da box E esvaziando — "combustível no fim"), `~`
  retomada (dentro da box re-expandindo a favor). Os glifos ↑/↓/⚠/↻ do
  pedido foram mapeados p/ ASCII por compatibilidade com Consolas/ANSI
  nos labels do MT5 — legenda no rodapé do painel.
- Buffers 10..17 = dpeso por moeda (ordem USD,EUR,GBP,JPY,CHF,CAD,AUD,
  NZD) no TF das linhas, INDICATOR_CALCULATIONS p/ iCustom — **ler com
  shift>=1** (barra 0 em formação). `indicator_buffers` 11→18.
- `ComputeAt(tf,k,out)` generaliza o ComputeNow (que vira wrapper k=0);
  a camada de peso usa k>=1 (barras fechadas, sem repaint). Caminho
  v2.20 (linhas, painel de valores, alertas) inalterado.
- DISCLAIMER no cabeçalho: vocabulário de leitura que espelha os termos
  do especialista, SEM valor preditivo demonstrado — a13 (lente classic)
  e a13b (esta lente) testaram estas leituras em T0 e deram NULO.
- PENDENTE: compilação manual no MetaEditor do dono (mesmo status dos
  parities). Junto: `indicators/Export_CSS_Parity.mq5` (paridade
  css_screen, leitura ao vivo ancorada no tempo) também aguarda
  compilação/execução manual.

## CurrencySlopeStrength v2.33 (2026-07-08) — aba MATRIZ 8×8 por par + visual estilo CSSM

Novo arquivo `indicators/CurrencySlopeStrength_v2_33.mq5` (a v2.32 em uso no
terminal foi importada verbatim no mesmo PR como referência). Pedido do dono:
trazer a ideia da matriz do CSSM v1.40 para o CSS, **mas falando a língua do
próprio CSS** — e polir o visual sem tocar em nenhum cálculo.

- **MATRIZ 8×8 (botão MTX)**: célula (a,b) = valor de slope TMA do PAR a/b,
  calculado por `ComputePairVals()` — réplica passo a passo do corpo por-par
  do `ComputeAt` (mesmo W, mesma âncora `InpSyncBars`, mesmo norm ATR/stdev,
  mesma TMA peso-21, mesmo clamp em ScaleMax), só que SEM agregar na cesta.
  Deliberadamente NÃO é o t Newey-West do CSSM: a matriz do CSS mostra o
  mesmo número que as linhas/painel mostrariam para aquele par. Orientação
  antissimétrica por construção (b,a = −(a,b), o mesmo valor com sinal
  trocado). Barra FECHADA (kShift=1, sem repaint), TF das linhas. Cores pelo
  vocabulário do CSS: verde/vermelho = par fora da box 0.20 (limiar validado
  no a19 Q5 — nenhum limiar novo inventado), cinza = dentro; célula mostra o
  valor numérico. Rodapé: forte/fraca pela cesta + aviso "leitura descritiva,
  não é sinal" (mesmo status de sempre).
- **ComputeAt intocado**: contrato v2.30/v2.32 dos buffers 0–17 preservado;
  a duplicação do corpo por-par foi escolhida de propósito para não alterar
  a assinatura nem o caminho de código existente.
- **Visual (só render, zero matemática)**: rótulos na ponta das linhas com
  anti-colisão (herdado do CSSM v1.10; `InpEndLabels`); título no painel;
  células chapadas (borda = fundo, estilo CSSM); cabeçalhos de coluna em
  cinza; aviso do rodapé no tom do CSSM; objetos do painel movidos para o
  grupo `CSS_p_` e da matriz para `CSS_mx_` (alternância painel ⇄ matriz
  sem vazamento de objetos — infra idêntica à do CSSM v1.40).
- **Aceite**: MetaEditor 5 CLI — `0 errors, 0 warnings`. Diff v2.32→v2.33
  auditado: nenhuma linha de `TMA/ATRrel/Vol/ComputeAt/ComputeSeries/
  FillPar/FillDpeso/PhaseDir/ColorState` alterada.

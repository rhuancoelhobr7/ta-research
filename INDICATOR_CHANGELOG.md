# CSSM_Contexto — changelog do indicador

## v1.45 (2026-08-12) — modo REPLAY (inspeção do passado)

**Motivação direta** (pedido do usuário): poder olhar o painel como ele estava
em qualquer barra fechada do histórico, sem depender do Testador.

Botões `<<  <  >  >>  [AO VIVO]` ao lado do MTX. `<<` e `<` andam para trás no
tempo, `>` e `>>` voltam, e o botão do meio zera. Passo dos botões duplos no
input `InpReplayStep` (default 10). Marcador pontilhado laranja no gráfico na
barra lida, e um rótulo com o horário dela.

### O que o replay move
Painel, rótulos de ponta, matriz 8×8, idade do estado, setas de aceleração
**e as próprias linhas plotadas**. Tudo lê `gRK` barras fechadas atrás.

**Correção da 1ª tentativa desta versão:** os buffers ficavam ao vivo, para não
contaminar consumidores via `iCustom`. Estava errado para o uso: as linhas
continuavam desenhando até o presente e o **futuro em relação à barra do
replay ficava visível** — que é justamente o que um replay tem de esconder.
Agora as barras mais novas que a barra exibida vão para `EMPTY_VALUE`: a linha
termina no replay e os rótulos de ponta acompanham essa ponta em vez da borda
direita do gráfico. `RpStep` reescreve os buffers a cada clique.

**Consequência assumida:** um consumidor que compartilhe *esta instância* lê
`EMPTY_VALUE` nas barras escondidas e mostra "—". É o comportamento honesto —
melhor "não sei" do que servir dado do futuro. Na prática o `IFM.mq5` v1.3
abre a sua própria instância via `iCustom` com os inputs default; só coincide
com a do gráfico se símbolo, TF **e** todos os inputs forem iguais.

### O que o replay NÃO move
**Os alertas.** Disparar alerta de um evento do passado seria mentira — eles
continuam olhando o índice 0.

### Isto não é um backtest
É uma **lente**, não uma régua: mostra o passado sem detecção, latência,
captura restante, precisão, calibração a iso-ruído ou pré-registro. Olhar
histórico garimpado no olho é exatamente o modo de se enganar que o
`FALHAS.md` cataloga. Medição continua sendo no motor Python vendorado
(`cssm_engine.py`, com gate de paridade) dentro do arcabouço de pesquisa.

### Segurança
`RK()` sempre devolve índice dentro das séries calculadas — o `gRK` persiste
entre recálculos e as séries encolhem quando o histórico é curto. `OnDeinit`
já limpava tudo por prefixo `PFX`, o que cobre os botões e a linha vertical.

## v1.44 (2026-08-12) — ER exposto em buffer (40–47), somente exportação

O `ER` era calculado desde a v1.30 (o `M` depende dele) e exibido no painel
desde a v1.42, mas era o **único ingrediente do `M` sem saída por buffer** —
ou seja, invisível para qualquer consumidor via `iCustom`. Os buffers 40–47
passam a expô-lo por moeda, na mesma ordem dos demais
(`USD,EUR,GBP,JPY,CHF,CAD,AUD,NZD`).

**Motivação:** o `IFM.mq5` v1.3 do `ifm-lab` passa a mostrar as colunas `M` e
`er` no painel MÉTRICAS, lendo deste indicador. Ler daqui em vez de
recalcular lá preserva a identidade do objeto medido pelo b1 e pelo B14.

### O que mudou
- `#property indicator_buffers` 40 → **48**.
- Arrays `BE0..BE7` + `SetIndexBuffer(40..47, INDICATOR_CALCULATIONS)`.
- `SetER(c, idx, v)` no mesmo molde de `SetM`/`SetSD`/`SetBr`, chamado nos
  mesmos quatro pontos: limpeza, laço principal, barra em formação e o
  refresh cosmético da barra viva.

### O que NÃO mudou
**Zero alteração de cálculo, de gate, de plot ou dos buffers 0–39.** Nenhum
consumidor existente é afetado. O ER continua sendo o mesmo
`EffRatio(c, k, gWMid)` de sempre — a mudança é só de exportação.

### Lembrete de leitura (inalterado desde a v1.42)
O `M` **já contém** o ER: `M = sinal(t) × min(|t|/2, 1) × ER`. As duas saídas
não são independentes — o ER é o fator de qualidade **dentro** do M. E o ER
tem dois papéis: como **portão** (~0,25 com o zS ligado) marca o cruzamento
que merece atenção; como **gradiente** dentro do movimento, **ER alto = pouca
captura restante** (b1: rho −0,51) — não é "entre agora", é "já andou".

## v1.43 (2026-07-28) — layout escalado pelo DPI (corrige sobreposição)

**Bug ANTERIOR à v1.42, corrigido agora.** O painel estimava a largura de um
caractere com `chpx = InpFont*7/9`, número fixo que assume **96 DPI**. Com o
Windows em 125% ou 150%, a Consolas renderiza mais larga do que o código supõe
e as colunas se sobrepõem.

E não era só em DPI alto: a conta mostra que a folga do cabeçalho
`ESTADO(idade)` contra a coluna `amp` era de **−3 px já em 96 DPI** —
`colAmp - (colState + 13·chpx) = 204 - 207`. **Sobrepunha para todo mundo,
sempre.** Aparecia como `ESTADO(idade)ap`.

### O que mudou

| | antes | agora |
|---|---|---|
| largura do caractere | `InpFont*7/9` (fixo, 96 DPI) | `InpFont*7*dpi/(9*96)` via `TERMINAL_SCREEN_DPI` |
| `colBar`, `colState`, `stW`, `colAmp`, `ampW`, `colRest`, `cellW`, `colGrid`, `colAlin`, `colW` | constantes mágicas | **derivados de `chpx`**, com `MathMax` preservando os mínimos antigos |
| offset do `•soft` no `amp` | `+26` fixo | `+4·chpx` |
| offset do nome (⚠) | `+13` fixo | `+2·chpx` |

Folga resultante, verificada por simulação em 96/120/144/192 DPI:
**+8 px no cabeçalho `hd2` e +4 px no `ESTADO`, em todos.**

Em 96 DPI o layout fica praticamente onde estava (`colGrid` 489 vs 483) — não
há salto visual para quem já estava bem.

### Paridade

**Preservada: zero linhas de cálculo, de buffer ou de gate.** Só geometria de
painel. Contrato de buffers 0–39 idêntico.

- sha256 do `Cssm.mq5` v1.43: `22591bde9ba581ea…`

## v1.42 (2026-07-28) — coluna `er` no painel (SOMENTE EXIBIÇÃO)

**O ER já era calculado desde a v1.30** — o `M` depende dele
(`M = sign(t)·min(|t|/2,1)·ER`) — mas era **o único ingrediente do M que não
aparecia no painel**. Esta versão só o exibe.

Motivação (pesquisa detector-g8, jul-2026):
- **b1**: o ER contínuo ordena a captura restante **2× melhor** que o rótulo de
  4 estados (|ρ| 0,5135 vs 0,2640; Δ +0,2496 IC[+0,09 · +0,41]).
- **b9/b10**: `|ER| ≥ 0,2528 ∧ zS` confirma melhor que `|M| ≥ 0,20 ∧ zS`
  (+0,41 a +0,84pp em 4 células, zero inversões).

⚠ **STATUS: HIPÓTESE EXPLORATÓRIA.** Congelada em pré-registro prospectivo
**P2** (`detector-g8/research/p2_er_prospectivo/`). A coluna existe para
**observação**, não para operar.

**Por que NÃO há marcador de ligado/desligado no limiar:** o painel já teve uma
regra que acendia como gatilho (a "candidata") e detectou **0% no teste selado**
do ifm-lab. Número cru, sem destaque — quem quiser o limiar, lê o número.

**Como ler** — o ER tem dois papéis, e confundi-los é o jeito de errar:
- como **portão** (~0,25 com o zS ligado): marca o cruzamento que merece atenção;
- como **gradiente dentro do movimento**: ER alto = **pouca captura restante**
  (b1, ρ −0,51). Não é "entre agora", é "já andou".

### Âncoras de linha em `Cssm.mq5` (1.640 linhas; v1.41 tinha 1.607)

| Mudança | Onde | O quê |
|---|---|---|
| Cabeçalho | 59–81 | bloco v1.42: motivação, status exploratório, como ler, e a nota de que `InpShowER=false` restaura o layout v1.41 EXATO |
| Versão | 92 | `#property version "1.42"` |
| Input novo | 173–177 | `InpShowER` (default `true`) — **no FIM de propósito**: `iCustom` posicional de EAs antigos continua válido (parâmetros omitidos assumem o default) |
| Layout | 1063 | `chpx` movido para cima (era declarado depois) — mesma expressão, sem efeito |
| Layout | 1070–1073 | `erW`; `colGrid` e `colW` deslocados por `erW` (o `colW` também no ramo `InpMTF=false`, senão a coluna cortaria) |
| Cabeçalho do painel | 1084–1086 | header condicional: `" DIR    M      t   pers  er acc"` |
| Linha do painel | 1165–1169 | `er` entre `pers` e `acc`, lendo `gER[c*gLf+0]` — o mesmo array que o `M` já usa |

### Paridade

**Preservada por construção: ZERO linhas de cálculo, de buffer ou de gate foram
tocadas.** O diff inteiro é layout + uma leitura de array já existente. O
contrato de buffers 0–39 é idêntico.

⚠ **Pendente (👤):** recompilar no MetaEditor e rodar `Export_CSSM_Parity.mq5`
para o carimbo formal. Não dá para fazer fora do MT5.

- sha256 do `Cssm.mq5` v1.42: `e61c0c4366b49fce…`

## NOTA DE PESQUISA (2026-07-11) — CSS é APENAS DESCRITIVO (a37 fecha o a26b)

O a26b sugeriu que o CSS servia como "confirmação concorrente" (movimento
persiste após alinhamento, MFE 1.46× o controle). O **a37** refez com controle
PAREADO por volatilidade prévia: o incremento **SOME** (1.46× → **1.08×**) — o
alinhamento ocorre em regime mais volátil (vol prévia 47 vs 27), e o "extra" era
CLUSTERING DE VOLATILIDADE, não valor do CSS. **Não há badge de confirmação
concorrente.** Somado ao restante (a24/a29/a30/a34: CSS não prevê e cola nas
métricas de preço), o veredito consolidado é: **o CSS/CSSM é DESCRITIVO** (leitura
de força/geometria do preço), sem valor incremental preditivo NEM concorrente.
Nenhum badge de sinal entra no indicador.


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

# Guia completo do CurrencySlopeStrength v2.33 (`indicators/CurrencySlopeStrength_v2_33.mq5`)

O CSS ("Currency Slope Strength") mede a **força de cada moeda do G8**
(USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD) pela **inclinação de uma média
móvel triangular (TMA)** em todos os pares em que a moeda participa.
É o indicador de "camada 2" do estilo Anderson Bonoto: em vez de olhar
um par, olha a cesta — quem está empurrando o EURUSD, o EUR ou o USD?

**Status dentro da pesquisa (leia antes de operar):** o CSS é
**LEITURA, não sinal**. Os estudos a13/a13b, a19 e a20 do repositório
testaram as leituras dele contra alvos reais e o resultado preditivo
foi **nulo** (detalhes na §9). Ele descreve o presente com honestidade;
não prevê o dia.

---

## 1. A ideia em 4 passos

1. **Suaviza**: para cada um dos ~28 pares G8 disponíveis na corretora,
   calcula uma TMA de 20 períodos sobre os fechamentos.
2. **Mede a inclinação**: quanto a TMA se moveu da barra anterior para
   a atual, como fração do preço (`slope`). TMA subindo = par subindo
   "de verdade", sem o serrilhado do candle a candle.
3. **Normaliza pela volatilidade**: divide o slope pelo ATR relativo do
   par. Sem isso, GBPJPY (volátil) sempre pareceria mais "forte" que
   EURCHF (quieto). Depois da normalização, todos os pares falam a
   mesma língua: "quantas volatilidades por barra".
4. **Distribui para as moedas**: num par BASE/QUOTE que sobe, a BASE
   ganha `+val` e a QUOTE ganha `-val`. A linha de cada moeda é a
   **média dos seus ~7 pares**. USD em +0.30 significa: "na média dos
   7 pares do dólar, o dólar está subindo a 0.30 na régua do
   indicador".

O resultado são 8 linhas numa janela separada, com escala fixa ±1.00 e
uma **box em ±0.20**: dentro da box = moeda "andando de lado"; fora da
box = impulso direcional.

---

## 2. O que aparece na tela

| Elemento | O que é |
|---|---|
| **8 linhas coloridas** | Força de cada moeda no TF das linhas (`InpLineTF`, default = TF do gráfico). Cores: USD verde-limão, EUR azul, GBP vermelho, JPY magenta, CHF prata, CAD laranja, AUD dourado, NZD ciano. |
| **Box ±0.20** | Linha verde em +0.20, vermelha em −0.20, cinza no zero. Limiar validado empiricamente (a19 Q5: corresponde ao percentil ~46–52 de \|val\| em todos os TFs — estável, não precisa recalibrar por TF). |
| **Painel (direita)** | 5 colunas (default H1, H4, D1, W1, MN), cada uma com o ranking das 8 moedas da mais forte para a mais fraca, células coloridas, barra proporcional e seta de direção. |
| **Aba MATRIZ (botão MTX)** | Matriz 8×8 com o slope de **cada par direto** (não a cesta), na última barra fechada. Alterna com o painel. |
| **Rótulos de ponta** | Nome + valor de cada moeda na ponta direita das linhas, com anti-colisão (herdado do CSSM). |
| **Botões (canto sup. esquerdo)** | `[ 8 LINHAS ]`/`[ PAR (1 LINHA) ]` alterna cesta ↔ linha única do par do gráfico; `[ RESET ]` reexibe moedas ocultas; `[ MTX ]` alterna painel ↔ matriz. |
| **Comment "carregando..."** | Aparece até o histórico dos pares sincronizar. `H1:7` = 7 **pares** (de ~28) com dados prontos naquele TF — não são moedas. Some quando ≥ metade dos pares responde. |

Interação extra: **clicar no nome de uma moeda na coluna A do painel
esconde/mostra a linha dela** no gráfico (útil para isolar 2–3 moedas).
`[ RESET ]` desfaz tudo.

---

## 3. Parâmetros (referência completa)

### Motor do cálculo

| Parâmetro | Default | O que faz |
|---|---|---|
| `InpMAPeriod` | 20 | Período "nominal" da TMA. **Atenção**: a janela real da TMA é fixa em 20 (pesos triangulares 21..1, réplica do original); o parâmetro entra nos tamanhos de janela de dados e no rótulo de horizonte. |
| `InpSlope` | 1 | Lookback do slope: compara `TMA[k]` com `TMA[k+slope]`. 1 = inclinação barra a barra (original). Valores maiores suavizam o slope (e a normalização escala por √slope). |
| `InpUseATR` | true | `true` = normaliza pelo ATR relativo (modo original); `false` = normaliza pelo desvio-padrão dos retornos (`InpVolWin`). |
| `InpATRPeriod` | 100 | Janela do ATR de normalização (modo original: 100). |
| `InpVolWin` | 20 | Janela do desvio-padrão (só usado com `InpUseATR=false`). |
| `InpScale` | 0.40 | Ganho aplicado ao z antes de plotar. Puramente cosmético: afina a amplitude até "bater" com a faixa visual do indicador de referência. |
| `InpScaleMax` | 1.00 | Escala fixa da janela (±). Os valores são clampados em ±(ScaleMax−0.02), então a linha nunca encosta na borda. |
| `InpAddSunday` | true | Corretoras com candle de domingo deslocam o offset do ATR em +1 barra (compatibilidade com o cálculo original). |

### Timeframes e plotagem

| Parâmetro | Default | O que faz |
|---|---|---|
| `InpLineTF` | CURRENT | TF usado pelas **linhas** (e pela matriz e pelos buffers dpeso). CURRENT = TF do gráfico. |
| `InpSyncBars` | true | Âncora temporal: alinha as linhas com as barras do gráfico pelo horário (essencial em backtest/histórico; sem custo em tempo real). |
| `InpBars` | 300 | Quantas barras plotar para trás. Mais barras = mais custo na carga. |
| `InpTF1..InpTF5` | H1, H4, D1, W1, MN | Os 5 TFs das colunas do painel. |
| `InpWidth` | 2 | Espessura das linhas. |

### Painel, box e leitura

| Parâmetro | Default | O que faz |
|---|---|---|
| `InpPanel` | true | Liga/desliga o painel. |
| `InpBox` | 0.20 | Meia-altura da box (o "LevelCrossValue" do original). Também é o limiar das cores de célula do painel e da matriz. |
| `InpTrigger` | 0.20 | Limiar dos 6 estados de cor do modo PAR (1 linha). |
| `InpExtLevel` | 0.50 | Nível de "exaustão forte" (linhas pontilhadas). **a19 Q1b: sem base empírica** — a transição real exaustão→fraqueza acontece perto de val≈0.17, não 0.50. |
| `InpShowExt` | false | Mostra as linhas ±0.50. Desligado por padrão pelo achado acima. |
| `InpDiffThr` | 0.0 | "Regra de ouro": distância mínima entre a moeda mais forte e a mais fraca para o header da coluna ganhar o marcador `>>` (trend com combustível). 0 = qualquer distância. |
| `InpPanelX/Y` | 12 / 16 | Posição do painel (X é margem a partir da DIREITA). |
| `InpFont` | 9 | Fonte do painel/matriz. |
| `InpMatrix` | true | Habilita a aba MATRIZ (botão MTX). |
| `InpEndLabels` | true | Rótulos na ponta das linhas. |
| `InpAlerts` | false | Alertas quando uma moeda CRUZA a box (entra/sai), na barra fechada do TF das linhas. |
| `InpPesoK` | 3 | k (em barras FECHADAS) usado nas setas de direção do painel e nos buffers dpeso (pré-registro do a13). |

---

## 4. Os cálculos, um a um

### 4.1 TMA — a média triangular (réplica exata do original)

A TMA é uma média ponderada onde o candle central pesa mais e os
vizinhos pesam cada vez menos (pesos 21, 20, 19, ..., 1 para cada
lado). É uma média **centrada**: para calcular a TMA da barra `k`,
entram até 20 barras de CADA lado — passado E "futuro" relativo a `k`.

Consequência honesta disso (vale para o CSS original também):

- Nas barras antigas (≥20 barras atrás da ponta) a janela é simétrica
  e o valor é definitivo.
- Na **ponta direita** a janela fica assimétrica: a TMA da barra atual
  usa só o passado e vai **se acomodando** conforme novas barras
  chegam. É o "repaint natural" de toda TMA centrada — as últimas ~20
  barras das linhas se ajustam um pouco em retrospecto.
- Mesmo em `k=1` (barra fechada) a barra 0 em formação ainda entra com
  peso 20/251 ≈ 8% na TMA. Pequeno, mas não zero.

### 4.2 Slope normalizado — o "z" que vira a linha

Para cada par, em cada barra `k`:

```
slope = (TMA[k] - TMA[k+InpSlope]) / preço[k]     # inclinação relativa
z     = slope / (norm + 1e-12)                    # em "volatilidades"
val   = clamp(z * InpScale, ±(InpScaleMax-0.02))  # o que é plotado
```

onde `norm = ATRrel * √InpSlope` (ou stdev dos retornos no modo
legado). A divisão pela volatilidade é o que torna os 28 pares
comparáveis entre si e os TFs comparáveis entre si.

### 4.3 ATRrel — o "ATR" do CSS original (não é um ATR de verdade)

Réplica fiel da fórmula original, com as excentricidades dela:

```
shift = 10 (+1 se InpAddSunday)          # começa 10 candles atrás
tr_i  = |close[i] - close[i+1]|          # só fechamentos, sem high/low
ATR   = média(tr_i, i = shift..shift+100) / 10
ATRrel= ATR / preço_atual
```

Ou seja: é a média dos |Δfechamento| de 100 barras, **começando 10
barras atrás** e **dividida por 10** — herdada do indicador original
"por compatibilidade de escala", não por teoria. Não usa high/low como
um ATR clássico.

### 4.4 Da linha do par para a linha da moeda (a cesta)

```
acc[BASE]  += val_do_par
acc[QUOTE] -= val_do_par
linha[moeda] = acc[moeda] / nº de pares da moeda   # tipicamente 7
```

Por isso a leitura é "contra a cesta": USD +0.30 = na média dos 7
pares do dólar, o dólar sobe. E por construção a soma das 8 linhas é
~zero — força de um lado implica fraqueza do outro.

### 4.5 dpeso — enchendo ou esvaziando (buffers 10–17)

```
dpeso[t] = |val[t]| - |val[t-k]|      # k = InpPesoK = 3 barras FECHADAS
```

- `dpeso > 0`: o movimento está "enchendo" (ganhando amplitude);
- `dpeso < 0`: "esvaziando" (perdendo amplitude), independente da
  direção.

É o vocabulário do especialista ("peso", "combustível no fim",
"retomada") em número. **Testado no a13/a13b: valor preditivo NULO** —
por isso os símbolos `+ - ! ~` que existiam no painel v2.30/v2.31
foram removidos no v2.32. Os buffers continuam expostos para consumo
via `iCustom` (§6).

### 4.6 Modo PAR (1 linha) — o par do gráfico na régua do CSS

`val_par = V[base] - V[quote]`, clampado na mesma escala. A linha é
colorida por 6 estados (limiar `InpTrigger`):

| Cor | Estado |
|---|---|
| Lime | acima de +0.20 e subindo (alta acelerando) |
| Green | acima de +0.20 e caindo (alta desacelerando / exaustão) |
| Red | abaixo de −0.20 e caindo (baixa acelerando) |
| FireBrick | abaixo de −0.20 e subindo (baixa desacelerando) |
| Teal | dentro da box, subindo |
| HotPink | dentro da box, descendo |

### 4.7 Setas de direção do painel (`PhaseDir`)

Para cada TF do painel: `dir[moeda] = sinal(V_fechada_agora −
V_fechada_k_atrás)`, com k = `InpPesoK` = 3 barras **fechadas** —
sem repaint. A seta responde "a força desta moeda cresceu ou caiu nas
últimas 3 barras fechadas deste TF?".

---

## 5. Funções principais (mapa do código)

| Função | Papel |
|---|---|
| `TMA()` | Média triangular centrada (réplica do original, pesos 21..1). |
| `ATRrel()` / `Vol()` | Normalizadores de volatilidade (original / legado). |
| `ComputeAt(tf, k, out[])` | Valor de força das 8 moedas na barra `k` de um TF. `k=0` = barra em formação (painel), `k≥1` = fechada (setas, matriz, rodapé). Retorna quantos PARES entregaram dados. |
| `ComputeNow(tf, out[])` | Atalho `ComputeAt(tf, 0, ...)` — usado pelas 5 colunas do painel. |
| `ComputeSeries()` | As linhas do gráfico: mesmo cálculo, para `InpBars` barras do TF das linhas. Preenche os buffers 0–7, o plot do PAR e os dpeso. |
| `ComputePairVals(tf, k, pv[], pok[])` | Slope de cada PAR direto (sem agregar na cesta) — alimenta a MATRIZ. |
| `PhaseDir(tf, dir[])` | Setas de direção (barras fechadas, k=3). |
| `CheckAlerts(V[])` | Alertas de cruzamento da box no TF das linhas (barra fechada). |
| `DrawPanel/DrawCol` | Painel de 5 colunas ranqueadas. |
| `DrawMatrix()` | Aba MATRIZ 8×8. |
| `DrawEndLabels()` | Rótulos de ponta com anti-colisão. |
| `Compute()` | Orquestra tudo; retorna `ready` (linhas ok E colunas H1/H4/D1 com ≥1 par). |
| `OnCalculate/OnTimer` | Recalcula em barra nova (e a cada tick/2s enquanto não `ready`). |

Detalhe de inicialização: o `OnInit` varre TODOS os símbolos da
corretora, reconhece os pares cujo base e quote são moedas G8,
deduplica e os seleciona no Observação do Mercado. O número detectado
sai no diário: `CurrencySlopeStrength: N pares detectados` (esperado:
28). A primeira carga em terminal "frio" baixa histórico de N pares ×
6 TFs — leva minutos; depois fica em cache e abre em segundos.

---

## 6. Outputs — buffers para consumo via `iCustom`

| Buffer | Conteúdo | Observação |
|---|---|---|
| 0–7 | Linhas USD, EUR, GBP, JPY, CHF, CAD, AUD, NZD | No TF das linhas. `EMPTY_VALUE` fora da janela plotada ou moeda oculta. |
| 8 | Linha do PAR (modo 1 linha) | Só preenchido com o botão PAR ativo. |
| 9 | Índice de cor do plot do PAR | Estados da §4.6. |
| 10–17 | `dpeso` por moeda (mesma ordem USD..NZD) | `INDICATOR_CALCULATIONS` (não plotado). **Ler com `shift ≥ 1`**: a barra 0 recebe valor em formação e repinta até fechar. |

Exemplo de leitura externa:

```mql5
int h = iCustom(_Symbol, PERIOD_H1, "CurrencySlopeStrength_v2_33");
double usd[1];
CopyBuffer(h, 0, 1, 1, usd);   // força do USD na última barra FECHADA
double dpesoUsd[1];
CopyBuffer(h, 10, 1, 1, dpesoUsd);  // dpeso do USD, shift 1 obrigatório
```

---

## 7. O painel — como ler cada pedaço

```
CSS FORCA (TMA)  linhas:H1  box:0.20
H1·20h      H4·3d       D1·20d      W1·140d     MN·20m
USD +0.42 ▲ ...
EUR +0.18 ▲
...
NZD -0.35 ▼
verde=forca verm=fraqueza cinza=box | verde+▼=exaustao cinza+▲=expansao
ciclo=LEITURA, nao sinal (a19: 40% falsa exaustao; a20: confluencia MTF nula)
```

- **Header da coluna** (`H1·20h`): TF + **horizonte real** da TMA(20)
  naquele TF — 20 barras de H1 = 20 horas; de D1 = 20 dias. As colunas
  NÃO são comparáveis sem esse rótulo: "força no D1" é um fenômeno de
  semanas, não de horas. Ganha `>` quando há trend (mais forte acima
  da box E mais fraca abaixo) e `>>` (dourado) quando além disso a
  distância forte−fraca ≥ `InpDiffThr`.
- **Ranking**: as 8 moedas ordenadas da mais forte para a mais fraca
  **naquele TF** (barra em formação, k=0 — o painel "respira"
  intrabar).
- **Cor da célula**: verde = fora da box por cima (força); vermelho =
  fora por baixo (fraqueza); cinza = dentro da box.
- **Barra fina na base da célula**: |valor| proporcional à escala —
  régua visual rápida de "quanto" além do "onde".
- **Seta**: direção da força em 3 barras fechadas (§4.7). `·` =
  parado.

### O ciclo de fases (vocabulário a19)

Cor + seta formam a fase da moeda naquele TF:

| Célula | Fase |
|---|---|
| verde + ▲ | **FORÇA** (fora da box, ganhando) |
| verde + ▼ | **EXAUSTÃO** (fora da box, devolvendo) |
| cinza/vermelho + ▼ | **FRAQUEZA** |
| cinza + ▲ | **EXPANSÃO** (dentro da box, re-expandindo) |

O que o a19 mediu sobre esse ciclo (por isso ele é só vocabulário):

- A rotação FORÇA→EXAUSTÃO→FRAQUEZA→EXPANSÃO **existe como gramática**
  (transição canônica com probabilidade 0.65–0.67 vs 0.33 do acaso, em
  todos os TFs)...
- ...mas só **13–15%** dos ciclos completam a volta na ordem, e ~**40%
  das saídas de EXAUSTÃO voltam direto para FORÇA** ("falsa
  exaustão"). Ver EXAUSTÃO não autoriza apostar em reversão.
- O tempo de permanência mediano em cada fase é 3–5 barras, em
  qualquer TF, com pouca memória além disso.

---

## 8. A MATRIZ 8×8 (botão MTX)

Célula `(a, b)` = slope TMA do **par direto a/b**, orientado de `a`
para `b`, na **última barra fechada** do TF das linhas — a MESMA
fórmula das linhas (§4.2), só que sem agregar na cesta. `b/a` é o
espelho negado. Verde/vermelho = par fora da box ±0.20; cinza =
dentro; `-` = diagonal; `?` = par sem símbolo na corretora.

Diferença importante para a matriz do CSSM: aqui NÃO há t-stat nem
teste de significância — é o valor cru do CSS falando a própria
língua. Rodapé: moeda mais forte e mais fraca pela cesta (mesmo
cálculo do painel, barra fechada).

Uso típico: você vê no painel "USD forte, NZD fraco" e abre a matriz
para conferir o par específico NZDUSD — às vezes a força da cesta vem
de outros pares e o par que você ia operar está morno.

---

## 9. Leitura na prática — e o que a pesquisa já descartou

A leitura clássica do estilo (o que o indicador FOI DESENHADO para
mostrar):

1. **Moeda fora da box = impulso.** Dentro da box = ruído/lateralidade.
2. **Trend novo**: a moeda do topo fora da box por cima E a do fundo
   fora por baixo, com distância entre elas ("combustível").
3. **Par ideal**: comprar a moeda forte contra a fraca, no TF onde a
   leitura aparece, de preferência com TFs maiores apontando junto
   (a "cascata").

O que os estudos deste repositório mediram sobre essas leituras
(CHANGELOG 2026-07-06 a 2026-07-08):

| Leitura | Veredito empírico |
|---|---|
| Box 0.20 fixa | **Validada como régua descritiva** (a19 Q5: percentil estável ~50 em todos os TFs; recalibração por TF rejeitada por desnecessária). |
| Nível 0.50 de "exaustão forte" | **Sem base empírica** (a19 Q1b: 0% das transições exaustão→fraqueza acontecem em [0.4,0.6]; a real ocorre ~0.17). Por isso as linhas 0.50 vêm desligadas. |
| Ciclo de fases como GATILHO | **Não** — gramática real, mas 40% de falsa exaustão (§7). |
| Peso/dpeso como previsão do dia | **Nulo** (a13 na lente clássica E a13b na lente desta tela, contra o alvo Tokyo→NY). |
| Confluência/cascata MTF (colunas alinhadas ⇒ grande movimento) | **Nula** (a20 Q7/Q8: lift 1.04–1.11 vs baseline embaralhado 1.07–1.08, sem monotonia, sem sobrevivência out-of-sample). Alinhamento de TFs NÃO é gatilho de entrada. |
| Assinatura por moeda | JPY mostrou continuação pós-exaustão no D1; EUR/CHF/USD, reversão — provável regime da década (iene em queda secular), **não generalizar**. |

Tradução prática: use o CSS para **descrever** o campo de forças
(quem está forte, contra quem, em que horizonte, desde quando) e para
narrar o gráfico com vocabulário disciplinado. Não use nenhuma leitura
dele, isolada ou em confluência, como gatilho mecânico de entrada —
foi exatamente isso que os testes não sustentaram.

### Alertas

Com `InpAlerts=true`, dispara `Alert()` quando uma moeda **cruza** a
box (entra ou sai) na barra fechada do TF das linhas — "USD SAIU p/
CIMA da box (+0.23) = forca". Sem repaint (barra fechada), mas herda o
status de leitura: é um aviso de mudança de descrição, não um sinal.

---

## 10. Ciclo de vida, desempenho e pegadinhas

- **Primeira carga** (terminal sem cache): o comment
  `Slope Strength carregando... H1:x H4:y D1:z linhas:...` mostra
  quantos **pares** (de ~28) já sincronizaram por TF. O MT5 baixa o
  histórico completo de cada símbolo×TF na primeira requisição — 28
  símbolos × 6 TFs leva minutos em conexão comum. **Custo único**;
  depois abre em segundos. Se travar: Ctrl+U → aba Barras → solicite
  H1/D1 dos pares atrasados, ou deixe o terminal quieto uns minutos.
- **Recalculo**: em barra nova do gráfico (e a cada tick/timer de 2s
  enquanto não `ready`). O painel usa k=0 (barra em formação), então
  os números das colunas se mexem intrabar; setas, matriz e alertas
  usam barra fechada e não repintam.
- **Ponta das linhas se acomoda**: TMA centrada (§4.1) — as últimas
  ~20 barras das linhas se ajustam em retrospecto. Ao avaliar "o que o
  indicador mostrava na hora", use barra fechada e desconte esse
  efeito (os estudos do repo fazem isso via `kShift≥1`).
- **Dependência da corretora**: o universo de pares vem da lista de
  símbolos da SUA corretora. Menos de 28 pares = cestas com menos
  membros (o denominador `cnt` se ajusta sozinho, mas a leitura fica
  mais pobre). Confira o diário: `N pares detectados`.
- **Moedas ocultas** (clique na coluna A) afetam SÓ a plotagem das
  linhas — cálculo, painel, matriz e buffers continuam com as 8.
- **Backtest**: `InpSyncBars=true` ancora as janelas pelo horário da
  barra do gráfico, para o painel/linhas baterem com o passado.

---

## 11. Linha do tempo das versões (o que mudou e por quê)

| Versão | Mudança | Motivo |
|---|---|---|
| v2.30 | Camada de "peso" (dpeso + símbolos `+ - ! ~` no painel); buffers 10–17 | Espelhar o vocabulário do especialista para o teste a13. |
| v2.31 | Breadth por moeda×TF, marcadores `*`/`°`, horizontes reais no header | Fase 1 de instrumentação. |
| v2.32 | Painel redesenhado: células coloridas + setas (ciclo a19); símbolos de peso REMOVIDOS (a13/a13b nulos); linhas 0.50 desligadas (a19 Q1b); legenda com o veredito | Alinhar o visual ao que sobreviveu aos testes — o indicador só afirma o que foi validado. |
| v2.33 | Aba MATRIZ 8×8 por par (botão MTX) + rótulos de ponta + polimento visual. **Nenhum cálculo alterado.** | Usabilidade herdada do CSSM v1.40/v1.10. |

Regra de governança (CHANGELOG): mudança no cálculo ou nos limiares só
com sobrevivência out-of-sample + melhora de leitura, sem venda
preditiva. Foi por essa régua que a v2.32/v2.33 NÃO mudaram nenhuma
fórmula.

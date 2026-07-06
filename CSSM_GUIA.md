# Guia completo do CSSM_Contexto v1.41 (`Cssm.mq5`)

Mapa de tudo que o indicador calcula e mostra: parâmetros, matemática e —
principalmente — **como ler cada saída**. Escrito para quem vai operar o
painel no dia a dia ou consumir os buffers num EA.

> **O que ele NÃO é (leia primeiro).** O CSSM é um painel de **contexto /
> nowcasting**: ele descreve a tendência EM CURSO de cada moeda G8 com
> disciplina estatística. A pesquisa deste repositório testou exaustivamente
> se esse reconhecimento prevê continuação (estudo de evento com 26k
> eventos; a5/a11/a12/a13) — resultado **NULO**. Ele diz *"o EUR está em
> tendência de alta madura, confirmada por 6 dos 7 pares"*; ele **não** diz
> *"compre EUR"*. Use-o para enquadrar, filtrar e escolher instrumento — não
> como gatilho.

---

## 1. A ideia em 4 passos

1. **Índices sintéticos.** O indicador detecta os 28 pares G8 do Market
   Watch e decompõe cada retorno de par entre as duas moedas: o log-retorno
   de EURUSD soma para o índice do EUR e subtrai do índice do USD. O índice
   de cada moeda é a média dos seus retornos contra as outras 7, acumulada.
   Resultado: 8 séries "força da moeda" livres da escolha de par.
2. **Features estatísticas** sobre uma janela `w_mid` de cada índice:
   significância da tendência (t Newey-West), eficiência (ER), momentum
   normalizado, persistência, curvatura e aceleração (ver §4).
3. **Máquina de estados** por moeda: Ruído → Emergindo → Madura → Exausta,
   com portões calibrados em random walk (≈5% de falso positivo) (§5).
4. **Duas camadas de confirmação**: a **relacional** (v1.40) checa moeda a
   moeda quantos dos 7 pares confirmam o índice — mata a "força espúria" da
   média; a **grade MTF** repete o motor em 6 timeframes, cada um com a
   janela adequada ao seu horizonte (v1.41).

Tudo é calculado **só com barras fechadas** (`CopyClose(...,1,W)`): nada
repinta. A barra em formação exibe uma cópia cosmética da última fechada.

---

## 2. Janelas por horizonte (v1.41) — o conceito central

### O problema que o modo HOURS resolve

Uma janela fixa de 64 barras significa horizontes temporais completamente
diferentes conforme o TF: 32 h no M30, 2,7 dias no H1, 10,7 dias no H4. O
indicador "procurava tendências remotas" nos TFs curtos, e a grade MTF
comparava coisas incomparáveis.

### Como funciona

Você declara **o que procura em horas**, e cada TF converte para barras:

- `InpHorizonHours = 18` → horizonte de **DETECÇÃO** (o fenômeno-alvo da
  pesquisa, "tendência absoluta", vive em 12–24 h);
- `InpContextHours = 120` → horizonte de **CONTEXTO** (~5 dias), para TFs
  cuja barra é grande demais para a detecção;
- piso estatístico: **16 barras** (menos que isso o t Newey-West não tem
  resolução — não é ajustável sem recalibrar os portões); teto: 96 barras.

Regra por TF (`WinFor`): se `round(18h / barra)` ≥ 16 → camada **detecção**;
senão, se `round(120h / barra)` ≥ 16 → camada **contexto**; senão → camada
**estrutural** (w = 64 legado). Derivados: `w_fast = max(4, w/4)` e
`z_win = clamp(8·w, 150, 500)`.

### Tabela efetiva com os defaults

| TF  | barras p/ 18h | w_mid | camada         | w_fast | z_win | t_gate / t_low |
|-----|---------------|-------|----------------|--------|-------|-----------------|
| M5  | 216 (→ teto)  | 96    | detecção ᵈ     | 24     | 500   | 2.134 / 1.280   |
| M15 | 72            | 72    | detecção ᵈ     | 18     | 500   | 2.134 / 1.280   |
| M30 | 36            | 36    | detecção ᵈ     | 9      | 288   | 2.314 / 1.444   |
| H1  | 18            | 18    | detecção ᵈ     | 4      | 150   | 2.800 / 1.651   |
| H4  | 4,5 < 16 → ctx| 30    | contexto ᶜ     | 7      | 240   | 2.390 / 1.477   |
| D1  | <16 nas duas  | 64    | estrutural ˢ   | 16     | 500   | 2.134 / 1.280   |
| W1  | idem          | 64    | estrutural ˢ   | 16     | 500   | 2.134 / 1.280   |
| MN  | idem          | 64    | estrutural ˢ   | 16     | 500   | 2.134 / 1.280   |

**Como ler as camadas:** só os TFs ᵈ *detectam* o horizonte que você pediu.
H4 ᶜ dá o pano de fundo da semana; D1+ ˢ dão o regime de meses. **Nunca leia
um TF estrutural como se ele detectasse o dia** — o piso de 16 barras em H4
equivale a 2,7 dias: é resolução estatística, não defeito.

### Portões auto-calibrados (`InpAutoGates`)

O limiar de t que segura os falsos positivos **depende da janela** (janela
curta = mais ruído no t). Tabela calibrada em random walks (FP 5% / 20%):

| w      | 16    | 24    | 32    | 48    | 64    |
|--------|-------|-------|-------|-------|-------|
| t_gate | 2.896 | 2.511 | 2.350 | 2.205 | 2.134 |
| t_low  | 1.692 | 1.527 | 1.460 | 1.397 | 1.280 |

`GateFor(w)` interpola linearmente entre os nós; acima de 64 mantém o nó 64
(curva assintótica). Com AutoGates ligado, o motor do gráfico, **cada TF da
grade** e a camada relacional usam o gate da própria janela efetiva — a
régua é sempre coerente com o que se mede.

### Modo BARS

`InpWindowMode = WM_BARS` reproduz o v1.40 **byte a byte** (verificado:
buffers 0–39 idênticos em 100 barras). Nesse modo os inputs legados
(`InpWFast/InpWMid/InpZWin/InpTGate/InpTLow/InpPairGate/Low`) mandam e o
horizonte/AutoGates são ignorados.

---

## 3. Parâmetros (referência completa)

### Modo de janela (v1.41)

| Input | Default | O que faz |
|---|---|---|
| `InpWindowMode` | `WM_HOURS` | HOURS = janelas por horizonte; BARS = v1.40 exato |
| `InpHorizonHours` | 18 | horizonte de detecção (h). Mexa aqui para mudar "o que" o indicador procura |
| `InpContextHours` | 120 | horizonte de contexto (h) p/ TFs que não alcançam a detecção |
| `InpAutoGates` | true | portões t interpolados pela janela efetiva (só HOURS) |

### Motor

| Input | Default | O que faz |
|---|---|---|
| `InpTF` | CURRENT | TF do cálculo (deixe = TF do gráfico p/ linhas alinhadas) |
| `InpWFast` | 16 | janela rápida — **só modo BARS** (HOURS deriva w/4) |
| `InpWMid` | 64 | janela média, base de tudo — **só modo BARS** |
| `InpZWin` | 500 | janela do z-score adaptativo — **só modo BARS** |
| `InpBars` | 300 | barras plotadas/preenchidas nos buffers |
| `InpAccSpan` | 8 | EMA da aceleração (suavização) |

### Máquina de estados

| Input | Default | O que faz |
|---|---|---|
| `InpTGate` | 2.0 | \|t\| mínimo p/ Madura — só BARS ou AutoGates=false |
| `InpTLow` | 1.0 | \|t\| mínimo p/ Emergindo — idem |
| `InpPersist` | 0.55 | fração mínima de barras a favor p/ Madura |
| `InpAccEmg` | 0.75 | \|z da aceleração\| mínimo p/ Emergindo |
| `InpCxExh` | −1.0 | z de curvatura CONTRA a tendência p/ Exausta |
| `InpAcExh` | −0.75 | z de aceleração CONTRA a tendência p/ Exausta |

### Visual / alertas

| Input | Default | O que faz |
|---|---|---|
| `InpPanel` / `InpEndLabels` | true | painel; rótulos na ponta das linhas |
| `InpFocusStart` | false | iniciar já em modo FOCO no par do gráfico |
| `InpPanelX/Y`, `InpFont` | 12 / 16 / 9 | posição (X a partir da DIREITA) e fonte |
| `InpAlerts` | false | alerta em transição p/ Madura/Exausta (barra fechada) |

### Camada relacional

| Input | Default | O que faz |
|---|---|---|
| `InpRelational` | true | liga matriz 8x8, breadth e ⚠ |
| `InpPairGate` | 2.13 | \|t\| do PAR p/ confirmação — só BARS ou AutoGates=false |
| `InpPairGateLow` | 1.28 | \|t\| baixo do par — idem |
| `InpAlertBreadth` | false | alerta quando breadth ≥ 6/7 (barra fechada) |

### Grade MTF

| Input | Default | O que faz |
|---|---|---|
| `InpMTF` | true | grade no painel |
| `InpGT1..GT6` | M30, H1, H4, D1, W1, MN | os 6 TFs da grade |

---

## 4. Os cálculos, um a um (aprofundado)

Convenções desta seção: a "janela" tem `w = w_mid` barras **fechadas**, da
mais recente para trás; a "série" é o índice sintético da moeda (um
log-preço acumulado); "retorno" é a diferença entre duas barras consecutivas
do índice. Cada cálculo vem com: o que ele responde, como é feito, por que
foi desenhado assim, e uma régua de leitura com exemplo.

### 4.0 O índice sintético — a matéria-prima

**O que responde:** "quanto desta variação é da MOEDA, e não do par?"

**Como é feito.** A cada barra, o log-retorno de cada um dos 28 pares é
repartido entre as duas moedas: se EURUSD subiu 0,20%, o EUR ganha +0,20% e
o USD ganha −0,20% *naquela relação*. O passo do índice de uma moeda é a
**média dos seus 7 retornos orientados**; o índice é a soma acumulada
desses passos (começando em 0 na barra mais antiga).

**Exemplo.** Numa barra: EURUSD +0,20%, EURJPY +0,10%, EURGBP +0,05% e os
outros 4 pares do EUR parados. Passo do índice EUR =
(0,20 + 0,10 + 0,05 + 0 + 0 + 0 + 0) / 7 ≈ **+0,05%**.

**Por que assim.** EURUSD mistura duas histórias (EUR forte? USD fraco?); a
média contra a cesta inteira isola a parte que é do EUR. Log-retornos porque
são somáveis e simétricos (+1% e −1% se cancelam de verdade).

**A armadilha embutida** (que motiva a camada relacional, §4.9 e §6): uma
média pode subir porque UM par disparou enquanto os outros seis dormem — o
índice acusa "EUR forte" sem o mercado inteiro concordar.

### 4.1 t Newey-West (`TStat`) — "a tendência é maior que o ruído?"

**O que responde:** a deriva média por barra é distinguível de zero, dado o
tamanho do ruído? É o número mais importante do indicador.

**Como é feito, passo a passo:**
1. Calcula os `w` retornos da janela e a média deles, `μ` (a "deriva").
2. Mede o ruído: a variância dos retornos (γ₀) **e** as autocovariâncias
   de defasagem 1, 2 e 3 (γ₁, γ₂, γ₃) — o quanto um retorno "puxa" o
   seguinte.
3. Monta a variância robusta:
   `v = γ₀ + 2·(0,75·γ₁ + 0,50·γ₂ + 0,25·γ₃)` (pesos de Bartlett, que
   decaem com a defasagem).
4. Aplica um piso `v ≥ 0,1·γ₀` (autocovariância muito negativa não pode
   "zerar" o ruído e inflar o t artificialmente).
5. Erro-padrão da média: `EP = √(v/w)`. Resultado: `t = μ / EP`.

**Analogia.** Pesquisa eleitoral: `μ` é a vantagem do candidato, `EP` é a
margem de erro, e o t é a vantagem medida **em múltiplos da margem de
erro**. A correção Newey-West existe porque retornos consecutivos não são
opiniões independentes: entrevistar 18 pessoas da mesma família não vale 18
entrevistas. Quando os retornos vêm "encadeados" (autocorrelação positiva),
a amostra efetiva é menor do que parece, e o NW infla o erro-padrão para
compensar — sem isso o t mentiria para cima exatamente nos momentos
trending, que é quando você mais o consulta.

**Exemplo numérico** (H1, janela de detecção w=18): retornos do índice com
média +0,030% e desvio 0,10%, sem autocorrelação relevante.
`EP = 0,10%/√18 ≈ 0,024%` → `t ≈ +1,27`. Está acima do t_low do H1 (1,651)?
Não — ainda é ruído provável. Se a deriva dobrar para +0,060% mantendo o
ruído: `t ≈ +2,5` — ainda **abaixo** do gate do H1 (2,800). É proposital:
com só 18 barras, random walks produzem t grandes com facilidade, então a
régua sobe (§4.10). A mesma deriva relativa sustentada por 64 barras
passaria com folga no D1.

**Por que não uma regressão sobre os preços?** Era o v1.1x — e regressão de
tendência sobre *níveis* de um random walk acusa tendência em **84%** dos
casos (regressão espúria). Sobre *retornos*, com NW, a taxa de falso
positivo calibra em ~5%. Essa troca (v1.20) é a alma estatística do
indicador.

**Régua de leitura:** \|t\| < t_low → ruído; entre t_low e t_gate → zona de
atenção (só vira Emergindo com aceleração coerente); ≥ t_gate → só ~5% de
chance de sair de puro acaso naquela janela.

### 4.2 ER — Efficiency Ratio: "quanto do caminho virou deslocamento?"

**Como é feito:** `ER = |deslocamento líquido| / soma dos |passos|`, de 0
a 1.

**Exemplo.** O índice faz +10, −5, +10, −5, +10 (em unidades quaisquer):
deslocamento líquido +20, caminho percorrido 40 → **ER = 0,50**. Se tivesse
ido em linha reta (+4,+4,+4,+4,+4), ER = 1,00 com o mesmo destino.

**Por que existe.** O t (§4.1) pergunta *"é estatisticamente real?"*; o ER
pergunta *"foi eficiente?"*. São independentes: dá para ter t alto com ER
baixo (deriva pequena mas teimosa dentro de muito serrilhado). O M (§4.8)
multiplica os dois de propósito.

**Régua:** > 0,3 = movimento limpo, direcional; 0,1–0,3 = tendência suja;
< 0,1 = zigue-zague puro. (O rótulo da pesquisa usava er ≥ 0,12 como piso.)

### 4.3 VolMom — momentum em "distâncias de passeio aleatório"

**Como é feito:** `(P_agora − P_atrás) / (sd·√w)`, onde sd é o
desvio-padrão dos retornos da janela.

**A intuição do √w** (o detalhe bonito): um random walk se afasta do ponto
de partida, em média, `sd·√w` após w passos — dobrar o tempo NÃO dobra a
distância típica, multiplica por √2. É a assinatura da difusão (o passeio
do bêbado). Dividir o deslocamento por `sd·√w` transforma o momentum em
*"quantas distâncias-típicas-de-acaso este movimento percorreu"*.

**Régua:** ±1 = indistinguível de acaso; ±2 ou mais = deslocamento incomum
para o próprio ruído da janela. É calculado em duas janelas — rápida
(`w_fast = w/4`) e média (`w_mid`) — e a **diferença** entre elas alimenta a
aceleração (§4.6).

### 4.4 Persistência — "quantas barras remaram a favor?"

**Como é feito:** conta as barras de alta e de baixa na janela; devolve a
fração que fechou **na direção do deslocamento líquido**.

**Régua:** 0,50 = cara-ou-coroa; 0,55 (o limiar de Madura) parece pouco,
mas manter 55% ao longo de dezenas de barras é um vento consistente; 0,65+
é marcha forçada.

**O que ela filtra:** o modo de falha clássico do t — um gap único gigante
seguido de deriva lateral. O gap infla a média dos retornos (t alto), mas
as barras seguintes ficam ~50/50 → persistência ≈ 0,50 → **não vira
Madura**. Tendência de verdade avança por acúmulo, não por um susto.

### 4.5 Curvatura (`Convex`) — "a trajetória está arqueando?"

**Como é feito:** ajusta uma parábola aos preços da janela e extrai **só o
termo quadrático** (a "boca" da parábola), construído de forma ortogonal —
ou seja, o valor não se contamina nem pelo nível nem pela inclinação da
reta. Depois normaliza por `w²/sd` para virar "curvatura acumulada na
janela, em unidades de ruído por barra".

**Leitura do sinal:** positivo = boca para cima (trajetória acelerando para
cima, ou freando uma queda); negativo = boca para baixo.

**Como o estado usa:** multiplica pelo sentido da tendência (`cx =
z_curv·dir`). `cx ≤ −1,0` significa *"a janela inteira está arqueando
CONTRA a tendência"* — numa alta, é o desenho do topo arredondado: os
preços ainda sobem, mas cada trecho sobe menos que o anterior. É metade do
critério de Exausta.

### 4.6 Aceleração (`gAcc`) — "o motor curto está ganhando do médio?"

**Como é feito:** `acc = EMA₈(VolMom_rápido − VolMom_médio)`. Os dois
momentums estão na mesma escala (graças ao §4.3), então a diferença é
justa; a EMA de span 8 tira o serrilhado barra a barra.

**Leitura:** positivo = o empurrão recente supera a tendência média → o
movimento está se intensificando; negativo = o trecho recente é mais fraco
que a média da janela → perdendo força.

**Onde entra:** em **Emergindo** (aceleração forte, \|z\| ≥ 0,75, e no
MESMO sentido do momentum rápido — evita "acelerar" para o lado errado) e
em **Exausta** (z_acc contra a tendência ≤ −0,75 = freando; é a outra
metade do critério, junto com a curvatura).

### 4.7 z-scores adaptativos — a régua que se recalibra sozinha

Curvatura e aceleração não têm escala universal: o "normal" delas muda por
moeda, por TF e por regime de volatilidade. Solução: dividir cada valor
pelo desvio-padrão dos **próprios últimos `z_win` valores** daquela métrica
naquela moeda. Um z de −1,0 então significa *"1 sigma abaixo do que tem
sido normal PARA ESTA MÉTRICA, aqui, recentemente"* — e os limiares fixos
dos inputs (0,75; −1,0) ficam comparáveis em qualquer contexto.

**Efeito colateral honesto:** janelas de detecção curtas usam z_win menor
(H1: 150 barras) → a régua se recalibra mais rápido → as setas ▲▼ do painel
piscam mais no H1 do que no D1. Não é defeito, é a régua respirando.

### 4.8 M — o resumo plotado

`M = sinal(t) · min(|t|/2, 1) · ER`

Direção pelo t; magnitude = significância (saturando em \|t\| = 2) vezes
eficiência. Três exemplos que mostram o caráter da fórmula:

| t | ER | M | Leitura |
|---|----|----|---------|
| +3,0 | 0,40 | **+0,40** | significativo E eficiente — tendência de livro |
| +4,0 | 0,15 | **+0,15** | muito significativo, mas serrilhado — o M não se empolga |
| +1,2 | 0,50 | **+0,30** | eficiente, mas evidência fraca — por isso o painel mostra t e estado ao lado do M |

A saturação em \|t\|=2 é deliberada: acima do gate, "mais t" não é "mais
tendência", é só mais certeza da mesma coisa — quem diferencia a partir
dali é a eficiência. Faixa teórica −1..+1; a janela exibe −0,6..+0,6 com
níveis pontilhados em ±0,25.

### 4.9 Breadth — a aritmética da confirmação

Para a moeda `c` com direção `d` (sinal do t do índice), olha-se o t **do
par** (mesmo cálculo do §4.1, sobre o log-preço do par) orientado do ponto
de vista de `c`: se `c` é a base do par, usa t como está; se é a cotada,
inverte o sinal.

- **soft** = fração dos 7 pares com t orientado a favor (qualquer tamanho);
- **hard** = fração com t orientado a favor **e** \|t\| ≥ pair_gate.

**Exemplo** (EUR em alta): EURUSD t=+2,5 → conta no hard; EURJPY +1,9 →
só soft; EURGBP −0,4 → nada; EURCHF +2,6, EURCAD +2,2 → hard; EURAUD +0,9,
EURNZD +1,1 → soft. Resultado: **hard 3/7, soft 6/7** → painel `3/7 •6`.
Leitura: a cesta inclina a favor (6 de 7), mas só 3 relações têm
confirmação estatística — tendência real porém ainda rasa; um `6/7 •7`
seria tendência ampla de verdade.

### 4.10 GateFor — por que janela menor exige t maior

Com poucas barras, random walks produzem \|t\| grandes com facilidade — a
sorte tem menos tempo para se diluir. Para manter a taxa de falso positivo
em ~5% em qualquer janela, o limiar precisa SUBIR quando w encolhe. A
tabela (calibrada por simulação) é interpolada linearmente:

**Exemplo:** w = 36 cai entre os nós 32 (2,350) e 48 (2,205). Fração =
(36−32)/(48−32) = 0,25 → `t_gate = 2,350 − 0,25·(2,350−2,205) = 2,314`.
Acima de w=64 o gate congela em 2,134/1,280: mais dados não relaxam a
régua além do assintótico. Abaixo de 16 não existe gate — é o piso
estatístico que define as camadas do §2.

---

## 5. A máquina de estados

Avaliada por moeda, a cada barra fechada (dir = sinal do t):

| Estado | Condição | Tradução |
|---|---|---|
| **Ruído** (cinza) | nenhuma das outras | sem evidência de tendência |
| **Emergindo** (amarelo) | t_low ≤ \|t\| < t_gate **e** \|z_acc\| ≥ 0.75 **e** aceleração e momentum rápido no MESMO sentido | ainda não significativo, mas acelerando de forma coerente |
| **Madura** (verde) | \|t\| ≥ t_gate **e** persistência ≥ 0.55 | tendência estatisticamente confirmada e disciplinada |
| **EXAUSTA** (vermelho) | \|t\| ≥ t_gate **e** curvatura contra ≤ −1.0 **e** aceleração contra ≤ −0.75 (sobrepõe Madura) | a tendência existe, mas está arredondando E freando — trecho final típico |

**De onde vêm os números:** t_gate/t_low são **calibrados** (simulação em
random walk, §4.10) — são os únicos com garantia estatística formal (~5% /
~20% de excedência no acaso puro). Os demais (persistência 0,55, aceleração
0,75, curvatura −1,0) são limiares de desenho em unidades interpretáveis
(fração de barras; sigmas da própria métrica) — razoáveis, mas não
otimizados; mexer neles muda a sensibilidade, não a validade.

**Como ler:** Madura é o estado "confiável"; Emergindo é aviso antecipado
(mais falso positivo, por construção); Exausta **não é sinal de reversão**
— é "não conte com esticada". A **idade** (nº de barras no estado) aparece
ao lado do nome: Madura 25 no H1 = 25 horas confirmada; Madura 2 = recém
qualificada.

---

## 6. Camada relacional — a checagem contra força espúria

Motivação (medida na pesquisa, H1/2 anos): o índice, por ser média da
cesta, acusa força com \|t\| ≥ gate em instantes onde **menos de 3 dos 7
pares confirmam** em ~64% dos casos ativos. A camada corrige isso olhando
os pares um a um.

- **Motor por par**: t NW + ER sobre o log-preço de cada um dos 28 pares,
  mesma janela efetiva e mesma disciplina anti-repaint do índice.
- **Breadth por moeda** (coluna `amp`): dos 7 pares da moeda, quantos têm t
  orientado a favor da direção do índice. **Hard** = com \|t\| ≥ pair_gate
  (confirmação estatística); **soft** = qualquer concordância de sinal.
- **⚠ força espúria**: índice ativo (\|t\| ≥ gate) com hard < 3/7. O M da
  moeda fica acinzentado. Tradução: *"a média diz tendência, os pares não
  sustentam — desconfie"*. Tipicamente 1–2 pares esticados distorcendo a
  cesta.
- **Estados do par (aba MTX)**: Madura / Emergindo-lite / Ruído. **Não
  existe Exausta por par** (exigiria z_win por par — limitação documentada).

---

## 7. Grade MTF

Cada um dos 6 TFs roda o motor completo **com a sua própria janela efetiva**
(v1.41) e mostra o estado atual (k=0) de cada moeda. O z-score se adapta ao
histórico disponível; sem dados suficientes a célula mostra `.`.

---

## 8. Guia de leitura de cada saída

### 8.1 As 8 linhas do gráfico (M por moeda)

- **Acima de 0** = moeda forte contra a cesta; abaixo = fraca. ±0.25
  (pontilhado) é o nível "movimento relevante".
- **Leque abrindo** (linhas se afastando) = mercado direcional; linhas
  trançadas perto de 0 = dia de range.
- **O par ideal** é o das duas pontas do leque: moeda mais alta contra a
  mais baixa — tendência dos dois lados.
- O valor na ponta (rótulo colorido) é o M atual; a barra em formação
  repete a última fechada (não é cálculo novo).

### 8.2 Painel — coluna a coluna (linhas ordenadas por M, maior→menor)

| Coluna | O que é | Como ler |
|---|---|---|
| `⚠` | força espúria | presente = índice ativo sem 3/7 de confirmação → **não confie no M desta linha** |
| Nome | moeda, na cor da linha | — |
| Barra | \|M\| relativo ao maior \|M\| do momento | comprimento = força relativa AGORA (escala se adapta) |
| `ESTADO (idade)` | célula colorida | verde velho = tendência estabelecida; amarelo = atenção; vermelho = não esticar; cinza = nada |
| `amp` | breadth `h/7 •s` | **h ≥ 5/7 = tendência ampla de verdade**; h ≥ 3/7 razoável; h < 3 com estado ativo = espúrio. O `•s` (soft) esmaecido mostra a concordância frouxa |
| `DIR` | ALTA/BAIXA | sinal do t |
| `M` | valor numérico | acinzentado quando espúrio |
| `t` | t Newey-West | a evidência crua; compare com o gate do rodapé/journal |
| `pers` | persistência | ≥ 0.55 sustenta Madura |
| setas | z da aceleração | ▲▲ ≥ 1.5σ, ▲ ≥ 0.5σ, `-`, ▼, ▼▼ — acelerando ou freando |
| grade MTF | 6 células | ver 8.3 |
| `alin` | alinhamento | `n/6▲` = n TFs (Emergindo+) na mesma direção |

**Leitura da linha inteira em um segundo:** *"EUR: Madura 18, 6/7, ALTA,
t 3.2, ▲"* = alta do EUR confirmada há 18 barras, quase toda a cesta junto,
ainda acelerando. *"USD: Madura 4 ⚠ 2/7"* = ignore, é artefato da média.

### 8.3 Grade MTF — células e cabeçalho

- **Célula** = fundo na cor do estado + seta de direção (▲/▼); `.` = TF sem
  histórico suficiente.
- **Cabeçalho com sufixo ᵈ/ᶜ/ˢ** (e cada camada mais apagada): `30ᵈ H1ᵈ`
  detectam o horizonte de 18 h; `H4ᶜ` contextualiza (~5 dias); `D1ˢ W1ˢ MNˢ`
  são regime estrutural.
- **Método**: primeiro os ᵈ — eles respondem "existe tendência NO horizonte
  que eu pedi?". Concordância M30+H1 na mesma direção = o dia tem dono.
  Depois ᶜ: o H4 confirma ou contradiz o pano de fundo semanal? Por último
  ˢ: a favor = vento de cauda; contra = você está operando contra o regime
  (válido, mas saiba disso).
- **`alin` alto (4-5/6)** só é comparável porque cada TF mede com a própria
  régua (v1.41); ainda assim, lembre que os ˢ respondem por outra pergunta.
- **Linha `lente:`** no rodapé, ex.
  `lente: 18h -> 30:36 H1:18 | ctx120h -> H4:30 | estr: D1 W1 MN` — é o
  mapa "quem enxerga o quê" da grade. O título mostra o w do motor do
  gráfico (ex.: `w=18ᵈ` num gráfico H1, `w=30ᶜ` num H4).

### 8.4 Aba MATRIZ (botão MTX)

Matriz 8×8: célula (linha A, coluna B) = estado do par orientado A vs B.
`M↑` = A em tendência madura de alta contra B; `E↓` = emergindo de baixa;
`·` = ruído; `?` = par sem dados; a linha é antissimétrica à coluna por
construção (verificado no init).

- **Uso principal: escolher o instrumento.** Achou a moeda líder no painel?
  Abra a MTX e olhe a LINHA dela: os `M↑` são os pares onde a tendência é
  estatisticamente confirmada NO PAR (não só na média).
- **Rodapé**: líder por breadth + decomposição de dominância, ex.
  `EUR↑ 6/7 | dom: JPY +85bp 42% · USD +51bp 25% · GBP +33bp 16%` — contra
  quem o movimento do líder se concentrou na janela (em basis points e % do
  total). Dominância concentrada num par só = movimento de UMA relação, não
  da moeda.

### 8.5 Botão FOCO

Alterna entre 8 moedas e destaque das 2 moedas do par do gráfico (as demais
esmaecem). Puramente visual.

### 8.6 Alertas (sempre em barra fechada, só em transição)

- `InpAlerts`: entrada em **Madura** ou **EXAUSTA** (com direção).
- `InpAlertBreadth`: breadth hard cruzou **≥ 6/7** — reconhecimento de
  tendência ampla EM CURSO. A pesquisa (a11/v2) testou continuação após
  esse reconhecimento: **nula**. Trate como "olhe o mercado", não "entre".

### 8.7 Journal (aba Experts) — diagnóstico

No attach, em modo HOURS: tabela de conversão TF→janela/gates, verificação
do `GateFor` (nós exatos + monotonicidade), lente da grade, tempo do
`ComputePairs` e do `Recalc` inicial, teste de antissimetria. Se a camada
relacional passar de 200 ms ela se **autodesliga** (aviso no painel e no
Journal). `"aguardando historico dos pares..."` = menos da metade dos 28
pares com histórico — espere o download ou confira o Market Watch.

### 8.8 Buffers para EA / iCustom (a interface programática)

| Buffers | Conteúdo | Faixa |
|---|---|---|
| 0–7 | M por moeda | −1..+1 (útil: −0.6..0.6) |
| 8–15 | estado | 0 Ruído, 1 Emergindo, 2 Madura, 3 Exausta |
| 16–23 | direção | +1 / −1 / 0 |
| 24–31 | breadth_hard × dir | −1..+1 (ex.: +0.857 = 6/7 confirmando alta) |
| 32–39 | breadth_soft × dir | −1..+1; EMPTY se camada relacional off |

Ordem das moedas em todos os blocos: **USD, EUR, GBP, JPY, CHF, CAD, AUD,
NZD** (buffer 0 = USD, 1 = EUR, …; 24 = hard do USD, 25 = hard do EUR…).

**Regras de consumo:**
1. **Sempre `shift ≥ 1`.** O shift 0 é cópia cosmética da última barra
   fechada — ler shift 0 como "valor da barra atual" é lookahead.
2. Só as últimas `InpBars` (300) barras são preenchidas; antes disso,
   `EMPTY_VALUE`.
3. A ordem posicional do iCustom no v1.41 tem **os 4 inputs de modo NA
   FRENTE**:

```mql5
iCustom(_Symbol, tf, "Cssm",
        0, 18.0, 120.0, false,            // modo: WM_BARS(0)/WM_HOURS(1), horizonte, contexto, autogates
        tf, 16, 64, 500, 300, 8,          // motor
        2.0, 1.0, 0.55, 0.75, -1.0, -0.75,// estados
        true, true, false, 12, 16, 9, false, // visual (não afeta buffers)
        true, 2.13, 1.28, false,          // relacional
        false);                           // MTF off (não afeta buffers)
```

(Chamadas posicionais antigas, escritas para o v1.40, ficam desalinhadas —
foi exatamente o bug corrigido no `Export_CSSM_Parity.mq5` v1.01.)

---

## 9. Método de leitura em 60 segundos (rotina sugerida)

1. **Lente** (rodapé): confirme o que cada coluna da grade enxerga — em
   qual camada está o TF do seu gráfico?
2. **Pontas do painel**: moeda do topo e do fundo. Estados? Idades?
3. **Valide com `amp` e ⚠**: topo com Madura + ≥5/7 e sem ⚠ = tendência
   real da moeda. Com ⚠ ou 2/7 = artefato, próxima.
4. **Grade**: os TFs ᵈ concordam entre si? O ᶜ está a favor? Os ˢ dizem em
   que regime você está remando.
5. **MTX**: na linha da moeda forte, escolha um par `M↑` — de preferência
   contra a moeda mais fraca do painel — e cheque a dominância no rodapé
   (movimento distribuído > concentrado).
6. **Releia o aviso**: tudo isso descreve o presente. A decisão de entrada,
   nível e risco vem do SEU método — o CSSM só diz onde o vento sopra e com
   que consistência estatística.

---

## 10. Armadilhas e limitações (honestas)

- **~5% de falso positivo é por construção**: o gate foi calibrado para
  isso. Em 8 moedas, espere estados ativos espúrios ocasionais — por isso a
  coluna `amp` existe; use-a sempre.
- **Exausta ≠ reversão**; e não existe Exausta na célula do par.
- **W1/MN são estruturais sempre** (a barra deles nunca cabe 16× em 18 h ou
  120 h) e no modo reduzido não têm o mesmo poder do motor completo — são
  pano de fundo.
- **z_win curto em janelas curtas** (H1 detecção usa z_win 150): os z de
  aceleração/curvatura ficam mais nervosos — as setas do painel piscam mais
  no H1 do que no D1. Normal.
- **Persistência entre estados dia a dia é nula** (a3): Madura hoje não
  aumenta a chance de Madura amanhã. A idade descreve o passado do estado,
  não sua expectativa de vida.
- **Barra em formação**: tudo que você vê no shift 0 é decoração; decisões
  e backtests, sempre com a barra fechada.
- **Trocar `InpHorizonHours` troca a pergunta** — 18 h responde "tendência
  do dia"; 60 h já é outra pesquisa. Os resultados nulos/validados do repo
  referem-se ao perfil 12–24 h.

---

*Documento gerado a partir do código em 2026-07-06 (v1.41, pós PR #6 e
verificação de paridade no MT5). Se o `Cssm.mq5` mudar, atualize este guia
no mesmo PR.*

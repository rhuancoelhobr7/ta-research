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

## 4. Os cálculos, um a um

Todos operam sobre a janela `w_mid` do índice sintético da moeda (barras
fechadas, da mais recente para trás).

**t Newey-West (`TStat`)** — o coração. É o t-statístico da média dos
retornos da janela, com erro-padrão Newey-West (kernel Bartlett, defasagem
3) para não ser enganado por autocorrelação. Leitura intuitiva: *"quantos
erros-padrão a deriva média está longe de zero"*. Num random walk puro,
\|t\| ≥ t_gate acontece só ~5% do tempo — o gate é uma régua de "isso
provavelmente não é ruído". (v1.20 substituiu o t de regressão sobre níveis,
que dava 84% de falsos positivos.)

**ER — Efficiency Ratio (`EffRatio`)** — `|deslocamento líquido| / soma dos
|passos|`, de 0 a 1. ER 0.30 = 30% do caminho percorrido virou deslocamento;
ER baixo = zigue-zague.

**Momentum normalizado (`VolMom`)** — deslocamento da janela dividido por
`sd·√w` (sd = desvio dos retornos). É um "z do movimento": +2 significa
deslocamento de 2 sigmas para a janela. Calculado em `w_fast` (rápido) e
`w_mid` (médio).

**Persistência (`Persist`)** — fração das barras da janela que fecharam na
direção do deslocamento líquido. 0.55 = 55% das barras a favor.

**Curvatura (`Convex`)** — coeficiente quadrático de um ajuste polinomial na
janela, normalizado pela vol. Positivo = trajetória acelerando para cima;
combinado com a direção, detecta o "arredondamento" de fim de movimento.

**Aceleração (`gAcc`)** — EMA (span 8) de `VolMom(w_fast) − VolMom(w_mid)`:
o momentum curto está ganhando ou perdendo do momentum médio?

**z-scores adaptativos** — curvatura e aceleração são divididas pelo próprio
desvio-padrão dos últimos `z_win` valores → escalas comparáveis entre moedas
e regimes. (São esses z que aparecem nas setas do painel.)

**M — a linha plotada** — `M = sinal(t) · min(|t|/2, 1) · ER`. Direção pelo
t, magnitude pela significância (satura em \|t\|=2) vezes a eficiência.
Faixa teórica −1..+1; a janela exibe −0.6..+0.6 com níveis em ±0.25.

---

## 5. A máquina de estados

Avaliada por moeda, a cada barra fechada (dir = sinal do t):

| Estado | Condição | Tradução |
|---|---|---|
| **Ruído** (cinza) | nenhuma das outras | sem evidência de tendência |
| **Emergindo** (amarelo) | t_low ≤ \|t\| < t_gate **e** \|z_acc\| ≥ 0.75 **e** aceleração e momentum rápido no MESMO sentido | ainda não significativo, mas acelerando de forma coerente |
| **Madura** (verde) | \|t\| ≥ t_gate **e** persistência ≥ 0.55 | tendência estatisticamente confirmada e disciplinada |
| **EXAUSTA** (vermelho) | \|t\| ≥ t_gate **e** curvatura contra ≤ −1.0 **e** aceleração contra ≤ −0.75 (sobrepõe Madura) | a tendência existe, mas está arredondando E freando — trecho final típico |

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

# Plano de Pesquisa — Tendência Absoluta Diária

*Estudo em duas fases: (A) medir a realidade — rotular, nos últimos 2 anos, os dias em que uma moeda entrou em "tendência absoluta" intraday; (B) engenharia reversa — descobrir o que o CSSM mostrava na abertura de Tokyo que teria permitido prever o dia. Com auditoria prioritária das 7 chamadas reais do especialista.*

---

## 1. O fenômeno e as duas perguntas

**Definição informal (do especialista):** tendência absoluta é quando uma moeda entra em tendência que se reflete no intraday de *todos* os seus pares — moeda na base sobe em todos, moeda na cotação cai em todos (ou o inverso). A decisão é tomada no início (ou pouco antes) da sessão de Tokyo, observando TFs do MN ao H1/M30, e vale para as ~12 horas seguintes. O veículo é um portfólio diário de 7 pares da moeda escolhida.

Isso gera duas perguntas empiricamente separáveis — e mantê-las separadas é a espinha dorsal do estudo:

**P-A (existência e anatomia):** com que frequência tendências absolutas realmente acontecem? Quantas por dia? Elas persistem (NZD em 17 e 19/06 sugere que sim)? Em qual sessão o movimento se concentra?

**P-B (previsibilidade):** o estado do mercado *na abertura de Tokyo* — medido pelo CSSM em MN→M30, só com barras fechadas — separa os dias/moedas que terão tendência absoluta dos que não terão?

A Fase A não usa o indicador em nada. Ela só mede o que aconteceu. Misturar as fases (ajustar a definição do fenômeno olhando o que o indicador consegue prever) é a forma mais sutil de fraude estatística deste estudo, e o plano a proíbe explicitamente (§7).

---

## 2. Definição operacional v1 (a ser congelada)

"Todos os pares sobem" precisa virar número. Para cada dia D e moeda C, na janela de avaliação W = [T0, T0+12h]:

**Retornos orientados:** para cada um dos 7 pares de C, o log-retorno na janela, com sinal orientado a C (base: +ret; cotação: −ret).

**Três métricas, três aspectos do fenômeno:**

| Métrica | O que mede | Critério v1 |
|---|---|---|
| `breadth` | fração dos 7 pares na direção de C | ≥ 6/7 |
| `z` | retorno do índice sintético de C na janela ÷ desvio-padrão dos retornos de janela dos últimos 63 dias (somente passado) | \|z\| ≥ 1,0 |
| `er` | Efficiency Ratio intraday do índice de C dentro da janela (M5) | ≥ 0,25 |

**Rótulo:** C está em tendência absoluta no dia D se as três condições valem simultaneamente; direção = sinal de z; intensidade = `score = |z| × breadth × er`. **Mais de uma moeda pode ser rotulada por dia** (e frequentemente será, por acoplamento mecânico: se o CHF dispara, a moeda mais fraca do dia tende a rotular no sentido oposto — o ranking por score ordena as protagonistas).

Por que três métricas e não uma: breadth sozinho rotula dias de deriva mínima porém unânime; z sozinho rotula um único salto de notícia sem amplitude entre pares; er garante que foi *tendência* (caminho eficiente), não um choque com devolução. A tríade é a tradução direta de "entrou em tendência refletida em todos os pares".

**Calibração e congelamento:** os limiares v1 acima são o ponto de partida. A Fase A reporta uma grade de sensibilidade (breadth ∈ {5,6,7}/7, z ∈ {0,8, 1,0, 1,5}, er ∈ {0,15, 0,25, 0,35}) e a taxa-base resultante de cada combinação. A escolha final é feita por **dois critérios apenas**: reproduzir as 7 chamadas do especialista (âncoras) e produzir uma taxa-base coerente com "praticamente todo dia acontece" (~0,8–2 moedas/dia). Depois da auditoria (§4), a definição é **congelada como v1** em arquivo de metadados; qualquer mudança posterior cria uma v2 e reinicia a Fase B do zero.

---

## 3. Dados, tempo e a armadilha do aquecimento

**Duas exportações, não uma:**

| Conjunto | TF | Histórico | Para quê |
|---|---|---|---|
| Intraday | M5 | 2 anos (até os dias mais recentes) | rotulagem (Fase A) + features M30/H1/H4 |
| Macro | D1 | 4 anos | features D1 (modo completo) e W1 (modo reduzido) |

O motivo é aritmético: o z-score adaptativo precisa de centenas de barras de *aquecimento* antes do primeiro dia analisado — e essa é a única função dos dados com mais de 2 anos: normalização estatística, nunca rótulo, treino ou avaliação (que ficam estritamente nos últimos 2 anos). Para minimizar histórico, cada TF opera no modo que sua disponibilidade permite:

| TF | Modo | O que entrega | Histórico mínimo p/ cobrir 2 anos |
|---|---|---|---|
| M30, H1, H4 | completo | todas as features + estados 0-3 | ~2,1 anos de M5 ✓ |
| D1 | completo (z_win reduzido, mín. 150) | idem | ~2,8 anos de D1 ✓ (4a exportados) |
| W1 | **reduzido** | t, ER, M, persist, direção; sem acc_z/conv_z; estados restritos a Ruído/Madura | ~3,6 anos ✓ (4a exportados) |
| MN | **omitido** | — (exigiria 9-20 anos) | o W1 assume o papel de macro-teto |

O modo reduzido não é uma grande perda no papel macro: o que a cascata pede do topo é *direção e peso* (t, M, persist) — exatamente o que sobrevive sem z-features. O que se perde é a detecção formal de Exausta no W1; a fase B1 pode aproximá-la pelo par (t alto, M em queda vs. barras anteriores). O MN omitido segue a prática do próprio grid MTF do MQ5, que exibe "." quando falta histórico.

**T0 e fuso — a decisão mais delicada do estudo.** "Início da sessão de Tokyo" precisa virar um timestamp no fuso do servidor da corretora (tipicamente GMT+2/+3, onde a meia-noite do servidor ≈ 17h NY ≈ pré-Tokyo). Default: T0 = 00:00 do servidor (um pouco antes de Tokyo, como o especialista opera), janela de 12h — ambos configuráveis e gravados nos metadados dos rótulos. Erro de fuso aqui desloca a janela inteira e invalida tudo, então a fase 0 inclui uma verificação manual: conferir 2–3 dias conhecidos contra o gráfico do MT5.

**Regra de ouro da Fase B:** toda feature em T0 usa exclusivamente barras **fechadas antes de T0**. Na prática: o D1 disponível é o de ontem; o H4 é o último fechado antes de T0; alinhamento por `merge_asof` backward. Um teste automatizado desloca o futuro e verifica que as features de T0 não mudam.

---

## 4. Fase A — Rotulagem e auditoria das 7 chamadas

**Passo A1 — rotular** os ~500 dias úteis × 8 moedas com a definição v1 (script `a1_label_days.py`, já implementado e testado sinteticamente). Saída: tabela dia × moeda com breadth, z, er, score, rótulo e direção.

**Passo A2 — auditar as chamadas do especialista** (prioridade declarada do estudo). Para cada uma das 7 datas:

| Data | Chamada |
|---|---|
| 2026-06-15 | CHF ALTA |
| 2026-06-16 | EUR ALTA |
| 2026-06-17 | NZD BAIXA |
| 2026-06-18 | GBP BAIXA |
| 2026-06-19 | NZD BAIXA |
| 2026-06-22 | GBP ALTA |
| 2026-07-03 | NZD ALTA |

...responder três perguntas em ordem: (1) o dia foi rotulável — a moeda chamada de fato teve tendência absoluta medida? (2) a direção bate? (3) a moeda chamada era a de **maior score do dia**, ou havia outra mais óbvia? A distinção importa: acertar a direção de uma moeda que rotulou com score fraco é diferente de cravar a protagonista do dia. O relatório da auditoria também registra, com honestidade, o que 7 exemplos podem e não podem provar: confirmam ou refutam as chamadas individuais, mas não sustentam nem refutam "praticamente 100%" — para isso serviria só a Fase B em 2 anos de dados.

**Passo A3 — anatomia do fenômeno** (estatística descritiva que já vale o estudo): taxa-base de dias com ≥1 rótulo; distribuição de moedas por dia; matriz de persistência dia-a-dia (rótulo de ontem prevê o de hoje? — o par NZD 17→19/06 sugere investigar); decomposição por sessão (o retorno da janela se concentra em Tokyo, Londres ou NY? — se Londres domina, o "dia" do especialista é na prática uma aposta na sessão de Londres armada em Tokyo); e ranking de moedas mais frequentemente protagonistas.

---

## 5. Fase B — Engenharia reversa em T0

Com rótulos congelados, monta-se a matriz: para cada (dia, moeda), as features do CSSM em T0 — state, dir, M, t, pers, acc_z, conv_z em M30, H1, H4, D1, W1 (e MN se viável) — e o alvo (rotulou? direção?). Quatro abordagens, da mais interpretável à mais potente:

**B1 — Contraste descritivo.** Distribuição das features em T0 nos dias-rotulados vs. não-rotulados. Pergunta-chave: como estava a *grade* (o retrato MTF) da moeda na madrugada dos dias em que ela protagonizou? Existe uma assinatura visual? Esta análise é o coração da "engenharia reversa" — é literalmente reconstruir o que o especialista via.

**B2 — Regras candidatas.** Testar como classificadores: os cenários A/B/C do Protocolo avaliados em T0; a regra ingênua "moeda de maior |M| no H4"; contagem de alinhamento entre TFs; combinações estado-D1 × estado-H4. Cada regra vira uma previsão diária (moeda + direção) avaliada por acurácia top-1 e precision@2.

**B3 — Baselines obrigatórios** (as réguas de honestidade): (i) continuação — "a direção do D1 de ontem continua hoje"; (ii) persistência — "o rótulo de ontem repete hoje"; (iii) aleatório pareado. Qualquer regra do B2 que não bater os três baselines é descartada por mais elegante que seja. Suspeita a registrar: a persistência (ii) pode ser um baseline surpreendentemente forte — se for, parte do "edge" do especialista pode ser simplesmente surfar sequências.

**B4 — Teto com ML honesto.** Regressão logística e gradient boosting raso sobre as features contínuas, validação cruzada purgada com gap de 5 dias, prevendo (rotula?, direção). Não para operar: para saber quanto sinal *existe* na matriz. Se o ML fica em AUC ~0,5, as regras discretas não têm onde achar sinal, e a conclusão — "a tendência absoluta existe mas não é prevista pelo estado do CSSM em T0" — fecha o estudo com uma resposta sólida e valiosa: o edge do especialista, se real, vem de informação fora do indicador (calendário, fluxo, preço).

---

## 6. Fase C — O portfólio de 7 pares

Tradução final para o veículo real do especialista: todo dia, a regra vencedora escolhe moeda + direção em T0; monta-se o portfólio de 7 pares igualmente ponderados (base a favor, cotação contra); segura-se por 12h; desconta-se spread típico por par (tabela em bps, configurável). Métricas: retorno líquido por dia, taxa de dias vencedores, curva de capital, drawdown máximo, e comparação contra os baselines do B3 operados da mesma forma. Um detalhe que o portfólio de 7 pares embute e o relatório deve explicitar: ele é uma aposta *pura* na moeda (as outras 7 moedas aparecem uma vez cada, se anulando parcialmente) — é exatamente o índice sintético tornado negociável, com 7 spreads de custo.

---

## 7. Regras anti-autoengano (específicas deste estudo)

Além do arsenal herdado do estudo anterior (split temporal, holdout intocável, bootstrap em blocos, reality check por permutação, mínimo de eventos), três regras novas nascem dos riscos específicos daqui:

**Congelamento da definição.** A definição v1 é fixada ao fim da Fase A, *antes* de qualquer contato com features do indicador. O arquivo de metadados dos rótulos registra versão, limiares e data de congelamento. Se a Fase B sugerir que "com outra definição funcionaria melhor" — isso é uma hipótese v2, que exige re-rodar tudo e ser reportada como segunda tentativa (com o desconto de credibilidade que segundas tentativas merecem).

**As 7 chamadas são âncoras de auditoria, nunca de treino.** Elas validam a definição na Fase A; na Fase B, os 7 dias entram no conjunto como dias comuns, sem peso especial — e o relatório final mostra, separadamente, o que a regra vencedora teria previsto em cada um deles.

**Split por dias, holdout = últimos ~20% dos dias** (~100 dias úteis, incluindo os mais recentes — que contêm 6 das 7 chamadas do especialista; conveniente: o teste final e a auditoria das chamadas se encontram no mesmo trecho de dados nunca usado para desenvolver nada).

---

## 8. Ideias novas inferidas

**Calendário como confundidor e como feature.** Dias de tendência absoluta provavelmente se concentram em dias de evento (decisão de BC, CPI, payroll). Sem um calendário econômico histórico, um proxy barato: volatilidade realizada da primeira hora pós-T0 e dia-da-semana como covariáveis. Se os rótulos se concentram em quintas de BC, o "método" pode ser, em parte, um calendário — descobrir isso é resultado, não constrangimento.

**Assimetria de moedas.** Hipótese: moedas de menor liquidez (NZD aparece 3× em 7 chamadas) rotulam mais — menos fluxo para absorver um tema. O ranking de protagonistas da Fase A testa isso de graça.

**O especialista como processo, não como oráculo.** Se a Fase B achar uma regra com acurácia top-1 de, digamos, 45% (vs ~6% do acaso com 16 opções moeda×direção), isso já reconstruiria um processo *operável* — mesmo longe de 100%. O critério de sucesso do estudo é bater baselines com folga estatística, não igualar a narrativa.

---

## 9. Ordem de execução

| Etapa | Script | Critério para avançar |
|---|---|---|
| 0. Exportar M5 (2a) + D1 (4a) | s0 | ≥ 26 pares; fuso verificado manualmente |
| A1. Rotular | a1 (pronto) | rótulos + grade de sensibilidade gerados |
| A2. Auditoria das 7 chamadas | a2 (pronto) | definição congelada v1 |
| A3. Anatomia | a3 | relatório descritivo |
| B. Features T0 + regras + ML | a4, a5 | sobreviventes de baseline+reality check |
| C. Portfólio | a6 | resultado líquido |
| Final. Holdout | a7 | UMA execução, sob ordem explícita |

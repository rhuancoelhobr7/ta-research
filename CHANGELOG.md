# Histórico de decisões e resultados

Registro cronológico das decisões metodológicas — o "porquê" que o código não
conta. Toda IA (ou humano) trabalhando neste repositório deve ler isto antes
de propor mudanças: várias escolhas abaixo são IRREVERSÍVEIS por regra
(CLAUDE.md, "Regras duras").

## 2026-07-10 — a29: curva de detecção da moeda líder (a pergunta central)

Acurácia de detecção da líder do dia x tempo desde a abertura, por indicador
(CSS/CSSM/site-pct) x TF (M5/M15/H1/H4) x régua (A exata / B top-3). Verdade =
líder por preço no fechamento. Indicadores recomputados dos M5 (3 anos, 237 dias
de teste OOS). MÉTODO v1: barras fechadas (cada TF atualiza no fechamento da sua
barra — capta o trade-off rápido/lento; forming-bar = refinamento v2). Custo do
atraso (fração do range do dia já feito) sobreposto. BH 5% sobre as 96 células.

- **Q10 (30 min de Tóquio)**: detecção no ACASO em todos os indicadores/TFs
  (top-3 ~0.38 = acaso; régua A ~0.13 = acaso). A intuição dos "30 min" não se
  sustenta.
- **Custo do atraso é baixo**: range do dia sobe devagar — 18% aos 30 min, 40%
  às 4h, 53% às 8h. Sobra movimento mesmo detectando tarde.
- **Régua A (líder exata): NULA** — nunca utilizável (~0.30 máx às 8h).
- **Régua B (top-3): sinal real, precoce e MODESTO** — trade-off ordenado
  confirmado: **M5 bate o acaso (BH, OOS) aos 90 min** (acc 0.48 vs 0.375, só
  26% do range feito), M15 aos 180 min, H1 aos 360 min, **H4 nunca**. Fortalece
  a ~0.6 às 4-6h. 29/96 células sobrevivem a BH.
- **Veredito**: não dá pra cravar a líder cedo, mas dá pra ESTREITAR para 3
  candidatas já aos 90 min (M5) com 74% do movimento por vir — melhor que o nulo
  pré-abertura do a24, coerente com o a31 (43% do campeão visível na asia). Edge
  pequeno: badge probabilístico com latência conhecida, nunca sinal de T0.

## 2026-07-10 — a31: o par campeão dentro da moeda preponderante

Dada a moeda LÍDER do dia (preponderante.py), qual dos 7 pares anda mais?
Campeão ABS = maior range em pips; REL = maior range/ATR (controla largura
estrutural). 3116 dias. (Corrigido bug: a lista de pares do líder usava
combinações em ordem G8 — "USDEUR" — em vez dos símbolos reais do broker;
enviesava p/ EUR/GBP. Agora usa as colunas reais.)

- **Q15**: campeão claro (>=1.3x o 2º) em só 37% dos dias; concentra mediana 23%
  do range dos 7 — movimento é distribuído na maioria dos dias.
- **Q16**: o campeão anda **+63 pips / +0.67 ATR** a mais que a média dos outros
  6 (p90 +142 pips / +1.26 ATR). Resposta direta do Carlos.
- **Q17**: par campeão por líder é concentrado mas não fixo (top-share 17-31%):
  USD->USDJPY 31%, JPY->USDJPY 30%, EUR->EURCHF 28%, CHF->CHFJPY 26%,
  AUD->AUDNZD 23% — vários apontam p/ JPY (a anti-líder frequente do a28).
- **Q18 (forte)**: o campeão REL é **líder×anti-líder em 55%** (baseline 1/7 =
  14%); ABS 36%. A anti-líder resolve boa parte da seleção do par. CAVEAT: há
  componente MECÂNICO — o par líder×anti-líder tem o maior diferencial de força,
  logo tende ao maior movimento por construção; mas 55% (não 100%) e o controle
  por ATR (REL) tornam a associação real e não trivial.
- **Q19**: campeão do dia já é o campeão da sessão asia em **43%** (base 14%) —
  parcialmente identificável cedo (a29 vai refinar com M5).

Ressalva operacional: líder e anti-líder são conhecidas no FECHAMENTO
(retrospecto); usar isto p/ seleção exige identificá-las cedo — o que o a29 mede.

## 2026-07-10 — a32: matriz completa de autocorrelação de range entre sessões

Fecha o a23 (que só olhou Tóquio->Londres->NY). Sequência asia->londres->ny->
asia(dia+1); matriz 3x3 "de sessão X p/ a próxima Y" (inclui wrap NY->Tóquio
d+1). Spearman por par, out-of-sample (30% finais), IC bootstrap em blocos.

- **Q20/Q21**: TODAS as 9 células positivas e significativas (0.26-0.34, IC não
  cruza 0) — a volatilidade gruda em QUALQUER transição, não só Tóquio->Londres.
  Adjacentes mais fortes: asia->londres 0.341, londres->ny 0.337 (iguais).
- **Q22**: NY->Tóquio(d+1) Spearman **0.273** IC [0.247, 0.301] = **7.4%** da
  variância de rank compartilhada — a vol de NY VAZA para a abertura asiática
  seguinte (efeito real, porém menor que o adjacente intradia).
- **Q23 (não-monotônico)**: dist1=0.337 > dist3=0.281 > dist2=0.265. O salto no
  dist3 (mesma sessão no dia seguinte, ex. asia->asia 0.311) acima do dist2
  revela SAZONALIDADE de sessão — a sessão correlaciona com ela mesma no dia
  seguinte mais que com a sessão 2 slots à frente.

Consolida o achado transversal da bateria: RANGE/volatilidade tem memória forte
e pervasiva (a23/a32); DIREÇÃO/liderança não (a28 Q3/Q4).

## 2026-07-10 — Bateria a28-a32: definições compartilhadas + a28

Nova bateria (spec `a28_a32_ESPEC.md`): a moeda preponderante (a dos ~88%),
curva de detecção, volume, par campeão e a matriz completa de sessões. Constrói
sobre a infra do a22-a26 (mergeada no main via PR #17). M5 exportado à parte
(InpM5Years) p/ a29/a30.

- **`preponderante.py`** (definições compartilhadas, por PREÇO, não pelo
  indicador): `currency_strength` — perfil das 8 moedas a partir dos net-moves
  dos 28 pares (dirmove = ±net/ATR conforme base/cotada); `leaders` —
  líder(mais forte)/anti-líder(mais fraca)/preponderante; `regua_acerto` — A
  (líder exata) vs B (top-2/3). Testado.
- **a28 (comportamento por sessão)**: 3116 dias, janelas asia/londres/ny + dia.
  - **Q1**: consistência direcional sozinha é quase universal (líder bate >=6/7
    em 98% dos dias, 7/7 em 85%) — o "~88%" da tese só aparece com MAGNITUDE
    (7/7 E forca>=0.5 ATR = 62%). Direção sozinha não seleciona dia; magnitude sim.
  - **Q2**: lidera por força 50% / fraqueza 50%; viés por moeda confirma o
    folclore — **JPY** anti-líder 61%, CHF 56% (lideram por FRAQUEZA); AUD 43%,
    GBP 44% (por FORÇA).
  - **Q3**: continuidade de liderança entre sessões ~13.5% (acaso 12.5%) —
    Londres/NY criam líder novo ~86% dos dias. A liderança DIRECIONAL não gruda
    (contraste com o a23: RANGE gruda, direção não).
  - **Q4**: líder do dia = líder de ontem em 14% (~acaso). Meia-vida curta.
  - **Q5 (forte)**: força da líder cresce monotônica com a consistência —
    4/7=0.24, 5/7=0.29, 6/7=0.46, **7/7=0.74** (~3x). O 7/7 limpo é um dia
    materialmente maior: "quão preponderante" importa muito.

## 2026-07-09 — a26: anatomia dos dias valiosos vs mortos (fecha a agenda)

Nível de moeda. Atividade = média do range normalizado dos 7 pares da moeda;
líder = mais ativa. "Dia com destaque" = líder ≥1.5× a norma = **39%** dos dias
(sensível ao threshold; o "~88%" da spec era a métrica de tendência absoluta do
projeto CSSM, não de range). Estado CSS de manhã (pré-Tokyo 00:00 UTC, sem
lookahead).

- **Q11**: a líder do dia é identificável de manhã? Acerto pela moeda mais
  extrema no CSS de manhã **18.1%** (acaso 12.5%); pela líder de ontem 21.1%.
  → a líder NÃO é antecipável — confirma o a24.
- **Q12**: dias mortos têm assinatura? Dispersão do ranking CSS de manhã
  destaque 19.0 vs morto 18.1 — diferença ínfima; sem sinal prévio claro de
  "ficar de fora".
- **Q13**: persistência de liderança 18.6% (acaso 12.5%) — marginal, ~nula
  (coerente com a persistência-dia-a-dia nula já achada no projeto irmão).

Síntese: o dia/moeda valioso não é previsível pelo estado CSS de manhã. Fecha a
agenda a22-a26 de forma coerente: seleção por range = ATR de sessão (a25); CSS
só tem dimensão concorrente (a26b), nunca preditiva. a26 não introduz primitiva
estatística nova (composição de idxmax/std/shift + funções já testadas).

## 2026-07-09 — a26b: CSS como confirmação concorrente — PERSISTE (não nulo)

Última chance do CSS, na dimensão NÃO-preditiva: dado alinhamento ativo em T
(|pct_base−pct_quote|≥70 em M15 E H1, ao vivo), o movimento em curso continua?
Estado em T como gatilho concorrente, mede o futuro (distinto de a22-a25). M15
proxy do M5 pedido pela spec. 23.384 eventos alinhados vs controle.

- **Q14 duração**: mediana 4 barras M15 (~60 min) até devolver ≥30% do pico.
- **MFE**: alinhado 16.8 pips vs controle 11.6 → **1.45×**.
- **Q16 persistência (o achado limpo)**: residual mediano entrando em T+0=12.8,
  T+1=11.5, T+2=10.0 pips — entrar 1-2 barras depois ainda captura 90%/78%. O
  movimento PERSISTE; entrar "no meio" funciona.
- **Q15 degradação**: pct da moeda forte 90 (T+0) → 70 (T+15), gradual — janela
  de oportunidade moderadamente ampla.
- **CAVEAT (registrado no REPORT)**: controle NÃO é vol-pareado; parte da razão
  1.45× é clustering de volatilidade (a23, já no ATR), não valor único do CSS. O
  achado sólido é a PERSISTÊNCIA. Isolar o incremento do CSS exige controle
  pareado por volatilidade recente (follow-up).

**Contraste central da agenda**: o CSS FALHA como preditor de seleção (a24) mas
o movimento sob alinhamento PERSISTE como fenômeno concorrente (a26b) — coerente
com o processo real do trader (confirmar, não prever) e com a âncora (CSS
atrasado). Não muda o produto a25 (seleção = ATR); no máximo o CSS vira leitura
de confirmação/timing marcada como concorrente, nunca sinal preditivo.

## 2026-07-09 — a25: ranqueador de par operável (CSS-free) — o produto

Ranqueador final com o que sobreviveu ao a24 (CSS excluído): modelo logístico
interpretável em log(base_atr) [largura estrutural] + asia_norm [atividade de
hoje vs a norma do par]. Alvo: top-quartil de range da janela pós-abertura entre
os 28 pares. Split 70/30, backtest no teste (775 dias).

- **Q8**: coef log_atr **1.52** (domina); coef asia_norm **0.006** (~zero). Para
  SELEÇÃO cross-section de par, a largura estrutural é praticamente o único sinal
  — o Tokyo→Londres do a23 (real no tempo) é redundante com o ATR aqui.
- **Q9**: top-1 do modelo **77.7 pips ≈ sempre-o-mais-volátil 77.5** (ATR puro),
  **1.81× o aleatório (43)**, ~80% do teto do dia (97.7). O modelo não supera só
  ranquear por ATR-sessão — honesto: o produto É "opere o par de maior ATR de
  sessão".
- **Q10**: top-1 igual ao dia anterior **84%**; só **8 pares** já foram top-1 —
  ranqueador estável, baixo custo de troca de instrumento.

Deliverable diz explícito: ranqueia por MOVIMENTO ESPERADO, não lucro. Produto =
ATR-de-sessão; CSS e até o tilt de Tokyo ficam de fora por não agregarem.

## 2026-07-09 — a24: CSS como preditor de range — NULO (regra de parada)

Teste do CSS focado no PROCESSO REAL do trader (P8 alinhamento percentil, P9
limpo×conflitado, P10 breadth), medido na virada de NY (13:00 UTC, barra
fechada anterior — merge_asof backward EXCLUSIVO, sem lookahead). Split 70/30,
teste out-of-sample, bootstrap semanal, controle negativo (P8 embaralhado entre
pares no dia). Dois enquadramentos:

- **(A) ABSOLUTO** (pergunta do trader — qual par move mais): ranquear 28 pares
  por range pós-abertura [13,17) UTC.
  - **base_atr: top3=71 pips, lift 1.65, Spearman 0.79** — baseline FORTE.
  - base_asia (a23): top3=69, lift 1.59, Spearman 0.63.
  - **P8_mag: top3=47, lift 1.08, Spearman 0.05** — colado no controle
    (P8_shuf: 44, 1.01, 0.005). P8/P8_intra/P8_long/P10 todos ~=controle.
  - **stack_atr_P8: 64 < base_atr 71** — juntar CSS ao ATR PIORA (dilui).
  → O CSS NÃO ajuda a escolher o par de maior amplitude além da largura
    estrutural (que o ATR já captura). Nulo econômico.
- **(B) RELATIVO** (o CSS tem QUALQUER informação? alvo = range/ATR-próprio):
  - **P8_mag: lift 1.032, Spearman 0.035** vs controle 1.002/−0.002 — um
    SUSSURRO de sinal acima do embaralhado (P8_intra 1.027/0.036 > P8_long
    1.010/0.027, coerente com "impulso de curto prazo" da spec). P10 lift 0.996
    (=controle, nulo — breadth é redundante com o rank no CSS agregado).
  → O CSS carrega informação minúscula sobre o par exceder a PRÓPRIA norma,
    economicamente irrelevante e muito abaixo do baseline do a23.
- **P9**: traj limpo 0.454 vs conflitado 0.441 — diferença ínfima (0.013), na
  direção prevista mas sem sustentação prática.

**VEREDITO (regra de parada da spec confirmada)**: para escolher par por
movimento, use ATR de sessão + o efeito Tokyo→Londres (a22/a23); **o CSS não
agrega** — nem no processo real do trader (P8/P9/P10). Consistente com o achado
da âncora (CSS concorrente/atrasado, não preditivo). Nada do CSS entra no
indicador como sinal de seleção de par. O valor eventual do CSS fica p/ o a26b
(confirmação concorrente, dimensão não-preditiva) — não p/ a24/a25.

## 2026-07-09 — Agenda a22-a26: export M15, ingestão e TAREFA 0

Início da agenda de movimento/volatilidade (a22–a26 — escolher o PAR com maior
amplitude esperada na janela, NÃO prever direção). Especificação pré-registrada
em `a22_a26_ESPEC.md` (fornecida pelo dono).

- **TAREFA -1 (`export_ta.mq5`)**: script MQL5 novo (o caminho Python `s3` já
  existia, mas a spec pede export via tela p/ forçar histórico M15 profundo).
  Rodado 1× pelo dono. Broker **Evalanch Ltd. / TenTrade-Server**. Exportou
  **28/28 pares G8 em M15, ~248k barras (~10 anos, 2016-07→2026-07), 0 fallback
  H1**. Campos OHLC+tick_volume+spread; `broker_info.csv` long-format com
  offset servidor↔GMT e point/tick_size/digits por par.
- **Ingestão (`s4_ingest_ta.py`)** → `data/raw/M15_{SYMBOL}.parquet` (tempo de
  SERVIDOR naive, p/ casar com a paridade MQ5 e a19/a20) + `_meta_ta.json`.
  pip = point×10 (JPY 0.01, resto 0.0001). Integridade: 0 NaN/dup/desordem.
- **DST (atenção p/ a22)**: o offset servidor↔UTC NÃO é constante — UTC+2
  inverno / UTC+3 verão (DST dos EUA, já documentado na Fase 0). `broker_info`
  capturou só o instante atual (verão, 10799s≈+3h). Conversão sessão↔UTC no a22
  deve ser DST-aware; "meia-noite servidor = 17:00 NY" é estável nos dois lados.
- **TAREFA 0 (`t0_normalize.py`)**: `val` bruto + percentil rolante CAUSAL
  (janelas 100/200/500, POR TF, sem lookahead) → `pct` 0-100, recriando a escala
  do site currencystrengthzone. **Dois motores em paralelo** (decisão do dono):
  `screen` (css_screen v2.20 — o CSS da tela, o PRODUTO) e `cssm` (cssm_engine —
  comparação/ablação no a24). TFs M15/H1/H4/D1/W1/MN reamostrados de M15.
  Saída em `data/derived/css_{engine}_{tf}.parquet`.
- **Validação de paridade**: css_screen H1 (reamostrado de M15) vs
  `css_parity_H1.csv` congelado → **max|dif|=5e-9** (exato). Pipeline fiel.
- **Limitação MN**: 10 anos = 121 barras mensais; pct com janela ≥100 é
  quase inútil no MN (e marginal no W1). O alinhamento P8 nos TFs longos terá
  que usar o `val`/sinal, não o pct rolante — a decidir no a24.
- **Achado do caso-âncora (GBP/JPY 08/07)** — o mais importante: o par teve
  132 pips range / +101 net (dia limpo, traj 0.77), mas o CSS é
  **CONCORRENTE/ATRASADO, não preditivo**. Na virada de NY (~12:00 UTC) o
  css_screen de curto prazo mostrava **GBP FRACO** (H1 pct 5.5), com divergência
  D1(forte)↔H1(fraco); GBP só "acende" (pct 76→93) das 17→20 UTC, DEPOIS do
  movimento. Confirma a distinção central da agenda: a âncora é confirmação em
  andamento (a26b), não setup preditivo (a24). Sugere que P8 pré-abertura terá
  poder preditivo fraco — o nulo que a agenda foi feita p/ detectar. O "GBP=100
  em todos os TFs" da spec é a escala do SITE (≠ nosso pct rolante) e ocorreu
  pós-movimento, não na abertura.

## 2026-07-09 — a23: inter-sessão (o OURO — resultado POSITIVO)

Autocorrelação de volatilidade entre sessões, com partição ORDENADA sem
sobreposição (`SEQ_SESSIONS`: asia[00-07)/londres[07-13)/ny[13-21) UTC — asia
fecha antes de londres abrir, sem lookahead). Split 70/30, métricas no TESTE,
thresholds do treino, bootstrap semanal, BH na família Q4. `sessions.py`
parametrizado por `windows` (SESSIONS descritivo × SEQ_SESSIONS preditivo).

- **Q4 (o ouro)**: asia→londres Spearman mediana **0.342** (IC95 [0.316, 0.367]),
  **acima** do baseline de persistência londres-ontem→hoje (**0.267**), com
  **28/28 pares significativos após BH**, out-of-sample. Volatilidade tem
  memória inter-sessão e o efeito Tokyo→Londres é real e robusto.
- **Matriz de transição** (teste): asia_Q1→63% londres_Q1 (calma persiste);
  asia_Q4→38% londres_Q4 (vol persiste). Diagonal pesada e monotônica.
- **Q5**: overlap Londres∩NY captura **~49% do range diário em 3h** (ny 63%,
  londres 59%, asia 45% — não somam 1, são max-min de subconjuntos aninhados).
- **Q6**: "mola comprimida" **REFUTADA** — londres cresce monotônico com o
  quartil de asia (Q1 0.70 → Q4 1.03); asia apertada prevê londres abaixo da
  mediana (a calma continua), não expansão.
- **Q7**: fator asia da moeda NÃO agrega sobre o range asia do próprio par
  (r_fator 0.19-0.43 < r_próprio 0.40-0.64) — null p/ lead-lag entre moedas.

**Consequência p/ a regra de parada (spec)**: já existe um ranqueador de range
utilizável SEM CSS (ATR/range de sessão + Tokyo→Londres). O a24 (CSS) agora tem
um baseline ALTO a bater; combinado com o achado da âncora (CSS concorrente, não
preditivo), a expectativa é que P8 pré-abertura adicione pouco — a testar.

## 2026-07-09 — a22: mapa descritivo de sessões

`sessions.py` (framework reutilizável a22–a26): conversão servidor→UTC
**DST-aware** (servidor = ET+7h; offset +3 verão/+2 inverno resolvido via
US/Eastern), sessões em janela UTC fixa (tokyo 00-09, londres 07-16, ny 12-21,
overlap 13-16). Limitação v1: sem bucket pré-Tokyo/Sydney (~21-00 UTC).
`a22_sessoes.py` sobre 28 pares × ~10 anos (290k linhas par×sessão×dia).

- **Q1 (intensidade = pips/HORA, não total)**: correção importante — overlap tem
  3h vs 9h das outras; comparar total confundiria com duração. Ranking:
  **overlap 11.9 pips/h (1.85× a mediana do par) >> londres 6.2 > ny 5.5 >
  tokyo 4.6**. Overlap Londres∩NY é disparado a janela mais intensa (premissa da
  Q5/a23 confirmada). Estabilidade 1ª×2ª metade (Spearman par×sessão): 0.868.
- **Q2 (absoluto)**: crosses de **GBP dominam TODAS as sessões** em pips
  (GBPNZD/GBPJPY/GBPAUD no topo até no Tokyo) — **refuta o folclore** "JPY-cross
  domina Tokyo" no sentido absoluto.
- **Q2b (relativo)**: mas no share de intensidade Tok/Ldn/NY, AUD/NZD/JPY-crosses
  puxam p/ Tokyo (share ~0.31-0.35; AUDNZD/AUDJPY/NZDJPY no topo) e CAD/USD/EUR
  puxam p/ Londres/NY (~0.22-0.25). Folclore confirmado no sentido RELATIVO.
- **Q3**: overlap sobe de seg (1.64) p/ sex (1.95); segunda é a mais fraca.
  Notícias HIGH (calendário 2024-07→) dão lift modesto de range (ny +14%,
  londres/overlap +10%) — coerente, sem ser dramático.

Nenhuma decisão de trade — é o eixo descritivo p/ a23 (inter-sessão) e o
baseline que o CSS terá que bater no a24.

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

## 2026-07-06 — a13 executado: **RESULTADO NULO** (results/*_a13)

Três execuções (usd7 15h primária; all28 15h e usd7 12h sensibilidades),
395 dias research, holdout intocado:

- Nenhuma regra sobrevive. Os dois quase-positivos morrem no reality
  check: RB usd7 50.9% e RA all28 53.9% batem os baselines mas ficam
  ABAIXO do p95 permutado (57.7% / 56.5%) — com 3 regras testadas contra
  alvo binário, máximos dessa ordem saem de graça do acaso.
- RC (amparo-D1) dispara em só 51-59 dias (n<100 = amostra insuficiente
  por regra dura 6) e ainda assim fica abaixo de 50%.
- ML teto sobre as 35 features de peso: AUC 0.500-0.520 — sem sinal.
- Conclusão: a formulação "variação de intensidade + veto hierárquico +
  janela Tokyo→NY declarada pelo especialista" TAMBÉM é nula. Com a5
  (estado), a12 (posição/geometria) e a13 (derivada/peso), as leituras
  1ª ordem, 2ª ordem e a janela operacional dele estão todas testadas e
  nulas. Próximo passo racional: a auditoria prospectiva acima — medir o
  hit rate REAL das chamadas antes de reverter mais qualquer coisa.

## 2026-07-06 — Cssm.mq5 v1.41: janelas por horizonte temporal (WM_HOURS)

Mudança de FERRAMENTA (indicador de leitura), não de metodologia da
pesquisa — nenhuma fase, rótulo ou script Python é afetado.

- **Motivação**: com janela fixa em barras (w=64) o horizonte temporal
  varia selvagemente entre TFs (M30: 32h; H1: 2,7 dias; H4: 10,7 dias) —
  o indicador "procura tendências remotas" nos TFs curtos e a grade MTF
  compara coisas incomparáveis.
- Novo modo `WM_HOURS` (default): o usuário declara o horizonte de
  DETECÇÃO em horas (18h; perfil tendência absoluta 12-24h) e um
  horizonte de CONTEXTO (120h). Conversão por TF com piso estatístico
  de 16 barras → camadas: M15:72/M30:36/H1:18 detecção; H4:30 contexto;
  D1/W1/MN estruturais (w=64 legado). Derivados w_fast=max(4,w/4),
  z_win=clamp(8w,150,500).
- Portões t auto-calibrados (`InpAutoGates`): interpolação linear da
  tabela de calibração v1.40 (random walk, FP 5%/20%) pela janela
  efetiva de CADA TF — índice, grade MTF e camada relacional sempre com
  a régua da própria janela (antes a grade usava gate de w=64 com
  qualquer w).
- Grade MTF passa a calcular cada TF com a SUA janela efetiva; cabeçalho
  das colunas marca a camada (sufixo ᵈ/ᶜ/ˢ + dimming) e o painel ganha a
  linha "lente:" — um TF estrutural nunca deve ser lido como se
  detectasse o dia (piso de 16 barras em H4 = 2,7 dias é RESOLUÇÃO, não
  defeito).
- `WM_BARS` preserva o v1.40 byte a byte (inputs legados valem);
  Journal imprime tabela de conversão, verificação do GateFor (nós
  exatos + monotonicidade) e tempo do Recalc inicial. Anti-repaint,
  alertas em barra fechada e idade dos estados intactos.

## 2026-07-06 — a15: ledger dos prints + autenticação contra o M5

Motivação: o dono do repo tem prints quase diários dos stories do
especialista (históricos MT5 de portfólios encerrados); 9 dias transcritos
(19/06–06/07/2026, 63 pernas) em `specialist_ledger.csv` (append-only; não
confundir com `specialist_calls.csv` imutável nem com o prospectivo do a14).

Enquadramento honesto: o ledger NÃO mede hit rate preditivo — são trades
encerrados publicados ex-post, vencedores por construção (seleção); hit
rate é papel exclusivo do a14. "Consistente com preços reais" NÃO prova
conta real nem skill (demo usa os mesmos preços). Restrição de holdout
respeitada: os dias caem na região de holdout; `a15_ledger_check.py` lê
APENAS closes M5 brutos (sem labels/splits/índices/regras — precedente
a11 Etapa 3; travado em teste que inspeciona a AST do módulo).

Resultado da autenticação (results/*_a15, tol 15bp preço / 3% lucro):

- **profit reconstruído: 63/63 PASS** (conversão QUOTE→USD no carimbo);
  **price_in plausível: 63/63 PASS**; price_out estrito: 48/63.
- Dos 15 FAIL de price_out: as 7 pernas de 22/06 desviam 17–34bp no
  horário do print mas convergem UNIFORMEMENTE com offset de relógio
  **+3h** (0.9–3.5bp) — consistente com print em UTC+0 vs servidor UTC+3.
  As 8 restantes (23–25/06) são marginais (15–31bp) com offsets mistos —
  inconclusivas (spread/granularidade M5/revisita de nível).
- Somas por dia: 8/9 batem o total_print a ±0.02. **02/07 FALHA por
  −966.06 (0.5%)**: único portfólio de 2 dias — compatível com swap/
  comissão de overnight incluídos no total do MT5 e ausentes do P/L puro
  de preço das pernas. Achado registrado; CSV não editado.
- Perna PERDEDORA publicada em 24/06 (USDJPY, −5.342,44) — existe, mas
  1 em 63 não mitiga o viés de seleção dos dias/portfólios publicados.
- Cobertura: 9 de 12 dias úteis do intervalo; faltam 26/06 e 03/07
  (sextas) e 01/07.
- Veredito: prints AUTÊNTICOS quanto a preços (nível de mercado real);
  autenticidade ≠ conta real ≠ skill preditivo.

## 2026-07-06 — infra de paridade do Cssm v1.41

- `Cssm_v140_ref.mq5`: cópia CONGELADA do v1.40 (git show main:Cssm.mq5),
  só para servir de referência no teste de paridade. Não editar.
- `Test_CSSM_Parity_V141.mq5`: script MT5 que compara buffers 0-39 do
  v1.40 vs v1.41(WM_BARS) em 100 barras fechadas — critério de aceite
  nº 1. O handle v1.41 recebe horizonte/AutoGates ativos de propósito:
  em WM_BARS devem ser ignorados; se vazarem, o diff acusa.
- `Export_CSSM_Parity.mq5` v1.01 — bug latente descoberto e corrigido:
  a chamada iCustom posicional pulava os 7 inputs visuais, então o gate
  exato da pesquisa (2.137276) caía em InpEndLabels e NUNCA chegava em
  InpPairGate (ficava 2.13). Consequência: a checagem de paridade do
  breadth (a11/v1.40) rodou com gate 2.13, não 2.137276 — diferença só
  em barras com |t| entre os dois valores; se a paridade for re-checada,
  usar o script corrigido. Também realinhado à ordem de inputs do v1.41
  (4 inputs de modo na frente, WM_BARS forçado).
- Verificação executada no MT5 (USDCAD, Journal 2026-07-06): paridade
  **PASS** — buffers 0-39, 100 barras, max|diff|=0.0 em H1 e H4; tabela
  de conversão, GateFor (nós + monotonicidade) e performance OK
  (Recalc 34-37 ms; ComputePairs 3,6 ms c/ w=18 vs 9,2 ms c/ w=64).
  Nota: este commit ficou fora do merge do PR #6 (merge feito antes do
  push); entra agora junto com o guia de leitura.

## 2026-07-06 — Fidelidade de instrumento: css_screen + pré-registro a12b/a13b

DESCOBERTA: o CSS que o dono olha na tela (indicators/
CurrencySlopeStrength_v2_20.mq5, agora versionado intocado) usa matemática
materialmente diferente do css_classic.py testado no a12/a13:

| | tela (v2.20) | css_classic (a12/a13) |
|---|---|---|
| TMA | triangular Gernard (21..1), janela 20 | SMA(SMA), per=14 |
| slope | lookback 1, norm × sqrt(slope) | suav=3 |
| normalização | ATRrel(100), shift 10(+1 domingo), ÷10 | relativa (‰) |
| escala | ×0.40, clamp ±0.98, FIXA | renorm por barra p/ ±0.4 |

A escala fixa muda a GEOMETRIA (pode não haver moeda fora da box; na
renorm por barra sempre há). Consequência honesta: os nulos do a12/a13
valem para o que testaram; a lente da TELA nunca foi testada.

- O dono AUTORIZOU (2026-07-06) re-execução única de correção de
  fidelidade (a12b/a13b) — exceção pontual ao compromisso "nada de
  retrospectivo até o veredito do a14", registrada como tal. Depois do
  a12b/a13b o retrospectivo FECHA até o veredito do a14.
- `css_screen.py`: porte exato da leitura AO VIVO (a TMA do MQ5 é
  centrada no histórico = repaint; o porte reproduz a leitura da barra
  corrente, única causal — divergência documentada na docstring). Golden
  tests com a aritmética verbatim do MQ5. css_classic.py INTOCADO
  (registro do que a12/a13 testaram).
- PRÉ-REGISTRO a12b/a13b (commit congelado antes da 1ª execução): cópias
  mínimas do a12/a13 trocando SÓ a fonte das linhas. Regras, alvos,
  baselines, reality check, dias research, universos e critérios de
  sobrevivência IDÊNTICOS. Proibido grid/regras novas/janelas novas.
  Prior honesto: positivo improvável (a5 nulo no motor; ML ~0.50 em
  todas as formulações); o valor é fechar a lacuna de fidelidade.
- Paridade MQ5×Python: indicators/Export_CSS_Parity.mq5 (recalcula a
  leitura ao vivo ancorada no tempo — comparação como-com-como) +
  p2_css_parity.py. Compilação/execução MANUAIS no Windows do dono =
  PENDENTE (mesmo status do parity do CSSM, critério 6).
- a16 (segunda lente nos snapshots): BLOQUEADO — a16_snapshot_t0.py não
  existe no repositório (nem em branch remota). Tarefa adiada até o a16
  ser entregue/pushado.

## 2026-07-06 — a12b/a13b executados: **RESULTADO NULO** (results/*_a12b, *_a13b)

A lente da tela não muda o veredito. 395 dias research, holdout intocado:

- a12b (rótulo v1): R1 10.3/10.3%, R2 11.3/12.1%, R3 12.2/9.4% top-1
  (usd7/all28) — nenhuma bate persistência 14.5% nem p95 15.8/15.4%;
  ML AUC 0.478–0.509.
- a13b (Tokyo→NY): melhor caso RB usd7 15h 50.3% (bate baselines por
  4.6pp mas p95=57.1%); all28 e 12h tudo abaixo dos baselines; RC sempre
  n<100; ML AUC 0.497–0.538 (o 0.538 é 1 fold-set, ±0.016, sem regra
  correspondente que sobreviva — não é sinal, é flutuação de teto).
- Fechamento: com a5 (motor CSSM), a12/a13 (css_classic) e a12b/a13b
  (css_screen fiel à tela), TODAS as leituras do indicador em T0 estão
  testadas e nulas — inclusive a formulação exata que o dono vê na tela.
  O retrospectivo FECHA aqui até o veredito do a14 (prospectivo).

## 2026-07-07 — v3 USD caso-controle: pré-registro, execução e RESULTADO NULO

Estudo completo em `v3_usd_casocontrole/` (protocolo pré-registrado pelo
dono do repo; regras duras no CLAUDE.md local; parâmetros em config.yaml).
Pergunta: features engine-agnostic em T0 (véspera de Tóquio) discriminam
os dias de USD protagonista fora da amostra?

- Dados novos: OHLC D1+H1, 4 anos, 7 pares do USD (Fase 0: cobertura
  1460d, gaps <= 0,82%, fuso confirmado — 206/208 segundas abrem 00:00).
- **Calibração do rótulo documentada pré-resultados**: leitura literal
  |close-open| >= p60(TR) deu taxa-base 6,4% (gate disparou; esperado
  12-25%). Investigação: breadth>=6/7 sozinho = 58,4% dos dias — a
  magnitude domina. Adotada leitura C ("movimento do dia" = True Range
  vs p60 TR 60d): taxa-base 26,5%, dentro da banda dura. Trilha completa
  no CLAUDE.md do v3.
- Gates de vazamento: test_no_leakage (prova de truncagem sintética) +
  self-check de truncagem em 12 dias reais + auditoria de max_ts <= T0.
- Descoberta (683d): F1-F3 logit AUC OOF 0,595 vs F4 (CSSM v1.41, lentes
  H1/H4, quarentena) 0,520 — mas p@k do modelo (0,315) JÁ não batia a
  persistência (0,319) na própria descoberta.
- **Confirmação (única, modelo congelado, 283d): NULO.** AUC 0,527
  (p-perm 0,25); lift vs persistência +0,019, IC95% [-0,091, +0,137];
  F4 AUC 0,473 (lift -0,108). Ambos nulos => o fenômeno é primariamente
  IDENTIFICÁVEL EM RETROSPECTO, não previsível em T0 — resposta direta
  à questão aberta do programa. O sinal da descoberta não sobreviveu.
- Guardião da confirmação testado: segunda execução recusada sem
  autorização humana explícita.

## 2026-07-07 — PRÉ-REGISTRO: a17 (tempo-de-trava) + s1 (calendário MT5) + a18 (calendário × rótulos)

**Motivação.** a3 mostrou: 87,6% dos dias research têm >=1 rótulo; Tokyo
carrega 56% do movimento. Análise descritiva (07/07) dos 49 dias sem
rótulo: o gate ER falha em 40/49 (mediana 0,108 vs 0,196) — dias sem
rótulo são majoritariamente dias SEM tendência limpa, não tendências
revertidas. Hipóteses vivas: (i) o horário em que a tendência "trava" é
cedo o bastante para ser operável; (ii) calendário econômico cria/impede
rótulos.

**a17 — tempo-de-trava (descritivo + 1 família de regra pré-registrada).**
- Universo: dias research (treino+validação via `research_days`), pares
  usd7 e all28, janela v1 [T0, T0+12h], M5.
- Métricas por (dia, moeda rotulada): `t_lock` = instante do ÚLTIMO
  cruzamento de zero do retorno acumulado do índice sintético (após ele,
  o sinal nunca mais vira dentro da janela); `t_half` = primeiro instante
  com |cum_ret| >= 50% do |idx_ret| final; `frac_restante(t)` = fração do
  movimento final ainda por vir em t ∈ {1h, 2h, 4h, 8h}.
- Saídas: distribuição (mediana, IQR, p90) de t_lock e t_half — geral,
  por moeda, por direção, por dia-da-semana; % de dias travados até
  T0+{1,2,4,8}h.
- HONESTIDADE OBRIGATÓRIA no REPORT: t_lock é definido COM RETROSPECTO
  (só se sabe que travou porque não virou depois). Ele descreve a
  anatomia, não é regra de entrada.
- Família de regra pré-registrada R-CONF(k), k ∈ {1, 2, 4} (grade
  fechada, 3 células, correção via reality check sobre a grade): em
  T0+k h, escolher a moeda com maior |cum_ret| normalizado (z usando o
  mesmo vol_lookback=63 do v1, shift(1)) entre as com breadth-parcial
  >= 6/7; prever protagonista=essa moeda, direção=sinal. Alvo: top-1
  accuracy contra o protagonista do dia (rótulo v1). Baselines:
  persistência D-1 (14,5%) e p95 do reality check por permutação em
  blocos (`stats_blocks`). Critério de sucesso: bater AMBOS. Nota
  pré-registrada: acertar em T0+4h só tem valor econômico se
  `frac_restante(4h)` medida no bloco descritivo for material — reportar
  as duas coisas juntas.
- Anti-lookahead: features de R-CONF usam exclusivamente barras <= T0+k h.

**s1_export_calendar.mq5 — export do calendário econômico do MT5.**
- Script MQL5 usando `CalendarValueHistory` cobrindo 2024-07-01 até hoje.
- Colunas: `event_id, time_server, country, currency, name, importance
  (LOW/MODERATE/HIGH), actual, forecast, previous`.
- Mapear país→moeda G8 (zona do euro inteira → EUR; descartar países
  fora do G8).
- Saída: `data/calendar/calendar_mt5.csv` + `_meta.json` com timestamp do
  export e verificação de fuso: conferir que um evento âncora conhecido
  (ex.: CPI dos EUA, 08:30 NY) aparece em 15:30 server no verão — mesmo
  protocolo do `_meta.json` do raw. Se a verificação falhar, PARAR e
  reportar.
- Limitação registrada: `actual` é o valor atual no provedor (revisões
  não reconstruíveis). Para QUALQUER uso preditivo em T0 só vale a
  AGENDA (evento marcado, moeda, horário, importância) — que é conhecida
  ex-ante. `actual`/surpresa só entram em análise descritiva pós-evento.

**a18 — calendário × rótulos (2 hipóteses + 1 regra preditiva, tudo
pré-registrado).**
- H-A18-1 (notícia CRIA rótulo): P(rótulo_C | >=1 evento HIGH de C na
  janela do dia) > P(rótulo_C | sem evento HIGH de C). Teste: diferença
  de proporções, IC95% bootstrap em blocos por dia. Nulo se IC contém 0.
- H-A18-2 (conflito IMPEDE rótulo): dias sem nenhum rótulo são
  enriquecidos em "conflito" (eventos HIGH de >=2 moedas distintas na
  janela) vs dias rotulados. Mesmo teste.
- H-A18-3 (agenda prevê em T0 — a única leitura legalmente ex-ante):
  regra "prever como protagonistas as moedas com evento HIGH agendado na
  janela; direção pela persistência D-1 quando disponível, senão abster".
  Métrica: top-1 accuracy nos dias em que a regra opina + taxa de
  abstenção. Baselines: persistência e reality check. Sucesso: bater
  ambos.
- Descritivo adicional (se a17 já rodou): histograma de (t_lock − horário
  do evento HIGH mais próximo) — a trava se agrupa depois de notícia?
- Só dias research. Nada de holdout.

**Critério global de reporte:** resultados nulos são reportados sem
suavização, no padrão do repo.

## 2026-07-07 — a17 executado: PRIMEIRO RESULTADO NÃO-NULO (results/*_a17)

Descritivo (784 eventos rotulados, usd7): t_lock mediana 3.3h (IQR 1.0–9.0);
55% dos eventos travados até T0+4h; fração do movimento ainda por vir em
T0+4h: mediana 73.7% — a tendência do dia "se anuncia" cedo E ainda deixa
a maior parte do movimento na mesa (compatível com Tokyo=56% do a3 e com o
align_4h=89% do a8).

R-CONF(k) — SOBREVIVENTES pela primeira vez no projeto:
- usd7: k=4h → top-1 12.1% (n=173) vs persistência 8.1% e p95 8.9%.
- all28: k=2h → 14.4% (n=326) e k=4h → **21.0%** (n=329) vs persistência
  8.1% e p95 12.8% — o k=4h all28 bate o p95 por 8.2pp.

RESSALVAS HONESTAS (antes de qualquer entusiasmo):
1. Correlação parcialmente MECÂNICA: o movimento até T0+k é parte do
   rótulo de 12h (breadth/z parciais correlacionam com os totais). O
   mitigante pré-registrado é a frac_restante (73% em 4h) — mas ela é
   computada CONDICIONADA a dias rotulados (retrospecto); não é P&L.
2. Identificar o protagonista ≠ capturar retorno: o a10-T2 mostrou que o
   momentum das primeiras 4h NÃO continua em média sobre TODOS os dias.
   A diferença aqui é a seleção (breadth>=6/7 + maior |z|) e o alvo
   (top-1). O valor ECONÔMICO de operar T0+4h→T0+12h nos dias em que a
   R-CONF(4) opina NÃO foi medido — exigiria novo estudo pré-registrado
   (estilo a6, com custos), fora do escopo autorizado deste pacote.
3. n=173–329 com IC largo; validação/treino misturados nos dias research
   (como nos estudos anteriores); holdout intocado.

a18: aguardando o dono rodar s1_export_calendar.mq5 e copiar o CSV
(depois: `python a18_calendar.py --ingest` e a análise).

## 2026-07-07 — a18 executado (results/*_a18): calendário IMPORTA (com nuances)

Fuso do calendário: ACHADO da verificação pré-registrada — timestamps em
UTC+3 fixo vs feed de preços UTC+2/+3 DST-EUA; normalização documentada
em `_normalize_calendar_tz` (pós-fix: 207/207 âncoras CPI em 15:30).

- **H-A18-1 (notícia CRIA rótulo): SIGNIFICATIVO.** P(rótulo|HIGH da
  moeda na janela) = 33.9% vs 24.1% sem HIGH; Δ=+9.8pp, IC95%
  [+3.5, +15.9]. Primeira variável EX-ANTE associada ao rótulo em todo
  o projeto.
- **H-A18-2 (conflito IMPEDE rótulo): SIGNIFICATIVO NO SENTIDO
  CONTRÁRIO ao pré-registrado.** Dias rotulados têm MAIS conflito
  (12.1%) que dias sem rótulo (4.1%); Δ=−8.1pp, IC [−13.6, −1.4].
  A hipótese como formulada está REFUTADA: conflito de notícias
  acompanha dias de tendência, não os impede.
- **H-A18-3 (agenda prevê protagonista): NULO** — abstém em 93.4% dos
  dias (n=23 <100), 17.4% < p95 26.1%. A agenda sozinha, com direção por
  persistência, não opera.
- Descritivo (n=80): t_lock mediana 3.2h ANTES do evento HIGH mais
  próximo; só 16% travam depois da notícia. Na janela [T0,T0+12h] os
  eventos são da manhã Ásia/Europa (os releases americanos de 15:30
  caem FORA da janela do rótulo v1) — leitura: a notícia da manhã marca
  o dia, mas a trava da tendência costuma preceder o horário do evento.
- Síntese honesta: o calendário é o primeiro sinal ex-ante com
  associação real ao fenômeno (H1), mas fraco demais sozinho para
  previsão operável (H3). Próximo candidato natural (exigiria novo
  pré-registro): combinar agenda (H1) com confirmação de preço
  intradiária (R-CONF do a17).

## 2026-07-08 — PRÉ-REGISTRO: a19 (ciclo de fases do CSS) + a20 (confluência MTF)

Espec fornecida pelo time ("a16/a17 — Ciclo de fases e confluência",
renumerada a19/a20 — a16/a17 já ocupadas). Postura herdada: nada é sinal
até provar o contrário; limiares definidos ANTES; breadth sempre como
covariável (lição a11); só barras fechadas.

DECISÕES DE IMPLEMENTAÇÃO (registradas antes de rodar):
- Lente: `css_screen.py` (leitura AO VIVO, causal, golden tests verbatim
  do MQ5). A TMA literal dos buffers é CENTRADA (usa até 20 barras
  futuras no histórico) — shift>=1 NÃO elimina o lookahead; usar os
  buffers literais em análises de retorno futuro (Q3/Q7+) seria viés de
  futuro. A leitura ao vivo é o que o trader vê no momento e é a única
  série causal. Divergência documentada também no css_screen.py.
- GATE DE PARIDADE (§1 da espec): "sem paridade, o estudo não roda" —
  a paridade MQ5×Python (Export_CSS_Parity.mq5 + p2_css_parity.py, já
  no repo) depende de execução MANUAL no MT5 do dono. As análises a19/
  a20 SÓ serão executadas depois do p2 passar (tol 1e-4; a espec pede
  1e-6 — reportar o número obtido).
- Dados: H1 10 anos × 28 pares exportados do MT5 (s2_export_h1.py;
  desde 2016-07; data/raw/H1_*.parquet + _meta_h1.json). H4/D1/W1/MN
  reamostrados do H1 no calendário do broker.
- dpeso k=3 (pré-registro a13); box=0.20; ext=0.50; breadth hard 3/7.

a19 — FASES (ciclo direcional FORÇA→EXAUSTÃO→FRAQUEZA→EXPANSÃO + espelho
vendedor; delta=val_t−val_{t−3}; delta=0 mantém fase):
- Q1 matriz de transição de Markov + taxa de rotação completa vs saltos;
- Q1b distribuição de val na transição EXAUSTÃO→FRAQUEZA (0.50 tem base?);
- Q2 dwell time + hazard de retorno à box;
- Q3 retorno futuro do índice condicionado à fase (1/3/5/10 barras do
  TF), bootstrap em blocos por dia, correção Benjamini-Hochberg nas
  ~células fase×TF×moeda×horizonte. Nulo é aceitável e publicável;
- Q4 whipsaw rate (reversão à box em <=2 barras);
- Q5 percentil empírico de 0.20/0.50 por TF (limiar fixo significa
  coisas diferentes por TF?);
- Q6 tudo repetido com breadth>=3/7.

a20 — CONFLUÊNCIA (por barra fechada de H1, fases por TF via último TF
fechado):
- Caveat mecânico registrado: soma das 8 forças ≈ 0 → baseline
  OBRIGATÓRIO por block-shuffle preservando estrutura;
- Estados: alinhamento de sinal (0–5 TFs), alinhamento de box, CASCATA
  (D1/W1 em FORÇA + H1/H4 em EXPANSÃO a favor), divergência, fase
  relativa (lead-lag);
- Alvo definido AGORA: par = mais forte vs mais fraca no ranking D1 em
  t; grande movimento = quartil superior do |retorno| 24h/72h
  normalizado por ATR(100) H1, quartil calculado SÓ na exploração;
- Q7 lift por alinhamento (monotonia vs baseline embaralhado);
- Q8 cascata > alinhamento simples? (tese central do estilo);
- Q9 lead-lag H1→H4/D1 (correlação cruzada de eventos de EXPANSÃO);
- Q10 W1/MN: reportar nº de eventos independentes; provavelmente
  inconclusivo — dizer com clareza;
- Q11 tudo com breadth>=3/7;
- Validação: split temporal 70/30 (exploração/confirmação); só é
  "padrão" o que sobreviver no out-of-sample.

Regra de decisão p/ v2.33+: mudança no indicador só com sobrevivência
OOS/BH + melhora de leitura (whipsaw↓/dwell↑) sem venda preditiva.

## 2026-07-08 — a19/a20 executados (results/*_a19, *_a20)

Gate de paridade FECHADO antes da execução: max|Δ| = 5e-9 nas 8 moedas em
H1 e D1 (espec pedia 1e-6). A paridade pegou bug real: o MQ5 calcula cada
par na sequência NATIVA de barras; o porte usava grade ffillada (GBPJPY
com 12 barras faltantes → Δ 1e-2). Corrigido em css_screen_lines.

a19 — FASES:
- Q1: a rotação EXISTE como gramática — transição canônica com prob.
  média 0.65–0.67 em TODOS os TFs (H0=0.33); mas só 13–15% das saídas de
  FORÇA completam o ciclo na ordem; a "falsa exaustão" (EXAUSTÃO→FORÇA)
  é ~40% das saídas de exaustão.
- Q1b: transição EXAUSTÃO→FRAQUEZA ocorre com val mediano 0.168; 0% em
  [0.4,0.6] — o nível 0.50 é DECORAÇÃO.
- Q2: dwell mediano 3–5 barras em todas as fases/TFs; hazard ~plano
  (0.15–0.25) até n=8 — pouca memória além do curto prazo.
- Q4: whipsaw ~22% em TODOS os TFs (não é pior no H1 — surpresa).
- Q5: box 0.20 = p46–52 e ext 0.50 = p86–92 em todos os TFs — limiares
  fixos têm significado ESTÁVEL entre TFs (hipótese de recalibração por
  quantil por TF: refutada; não há o que melhorar aqui).
- Q3: 54/492 células sobrevivem a BH 5% (~25 esperadas por acaso —
  estrutura fraca porém real), HETEROGÊNEA por moeda: JPY = continuação
  no D1 (FRAQUEZA −22bps/10d, EXAUSTÃO −45bps); CHF/EUR/USD = reversão.
  Provável assinatura de regime da década (iene em queda secular) —
  NÃO generalizar sem teste fora do regime. Q6 (breadth): 59 células,
  mesmo padrão — breadth não muda o quadro.
- BUG PEGO E CORRIGIDO ANTES DE PUBLICAR: 1ª execução usava bootstrap de
  médias diárias NÃO-ponderadas (dias de reversão rápida dominavam o IC;
  246 células "significativas" espúrias). Estimador corrigido para
  pooling ponderado por reamostragem de dias → 54.

a20 — CONFLUÊNCIA: **NULO na prática.**
- Q7: sem monotonia — alinh=5/5 tem lift MENOR que 3/5 na confirmação;
  3 células isoladas passam o p95 por 0.01–0.03 (28 comparações; ~1.4
  falsas esperadas) sem estrutura coerente.
- Q8: CASCATA (tese central do estilo: D1/W1 em força + H1/H4 em
  retomada) — lift confirmação 1.04–1.11 vs p95 1.07–1.08: NULA.
- Q9: 82.8% dos onsets de EXPANSÃO no D1 precedidos por EXPANSÃO no H1 —
  mecânico (24 barras H1 dentro de 1 D1; o H1 cicla rápido), não é
  "relógio" explorável.
- Q10: W1 523 barras / MN 121 — inconclusivo por construção, como
  pré-registrado.
- Q11: breadth não altera nada materialmente.

Síntese: o ciclo de fases é uma GRAMÁTICA descritiva real do indicador
(útil p/ leitura no painel), mas a confluência MTF — o coração do método
visual — não separa grandes movimentos do acaso. Nenhuma mudança no
indicador se qualifica pelas regras da espec (§5): Q5 refutou a
recalibração de limiares; Q7/Q8 não sobreviveram OOS.

## 2026-07-08 — PRÉ-REGISTRO: a21 (CSS como FILTRO de setup independente)

Espec do time. Pergunta única: condicionar um setup de entrada
INDEPENDENTE ao estado do CSS melhora o resultado do MESMO setup sem
filtro? É o último papel do CSS não refutado por a5→a13→a19→a20. Se não
agregar, a linha de pesquisa fecha: CSS = descritivo, ponto.

Definido ANTES de rodar (código congelado neste commit):
- Setups-base (arquétipos, não escolhidos por serem bons — medimos o
  DELTA do filtro): S1 breakout Donchian(20); S2 pullback EMA50/200;
  S3 reversão RSI(14) 30/70. Saída: stop 1.5×ATR, alvo 2×ATR (=> +1.33R
  no acerto), timeout 48 barras. Custo: spread mediano + 0.5 pip, em
  preço, round-trip. 1 posição/par; sinais em posição aberta ignorados.
- Filtros empilhados no bar do sinal (D1 âncora + H1, css_screen):
  F1 direção (base>=+box, quote<=-box, base-quote>=diffthr=0);
  F2 F1+breadth>=3/7 nas duas moedas; F3 F2+veto exaustão D1 (|val|>=box
  e delta contra, k=3); F4 só o par nº1 do ranking D1. Controle negativo
  F1-INV (contra o diferencial; deve piorar).
- Dados: H1 OHLC + spread 10a × 28 pares (s3_export_h1_ohlc.py). Split
  70/30 como a20.
- Sucesso: Δexpectancy>=+0.10R, IC exclui 0, BH-ok, OUT-OF-SAMPLE, em
  >=2/3 setups p/ o mesmo filtro. n_f<100 OOS = inconclusivo (não nulo).
  BH nas 24 células (3×4×2). Bootstrap por blocos semanais.
- Traps mitigadas: base ruim (<-0.5R) não conclui sobre CSS; F4 poucos
  trades = inconclusivo; regime por terços de ATR como secundário.

## 2026-07-08 — a21 executado: **NULO** (results/*_a21) — LINHA DE PESQUISA FECHA

O CSS como filtro de setup independente não agrega. 84k+ trades, 28 pares,
10 anos, custos incluídos, split 70/30.

- Trap #1 NÃO acionada: setups-base têm expectancy −0.04 a −0.12R
  (near-breakeven; hit ~42% ≈ breakeven de um alvo 2×ATR/stop 1.5×ATR =
  42.9%). São minimamente funcionais → o DELTA do filtro é interpretável.
- Teste principal: **0/24 células passam.** Todos os Δexpectancy são
  ±0.05R típico, IC sempre cruza zero, nenhum sobrevive a BH. F4
  (atenção ao par nº1) tem os maiores Δ positivos (+0.04 a +0.11) mas n
  pequeno e IC cruzando zero; nenhum atinge +0.10R com IC excludente.
  Nenhum filtro atinge o critério de >=2/3 setups.
- CONTROLE NEGATIVO REFUTA O FILTRO: F1-inverso (operar CONTRA o
  diferencial CSS) deveria PIORAR — mas ficou ~0, e em S2-short
  MELHOROU +0.313R (IC [+0.105, +0.511], exclui zero). Operar contra o
  CSS não é pior que operar a favor: a direção do CSS é ruído para
  timing de entrada, confirmação direta e limpa.
- Custo de oportunidade: F3 mantém só 2–6% dos trades e descarta 94–98%
  dos vencedores — mesmo que ajudasse à margem, joga fora quase tudo.

VEREDITO DA LINHA DE PESQUISA (a5→a13→a19→a20→a21): o CSS/CSSM é um
INDICADOR DESCRITIVO. Nenhum uso preditivo ou operacional sobreviveu:
estado (a5), geometria (a12), peso (a13), fases/confluência (a19/a20),
filtro de setup (a21) — todos nulos, com paridade de instrumento
confirmada a 5e-9. Linha final adicionada ao header do
CurrencySlopeStrength_v2_30.mq5. O que resta com evidência POSITIVA é
externo ao indicador: calendário (a18, +9.8pp ex-ante) e confirmação de
preço intradiária (a17 R-CONF); o a14 prospectivo segue como juiz do
especialista.

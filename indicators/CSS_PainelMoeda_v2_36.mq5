//+------------------------------------------------------------------+
//|                                     CurrencySlopeStrength.mq5     |
//|   Forca de moeda por slope de TMA, estilo Anderson Bonoto.       |
//|   - Linhas (TF do grafico) + box +/-0.2                          |
//|   - Painel com 3 timeframes lado a lado (ranking forte->fraca)   |
//|   - Sinal: moeda fora da box (|val|>box) = impulso.              |
//|     Topo fora por cima + fundo fora por baixo = trend novo.      |
//|  ===== CSS_PainelMoeda v2.36 =====                                |
//|  DERIVADO do CurrencySlopeStrength_v2_35_EXP (nucleo IDENTICO).   |
//|  Existe como ARQUIVO SEPARADO de proposito: o v2_35_EXP alimenta  |
//|  o app (fm-app) e nao deve ser tocado.                            |
//|                                                                  |
//|  O QUE MUDA:                                                      |
//|   1) PAINEL POR MOEDA (default). Transpoe o painel classico:      |
//|      8 linhas = 8 moedas, colunas =                              |
//|        pos    | valor do CSS no TF das linhas (POSICAO da linha)  |
//|        ang    | variacao de |V| em k barras fechadas (ANGULACAO)  |
//|        estado | EXPANSAO / EXAUSTAO / NEUTRA / FRAQUEZA          |
//|        MTF    | seta da angulacao em H4, D1, W1, MN              |
//|      Ordenado por |V| decrescente (a mais mobilizada no topo).    |
//|      InpPainelModo=MP_TF volta ao painel classico de 5 TFs.       |
//|   2) PREFIXOS de objeto trocados (CSS_ -> CSSPM_) para os dois    |
//|      indicadores ficarem no MESMO grafico sem brigar.             |
//|   Nada mais muda: calculo, buffers, linhas, matriz, replay.       |
//|                                                                  |
//|  ESTADO por MAGNITUDE (nao-direcional; vale p/ forte e p/ fraca): |
//|    |V|>=box e d|V|>0  -> EXPANSAO   (movimento ampliando)        |
//|    |V|>=box e d|V|<=0 -> EXAUSTAO   (fora da box, encolhendo)    |
//|    |V|< box e d|V|>0  -> NEUTRA     (dentro da box, subindo)     |
//|    |V|< box e d|V|<=0 -> FRAQUEZA   (dentro da box, murchando)   |
//|  A COR da celula continua marcando o LADO (verde forte/vermelho   |
//|  fraca/cinza dentro da box) — lado e dinamica ficam separados.    |
//|                                                                  |
//|  (!) LEITURA, NAO SINAL — regra do INDICATOR_CHANGELOG ("nenhum   |
//|  badge de sinal entra no indicador"). Tudo que este painel mostra |
//|  ja foi testado como preditor e deu NULO: posicao vs box          |
//|  (a12/a12b), angulacao/"peso" (a13/a13b), confluencia MTF (a20 e  |
//|  E7, efeitos <=9%). O ciclo em si o a19 mediu: so 13-15%          |
//|  completam e ~40% das exaustoes sao falsas.                      |
//|                                                                  |
//|   v2.35 - NUCLEO DE CALCULO TROCADO pelo do CSS ORIGINAL (MT4).   |
//|     A partir daqui o valor por par e, literalmente, a formula do  |
//|     CurrencySlopeStrength de Paul Geirnaerdt convertida p/ MQL5:  |
//|                                                                  |
//|       atr   = ATR(100)[shift+10] / 10                            |
//|       tma   = LWMA(21)[shift]                                    |
//|       prev  = (LWMA(21)[shift+1]*231 + close[shift]*20) / 251    |
//|       slope = (tma - prev) / atr                                 |
//|       forca(moeda) = media dos slopes dos pares em que aparece   |
//|                      (+ como base, - como quote)                 |
//|                                                                  |
//|     O QUE MUDOU em relacao a v2.34:                              |
//|     * ATR: era |close-close| medio dividido pelo preco (proxy);  |
//|       agora e True Range com media SIMPLES, igual ao iATR do MT4 |
//|       (o MQL5 usa suavizacao de Wilder — por isso e calculado    |
//|       aqui na mao, e nao via handle: fica fiel E sem estourar o  |
//|       limite de handles com 28 pares x 6 TFs).                   |
//|     * Normalizacao: sumiu a divisao pelo preco. Numerador e      |
//|       denominador ja estao em unidades de preco, entao o slope   |
//|       e adimensional por construcao — como no original.          |
//|     * TMA: por padrao usa a LWMA(21) "anti-repaint" (o ramo      |
//|       ignoreFuture=true do original). InpIgnoreFuture=false      |
//|       volta a TMA centrada da v2.34, que repinta.                |
//|     * InpScale passa a 1.00: a box 0.20 do original ja e a box   |
//|       0.20 daqui, entao nao ha mais fator de ajuste artificial.  |
//|     NAO mudou: replay, ancora temporal, painel, matriz, botoes,  |
//|     buffers de dpeso, alertas — tudo consome o mesmo contrato.   |
//|   v2.34 - botao REPLAY: retrocede o ESTADO das linhas/painel a um |
//|     instante passado e o reconstroi FIELMENTE (ancora no tempo    |
//|     ABSOLUTO daquele bar, nao no bar 0). Assim a TMA nao "settla" |
//|     com barras futuras e o ATR e medido naquele instante — a tela |
//|     fica igual ao que era ao vivo. Botoes << < LIVE > >> + VLINE. |
//|     NENHUM calculo alterado; muda so a ANCORA temporal e o        |
//|     deslocamento do plot. Ao vivo o comportamento e identico.     |
//|   v2.33 - aba MATRIZ 8x8 por par (ideia do CSSM v1.40) +          |
//|   polimento visual. NENHUM calculo alterado:                     |
//|     * MATRIZ (botao MTX): celula (a,b) = valor de slope TMA do   |
//|       PAR a/b — a MESMA formula das linhas/painel (z do slope    |
//|       normalizado por ATR, clamp em ScaleMax), calculada no par  |
//|       direto, SEM agregar pela cesta. NAO e o t Newey-West do    |
//|       CSSM: aqui a matriz fala a lingua do proprio CSS.          |
//|       Barra FECHADA (kShift=1, sem repaint), TF das linhas.      |
//|       Verde/vermelho = par fora da box 0.20 (limiar ja validado  |
//|       no a19 Q5); cinza = dentro. Leitura descritiva, nao sinal. |
//|     * Rotulos na ponta das linhas (moeda + valor, anti-colisao)  |
//|       — usabilidade herdada do CSSM v1.10.                       |
//|     * Painel: titulo, celulas chapadas (borda = fundo, estilo    |
//|       CSSM), cabecalhos de coluna em cinza, aviso "leitura, nao  |
//|       sinal" no tom do CSSM. Objetos do painel no grupo CSS_p_   |
//|       p/ alternar painel <-> matriz sem vazamento de objetos.    |
//|   v2.32 - ciclo de fases (FORCA/EXAUSTAO/FRAQUEZA/EXPANSAO) e     |
//|   cascata MTF testados em a19/a20 (ta-research). Resultado:      |
//|     * ROTACAO existe como padrao (P=0.65-0.67 vs 0.33 acaso),    |
//|       MAS so 13-15% dos ciclos completam a volta; ~40% e falsa   |
//|       exaustao (volta p/ FORCA sem passar por FRAQUEZA).         |
//|     * Nivel 0.50 (exaustao "forte") NAO tem base empirica —      |
//|       transicao real ocorre perto de val~0.17 (borda da box).    |
//|     * Box 0.20 fixo E ADEQUADO (percentil ~46-52 em todos os TF, |
//|       estavel) — recalibragem por quantil por TF, REJEITADA.     |
//|     * Cascata MTF (MN/W1/D1/H4/H1 alinhados => grande movimento, |
//|       tese "Anderson/cascata") e NULA: lift 1.04-1.11 contra     |
//|       baseline embaralhado 1.07-1.08, sem monotonia, sem         |
//|       sobrevivencia out-of-sample. NAO usar alinhamento de TFs   |
//|       como gatilho de entrada.                                   |
//|     * Assinatura por moeda: JPY mostra continuacao pos-exaustao  |
//|       no D1; EUR/CHF/USD mostram reversao. Provavel regime da    |
//|       decada, NAO generalizar como regra.                        |
//|     * DECISAO: nenhuma mudanca no calculo ou nos limiares.       |
//|       Ciclo de fases permanece VOCABULARIO de leitura no painel, |
//|       nunca sinal de entrada (mesmo status do a13/v2.30).        |
//|     * PAINEL redesenhado conforme os achados:                    |
//|       - grid ranqueado com celulas coloridas (verde=forca,       |
//|         vermelho=fraqueza, cinza=box) + barra proporcional;      |
//|       - setas de direcao (k=3 barras FECHADAS, sem repaint);     |
//|         cor+seta = fase do ciclo a19 (verde+baixo=exaustao...);  |
//|       - horizonte REAL da TMA no header da coluna (H1*20h etc,   |
//|         licao WM_HOURS);                                         |
//|       - simbolos de peso + - ! ~ REMOVIDOS (a13/a13b nulos);     |
//|       - linhas pontilhadas 0.50 DESLIGADAS por padrao            |
//|         (InpShowExt religa; a19 Q1b);                            |
//|       - legenda cita a19/a20 e o status "leitura, nao sinal".    |
//|                                                                  |
//|   v2.31 - Phase 1: breadth por moeda x TF, marcadores */°,       |
//|   horizontes reais (ex. H1*20h), alertas com breadth.            |
//|   v2.30 - camada de "peso" (LEITURA, NAO SINAL):                 |
//|     * simbolo por moeda x TF no painel: + (dpeso>0, enchendo)    |
//|       - (dpeso<0, esvaziando), ! (conv: fora da box E            |
//|       esvaziando), ~ (retomada: dentro da box re-expandindo a    |
//|       favor). k = 3 barras FECHADAS do TF (pre-registro a13).    |
//|     * buffers 10..17 = dpeso por moeda (ordem USD,EUR,GBP,JPY,   |
//|       CHF,CAD,AUD,NZD) no TF das linhas, INDICATOR_CALCULATIONS  |
//|       p/ iCustom — LER COM shift>=1 (barra 0 em formacao).       |
//|     * camada de peso calculada SO em barra fechada (sem repaint).|
//|                                                                  |
//|   DISCLAIMER (leia antes de operar com isto): a camada de peso   |
//|   e VOCABULARIO de leitura — espelha os termos do especialista   |
//|   ("peso", "combustivel no fim", "retomada") para descrever o    |
//|   grafico. NAO tem valor preditivo demonstrado: o a13 (lente     |
//|   classic) e o a13b (ESTA lente, a da tela) testaram estas       |
//|   leituras em T0 contra o alvo Tokyo->NY e o resultado foi NULO  |
//|   nas duas lentes (ta-research, CHANGELOG 2026-07-06). Use como  |
//|   descricao do presente, nunca como previsao do dia.             |
//|   OBS: o slope "anti-lag" original e proprietario; aqui e padrao.|
//+------------------------------------------------------------------+
#property copyright "Estudo - Camada 2 (forca de moeda)"
#property version   "2.40"
#property description "v2.35: calculo = formula ORIGINAL do CSS (LWMA 21 + ATR 100 estilo MT4) + REPLAY + MATRIZ 8x8"
#property indicator_separate_window
#property indicator_buffers 18
#property indicator_plots   9

#property indicator_type1   DRAW_LINE
#property indicator_label1  "USD"
#property indicator_color1  clrLime
#property indicator_type2   DRAW_LINE
#property indicator_label2  "EUR"
#property indicator_color2  clrDodgerBlue
#property indicator_type3   DRAW_LINE
#property indicator_label3  "GBP"
#property indicator_color3  clrRed
#property indicator_type4   DRAW_LINE
#property indicator_label4  "JPY"
#property indicator_color4  clrMagenta
#property indicator_type5   DRAW_LINE
#property indicator_label5  "CHF"
#property indicator_color5  clrSilver
#property indicator_type6   DRAW_LINE
#property indicator_label6  "CAD"
#property indicator_color6  clrOrange
#property indicator_type7   DRAW_LINE
#property indicator_label7  "AUD"
#property indicator_color7  clrGold
#property indicator_type8   DRAW_LINE
#property indicator_label8  "NZD"
#property indicator_color8  clrAqua
#property indicator_type9   DRAW_COLOR_LINE
#property indicator_label9  "PAR"
#property indicator_color9  clrLime,clrGreen,clrRed,clrFireBrick,clrTeal,clrHotPink
#property indicator_width9  2

// SE_: helper de export JSON atomico (FM App). So LE/exporta — nao altera calculo.
#include <StateExport.mqh>

// SE_: export da barra VIVA (kShift=0, igual ao painel do MT5) x ultima FECHADA
// (kShift=1, estavel/sem repaint). true = live (nao fica 1 barra atras).
input bool   InpExportLive = true;

input int    InpMAPeriod = 21;   // periodo da LWMA/TMA (CSS original: 21)
input int    InpATRPeriod= 100;  // periodo do ATR que normaliza o slope (original: 100)
input bool   InpIgnoreFuture = true; // true = LWMA anti-repaint (ignoreFuture do original); false = TMA centrada
input int    InpSlope    = 1;    // (legado v2.34 - sem efeito no calculo original)
input int    InpVolWin   = 20;   // (legado v2.34 - sem efeito no calculo original)
input bool   InpUseATR   = true; // (legado v2.34 - o original sempre normaliza por ATR)
input double InpScale    = 1.00; // escala (original = 1.00; a box 0.20 ja e a do CSS)
input double InpBox      = 0.20; // box +/- (LevelCrossValue)
input double InpScaleMax = 1.00; // escala fixa da janela (+/-): enquadra a box
// v2.38: o CLAMP dos valores continua em +/-(InpScaleMax-0.02), mas a JANELA
// passa a ser +/-(InpScaleMax*InpFolga). Antes os dois eram o mesmo numero, e
// por isso toda linha saturada (o clamp +/-0.98 do FALHAS C.4) colava na borda
// e brigava com o painel. Com folga 1.35 as linhas ocupam ~73% da altura.
input double InpFolga    = 1.35; // folga vertical da janela (1.00 = sem folga)
input int    InpBars     = 300;  // barras a plotar
input ENUM_TIMEFRAMES InpLineTF = PERIOD_CURRENT; // TF das LINHAS
input bool InpSyncBars = true; // sincronizar linhas com a barra do grafico (backtest)
input ENUM_TIMEFRAMES InpTF1 = PERIOD_H1;  // painel coluna 1
input ENUM_TIMEFRAMES InpTF2 = PERIOD_H4;  // painel coluna 2
input ENUM_TIMEFRAMES InpTF3 = PERIOD_D1;  // painel coluna 3
input ENUM_TIMEFRAMES InpTF4 = PERIOD_W1;  // painel coluna 4
input ENUM_TIMEFRAMES InpTF5 = PERIOD_MN1; // painel coluna 5
input int    InpWidth    = 2;    // espessura das linhas
input bool   InpPanel    = true; // mostrar painel
input double InpExtLevel = 0.50; // nivel das linhas pontilhadas cinza (+/-)
input bool   InpShowExt  = true; // mostrar as linhas pontilhadas em +/-InpExtLevel
input double InpTrigger  = 0.20; // trigger p/ cores de estado (modo par)
input int    InpPanelX   = 12;   // painel: margem a partir da DIREITA
input int    InpPanelY   = 16;   // painel Y
input int    InpFont     = 9;    // fonte do painel
input bool   InpMatrix   = true; // aba MATRIZ 8x8 por par (botao MTX) — v2.33
input bool   InpEndLabels= true; // rotulos na ponta das linhas (estilo CSSM) — v2.33
input bool   InpAlerts   = false; // alertas de cruzamento da box (ligue se quiser)

// v2.36 - modo do painel. Neste arquivo o default e MOEDA (e o motivo dele
// existir). Input no FIM: iCustom posicional de EAs antigos continua valido.
enum EModoPainel { MP_TF=0, MP_MOEDA=1 };
input EModoPainel InpPainelModo = MP_MOEDA; // painel: MOEDA-maior (novo) ou TF-maior
input int    InpFontPainel = 13;   // v2.37: fonte do painel por moeda (maior)
input bool   InpNeon       = true; // v2.37: visual futurista (acento neon)
input double InpDiffThr  = 0.0;  // distancia minima de forca (regra de ouro)
input bool   InpAddSunday= true; // somar candle de domingo na segunda
input int    InpPesoK    = 3;    // k (barras fechadas do TF) p/ dpeso — pre-registro a13
input bool   InpReplay    = true; // botao REPLAY (retroceder estado das linhas) — v2.34
input int    InpReplayStep= 12;   // passo do replay << >> (em barras do grafico)

double B0[],B1[],B2[],B3[],B4[],B5[],B6[],B7[];
double Bpar[];  // buffer do plot 9 (linha do par, modo single)
double ColPar[];// buffer de cor do plot 9
// v2.30: dpeso por moeda no TF das linhas (buffers 10..17, CALCULATIONS).
// dpeso[t] = |val[t]| - |val[t-k]| em barras FECHADAS. Ler com shift>=1.
double D0[],D1s[],D2[],D3[],D4[],D5[],D6[],D7[];

string cur[8]   = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};
color  colArr[8]= {clrLime,clrDodgerBlue,clrRed,clrMagenta,clrSilver,clrOrange,clrGold,clrAqua};

string gPair[];
int    gBaseIdx[], gQuoteIdx[];
int    gPairsN = 0;
int    cnt[8];
bool   gReady = false;
string PFX = "CSSPM_";
// v2.33: grupos de objetos alternaveis (mesma infra do CSSM v1.40).
// Ambos comecam com PFX, entao o ObjectsDeleteAll(0,PFX) do OnDeinit
// continua limpando tudo.
string PPFX= "CSSPM_p_";  // objetos do painel-normal
string MPFX= "CSSPM_mx_"; // objetos da aba MATRIZ
bool   gMtx = false;    // aba MATRIZ ativa (persiste como o gSingle)
bool   gSingle = false; // estado do botao linha unica
bool   gBoxPrev[8];     // estado anterior: estava fora da box?
bool   gHide[8];        // moeda oculta? (toggle pelo painel)
int    gRowCur[8];      // linha r do painel (col A) -> indice da moeda
int    gSolo = -1;      // v2.37: moeda isolada no painel MOEDA (-1 = nenhuma)
bool   gAlertInit=false;
// v2.35: corretora entrega candle de domingo? (addSundayToMonday do original)
bool   gSundayCandles=false;
// SE_: export AO VIVO — cada TF usa a propria barra atual (ignora o InpSyncBars
// do grafico); vale so durante SE_ExportCSS. Independe do TF do grafico.
bool   gExportLive=false;
// v2.34: REPLAY — congela o estado das linhas/painel num instante passado.
// gReplayTime=0 => ao vivo. Quando >0, TUDO e recalculado ancorado nesse
// tempo ABSOLUTO (nao no bar 0), reproduzindo fielmente a tela daquele
// momento: TMA "one-sided" na borda, ATR relativo aquele bar, sem futuro.
datetime gReplayTime=0;  // instante do replay (0 = ao vivo)
int      gReplayBars=0;  // deslocamento em barras do grafico (derivado, p/ plot)
// v2.34: TF das LINHAS mutavel em runtime (botoes TF- / TF+). Comeca em
// Rtf(InpLineTF). Trocar o TF NAO reseta o replay: gReplayTime e um tempo
// ABSOLUTO, entao o indicador continua no mesmo instante e so muda o TF.
ENUM_TIMEFRAMES gLineTF=PERIOD_CURRENT;
ENUM_TIMEFRAMES gTFList[9]={PERIOD_M1,PERIOD_M5,PERIOD_M15,PERIOD_M30,
                            PERIOD_H1,PERIOD_H4,PERIOD_D1,PERIOD_W1,PERIOD_MN1};

//+------------------------------------------------------------------+
int CurIdx(string code){ for(int i=0;i<8;i++) if(cur[i]==code) return i; return -1; }
ENUM_TIMEFRAMES Rtf(ENUM_TIMEFRAMES tf){ return (tf==PERIOD_CURRENT)?(ENUM_TIMEFRAMES)_Period:tf; }
string TfStr(ENUM_TIMEFRAMES tf){ string s=EnumToString(Rtf(tf)); StringReplace(s,"PERIOD_",""); return s; }
double Clamp(double v,double lo,double hi){ return (v<lo?lo:(v>hi?hi:v)); }

//+------------------------------------------------------------------+
//| v2.34: tempo-ancora para os CopyClose. Ao vivo = tempo do bar 0  |
//| do grafico; em replay = gReplayTime (instante congelado). Todo o |
//| calculo passa a enxergar "agora" = essa ancora, entao a leitura  |
//| retrospectiva fica FIEL: a TMA nao "settla" com barras futuras e |
//| o ATR e medido em relacao aquele instante (nada do futuro entra).|
datetime AnchorTime()
{
   if(gReplayTime>0) return gReplayTime;
   datetime tt[];
   if(CopyTime(_Symbol,_Period,0,1,tt)==1) return tt[0];
   return 0;
}
//+------------------------------------------------------------------+
//| v2.35: LWMA(P) sobre o close (cl em serie, cl[0] = barra ancora). |
//| Peso P na barra i, 1 na mais antiga — identico ao MODE_LWMA do   |
//| MT4, que e o que o CSS original usa no ramo ignoreFuture=true.   |
void LWMA(const double &cl[], int copied, int P, double &out[])
{
   ArrayResize(out,copied); ArraySetAsSeries(out,true);
   if(P<1) P=1;
   double wsum=P*(P+1)/2.0;
   for(int i=0;i<copied;i++)
   {
      if(i+P>copied){ out[i]=0.0; continue; }
      double sum=0.0;
      for(int j=0;j<P;j++) sum+=cl[i+j]*(P-j);
      out[i]=sum/wsum;
   }
}
//+------------------------------------------------------------------+
//| v2.35: ATR(P) no estilo MT4 = MEDIA SIMPLES do True Range.       |
//| Deliberadamente nao usa iATR: o iATR do MQL5 aplica suavizacao   |
//| de Wilder e daria um numero diferente do indicador original.     |
//| Sai em unidades de preco (nao relativo) — o slope divide por ele.|
void ATRmt4(const double &hi[], const double &lo[], const double &cl[],
            int copied, int P, double &out[])
{
   ArrayResize(out,copied); ArraySetAsSeries(out,true);
   ArrayInitialize(out,0.0);
   if(P<1 || copied<P+2) return;

   double tr[]; ArrayResize(tr,copied); ArraySetAsSeries(tr,true);
   for(int i=0;i<copied-1;i++)
   {
      double h=MathMax(hi[i],cl[i+1]);
      double l=MathMin(lo[i],cl[i+1]);
      tr[i]=h-l;
   }
   tr[copied-1]=hi[copied-1]-lo[copied-1];

   double sum=0.0;
   for(int j=0;j<P;j++) sum+=tr[j];
   out[0]=sum/P;
   for(int i=1;i+P<=copied;i++)
   {
      sum+=tr[i+P-1]-tr[i-1];
      out[i]=sum/P;
   }
}
//+------------------------------------------------------------------+
//| v2.35: deslocamento do "addSundayToMonday" (so faz sentido no D1)|
int SunPad(ENUM_TIMEFRAMES tf)
{
   return (InpAddSunday && gSundayCandles && Rtf(tf)==PERIOD_D1) ? 1 : 0;
}
//+------------------------------------------------------------------+
//| v2.35: soma bruta dos slopes da moeda -> valor plotavel.         |
//| Media pelas ocorrencias (como o original), depois escala e clamp |
//| p/ caber na janela +/-InpScaleMax. Unico ponto onde a escala e   |
//| aplicada — painel, linhas, matriz e dpeso passam todos por aqui. |
double NormVal(int c, double acc)
{
   if(c<0 || c>7 || cnt[c]<=0) return 0.0;
   return Clamp((acc/cnt[c])*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
}
//+------------------------------------------------------------------+
//| calcTma — replica EXATA da TMA do CSS original (Paul Gernard).   |
//| Original (shift = posicao do candle):                            |
//|   sum  = close[shift]*21;  sumw = 21;                            |
//|   for(jnx=1,knx=20; jnx<=20; jnx++,knx--){                       |
//|     sum  += close[shift+jnx]*knx; sumw += knx;                   |
//|     if(jnx<=shift){ sum += close[shift-jnx]*knx; sumw += knx; }  |
//|   }                                                              |
//|   return sum/sumw;                                               |
//| cl em serie (cl[0]=atual). i faz o papel de "shift".            |
//| Param N mantido por compatibilidade; a janela fixa e 20 (peso21).|
void TMA(const double &cl[], int copied, int N, double &out[])
{
   ArrayResize(out,copied); ArraySetAsSeries(out,true);
   for(int i=0;i<copied;i++)   // i = shift (posicao do candle)
   {
      double dblSum  = cl[i]*21.0;
      double dblSumw = 21.0;
      for(int jnx=1, knx=20; jnx<=20; jnx++, knx--)
      {
         int back = i+jnx;              // close[shift+jnx] (mais antigo)
         if(back < copied){ dblSum += cl[back]*knx; dblSumw += knx; }
         if(jnx <= i)                   // close[shift-jnx] (mais recente)
         {
            int fwd = i-jnx;
            if(fwd >= 0){ dblSum += cl[fwd]*knx; dblSumw += knx; }
         }
      }
      out[i] = (dblSumw>0)? dblSum/dblSumw : cl[i];
   }
}
//+------------------------------------------------------------------+
//| v2.35: NUCLEO. Slope do CSS ORIGINAL para um par/TF, do indice 0 |
//| (barra ancora) ate need-1. EMPTY_VALUE onde nao deu p/ calcular. |
//|                                                                  |
//|   atr   = ATR(100)[shift+10] / 10                                |
//|   tma   = LWMA(21)[shift]                                        |
//|   prev  = (LWMA(21)[shift+1]*wsum + close[shift]*(P-1))          |
//|           / (wsum + P-1)         , wsum = P*(P+1)/2 = 231 p/ P=21|
//|   slope = (tma - prev) / atr                                     |
//|                                                                  |
//| Continua ancorado em AnchorTime(): em REPLAY/backtest nenhuma    |
//| barra posterior a ancora entra na conta.                         |
//+------------------------------------------------------------------+
bool PairSlopes(string sym, ENUM_TIMEFRAMES tf, int need, double &slope[])
{
   if(need<1) return false;
   ArrayResize(slope,need);
   ArrayInitialize(slope,EMPTY_VALUE);

   ENUM_TIMEFRAMES rtf=Rtf(tf);
   int pad=SunPad(rtf);

   // barras pedidas + deslocamento do ATR (10) + janela do ATR +
   // janela da LWMA/TMA + folga
   int W = need + pad + 12 + InpATRPeriod + (int)MathMax(InpMAPeriod,21) + 8;

   datetime anchor=AnchorTime();
   // SE_: durante o export ao vivo (gExportLive) ignora o InpSyncBars p/ cada TF
   // usar a propria barra atual; replay continua ancorando por tempo absoluto.
   bool useAnchor=((InpSyncBars && !gExportLive) || gReplayTime>0) && anchor>0;

   double cl[],hi[],lo[]; datetime tm[];
   ArraySetAsSeries(cl,true); ArraySetAsSeries(hi,true);
   ArraySetAsSeries(lo,true); ArraySetAsSeries(tm,true);

   int nc,nh,nl;
   if(useAnchor)
   {
      nc=CopyClose(sym,rtf,anchor,W,cl);
      nh=CopyHigh (sym,rtf,anchor,W,hi);
      nl=CopyLow  (sym,rtf,anchor,W,lo);
   }
   else
   {
      nc=CopyClose(sym,rtf,0,W,cl);
      nh=CopyHigh (sym,rtf,0,W,hi);
      nl=CopyLow  (sym,rtf,0,W,lo);
   }
   int copied=MathMin(nc,MathMin(nh,nl));
   if(copied < need+pad+12+InpATRPeriod) return false;

   if(pad>0)
   {
      int nt = useAnchor ? CopyTime(sym,rtf,anchor,need+pad,tm)
                         : CopyTime(sym,rtf,0,need+pad,tm);
      if(nt<need+pad) pad=0;      // sem os tempos, ignora o ajuste de domingo
   }

   double atr[]; ATRmt4(hi,lo,cl,copied,InpATRPeriod,atr);

   double ma[];
   if(InpIgnoreFuture) LWMA(cl,copied,InpMAPeriod,ma);
   else                TMA (cl,copied,InpMAPeriod,ma);

   double wsum = InpMAPeriod*(InpMAPeriod+1)/2.0;   // 231 quando P=21
   double wlst = InpMAPeriod-1.0;                   //  20 quando P=21

   int ok=0;
   for(int k=0;k<need;k++)
   {
      int kk=k;
      if(pad>0)
      {
         MqlDateTime st; TimeToStruct(tm[k],st);
         if(st.day_of_week==0) kk=k+1;              // addSundayToMonday
      }
      if(kk+10>=copied || kk+1>=copied) break;

      double a=atr[kk+10]/10.0;
      if(a<=0.0) continue;

      double dblTma,dblPrev;
      if(InpIgnoreFuture)
      {
         if(ma[kk]==0.0 || ma[kk+1]==0.0) continue;
         dblTma  = ma[kk];
         dblPrev = (ma[kk+1]*wsum + cl[kk]*wlst)/(wsum+wlst);
      }
      else
      {
         dblTma  = ma[kk];
         dblPrev = ma[kk+1];
      }
      slope[k]=(dblTma-dblPrev)/a;
      ok++;
   }
   return (ok>0);
}
//+------------------------------------------------------------------+
//| Valor de forca por moeda na barra de shift k p/ um TF.           |
//| k=0: barra em formacao (painel legado). k>=1: barra FECHADA —    |
//| e o que a camada de peso do v2.30 usa (sem repaint).             |
int ComputeAt(ENUM_TIMEFRAMES tf, int kShift, double &out[])
{
   double acc[8]; ArrayInitialize(acc,0);
   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      double sl[];
      if(!PairSlopes(gPair[p],tf,kShift+1,sl)) continue;
      if(sl[kShift]==EMPTY_VALUE) continue;
      acc[gBaseIdx[p]]  += sl[kShift];   // moeda base:  + slope
      acc[gQuoteIdx[p]] -= sl[kShift];   // moeda quote: - slope
      good++;
   }
   for(int c=0;c<8;c++) out[c]=NormVal(c,acc[c]);
   return good;
}
int ComputeNow(ENUM_TIMEFRAMES tf, double &out[]) { return ComputeAt(tf,0,out); }
//+------------------------------------------------------------------+
//| v2.39: MESMO calculo do ComputeAt, mas SEM o clamp. As LINHAS     |
//| continuam clampadas (precisam caber na janela); o PAINEL passa a  |
//| mostrar o valor real. Antes, com quatro moedas no teto +/-0.98, a |
//| coluna ang media a aproximacao do teto, nao a inclinacao.         |
//+------------------------------------------------------------------+
int ComputeAtRaw(ENUM_TIMEFRAMES tf, int kShift, double &out[])
{
   double acc[8]; ArrayInitialize(acc,0);
   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      double sl[];
      if(!PairSlopes(gPair[p],tf,kShift+1,sl)) continue;
      if(sl[kShift]==EMPTY_VALUE) continue;
      acc[gBaseIdx[p]]  += sl[kShift];
      acc[gQuoteIdx[p]] -= sl[kShift];
      good++;
   }
   for(int c=0;c<8;c++)
      out[c] = (cnt[c]>0)? (acc[c]/cnt[c])*InpScale : 0.0;
   return good;
}
//+------------------------------------------------------------------+
//| v2.33: valor de slope POR PAR p/ a aba MATRIZ.                   |
//| Replica passo a passo o corpo por-par do ComputeAt (mesmo W,     |
//| mesma ancora, mesmo norm/TMA/z/clamp) — so NAO agrega na cesta.  |
//| pv[p] = valor do par gPair[p] orientado base->quote.             |
//| ComputeAt fica intocado (contrato v2.32 preservado).             |
int ComputePairVals(ENUM_TIMEFRAMES tf, int kShift, double &pv[], bool &pok[])
{
   ArrayResize(pv,gPairsN); ArrayResize(pok,gPairsN);
   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      pv[p]=0.0; pok[p]=false;
      double sl[];
      if(!PairSlopes(gPair[p],tf,kShift+1,sl)) continue;
      if(sl[kShift]==EMPTY_VALUE) continue;
      pv[p]=Clamp(sl[kShift]*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
      pok[p]=true; good++;
   }
   return good;
}
//+------------------------------------------------------------------+
//| v2.32: setas de direcao por moeda p/ um TF (barras FECHADAS).    |
//| dir[c] = +1 subindo, -1 caindo, 0 lateral (delta em k barras).   |
//| Junto com a cor da celula (posicao vs box) isso forma a leitura  |
//| do CICLO a19: verde+cima=FORCA, verde+baixo=EXAUSTAO,            |
//| cinza/verm+baixo=FRAQUEZA, cinza+cima=EXPANSAO. Descricao, nao   |
//| sinal: so 13-15% dos ciclos completam; ~40% e falsa exaustao.    |
//| Substitui os simbolos de peso + - ! ~ (a13/a13b: NULOS).         |
bool PhaseDir(ENUM_TIMEFRAMES tf, int &dir[])
{
   double Vn[8], Vp[8];
   int g1=ComputeAt(tf,1,Vn);                 // ultima barra fechada
   int g2=ComputeAt(tf,1+InpPesoK,Vp);        // k barras fechadas atras
   if(g1<1 || g2<1){ for(int c=0;c<8;c++) dir[c]=0; return false; }
   for(int c=0;c<8;c++)
   {
      double d=Vn[c]-Vp[c];
      dir[c]=(d>0)?1:((d<0)?-1:0);
   }
   return true;
}
//+------------------------------------------------------------------+
// Detecta moedas do par atual para modo linha unica
void GetPairCurrencies(int &iBase, int &iQuote)
{
   iBase  = CurIdx(SymbolInfoString(_Symbol, SYMBOL_CURRENCY_BASE));
   iQuote = CurIdx(SymbolInfoString(_Symbol, SYMBOL_CURRENCY_PROFIT));
}

// Determina indice de cor (0-5) pelo estado do slope (estilo CSS original):
// 0=Up acelerando, 1=Up desacelerando(exaustao), 2=Dn acelerando,
// 3=Dn desacelerando(exaustao), 4=Mid subindo, 5=Mid descendo.
int ColorState(double v, double vPrev)
{
   double trg=InpTrigger;
   // paleta plot9: 0=Lime(alta acel) 1=Green(alta desacel/exaustao)
   // 2=Red(baixa acel) 3=FireBrick(baixa desacel) 4=Teal(box sobe) 5=HotPink(box desce)
   if(v > trg)        return (v < vPrev) ? 1 : 0;
   else if(v < -trg)  return (v < vPrev) ? 2 : 3;
   else               return (v < vPrev) ? 5 : 4;
}

void Fill(double &buf[],int c,int kbars,int total,const double &S[])
{
   // Limpa o buffer da moeda
   for(int idx=0;idx<total;idx++) buf[idx]=EMPTY_VALUE;

   // No modo single, as 8 linhas de moeda ficam ocultas
   if(gSingle) return;

   // Modo 8 linhas normal
   if(cnt[c]<=0) return;
   if(gHide[c]) return;
   // v2.34: desloca o plot por gReplayBars — o "agora" do replay cai na
   // barra do cursor e nada e desenhado a direita dela (sem futuro).
   for(int k=0;k<kbars;k++)
   {
      int idx=total-1-gReplayBars-k; if(idx<0) break;
      buf[idx]=NormVal(c,S[c*kbars+k]);   // v2.35: media + escala + clamp
   }
}

// Preenche o plot dedicado do PAR (modo single)
void FillPar(int kbars,int total,const double &S[])
{
   for(int idx=0;idx<total;idx++){ Bpar[idx]=EMPTY_VALUE; ColPar[idx]=0; }
   if(!gSingle) return;

   int iBase=-1, iQuote=-1;
   GetPairCurrencies(iBase,iQuote);
   if(iBase<0 || iQuote<0) return;          // par fora do G8 -> vazio
   if(cnt[iBase]<=0 || cnt[iQuote]<=0) return;

   double prevVal=0; bool first=true;
   for(int k=kbars-1;k>=0;k--)
   {
      int idx=total-1-gReplayBars-k; if(idx<0) continue;  // v2.34: offset replay
      double vb=NormVal(iBase ,S[iBase *kbars+k]);
      double vq=NormVal(iQuote,S[iQuote*kbars+k]);
      double val=Clamp(vb-vq,-(InpScaleMax-0.02),(InpScaleMax-0.02));
      Bpar[idx]=val;
      ColPar[idx]=ColorState(val, first?val:prevVal);
      prevVal=val; first=false;
   }
}
// v2.30: preenche os buffers 10..17 com dpeso = |val_t| - |val_{t-k}|
// no TF das linhas. A barra 0 (em formacao) tambem recebe valor — por
// isso consumidores via iCustom DEVEM ler com shift>=1 (documentado).
void FillDpeso(int kbars,int total,const double &S[])
{
   for(int idx=0;idx<total;idx++)
   { D0[idx]=EMPTY_VALUE; D1s[idx]=EMPTY_VALUE; D2[idx]=EMPTY_VALUE;
     D3[idx]=EMPTY_VALUE; D4[idx]=EMPTY_VALUE; D5[idx]=EMPTY_VALUE;
     D6[idx]=EMPTY_VALUE; D7[idx]=EMPTY_VALUE; }
   for(int c=0;c<8;c++)
   {
      for(int k=0;k<kbars;k++)
      {
         int idx=total-1-gReplayBars-k; if(idx<0) break;  // v2.34: offset replay
         double v=EMPTY_VALUE;
         if(cnt[c]>0 && k+InpPesoK<kbars)
            v=MathAbs(NormVal(c,S[c*kbars+k]))-MathAbs(NormVal(c,S[c*kbars+k+InpPesoK]));
         switch(c)
         {
            case 0: D0[idx]=v;  break; case 1: D1s[idx]=v; break;
            case 2: D2[idx]=v;  break; case 3: D3[idx]=v;  break;
            case 4: D4[idx]=v;  break; case 5: D5[idx]=v;  break;
            case 6: D6[idx]=v;  break; case 7: D7[idx]=v;  break;
         }
      }
   }
}
//+------------------------------------------------------------------+
bool ComputeSeries()
{
   int total=ArraySize(B0);
   if(total<InpMAPeriod+InpATRPeriod+16 || gPairsN<1) return false;
   int kbars=MathMin(InpBars,total-2);
   double S[]; ArrayResize(S,8*kbars); ArrayInitialize(S,0);
   int good=0;
   ENUM_TIMEFRAMES tf=gLineTF;   // v2.34: TF mutavel (botoes TF- / TF+)

   // v2.35: a serie inteira sai do mesmo nucleo que o painel e a matriz.
   // A ancora temporal (backtest/REPLAY) vive dentro de PairSlopes, entao
   // o comportamento retrospectivo continua identico ao da v2.34.
   for(int p=0;p<gPairsN;p++)
   {
      double sl[];
      if(!PairSlopes(gPair[p],tf,kbars,sl)) continue;
      good++;
      int bi=gBaseIdx[p], qi=gQuoteIdx[p];
      for(int k=0;k<kbars;k++)
      {
         if(sl[k]==EMPTY_VALUE) continue;
         S[bi*kbars+k]+=sl[k]; S[qi*kbars+k]-=sl[k];
      }
   }
   Fill(B0,0,kbars,total,S); Fill(B1,1,kbars,total,S);
   Fill(B2,2,kbars,total,S); Fill(B3,3,kbars,total,S);
   Fill(B4,4,kbars,total,S); Fill(B5,5,kbars,total,S);
   Fill(B6,6,kbars,total,S); Fill(B7,7,kbars,total,S);
   FillPar(kbars,total,S);
   FillDpeso(kbars,total,S);
   return (good>=MathMax(1,gPairsN/2));
}
//+------------------------------------------------------------------+
void Lbl(string nm,int win,int x,int y,string txt,color cl)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_LABEL,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
   ObjectSetString (0,nm,OBJPROP_TEXT,txt);
   ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,InpFont);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,cl);
   ObjectSetInteger(0,nm,OBJPROP_BACK,false);
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}
// v2.37: label com tamanho de fonte proprio (o painel novo usa fonte maior)
void LblF(string nm,int win,int x,int y,string txt,color cl,int fs,string fnt="Consolas")
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_LABEL,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_LEFT_UPPER);
   ObjectSetString (0,nm,OBJPROP_TEXT,txt);
   ObjectSetString (0,nm,OBJPROP_FONT,fnt);
   ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,fs);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,cl);
   ObjectSetInteger(0,nm,OBJPROP_BACK,false);
   ObjectSetInteger(0,nm,OBJPROP_ZORDER,30);      // v2.39: prioridade de clique
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}
// v2.37: botao do painel novo (moeda / TODAS)
void BtnP(string nm,int win,int x,int y,int w,int h,string txt,
          color bg,color fg,int fs)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_BUTTON,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,nm,OBJPROP_YSIZE,h);
   ObjectSetString (0,nm,OBJPROP_TEXT,txt);
   ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,fs);
   ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,fg);
   ObjectSetInteger(0,nm,OBJPROP_BORDER_COLOR,bg);
   ObjectSetInteger(0,nm,OBJPROP_STATE,false);
   ObjectSetInteger(0,nm,OBJPROP_BACK,false);
   ObjectSetInteger(0,nm,OBJPROP_ZORDER,50);        // v2.39: prioridade de clique (o topo VISUAL vem da ordem de criacao)
}
// v2.33: borda parametrizavel (default = comportamento v2.32). Celulas
// internas passam borda = fundo (visual chapado, estilo CSSM).
void Rect(string nm,int win,int x,int y,int w,int hgt,color bg,color border=C'80,80,90',int zo=0)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_RECTANGLE_LABEL,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,nm,OBJPROP_YSIZE,hgt);
   ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,nm,OBJPROP_BORDER_TYPE,BORDER_FLAT);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,border);
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,nm,OBJPROP_BACK,false);
   ObjectSetInteger(0,nm,OBJPROP_ZORDER,zo);        // v2.39
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}
//+------------------------------------------------------------------+
void HLine(string nm,int win,double price,color cl,int w)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_HLINE,win,0,price);
   ObjectSetDouble (0,nm,OBJPROP_PRICE,price);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,cl);
   ObjectSetInteger(0,nm,OBJPROP_WIDTH,w);
   ObjectSetInteger(0,nm,OBJPROP_STYLE,STYLE_SOLID);
   ObjectSetInteger(0,nm,OBJPROP_BACK,true);
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}
// v2.34: cria/atualiza um botao generico (usado pela barra de REPLAY).
void MkBtn(string nm,int win,int x,int w,int y,string txt)
{
   if(ObjectFind(0,nm)<0)
   {
      ObjectCreate(0,nm,OBJ_BUTTON,win,0,0);
      ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
      ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,8);
      ObjectSetInteger(0,nm,OBJPROP_COLOR,clrWhite);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,C'50,50,65');
      ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
   }
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,nm,OBJPROP_YSIZE,18);
   ObjectSetString (0,nm,OBJPROP_TEXT,txt);
   ObjectSetInteger(0,nm,OBJPROP_STATE,false);
}
void DrawBtn(int win)
{
   string nm = PFX+"btnSingle";
   if(ObjectFind(0,nm)<0)
   {
      ObjectCreate(0,nm,OBJ_BUTTON,win,0,0);
      ObjectSetInteger(0,nm,OBJPROP_CORNER,   CORNER_LEFT_UPPER);
      ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,6);
      ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,4);
      ObjectSetInteger(0,nm,OBJPROP_XSIZE,    90);
      ObjectSetInteger(0,nm,OBJPROP_YSIZE,    18);
      ObjectSetString (0,nm,OBJPROP_FONT,     "Consolas");
      ObjectSetInteger(0,nm,OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
   }
   // Botao RESET (limpa moedas ocultas)
   string rn=PFX+"btnReset";
   if(ObjectFind(0,rn)<0)
   {
      ObjectCreate(0,rn,OBJ_BUTTON,win,0,0);
      ObjectSetInteger(0,rn,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,rn,OBJPROP_XDISTANCE,150);
      ObjectSetInteger(0,rn,OBJPROP_YDISTANCE,4);
      ObjectSetInteger(0,rn,OBJPROP_XSIZE,70);
      ObjectSetInteger(0,rn,OBJPROP_YSIZE,18);
      ObjectSetString (0,rn,OBJPROP_FONT,"Consolas");
      ObjectSetInteger(0,rn,OBJPROP_FONTSIZE,8);
      ObjectSetInteger(0,rn,OBJPROP_COLOR,clrWhite);
      ObjectSetInteger(0,rn,OBJPROP_BGCOLOR,C'70,40,40');
      ObjectSetString (0,rn,OBJPROP_TEXT,"[ RESET ]");
      ObjectSetInteger(0,rn,OBJPROP_SELECTABLE,false);
   }

   // v2.33: botao MTX (aba matriz por par) — mesma infra do CSSM v1.40
   if(InpMatrix)
   {
      string nx=PFX+"btnMtx";
      if(ObjectFind(0,nx)<0)
      {
         ObjectCreate(0,nx,OBJ_BUTTON,win,0,0);
         ObjectSetInteger(0,nx,OBJPROP_CORNER,CORNER_LEFT_UPPER);
         ObjectSetInteger(0,nx,OBJPROP_XDISTANCE,228);
         ObjectSetInteger(0,nx,OBJPROP_YDISTANCE,4);
         ObjectSetInteger(0,nx,OBJPROP_XSIZE,52);
         ObjectSetInteger(0,nx,OBJPROP_YSIZE,18);
         ObjectSetString (0,nx,OBJPROP_FONT,"Consolas");
         ObjectSetInteger(0,nx,OBJPROP_FONTSIZE,8);
         ObjectSetInteger(0,nx,OBJPROP_SELECTABLE,false);
      }
      ObjectSetString (0,nx,OBJPROP_TEXT,"[ MTX ]");
      if(gMtx)
      {
         ObjectSetInteger(0,nx,OBJPROP_COLOR,clrBlack);
         ObjectSetInteger(0,nx,OBJPROP_BGCOLOR,clrGoldenrod);
      }
      else
      {
         ObjectSetInteger(0,nx,OBJPROP_COLOR,clrWhite);
         ObjectSetInteger(0,nx,OBJPROP_BGCOLOR,C'50,50,65');
         ObjectSetInteger(0,nx,OBJPROP_STATE,false);
      }
   }

   if(gSingle)
   {
      ObjectSetString (0,nm,OBJPROP_TEXT,   "[ PAR (1 LINHA) ]");
      ObjectSetInteger(0,nm,OBJPROP_COLOR,  clrBlack);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,clrLimeGreen);
   }
   else
   {
      ObjectSetString (0,nm,OBJPROP_TEXT,   "[ 8 LINHAS ]");
      ObjectSetInteger(0,nm,OBJPROP_COLOR,  clrWhite);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,C'50,50,65');
   }

   // v2.34: barra de REPLAY (2a linha) — retrocede/avanca o instante.
   if(InpReplay)
   {
      int ry=26;
      MkBtn(PFX+"rvBB",  win,  6,34,ry,"[<<]");
      MkBtn(PFX+"rvB",   win, 44,28,ry,"[<]");
      MkBtn(PFX+"rvLive",win, 76,52,ry,"[LIVE]");
      MkBtn(PFX+"rvF",   win,132,28,ry,"[>]");
      MkBtn(PFX+"rvFF",  win,164,34,ry,"[>>]");
      bool live=(gReplayTime<=0);
      ObjectSetInteger(0,PFX+"rvLive",OBJPROP_COLOR,  live?clrBlack:clrWhite);
      ObjectSetInteger(0,PFX+"rvLive",OBJPROP_BGCOLOR,live?clrLimeGreen:C'50,50,65');
      string st = live ? "AO VIVO"
                       : StringFormat("REPLAY %s  (-%d barras)",
                         TimeToString(gReplayTime,TIME_DATE|TIME_MINUTES), gReplayBars);
      Lbl(PFX+"rvLbl",win,204,ry+4, st, live?C'150,150,150':clrGold);
   }

   // v2.34: troca do TF das LINHAS (3a linha) — nao reseta o replay.
   {
      int ty=48;
      MkBtn(PFX+"tfDn",win,  6,44,ty,"[ TF- ]");
      MkBtn(PFX+"tfUp",win, 52,44,ty,"[ TF+ ]");
      Lbl(PFX+"tfLbl",win,104,ty+4,"linhas: "+TfStr(gLineTF),clrGold);
   }
}

void DrawBox(int win)
{
   HLine(PFX+"bxhi", win,  InpBox,     clrForestGreen, 2);
   HLine(PFX+"bxlo", win, -InpBox,     clrFireBrick,   2);
   HLine(PFX+"bxmid",win,  0.0,        C'70,70,80',    1);
   // Linhas pontilhadas cinza em +/-InpExtLevel (0.50 por padrao).
   // LIGADAS por padrao desde a v2.35 — sao referencia VISUAL de escala.
   // Lembrete do a19 Q1b: 0.50 nao tem base empirica como nivel de
   // exaustao (a transicao real fica perto de ~0.17), entao nao usar
   // o toque nessas linhas como gatilho.
   if(InpShowExt)
   {
      if(ObjectFind(0,PFX+"exhi")<0) ObjectCreate(0,PFX+"exhi",OBJ_HLINE,win,0, InpExtLevel);
      ObjectSetDouble (0,PFX+"exhi",OBJPROP_PRICE, InpExtLevel);
      ObjectSetInteger(0,PFX+"exhi",OBJPROP_COLOR, clrDimGray);
      ObjectSetInteger(0,PFX+"exhi",OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0,PFX+"exhi",OBJPROP_WIDTH, 1);
      ObjectSetInteger(0,PFX+"exhi",OBJPROP_SELECTABLE,false);
      if(ObjectFind(0,PFX+"exlo")<0) ObjectCreate(0,PFX+"exlo",OBJ_HLINE,win,0,-InpExtLevel);
      ObjectSetDouble (0,PFX+"exlo",OBJPROP_PRICE,-InpExtLevel);
      ObjectSetInteger(0,PFX+"exlo",OBJPROP_COLOR, clrDimGray);
      ObjectSetInteger(0,PFX+"exlo",OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0,PFX+"exlo",OBJPROP_WIDTH, 1);
      ObjectSetInteger(0,PFX+"exlo",OBJPROP_SELECTABLE,false);
   }
   else
   {
      if(ObjectFind(0,PFX+"exhi")>=0) ObjectDelete(0,PFX+"exhi");
      if(ObjectFind(0,PFX+"exlo")>=0) ObjectDelete(0,PFX+"exlo");
   }
}
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| v2.32: horizonte REAL da TMA(20) por TF (licao WM_HOURS v1.41).  |
//| 20 barras de H1 = 20h; de D1 = 20d — colunas nao sao comparaveis |
//| sem esse rotulo.                                                 |
string HorizonStr(ENUM_TIMEFRAMES tf)
{
   long sec=(long)PeriodSeconds(Rtf(tf))*InpMAPeriod;
   long h=sec/3600;
   if(h<72)        return StringFormat("%dh",(int)h);
   long d=h/24;
   if(d<90)        return StringFormat("%dd",(int)d);
   long m=(long)MathRound((double)d/30.0);
   return StringFormat("%dm",(int)m);
}
//+------------------------------------------------------------------+
void DrawCol(int win,int x,int y,int rh,int colW,ENUM_TIMEFRAMES tf,const double &V[],const int &dir[],string cid)
{
   int ord[8]; for(int i=0;i<8;i++) ord[i]=i;
   for(int i=0;i<7;i++) for(int j=i+1;j<8;j++)
      if(V[ord[j]]>V[ord[i]]){ int t=ord[i]; ord[i]=ord[j]; ord[j]=t; }
   double spread = V[ord[0]] - V[ord[7]]; // distancia forte-fraca
   bool trend = (V[ord[0]]>InpBox && V[ord[7]]<-InpBox);
   bool hasGas = (spread >= InpDiffThr);  // regra de ouro: precisa de distancia
   string mark = (trend && hasGas) ? " >>" : (trend ? " >" : "");
   // header com horizonte real da TMA (v2.31/WM_HOURS); cinza como os
   // cabecalhos de coluna do CSSM, ouro quando ha trend+distancia
   Lbl(PPFX+cid+"h",win,x,y, TfStr(tf)+ShortToString(0x00B7)+HorizonStr(tf)+mark,
       (trend&&hasGas)?clrGold:C'150,150,150');
   string up=ShortToString(0x25B2), dn=ShortToString(0x25BC); // seta cima/baixo
   for(int r=0;r<8;r++)
   {
      int c=ord[r];
      // celula colorida pela posicao vs box (box 0.20 VALIDADA no a19 Q5)
      color cellBg;
      if(V[c]>= InpBox)      cellBg=C'18,64,28';   // verde  = forca
      else if(V[c]<=-InpBox) cellBg=C'78,22,22';   // vermelho = fraqueza
      else                   cellBg=C'38,38,46';   // cinza  = dentro da box
      if(gHide[c])           cellBg=C'30,30,34';
      // celula chapada (borda = fundo, estilo CSSM)
      Rect(PPFX+cid+"cell"+(string)r,win,x-2,y+rh*(r+1)-1,colW-4,rh-1,cellBg,cellBg);
      // barra de forca proporcional (|V| / ScaleMax) na base da celula
      int wmax=colW-8;
      int wbar=(int)MathRound(wmax*MathMin(MathAbs(V[c])/InpScaleMax,1.0));
      color barc=(V[c]>=0)?C'70,190,90':C'220,90,80';
      if(gHide[c]) barc=C'70,70,70';
      Rect(PPFX+cid+"bar"+(string)r,win,x,y+rh*(r+1)+rh-4,MathMax(wbar,1),2,barc,barc);
      // seta de direcao (k=3 barras fechadas; leitura do ciclo a19)
      string ar=(dir[c]>0)?up:((dir[c]<0)?dn:ShortToString(0x00B7));
      color shown = gHide[c] ? C'90,90,90' : colArr[c];
      string vis  = gHide[c] ? " (off)" : "";
      string lblName=PPFX+cid+(string)r;
      Lbl(lblName,win,x,y+rh*(r+1),
          StringFormat("%-3s %+5.2f %s%s",cur[c],V[c],ar,vis), shown);
      if(cid=="a")
      {
         gRowCur[r]=c;  // mapeia linha -> moeda
         ObjectSetInteger(0,lblName,OBJPROP_SELECTABLE,true);  // permite clique
         ObjectSetInteger(0,lblName,OBJPROP_SELECTED,false);
      }

   }
}
//+------------------------------------------------------------------+
//| v2.36 - ESTADO por magnitude. Ver cabecalho do arquivo.           |
//+------------------------------------------------------------------+
string EstadoStr(double v, double dAbs, color &cor)
{
   bool fora = (MathAbs(v) >= InpBox);
   if(fora && dAbs >  0){ cor=C'90,200,130'; return "EXPANSAO"; }
   if(fora && dAbs <= 0){ cor=C'230,180,90'; return "EXAUSTAO"; }
   if(!fora && dAbs > 0){ cor=C'150,150,160'; return "NEUTRA";  }
   cor=C'130,110,110';                        return "FRAQUEZA";
}
//+------------------------------------------------------------------+
void DrawPanelMoeda()
{
   if(!InpPanel) return;
   int win=ChartWindowFind(); if(win<0) return;

   // v2.39: valores SEM clamp (o painel mostra o real; a linha e que e clampada)
   double Vn[8], Vp[8];
   int g1=ComputeAtRaw(gLineTF,1,Vn);
   int g2=ComputeAtRaw(gLineTF,1+InpPesoK,Vp);
   if(g1<1 || g2<1) return;
   double lim=InpScaleMax-0.02;      // onde a LINHA satura

   ENUM_TIMEFRAMES mtf[4]; mtf[0]=InpTF2; mtf[1]=InpTF3; mtf[2]=InpTF4; mtf[3]=InpTF5;
   int mdir[4][8];
   for(int j=0;j<4;j++)
   {
      double A[8], B[8];
      int ga=ComputeAtRaw(mtf[j],1,A), gb=ComputeAtRaw(mtf[j],1+InpPesoK,B);
      for(int c=0;c<8;c++)
      {
         double d=(ga<1||gb<1)? 0.0 : (MathAbs(A[c])-MathAbs(B[c]));
         mdir[j][c]=(d>0)?1:((d<0)?-1:0);
      }
   }

   int ord[8]; for(int i=0;i<8;i++) ord[i]=i;
   for(int i=0;i<7;i++) for(int j2=i+1;j2<8;j2++)
      if(MathAbs(Vn[ord[j2]])>MathAbs(Vn[ord[i]])){ int t=ord[i]; ord[i]=ord[j2]; ord[j2]=t; }

   color BG      = InpNeon ? C'10,12,18'   : C'24,24,32';
   color BORDA   = InpNeon ? C'0,200,225'  : C'80,80,90';
   color ACC     = InpNeon ? C'0,200,225'  : C'150,150,150';
   color ROW_A   = InpNeon ? C'15,18,26' : C'38,38,46';
   color ROW_B   = InpNeon ? C'19,23,33' : C'38,38,46';
   color TXT     = C'225,230,238';
   color TXT_DIM = C'120,132,150';
   color TRACK   = C'28,32,44';

   int fs=InpFontPainel; if(fs<8) fs=8;
   int chpx=(fs*3)/4; if(chpx<6) chpx=6;
   int rh=fs+16;
   int pad=12, gap=3*chpx;                     // v2.39: respiro entre colunas

   int xBtn=pad,              wBtn=7*chpx;
   int xGau=xBtn+wBtn+gap,    wGau=12*chpx;
   int xPos=xGau+wGau+gap,    wPos=8*chpx;
   int xAng=xPos+wPos,        wAng=8*chpx;
   int xEst=xAng+wAng+gap/2,  wEst=11*chpx;
   int xMtf=xEst+wEst+gap,    wCel=4*chpx;
   int colW=xMtf+4*wCel+pad;
   int hHdr=rh+10;
   int hTot=hHdr+rh+rh*8+rh+10;

   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int x=cw-InpPanelX-colW+6; if(x<6) x=6;
   int y=InpPanelY;

   Rect(PPFX+"bg",win,x,y,colW,hTot,BG,BORDA,0);
   Rect(PPFX+"hdbar",win,x+1,y+1,colW-2,hHdr-3,InpNeon?C'14,18,28':C'38,38,46',
        InpNeon?C'14,18,28':C'38,38,46',1);
   Rect(PPFX+"hdline",win,x+1,y+hHdr-2,colW-2,2,ACC,ACC,2);
   LblF(PPFX+"hd",win,x+pad,y+6,"CSS "+ShortToString(0x00B7)+" POR MOEDA",ACC,fs+1);

   // v2.39: TODAS foi para a BARRA DE TITULO (antes colidia com o cabecalho FORCA)
   int wAll=8*chpx;
   BtnP(PPFX+"btnAll",win,x+colW-pad-wAll,y+5,wAll,rh-8,"TODAS",
        (gSolo<0)?C'26,32,44':C'0,200,225',(gSolo<0)?TXT_DIM:C'8,12,18',fs-2);
   LblF(PPFX+"hd2",win,x+colW-pad-wAll-13*chpx,y+8,
        StringFormat("%s  box %.2f",TfStr(gLineTF),InpBox),TXT_DIM,fs-2);

   int yB=y+hHdr+2;
   LblF(PPFX+"chdM",win,x+xBtn,yB+3,"MOEDA",TXT_DIM,fs-3);
   LblF(PPFX+"chd0",win,x+xGau,yB+3,"FORCA",TXT_DIM,fs-3);
   LblF(PPFX+"chd1",win,x+xPos,yB+3,"POS",TXT_DIM,fs-3);
   LblF(PPFX+"chd2",win,x+xAng,yB+3,"ANG",TXT_DIM,fs-3);
   LblF(PPFX+"chd3",win,x+xEst,yB+3,"ESTADO",TXT_DIM,fs-3);
   for(int j=0;j<4;j++)
      LblF(PPFX+"chm"+(string)j,win,x+xMtf+j*wCel,yB+3,TfStr(mtf[j]),TXT_DIM,fs-3);

   string up=ShortToString(0x25B2), dn=ShortToString(0x25BC), mid=ShortToString(0x00B7);
   int y0=yB+rh;

   // v2.40 — DUAS PASSADAS. No MQL5 o empilhamento visual segue a ORDEM DE
   // CRIACAO dos objetos (OBJPROP_ZORDER e prioridade de CLIQUE, nao de
   // desenho). Desenhando fundo+conteudo linha a linha, o botao da linha 0
   // nascia ANTES do retangulo da linha 1 — e quando a ordenacao mudava
   // (troca de TF) aquela moeda migrava para baixo de um retangulo criado
   // depois e SUMIA. Agora: todos os fundos primeiro, todo o conteudo depois.
   for(int r=0;r<8;r++)
   {
      int c=ord[r];
      gRowCur[r]=c;
      int yy=y0+rh*r;
      bool solo=(gSolo==c), off=gHide[c];
      color rowBg = solo ? (InpNeon?C'22,40,52':C'38,38,46') : ((r%2==0)?ROW_A:ROW_B);
      if(off && !solo) rowBg=C'14,15,19';
      Rect(PPFX+"row"+(string)r,win,x+1,yy,colW-2,rh-1,rowBg,solo?ACC:rowBg,5);
      Rect(PPFX+"stp"+(string)r,win,x+3,yy+3,4,rh-7,
           off?C'50,54,62':colArr[c], off?C'50,54,62':colArr[c],6);
      Rect(PPFX+"trk"+(string)r,win,x+xGau,yy+rh/2-4,wGau,7,TRACK,TRACK,6);
   }

   for(int r=0;r<8;r++)
   {
      int c=ord[r];
      int yy=y0+rh*r;
      double v=Vn[c], dAbs=MathAbs(Vn[c])-MathAbs(Vp[c]);
      bool sat=(MathAbs(v)>lim);
      color cEstado; string est=EstadoStr(v,dAbs,cEstado);
      bool solo=(gSolo==c), off=gHide[c];

      int wfill=(int)MathRound(wGau*MathMin(MathAbs(v)/InpScaleMax,1.0));
      if(wfill<2) wfill=2;
      color barc = off?C'60,64,72' : ((v>=0)?C'60,220,150':C'240,110,110');
      Rect(PPFX+"gau"+(string)r,win,x+xGau,yy+rh/2-4,wfill,7,barc,barc,7);
      Rect(PPFX+"chip"+(string)r,win,x+xEst-4,yy+4,wEst,rh-9,
           off?C'40,44,52':cEstado, off?C'40,44,52':cEstado,6);

      LblF(PPFX+"po"+(string)r,win,x+xPos,yy+6,
           StringFormat("%+6.2f%s",v,sat?"*":""), off?C'80,86,96':TXT,fs-1);
      LblF(PPFX+"an"+(string)r,win,x+xAng,yy+6,StringFormat("%+6.2f",dAbs),
           off?C'80,86,96':((dAbs>0)?C'90,220,160':C'240,130,120'),fs-1);
      LblF(PPFX+"es"+(string)r,win,x+xEst,yy+6,est,C'10,14,20',fs-3);

      for(int j=0;j<4;j++)
      {
         string a=(mdir[j][c]>0)?up:((mdir[j][c]<0)?dn:mid);
         color ac = off?C'80,86,96' : ((mdir[j][c]>0)?C'70,215,150':
                    ((mdir[j][c]<0)?C'240,120,110':C'90,100,116'));
         LblF(PPFX+"m"+(string)r+"_"+(string)j,win,x+xMtf+j*wCel+wCel/4,yy+6,a,ac,fs-2);
      }

      // botao por ULTIMO: nasce depois de todo retangulo, entao fica sempre
      // por cima, qualquer que seja a ordenacao
      BtnP(PPFX+"btn"+(string)c,win,x+xBtn,yy+3,wBtn,rh-7,cur[c],
           solo?C'0,150,175':C'24,29,40', off?C'80,86,96':colArr[c], fs-1);
   }

   LblF(PPFX+"lg",win,x+pad,y0+rh*8+3,
        "* = linha no teto (valor real exibido) "+ShortToString(0x00B7)+
        " leitura, nao sinal",TXT_DIM,fs-4);
}
//+------------------------------------------------------------------+
void DrawPanel(const double &V1[],const double &V2[],const double &V3[],
               const double &V4[],const double &V5[])
{
   if(!InpPanel) return;
   int win=ChartWindowFind(); if(win<0) return;
   int rh=InpFont+9, colW=94, yTop=InpPanelY;
   int y=yTop+rh;                 // v2.33: linha de titulo acima das colunas
   int panelW=colW*5+12;
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   // Ancora pela direita. Se nao couber, fica preso na borda esquerda.
   int x=cw-InpPanelX-panelW+6; if(x<6) x=6;
   Rect(PPFX+"bg",win,x-6,yTop-6, panelW, rh*12+12, C'24,24,32');
   // titulo no estilo do cabecalho do CSSM
   Lbl(PPFX+"hd",win,x,yTop,
       StringFormat("CSS FORCA (TMA)  linhas:%s  box:%.2f",
                    TfStr(gLineTF),InpBox), clrWhiteSmoke);
   // v2.32: setas de direcao por TF (barras fechadas, sem repaint)
   int d1[8],d2[8],d3[8],d4[8],d5[8];
   PhaseDir(Rtf(InpTF1),d1); PhaseDir(Rtf(InpTF2),d2);
   PhaseDir(Rtf(InpTF3),d3); PhaseDir(Rtf(InpTF4),d4);
   PhaseDir(Rtf(InpTF5),d5);
   DrawCol(win,x,            y,rh,colW,InpTF1,V1,d1,"a");
   DrawCol(win,x+colW,       y,rh,colW,InpTF2,V2,d2,"b");
   DrawCol(win,x+colW*2,     y,rh,colW,InpTF3,V3,d3,"c");
   DrawCol(win,x+colW*3,     y,rh,colW,InpTF4,V4,d4,"d");
   DrawCol(win,x+colW*4,     y,rh,colW,InpTF5,V5,d5,"e");
   string up=ShortToString(0x25B2), dn=ShortToString(0x25BC);
   Lbl(PPFX+"leg",win,x,y+rh*9,
       " verde=forca verm=fraqueza cinza=box | verde+"+dn+"=exaustao cinza+"+up+"=expansao",
       C'150,150,150');
   // aviso no tom do rodape do CSSM ("contexto, nao e sinal de entrada")
   Lbl(PPFX+"leg2",win,x,y+rh*10,
       " ciclo=LEITURA, nao sinal (a19: 40% falsa exaustao; a20: confluencia MTF nula)",
       C'150,120,120');
}
//+------------------------------------------------------------------+
//| v2.33: leitura pontual dos buffers plotados (so p/ visual).      |
double BufAt(int c,int idx)
{
   switch(c)
   {
      case 0: return B0[idx]; case 1: return B1[idx];
      case 2: return B2[idx]; case 3: return B3[idx];
      case 4: return B4[idx]; case 5: return B5[idx];
      case 6: return B6[idx]; case 7: return B7[idx];
   }
   return EMPTY_VALUE;
}
//+------------------------------------------------------------------+
//| v2.33: rotulos na ponta das linhas (moeda + valor) — herdado do  |
//| CSSM v1.10, com o mesmo anti-colisao. Puramente visual: le os    |
//| buffers ja plotados, nao recalcula nada.                         |
void DrawEndLabels(int win)
{
   string nmp=PFX+"endPAR";
   if(!InpEndLabels)
   {
      for(int c=0;c<8;c++)
         if(ObjectFind(0,PFX+"end"+cur[c])>=0) ObjectDelete(0,PFX+"end"+cur[c]);
      if(ObjectFind(0,nmp)>=0) ObjectDelete(0,nmp);
      return;
   }
   int total=ArraySize(B0); if(total<1) return;
   int endIdx=total-1-gReplayBars; if(endIdx<0) return;         // v2.34: borda do replay
   datetime tEnd=iTime(_Symbol,_Period,gReplayBars)+PeriodSeconds(_Period);

   // modo single: um rotulo so, na ponta da linha do PAR
   if(gSingle)
   {
      for(int c=0;c<8;c++)
         if(ObjectFind(0,PFX+"end"+cur[c])>=0) ObjectDelete(0,PFX+"end"+cur[c]);
      int iBase=-1,iQuote=-1; GetPairCurrencies(iBase,iQuote);
      double vp=Bpar[endIdx];
      if(vp==EMPTY_VALUE || iBase<0 || iQuote<0)
      { if(ObjectFind(0,nmp)>=0) ObjectDelete(0,nmp); return; }
      if(ObjectFind(0,nmp)<0)
      {
         ObjectCreate(0,nmp,OBJ_TEXT,win,tEnd,vp);
         ObjectSetString (0,nmp,OBJPROP_FONT,"Consolas");
         ObjectSetInteger(0,nmp,OBJPROP_ANCHOR,ANCHOR_LEFT);
         ObjectSetInteger(0,nmp,OBJPROP_SELECTABLE,false);
      }
      ObjectSetInteger(0,nmp,OBJPROP_TIME,tEnd);
      ObjectSetDouble (0,nmp,OBJPROP_PRICE,vp);
      ObjectSetString (0,nmp,OBJPROP_TEXT,
          " "+cur[iBase]+"/"+cur[iQuote]+StringFormat(" %+.2f",vp));
      ObjectSetInteger(0,nmp,OBJPROP_FONTSIZE,InpFont);
      ObjectSetInteger(0,nmp,OBJPROP_COLOR,clrWhiteSmoke);
      return;
   }
   if(ObjectFind(0,nmp)>=0) ObjectDelete(0,nmp);

   double v[8]; bool show[8];
   for(int c=0;c<8;c++)
   {
      v[c]=BufAt(c,endIdx);
      show[c]=(!gHide[c] && cnt[c]>0 && v[c]!=EMPTY_VALUE);
      if(!show[c] && ObjectFind(0,PFX+"end"+cur[c])>=0)
         ObjectDelete(0,PFX+"end"+cur[c]);
   }
   // anti-colisao: ordena por valor desc e impoe separacao minima
   // vertical (altura do texto convertida p/ unidades da janela)
   int ord[8]; for(int i=0;i<8;i++) ord[i]=i;
   for(int i=0;i<7;i++) for(int j=i+1;j<8;j++)
      if(v[ord[j]]>v[ord[i]]){ int t=ord[i]; ord[i]=ord[j]; ord[j]=t; }
   int hpx=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS,win);
   double range=2.0*InpScaleMax*(InpFolga>=1.0? InpFolga : 1.0);   // v2.38
   double minSep=(hpx>0)? range*(InpFont+5)/(double)hpx : 0.05;

   double prevY=0; bool first=true;
   for(int r=0;r<8;r++)
   {
      int c=ord[r]; if(!show[c]) continue;
      double want=v[c];
      if(!first && prevY-want<minSep) want=prevY-minSep;
      prevY=want; first=false;
      string nm=PFX+"end"+cur[c];
      if(ObjectFind(0,nm)<0)
      {
         ObjectCreate(0,nm,OBJ_TEXT,win,tEnd,want);
         ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
         ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_LEFT);
         ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
      }
      ObjectSetInteger(0,nm,OBJPROP_TIME,tEnd);
      ObjectSetDouble (0,nm,OBJPROP_PRICE,want);
      ObjectSetString (0,nm,OBJPROP_TEXT," "+cur[c]+StringFormat(" %+.2f",v[c]));
      ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,InpFont);
      ObjectSetInteger(0,nm,OBJPROP_COLOR,colArr[c]);
   }
}
//+------------------------------------------------------------------+
//| v2.33 — Aba MATRIZ 8x8 (botao MTX), layout do CSSM v1.40.        |
//| Celula (a,b) = valor de slope TMA do PAR a/b (ComputePairVals),  |
//| orientado a->b, na ULTIMA BARRA FECHADA do TF das linhas.        |
//| Fundo verde/vermelho = par fora da box (limiar 0.20 do proprio   |
//| CSS, validado no a19 Q5); cinza = dentro; "?" = par sem simbolo. |
//| E a matriz do CSSM falando a lingua do CSS: nada de t-stat aqui. |
void DrawMatrix()
{
   if(!InpPanel || !InpMatrix) return;
   int win=ChartWindowFind(); if(win<0) return;

   ENUM_TIMEFRAMES tf=gLineTF;   // v2.34: TF mutavel (matriz acompanha as linhas)
   double pv[]; bool pok[];
   int good=ComputePairVals(tf,1,pv,pok);

   // mapa orientado (a,b): par a/b visto de a (b/a entra negado)
   double mval[64]; bool mok[64];
   for(int i=0;i<64;i++){ mval[i]=0.0; mok[i]=false; }
   for(int p=0;p<gPairsN;p++)
   {
      if(!pok[p]) continue;
      int a=gBaseIdx[p], b=gQuoteIdx[p];
      mval[a*8+b]= pv[p]; mok[a*8+b]=true;
      mval[b*8+a]=-pv[p]; mok[b*8+a]=true;
   }

   int rh=InpFont+9;
   int cellw=44, hdrw=36;
   int colW=hdrw+8*cellw+16;
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int x=cw-InpPanelX-colW+6; if(x<6) x=6;
   int y=InpPanelY;

   Rect(MPFX+"bg",win,x-6,y-6,colW,rh*12+16,C'24,24,32');
   Lbl(MPFX+"hd",win,x,y,
       StringFormat("CSS MATRIZ 8x8  %s  (slope TMA do PAR, barra fechada)",
                    TfStr(tf)), clrWhiteSmoke);

   for(int b=0;b<8;b++)
      Lbl(MPFX+"ch"+(string)b,win,x+hdrw+b*cellw+8,y+rh,cur[b],colArr[b]);

   for(int a=0;a<8;a++)
   {
      int yy=y+rh*(a+2);
      Lbl(MPFX+"rh"+(string)a,win,x,yy+1,cur[a],colArr[a]);
      for(int b=0;b<8;b++)
      {
         string nc=MPFX+"c"+(string)a+"_"+(string)b;
         string nl=MPFX+"l"+(string)a+"_"+(string)b;
         int gx=x+hdrw+b*cellw;
         if(a==b)
         {
            Rect(nc,win,gx,yy,cellw-3,InpFont+6,C'30,30,38',C'30,30,38');
            Lbl(nl,win,gx+16,yy+1,"-",C'90,90,96');
            continue;
         }
         if(!mok[a*8+b])
         {
            Rect(nc,win,gx,yy,cellw-3,InpFont+6,C'40,40,46',C'40,40,46');
            Lbl(nl,win,gx+16,yy+1,"?",C'120,120,120');
            continue;
         }
         double vv=mval[a*8+b];
         color cbg; color ctx;
         if(vv>=InpBox)      { cbg=C'18,64,28';  ctx=clrWhite; }
         else if(vv<=-InpBox){ cbg=C'78,22,22';  ctx=clrWhite; }
         else                { cbg=C'38,38,46';  ctx=C'150,150,150'; }
         Rect(nc,win,gx,yy,cellw-3,InpFont+6,cbg,cbg);
         Lbl(nl,win,gx+3,yy+1,StringFormat("%+.2f",vv),ctx);
      }
   }

   // rodape: forte/fraca pela cesta (mesmo ComputeAt do painel, barra
   // fechada) — espelho do "lider" do rodape da matriz do CSSM
   string up=ShortToString(0x25B2), dn=ShortToString(0x25BC);
   double V[8]; int g=ComputeAt(tf,1,V);
   string foot="cesta indisponivel";
   if(g>0)
   {
      int hi=-1, lo=-1;
      for(int c=0;c<8;c++)
      {
         if(cnt[c]<=0) continue;
         if(hi<0 || V[c]>V[hi]) hi=c;
         if(lo<0 || V[c]<V[lo]) lo=c;
      }
      if(hi>=0 && lo>=0)
         foot=StringFormat("forte: %s %+.2f %s | fraca: %s %+.2f %s  (media da cesta, %d pares)",
              cur[hi],V[hi],up,cur[lo],V[lo],dn,good);
   }
   Lbl(MPFX+"ft",win,x,y+rh*10+4,foot,C'200,200,205');
   Lbl(MPFX+"ft2",win,x,y+rh*11+4,
       "verde/verm = par fora da box "+DoubleToString(InpBox,2)+
       " | leitura descritiva, nao e sinal",
       C'150,120,120');
}
//+------------------------------------------------------------------+
//| Alertas: dispara quando uma moeda CRUZA a box (entra/sai).       |
//| Usa o TF das linhas (V do grafico). So na barra fechada.         |
void CheckAlerts(const double &V[])
{
   if(!InpAlerts) return;
   for(int c=0;c<8;c++)
   {
      bool fora = (MathAbs(V[c])>=InpBox);
      if(gAlertInit && fora && !gBoxPrev[c])
      {
         // cruzou para FORA da box agora
         if(V[c]>0)
            Alert(StringFormat("CSS %s: %s SAIU p/ CIMA da box (+%.2f) = forca",
                  _Symbol, cur[c], V[c]));
         else
            Alert(StringFormat("CSS %s: %s SAIU p/ BAIXO da box (%.2f) = fraqueza",
                  _Symbol, cur[c], V[c]));
      }
      gBoxPrev[c]=fora;
   }
   gAlertInit=true;
}

bool Compute()
{
   // v2.34: deslocamento do replay em barras do grafico (para o plot).
   // Deriva de gReplayTime (tempo absoluto) a cada render, entao o replay
   // fica CONGELADO no instante mesmo quando novas barras vao surgindo.
   if(gReplayTime>0)
   {
      gReplayBars=iBarShift(_Symbol,_Period,gReplayTime,false);
      if(gReplayBars<0) gReplayBars=0;
      int cap=ArraySize(B0)-2; if(cap<0) cap=0;
      if(gReplayBars>cap) gReplayBars=cap;
   }
   else gReplayBars=0;

   bool ok = ComputeSeries();
   double V1[8],V2[8],V3[8];
   int g1=ComputeNow(Rtf(InpTF1),V1);
   int g2=ComputeNow(Rtf(InpTF2),V2);
   int g3=ComputeNow(Rtf(InpTF3),V3);
   double V4[8],V5[8];
   int g4=ComputeNow(Rtf(InpTF4),V4);
   int g5=ComputeNow(Rtf(InpTF5),V5);
   // Alertas usam o TF do grafico (coluna 1 do painel = mais rapido)
   double Vlinha[8]; ComputeNow(gLineTF,Vlinha);
   CheckAlerts(Vlinha);
   int win=ChartWindowFind();
   if(win>=0){ DrawBox(win); DrawBtn(win); DrawEndLabels(win); }
   // v2.34: marcador vertical do instante do replay (todas as janelas)
   if(gReplayTime>0)
   {
      string vn=PFX+"rvline";
      if(ObjectFind(0,vn)<0) ObjectCreate(0,vn,OBJ_VLINE,0,gReplayTime,0);
      ObjectSetInteger(0,vn,OBJPROP_TIME,gReplayTime);
      ObjectSetInteger(0,vn,OBJPROP_COLOR,clrGoldenrod);
      ObjectSetInteger(0,vn,OBJPROP_STYLE,STYLE_DASH);
      ObjectSetInteger(0,vn,OBJPROP_WIDTH,1);
      ObjectSetInteger(0,vn,OBJPROP_BACK,true);
      ObjectSetInteger(0,vn,OBJPROP_SELECTABLE,false);
   }
   else if(ObjectFind(0,PFX+"rvline")>=0) ObjectDelete(0,PFX+"rvline");
   // v2.33: aba MATRIZ alterna com o painel-normal (infra do CSSM);
   // ao trocar de vista, apaga so o grupo de objetos da outra
   static int prevView=-1;                  // 0 painel, 1 matriz
   int view=(gMtx && InpMatrix)?1:0;
   if(prevView!=-1 && prevView!=view)
      ObjectsDeleteAll(0,(view==1)?PPFX:MPFX);
   prevView=view;
   if(view==1) DrawMatrix();
   else if(InpPainelModo==MP_MOEDA) DrawPanelMoeda();   // v2.36
   else        DrawPanel(V1,V2,V3,V4,V5);
   bool ready = ok && g1>0 && g2>0 && g3>0;
   Comment(ready ? "" : StringFormat("Slope Strength carregando... %s:%d %s:%d %s:%d  linhas:%s",
           TfStr(InpTF1),g1,TfStr(InpTF2),g2,TfStr(InpTF3),g3, ok?"ok":"..."));
   ChartRedraw();
   return ready;
}
//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0,B0,INDICATOR_DATA); SetIndexBuffer(1,B1,INDICATOR_DATA);
   SetIndexBuffer(2,B2,INDICATOR_DATA); SetIndexBuffer(3,B3,INDICATOR_DATA);
   SetIndexBuffer(4,B4,INDICATOR_DATA); SetIndexBuffer(5,B5,INDICATOR_DATA);
   SetIndexBuffer(6,B6,INDICATOR_DATA); SetIndexBuffer(7,B7,INDICATOR_DATA);
   SetIndexBuffer(8,Bpar,INDICATOR_DATA);
   SetIndexBuffer(9,ColPar,INDICATOR_COLOR_INDEX);
   // v2.30: dpeso por moeda (USD..NZD) p/ iCustom — ler com shift>=1
   SetIndexBuffer(10,D0,INDICATOR_CALCULATIONS);
   SetIndexBuffer(11,D1s,INDICATOR_CALCULATIONS);
   SetIndexBuffer(12,D2,INDICATOR_CALCULATIONS);
   SetIndexBuffer(13,D3,INDICATOR_CALCULATIONS);
   SetIndexBuffer(14,D4,INDICATOR_CALCULATIONS);
   SetIndexBuffer(15,D5,INDICATOR_CALCULATIONS);
   SetIndexBuffer(16,D6,INDICATOR_CALCULATIONS);
   SetIndexBuffer(17,D7,INDICATOR_CALCULATIONS);
   PlotIndexSetDouble(8,PLOT_EMPTY_VALUE,EMPTY_VALUE);
   gLineTF=Rtf(InpLineTF);   // v2.34: TF inicial das linhas (mutavel via botoes)
   for(int i=0;i<8;i++){ gBoxPrev[i]=false; gHide[i]=false; gRowCur[i]=i; }
   for(int p=0;p<8;p++){ PlotIndexSetInteger(p,PLOT_LINE_WIDTH,InpWidth);
                         PlotIndexSetString(p,PLOT_LABEL,cur[p]);
                         PlotIndexSetDouble(p,PLOT_EMPTY_VALUE,EMPTY_VALUE); }
   ArrayInitialize(cnt,0);

   bool seen[64]; for(int s=0;s<64;s++) seen[s]=false;
   int total=SymbolsTotal(false);
   for(int s=0;s<total;s++)
   {
      string sym=SymbolName(s,false);
      int bi=CurIdx(SymbolInfoString(sym,SYMBOL_CURRENCY_BASE));
      int qi=CurIdx(SymbolInfoString(sym,SYMBOL_CURRENCY_PROFIT));
      if(bi<0||qi<0||bi==qi) continue;
      int key=(bi<qi)?bi*8+qi:qi*8+bi;
      if(seen[key]) continue;
      if(!SymbolSelect(sym,true)) continue;
      int n=gPairsN+1;
      ArrayResize(gPair,n); ArrayResize(gBaseIdx,n); ArrayResize(gQuoteIdx,n);
      gPair[gPairsN]=sym; gBaseIdx[gPairsN]=bi; gQuoteIdx[gPairsN]=qi;
      cnt[bi]++; cnt[qi]++; gPairsN++; seen[key]=true;
   }
   Print("CurrencySlopeStrength: ",gPairsN," pares detectados.");

   // v2.35: corretora com candle de domingo? (addSundayToMonday do original)
   gSundayCandles=false;
   datetime td[]; ArraySetAsSeries(td,true);
   if(CopyTime(_Symbol,PERIOD_D1,0,8,td)==8)
      for(int d=0;d<8;d++)
      {
         MqlDateTime st; TimeToStruct(td[d],st);
         if(st.day_of_week==0){ gSundayCandles=true; break; }
      }

   IndicatorSetInteger(INDICATOR_LEVELS,0);
   double _folga = (InpFolga>=1.0? InpFolga : 1.0);      // v2.38
   IndicatorSetDouble(INDICATOR_MINIMUM,-InpScaleMax*_folga);
   IndicatorSetDouble(INDICATOR_MAXIMUM, InpScaleMax*_folga);
   IndicatorSetString(INDICATOR_SHORTNAME,"Currency Slope Strength (CSS original)");
   IndicatorSetInteger(INDICATOR_DIGITS,3);
   EventSetTimer(2);
   SE_Preload();   // comeca a aquecer o historico dos pares ja na anexacao
   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason){ EventKillTimer(); Comment(""); ObjectsDeleteAll(0,PFX); }
//+------------------------------------------------------------------+
//| SE_: serie da MESMA forca do ComputeAt (v2.35) p/ shifts 1..N,   |
//| barras FECHADAS. Replica INLINE o PairSlopes numa passada por    |
//| par (1 CopyClose/High/Low por par, laco pelos shifts) — MESMA    |
//| formula (ATRmt4 / LWMA-ou-TMA / slope=(tma-prev)/atr / NormVal),  |
//| so o laco muda de lugar p/ nao chamar PairSlopes 500x. Tolera    |
//| historico parcial (TF alto): shift sem barra fica 0 e o front    |
//| corta os zeros do inicio. out achatado: out[c*N+j], j=0 = mais   |
//| antigo (shift N) ... j=N-1 (shift 1).                            |
//+------------------------------------------------------------------+
#define SE_HIST 500

int SE_ComputeSeries(ENUM_TIMEFRAMES tf, double &out[], long &tt[])
{
   int N = SE_HIST;
   ArrayResize(out, 8*N); ArrayInitialize(out, 0.0);
   ArrayResize(tt, N);    ArrayInitialize(tt, 0);
   double acc[]; ArrayResize(acc, 8*N); ArrayInitialize(acc, 0.0);

   ENUM_TIMEFRAMES rtf=Rtf(tf);
   int pad=SunPad(rtf);
   int W = N + pad + 12 + InpATRPeriod + (int)MathMax(InpMAPeriod,21) + 8;  // mesmo W do PairSlopes
   double wsum = InpMAPeriod*(InpMAPeriod+1)/2.0;   // 231 quando P=21
   double wlst = InpMAPeriod-1.0;                    //  20 quando P=21

   datetime anchor=AnchorTime();
   bool useAnchor=((InpSyncBars && !gExportLive) || gReplayTime>0) && anchor>0;

   // tempos da grade do TF (1o par): eixo do grafico + deteccao de domingo
   datetime tgrid[]; ArraySetAsSeries(tgrid,true); int ntg=0;
   if(gPairsN>0)
      ntg = useAnchor ? CopyTime(gPair[0],rtf,anchor,N+pad+1,tgrid)
                      : CopyTime(gPair[0],rtf,0,N+pad+1,tgrid);

   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      double cl[],hi[],lo[];
      ArraySetAsSeries(cl,true); ArraySetAsSeries(hi,true); ArraySetAsSeries(lo,true);
      int nc,nh,nl;
      if(useAnchor){
         nc=CopyClose(gPair[p],rtf,anchor,W,cl);
         nh=CopyHigh (gPair[p],rtf,anchor,W,hi);
         nl=CopyLow  (gPair[p],rtf,anchor,W,lo);
      } else {
         nc=CopyClose(gPair[p],rtf,0,W,cl);
         nh=CopyHigh (gPair[p],rtf,0,W,hi);
         nl=CopyLow  (gPair[p],rtf,0,W,lo);
      }
      int copied=MathMin(nc,MathMin(nh,nl));
      if(copied < 12+InpATRPeriod+3) continue;   // minimo p/ ao menos 1 ponto de slope

      double atr[]; ATRmt4(hi,lo,cl,copied,InpATRPeriod,atr);
      double ma[];
      if(InpIgnoreFuture) LWMA(cl,copied,InpMAPeriod,ma);
      else                TMA (cl,copied,InpMAPeriod,ma);
      good++;

      int k0 = InpExportLive ? 0 : 1;   // 0 = barra viva (live), 1 = ultima fechada
      for(int k=k0;k<k0+N;k++)
      {
         int idx=k-k0;                  // 0..N-1 (0 = ponto mais NOVO)
         int kk=k;
         if(pad>0 && k<ntg)
         {
            MqlDateTime st; TimeToStruct(tgrid[k],st);
            if(st.day_of_week==0) kk=k+1;      // addSundayToMonday (so D1)
         }
         if(kk+10>=copied || kk+1>=copied) break;
         double a=atr[kk+10]/10.0;
         if(a<=0.0) continue;
         double dblTma,dblPrev;
         if(InpIgnoreFuture)
         {
            if(ma[kk]==0.0 || ma[kk+1]==0.0) continue;
            dblTma  = ma[kk];
            dblPrev = (ma[kk+1]*wsum + cl[kk]*wlst)/(wsum+wlst);
         }
         else { dblTma = ma[kk]; dblPrev = ma[kk+1]; }
         double v=(dblTma-dblPrev)/a;
         int j=N-1-idx;
         acc[gBaseIdx[p]*N+j]  += v;
         acc[gQuoteIdx[p]*N+j] -= v;
      }
   }
   for(int c=0;c<8;c++)
      for(int j=0;j<N;j++)
         out[c*N+j]=NormVal(c, acc[c*N+j]);   // mesma agregacao/escala do ComputeAt

   int k0t = InpExportLive ? 0 : 1;
   for(int k=k0t;k<k0t+N;k++) if(k<ntg) tt[N-1-(k-k0t)]=(long)tgrid[k];
   return good;
}

//+------------------------------------------------------------------+
//| SE_: exporta forca por moeda nos TFs (M5/M15/M30 + os 5 do painel)|
//| + direcao (k=InpPesoK) + serie historica (SE_HIST barras).        |
//| Barra VIVA (kShift=0, igual ao painel do MT5) se InpExportLive,    |
//| senao ultima FECHADA (kShift=1). Direcao segue barras fechadas     |
//| (seta estavel). Nao exporta em replay. Formato = css_state.json.   |
//+------------------------------------------------------------------+
void SE_ExportCSS()
{
   if(gReplayTime > 0) return;
   gExportLive = true;   // cada TF na propria barra atual (independe do grafico)
   ENUM_TIMEFRAMES want[8], tfs[8]; int ntf = 0;
   want[0]=PERIOD_M5; want[1]=PERIOD_M15; want[2]=PERIOD_M30;
   want[3]=InpTF1; want[4]=InpTF2; want[5]=InpTF3; want[6]=InpTF4; want[7]=InpTF5;
   for(int i = 0; i < 8; i++)
   {
      bool dup = false;
      for(int j2 = 0; j2 < ntf; j2++) if(tfs[j2] == want[i]) dup = true;
      if(!dup) tfs[ntf++] = want[i];
   }
   string body = "";
   for(int t = 0; t < ntf; t++)
   {
      double V[8]; int dir[8]; ArrayInitialize(V, 0);
      int good = ComputeAt(tfs[t], InpExportLive ? 0 : 1, V);   // 0 = barra viva
      if(!PhaseDir(tfs[t], dir)) for(int c=0;c<8;c++) dir[c]=0;
      string vals = "", dirs = "";
      for(int c = 0; c < 8; c++)
      {
         if(c > 0) { vals += ","; dirs += ","; }
         vals += "\"" + cur[c] + "\":" + SE_Num(V[c], 4);
         dirs += "\"" + cur[c] + "\":" + IntegerToString(dir[c]);
      }

      double serie[]; long st[];
      SE_ComputeSeries(tfs[t], serie, st);
      string times = "", lines = "";
      for(int j = 0; j < SE_HIST; j++)
      {
         if(j > 0) times += ",";
         times += IntegerToString(st[j]);
      }
      for(int c = 0; c < 8; c++)
      {
         if(c > 0) lines += ",";
         string pts = "";
         for(int j = 0; j < SE_HIST; j++)
         {
            if(j > 0) pts += ",";
            pts += SE_Num(serie[c*SE_HIST+j], 3);
         }
         lines += "\"" + cur[c] + "\":[" + pts + "]";
      }

      if(body != "") body += ",";
      body += "{\"tf\":\"" + SE_TfName(tfs[t]) + "\",\"good\":" + IntegerToString(good) +
              ",\"vals\":{" + vals + "},\"dir\":{" + dirs + "}" +
              ",\"hist\":{\"t\":[" + times + "],\"vals\":{" + lines + "}}}";
   }
   string j = "{" + SE_Head() +
              ",\"box\":" + SE_Num(InpBox, 2) +
              ",\"scale_max\":" + SE_Num(InpScaleMax, 2) +
              ",\"tfs\":[" + body + "]}";
   SE_WriteJson("css_state.json", j);
   gExportLive = false;
}
//+------------------------------------------------------------------+
//| SE_: PRE-CARREGADOR de historico. So DISPARA/checa o download do  |
//| MT5 pros 28 pares nos TFs usados (linhas + M5/M15/M30 do export +  |
//| os 5 do painel); NAO calcula nada — nenhuma formula tocada.        |
//|                                                                    |
//| Resolve o "carregamento preguicoso" do MT5: sem isto, ao trocar   |
//| p/ um TF (ex.: MN) com o GRAFICO noutro TF, os simbolos de fundo   |
//| vem com poucas barras e o par/moeda e pulado ("2+ moedas nao       |
//| carregam"). CopyRates aqui dispara o download em background e      |
//| retorna na hora (nao bloqueia); rodando no timer, em poucos ciclos |
//| tudo sincroniza. Depois de sincronizado, so faz o check barato e   |
//| nao pede mais nada (self-limiting). Ao trocar de TF, o novo TF     |
//| entra pela lista e re-aquece sozinho.                              |
//+------------------------------------------------------------------+
void SE_Preload()
{
   if(gPairsN<1) return;
   ENUM_TIMEFRAMES tfs[9];
   tfs[0]=gLineTF; tfs[1]=PERIOD_M5; tfs[2]=PERIOD_M15; tfs[3]=PERIOD_M30;
   tfs[4]=Rtf(InpTF1); tfs[5]=Rtf(InpTF2); tfs[6]=Rtf(InpTF3);
   tfs[7]=Rtf(InpTF4); tfs[8]=Rtf(InpTF5);
   // profundidade alvo = a maior que o calculo pede (linhas: InpBars + folga)
   int want = InpBars + 12 + InpATRPeriod + (int)MathMax(InpMAPeriod,21) + 8;

   for(int t=0;t<9;t++)
   {
      ENUM_TIMEFRAMES tf=tfs[t];
      bool dup=false; for(int u=0;u<t;u++) if(tfs[u]==tf){ dup=true; break; }
      if(dup) continue;
      for(int p=0;p<gPairsN;p++)
      {
         // ja sincronizado com o servidor => historico completo disponivel; pula.
         if(SeriesInfoInteger(gPair[p],tf,SERIES_SYNCHRONIZED)) continue;
         MqlRates rr[];
         CopyRates(gPair[p],tf,0,want,rr);   // dispara o download; nao bloqueia
      }
   }
}
//+------------------------------------------------------------------+
void OnTimer()
{
   SE_Preload();   // garante o historico dos 28 pares nos TFs usados (lazy-load do MT5)
   static int tr=0;
   if(!gReady){ gReady=Compute(); if(++tr>15) gReady=true; if(!gReady) return; }
   SE_ExportCSS();   // SE_: exporta css_state.json a cada tick do timer (2s)
}
//+------------------------------------------------------------------+
// v2.34: move o cursor de replay. barsDelta>0 = volta no tempo (mais
// antigo); <0 = avanca. Ancora por TEMPO absoluto p/ nao "escorregar"
// quando novas barras surgem. Chegou na barra 0 => volta ao vivo.
void ReplayStep(int barsDelta)
{
   int cur=(gReplayTime>0)? iBarShift(_Symbol,_Period,gReplayTime,false) : 0;
   int maxBack=Bars(_Symbol,_Period)-2; if(maxBack<1) maxBack=1;
   int ns=cur+barsDelta;
   if(ns<0) ns=0;
   if(ns>maxBack) ns=maxBack;
   if(ns<=0) gReplayTime=0;                       // ao vivo
   else      gReplayTime=iTime(_Symbol,_Period,ns);
}
// v2.34: troca o TF das LINHAS (dir=+1 sobe, -1 desce na lista padrao).
// NAO mexe no replay: gReplayTime e absoluto, entao so o TF muda.
void TfStep(int dir)
{
   int idx=0;
   for(int i=0;i<9;i++) if(gTFList[i]==gLineTF){ idx=i; break; }
   idx+=dir; if(idx<0) idx=0; if(idx>8) idx=8;
   gLineTF=gTFList[idx];
}
void OnChartEvent(const int id, const long &lparam,
                  const double &dparam, const string &sparam)
{
   if(id!=CHARTEVENT_OBJECT_CLICK) return;

   // v2.37 — painel MOEDA: botao TODAS limpa o solo
   if(sparam==PPFX+"btnAll")
   {
      gSolo=-1;
      for(int i=0;i<8;i++) gHide[i]=false;
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
      gReady=false; Compute(); ChartRedraw();
      return;
   }
   // v2.37 — painel MOEDA: clique no botao da moeda ISOLA a linha dela
   {
      string pb=PPFX+"btn";
      if(StringFind(sparam,pb)==0 && sparam!=PPFX+"btnAll")
      {
         int c=(int)StringToInteger(StringSubstr(sparam,StringLen(pb)));
         if(c>=0 && c<8)
         {
            if(gSolo==c){ gSolo=-1; for(int i=0;i<8;i++) gHide[i]=false; }
            else        { gSolo=c;  for(int i=0;i<8;i++) gHide[i]=(i!=c); }
            ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
            gReady=false; Compute(); ChartRedraw();
         }
         return;
      }
   }

   // v2.34: troca de TF das linhas (mantem o instante do replay)
   if(sparam==PFX+"tfDn" || sparam==PFX+"tfUp")
   {
      TfStep(sparam==PFX+"tfUp" ? +1 : -1);
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
      gReady=false; Compute(); ChartRedraw();
      return;
   }

   // v2.34: barra de REPLAY
   if(sparam==PFX+"rvBB"||sparam==PFX+"rvB"||sparam==PFX+"rvF"||
      sparam==PFX+"rvFF"||sparam==PFX+"rvLive")
   {
      if(sparam==PFX+"rvBB")      ReplayStep(+InpReplayStep);
      else if(sparam==PFX+"rvB")  ReplayStep(+1);
      else if(sparam==PFX+"rvF")  ReplayStep(-1);
      else if(sparam==PFX+"rvFF") ReplayStep(-InpReplayStep);
      else                        gReplayTime=0;   // [LIVE]
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
      gReady=false; Compute(); ChartRedraw();
      return;
   }

   // Botao linha unica
   if(sparam==PFX+"btnSingle")
   {
      gSingle = !gSingle;
      int win=ChartWindowFind();
      if(win>=0) DrawBtn(win);
      gReady=false; Compute(); ChartRedraw();
      return;
   }

   // v2.33: botao MTX — alterna painel-normal <-> matriz por par
   if(sparam==PFX+"btnMtx")
   {
      gMtx=!gMtx;
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
      int win=ChartWindowFind();
      if(win>=0) DrawBtn(win);
      gReady=false; Compute(); ChartRedraw();
      return;
   }

   // Botao RESET: reexibe todas as moedas
   if(sparam==PFX+"btnReset")
   {
      for(int i=0;i<8;i++) gHide[i]=false;
      ObjectSetInteger(0,sparam,OBJPROP_STATE,false);
      gReady=false; Compute(); ChartRedraw(0);
      return;
   }

   // Clique num label da coluna A (PPFX+"a"+r): alterna a moeda daquela linha
   string prefA=PPFX+"a";
   if(StringFind(sparam,prefA)==0)
   {
      int r=(int)StringToInteger(StringSubstr(sparam,StringLen(prefA)));
      if(r>=0 && r<8)
      {
         int c=gRowCur[r];           // moeda que esta naquela linha
         if(c>=0 && c<8)
         {
            gHide[c]=!gHide[c];
            gReady=false; Compute(); ChartRedraw(0);
         }
      }
      return;
   }
}

int OnCalculate(const int rates_total,const int prev_calculated,
                const datetime &time[],const double &open[],const double &high[],
                const double &low[],const double &close[],const long &tick_volume[],
                const long &volume[],const int &spread[])
{
   static datetime lastBar=0;
   datetime t0[]; ArraySetAsSeries(t0,true);
   if(CopyTime(_Symbol,_Period,0,1,t0)<1) return rates_total;
   bool newbar=(t0[0]!=lastBar);
   if(prev_calculated>0 && !newbar && gReady) return rates_total;
   lastBar=t0[0];
   gReady=Compute();
   return rates_total;
}
//+------------------------------------------------------------------+
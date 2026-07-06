//+------------------------------------------------------------------+
//|                                              CSSM_Contexto.mq5   |
//|  Painel de CONTEXTO por índices sintéticos G8 — v1.40            |
//|  + camada relacional (matriz 8x8, breadth, deteccao de forca     |
//|    espuria)                                                      |
//|                                                                  |
//|  v1.10 (usabilidade diária):                                     |
//|   - Rótulo colorido na ponta de cada linha (moeda + valor M)     |
//|   - Botão FOCO: destaca as 2 moedas do par do gráfico,           |
//|     esmaece as demais (clique alterna; par fora do G8 = 8 linhas)|
//|   - Painel: nome na cor da linha + ESTADO como célula com fundo  |
//|   - Barra de força horizontal proporcional ao M                  |
//|   - Idade do estado (nº de barras no estado atual)               |
//|   - Setas de aceleração (z-score): ▲▲ ▲ - ▼ ▼▼                   |
//|   - Estados/direções HISTÓRICOS nos buffers 8-23 (p/ EA/tester)  |
//|   - Barra em formação limpa (sem 0.000 na janela de dados)       |
//|                                                                  |
//|  v1.40 (camada relacional — DESCRITIVA, diagnóstico/nowcasting): |
//|   - Motor por PAR: t Newey-West + ER sobre o log-preço de cada   |
//|     um dos 28 pares (mesma disciplina anti-repaint do índice)    |
//|   - MOTIVAÇÃO (pesquisa ta-research, H1/2 anos): o índice        |
//|     sintético, por ser média da cesta, gera FORÇA ESPÚRIA em     |
//|     ~64% dos instantes ativos — o agregado acusa |t| >= gate mas |
//|     menos de 3 dos 7 pares confirmam. A camada por par corrige   |
//|     a leitura (célula a célula, sobre quem a moeda tende).       |
//|   - Coluna "amp" no painel (breadth hard/soft), marcador ⚠ de    |
//|     força espúria, aba MATRIZ 8x8 (botão MTX), alerta opcional   |
//|     de amplitude >= 6/7.                                         |
//|   - LIMITAÇÃO: célula do par sem estado Exausta (exigiria z-win  |
//|     por par); estados do par = Madura / Emergindo-lite / Ruído.  |
//|   - Gates do PAR calibrados por simulação (random walk, ~5% FP)  |
//|     para a janela InpWMid. Se mudar InpWMid, ajuste InpPairGate: |
//|       w=16 -> 2.90 | w=24 -> 2.51 | w=32 -> 2.35                 |
//|       w=48 -> 2.21 | w=64 -> 2.13                                |
//|     (v1.41: InpAutoGates aplica esta tabela automaticamente via  |
//|      GateFor, interpolando pela janela efetiva.)                 |
//|                                                                  |
//|  v1.41 (janelas por HORIZONTE temporal — modo WM_HOURS):         |
//|   - MOTIVACAO: com janela fixa em barras (w=64) o horizonte      |
//|     temporal varia selvagemente entre TFs (M30: 32h; H1: 2,7d;   |
//|     H4: 10,7d) — o indicador "procura tendencias remotas" nos    |
//|     TFs curtos e a grade MTF compara coisas incomparaveis.       |
//|   - InpHorizonHours define O QUE se procura (DETECCAO; perfil    |
//|     "tendencia absoluta": 12-24h). InpContextHours (~5 dias)     |
//|     cobre TFs cuja barra e grande demais p/ a deteccao. Piso     |
//|     estatistico: 16 barras. Camadas com defaults (18h/120h):     |
//|       M15 w=72 det | M30 w=36 det | H1 w=18 det                  |
//|       H4  w=30 ctx | D1 / W1 / MN w=64 ESTRUTURAL (legado)       |
//|     Derivados: w_fast=max(4,w/4); z_win=clamp(8w,150,500).       |
//|   - Por que H4 NAO detecta fenomenos de 12-24h: o piso de 16     |
//|     barras em H4 = 2,7 dias — e RESOLUCAO estatistica, nao       |
//|     defeito. H4 contextualiza (120h = 30 barras); D1+ dao a      |
//|     estrutura. A grade marca a camada no cabecalho (d/c/s) e o   |
//|     painel mostra a lente efetiva. NUNCA leia um TF estrutural   |
//|     como se detectasse o horizonte do dia.                       |
//|   - InpAutoGates: t_gate/t_low interpolados da tabela de         |
//|     calibracao (random walk, FP 5%/20%) pela janela efetiva de   |
//|     CADA TF — motor do grafico, grade MTF e camada relacional    |
//|     sempre com a regua da propria janela.                        |
//|   - WM_BARS = comportamento v1.40 EXATO (inputs legados valem).  |
//|                                                                  |
//|  IMPORTANTE: este indicador NÃO gera sinal de entrada.           |
//|  Estudo de evento (26k eventos) rejeitou continuação nestes      |
//|  horizontes. Breadth/matriz são LEITURA DO PRESENTE (a pesquisa  |
//|  testou continuação pós-reconhecimento: NULA). O aviso           |
//|  "contexto, nao e sinal de entrada" cobre também a camada nova.  |
//|                                                                  |
//|  Buffers p/ iCustom:                                             |
//|   0-7  M por moeda | 8-15 estado (0-3) | 16-23 direção (+1/-1)   |
//|   24-31 breadth_hard*dir (assinado) | 32-39 breadth_soft*dir     |
//|  Ordem: USD,EUR,GBP,JPY,CHF,CAD,AUD,NZD. Ler com shift>=1.       |
//|  Barra em formação (shift 0) = cópia cosmética da última fechada.|
//+------------------------------------------------------------------+
#property copyright "Carlos — motor CSSM (validado por estudo de evento)"
#property version   "1.41"
#property description "+ janelas por horizonte temporal (WM_HOURS) + camada relacional (matriz 8x8, breadth)"
#property indicator_separate_window
#property indicator_buffers 40
#property indicator_plots   8

#property indicator_type1  DRAW_LINE
#property indicator_label1 "USD"
#property indicator_color1 clrLime
#property indicator_type2  DRAW_LINE
#property indicator_label2 "EUR"
#property indicator_color2 clrDodgerBlue
#property indicator_type3  DRAW_LINE
#property indicator_label3 "GBP"
#property indicator_color3 clrRed
#property indicator_type4  DRAW_LINE
#property indicator_label4 "JPY"
#property indicator_color4 clrMagenta
#property indicator_type5  DRAW_LINE
#property indicator_label5 "CHF"
#property indicator_color5 clrSilver
#property indicator_type6  DRAW_LINE
#property indicator_label6 "CAD"
#property indicator_color6 clrOrange
#property indicator_type7  DRAW_LINE
#property indicator_label7 "AUD"
#property indicator_color7 clrGold
#property indicator_type8  DRAW_LINE
#property indicator_label8 "NZD"
#property indicator_color8 clrAqua

//--- inputs: modo de janela (v1.41 — horizonte temporal; ver cabeçalho)
enum ENUM_WINDOW_MODE
  {
   WM_BARS,   // Barras fixas (v1.40 exato)
   WM_HOURS   // Horizonte em horas (janela por TF)
  };
input ENUM_WINDOW_MODE InpWindowMode = WM_HOURS; // modo de janela (BARS = comportamento v1.40 exato)
input double InpHorizonHours  = 18;   // horizonte de DETECÇÃO em horas (perfil tendência absoluta: 12-24h)
input double InpContextHours  = 120;  // horizonte de CONTEXTO em horas (~5 dias) p/ TFs que não alcançam a detecção
input bool   InpAutoGates     = true; // portões t auto-calibrados pela janela efetiva (só modo HOURS)
//--- inputs: motor
input ENUM_TIMEFRAMES InpTF      = PERIOD_CURRENT; // TF do cálculo (= TF do gráfico p/ linhas alinhadas)
input int    InpWFast   = 16;    // janela rápida (barras) — modo BARS; em HOURS deriva max(4,w_mid/4)
input int    InpWMid    = 64;    // janela média (barras) — modo BARS; em HOURS deriva do horizonte
input int    InpZWin    = 500;   // janela do z-score — modo BARS; em HOURS deriva clamp(8*w_mid,150,500)
input int    InpBars    = 300;   // barras a plotar
input int    InpAccSpan = 8;     // suavização EMA da aceleração
//--- inputs: máquina de estados
input double InpTGate   = 2.0;   // t mínimo p/ Madura — modo BARS ou HOURS c/ AutoGates=false
input double InpTLow    = 1.0;   // t mínimo p/ Emergindo — modo BARS ou HOURS c/ AutoGates=false
input double InpPersist = 0.55;  // persistência mínima p/ Madura
input double InpAccEmg  = 0.75;  // |z aceleração| p/ Emergindo
input double InpCxExh   = -1.0;  // z convexidade contra tendência p/ Exausta
input double InpAcExh   = -0.75; // z aceleração contra tendência p/ Exausta
//--- inputs: visual
input bool   InpPanel     = true;  // mostrar painel
input bool   InpEndLabels = true;  // rótulos na ponta das linhas
input bool   InpFocusStart= false; // iniciar em modo FOCO no par do gráfico
input int    InpPanelX    = 12;    // margem a partir da DIREITA
input int    InpPanelY    = 16;    // painel Y
input int    InpFont      = 9;     // fonte
input bool   InpAlerts    = false; // alertar mudança de estado (barra fechada)
//--- inputs: camada relacional (v1.40 — DESCRITIVA; ver cabeçalho)
input bool   InpRelational   = true;   // camada relacional (matriz + breadth)
input double InpPairGate     = 2.13;   // |t| p/ tendência confirmada no PAR — modo BARS ou AutoGates=false
input double InpPairGateLow  = 1.28;   // |t| baixo do par — modo BARS ou AutoGates=false
input bool   InpAlertBreadth = false;  // alerta quando breadth_hard >= 6/7 (barra fechada)
// gates calibrados por w: 16->2.90 | 24->2.51 | 32->2.35 | 48->2.21 | 64->2.13
// (v1.41: em HOURS c/ AutoGates, GateFor(w efetivo) substitui os dois acima)
//--- inputs: grade multi-timeframe
input bool   InpMTF = true;                    // grade multi-timeframe no painel
input ENUM_TIMEFRAMES InpGT1 = PERIOD_M30;     // MTF 1
input ENUM_TIMEFRAMES InpGT2 = PERIOD_H1;      // MTF 2
input ENUM_TIMEFRAMES InpGT3 = PERIOD_H4;      // MTF 3
input ENUM_TIMEFRAMES InpGT4 = PERIOD_D1;      // MTF 4
input ENUM_TIMEFRAMES InpGT5 = PERIOD_W1;      // MTF 5
input ENUM_TIMEFRAMES InpGT6 = PERIOD_MN1;     // MTF 6

//--- moedas e cores
string cur[8]    = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};
color  colArr[8] = {clrLime,clrDodgerBlue,clrRed,clrMagenta,clrSilver,clrOrange,clrGold,clrAqua};
color  COL_DIM   = C'70,70,78';

//--- estados
#define ST_NOISE     0
#define ST_EMERGING  1
#define ST_MATURE    2
#define ST_EXHAUSTED 3
string stName[4]  = {"Ruido","Emerg.","Madura","EXAUSTA"};
color  stBg[4]    = {C'60,60,66', C'170,140,20', C'26,140,70', C'170,45,35'};
color  stTxt[4]   = {C'190,190,190', clrBlack, clrWhite, clrWhite};

//--- buffers
double BM0[],BM1[],BM2[],BM3[],BM4[],BM5[],BM6[],BM7[];
double BS0[],BS1[],BS2[],BS3[],BS4[],BS5[],BS6[],BS7[];
double BD0[],BD1[],BD2[],BD3[],BD4[],BD5[],BD6[],BD7[];
double BH0[],BH1[],BH2[],BH3[],BH4[],BH5[],BH6[],BH7[];   // 24-31 breadth_hard*dir
double BB0[],BB1[],BB2[],BB3[],BB4[],BB5[],BB6[],BB7[];   // 32-39 breadth_soft*dir

//--- pares
string gPair[];
int    gBaseIdx[], gQuoteIdx[];
int    gPairsN = 0;

//--- séries internas (flat [c*len+k], k=0 = barra fechada mais recente)
int    gLf=0, gLi=0, gLs=0;
double gIdx[];
double gTmid[], gER[], gMomF[], gMomM[], gPers[], gConv[], gAcc[], gM[];
int    gStateSer[];   // estados históricos (8 * gLs)
int    gDirSer[];     // direções históricas (8 * gLs)
double gAccZ0[8];     // z da aceleração em k=0 (setas)
int    gAge[8];       // idade do estado atual (barras)
int    gPrevState[8];
bool   gPrevInit=false;

//--- foco
bool   gFocus=false;
int    gFocA=-1, gFocB=-1;   // moedas do par do gráfico

//--- grade MTF (6 TFs x 8 moedas)
ENUM_TIMEFRAMES gGTF[6];
int      gGridSt[48];        // estado por [tf*8+c]
int      gGridDir[48];       // direção por [tf*8+c]
bool     gGridOk[6];         // TF calculável (dados suficientes)
datetime gGridLast[6];       // última barra processada por TF

//--- camada relacional (v1.40): séries por par + breadth por moeda
int    gLp=0;                 // comprimento das séries por par
double gPairT[];              // t NW do par           [p*gLp+k]
double gPairER[];             // ER do par             [p*gLp+k]
double gPairLog[];            // log-closes do par     [p*gLp+k] (p/ dominância)
bool   gPairOk[];             // par com histórico suficiente
double gBrSoft[], gBrHard[];  // breadth por moeda     [c*gLs+k]
bool   gRelOk=false;          // camada calculada nesta barra
bool   gRelSlow=false;        // abortada por performance (>200ms)
bool   gRelLogged=false;      // log de tempo (só 1ª barra)
double gRelMs=0.0;
bool   gPrevBHHigh[8];        // anti-spam do alerta de amplitude
bool   gPrevBHInit=false;
bool   gMtx=false;            // aba MATRIZ ativa (persiste como o FOCO)
bool   gMtxDirty=false;

string   PFX ="CSSM_";
string   PPFX="CSSM_p_";      // objetos do painel-normal (grupo alternável)
string   MPFX="CSSM_mx_";     // objetos da aba MATRIZ
datetime gLastBar=0;

//--- v1.41: parâmetros efetivos do motor do TF do gráfico (em WM_BARS
//    recebem exatamente os inputs legados — comportamento v1.40)
int    gWMid=64, gWFast=16, gZWin=500, gLayer=-1;
double gTGate=2.0, gTLow=1.0, gPairGate=2.13, gPairLow=1.28;
string gLens="";              // lente efetiva da grade (linha de status)
bool   gPerfLogged=false;     // log do tempo de Recalc (só 1ª barra)

//+------------------------------------------------------------------+
ENUM_TIMEFRAMES Rtf(ENUM_TIMEFRAMES tf){ return (tf==PERIOD_CURRENT)?(ENUM_TIMEFRAMES)_Period:tf; }
string TfStr(ENUM_TIMEFRAMES tf){ string s=EnumToString(Rtf(tf)); StringReplace(s,"PERIOD_",""); return s; }
string TfShort(ENUM_TIMEFRAMES tf)
{
   switch(tf)
   {
      case PERIOD_M30: return "30";
      case PERIOD_MN1: return "MN";
      default: return TfStr(tf);
   }
}
int CurIdx(string code){ for(int i=0;i<8;i++) if(cur[i]==code) return i; return -1; }
string Arr(double z)
{
   string up=ShortToString(0x25B2), dn=ShortToString(0x25BC);
   if(z>=1.5)  return up+up;
   if(z>=0.5)  return up+" ";
   if(z<=-1.5) return dn+dn;
   if(z<=-0.5) return dn+" ";
   return "- ";
}

//+------------------------------------------------------------------+
//| v1.41 — janela efetiva por TF (conversão horizonte -> barras)     |
//| Camadas: DETECÇÃO (o horizonte cabe em >=16 barras do TF),        |
//| CONTEXTO (idem p/ InpContextHours), ESTRUTURAL (w=64 legado —     |
//| W1/MN caem aqui). Piso de 16 barras = resolução estatística do    |
//| t Newey-West, não é ajustável sem recalibrar os portões.          |
//+------------------------------------------------------------------+
#define WLAYER_DET 0
#define WLAYER_CTX 1
#define WLAYER_STR 2
#define WFLOOR     16

struct SWin
  {
   int    wMid;     // janela média efetiva
   int    wFast;    // janela rápida derivada
   int    zWin;     // janela do z-score derivada
   int    layer;    // WLAYER_*; -1 = modo BARS (sem camada)
   double tGate;    // portão t p/ Madura
   double tLow;     // portão t baixo (Emergindo)
  };

//--- tabela de calibração (random walks, FP 5% / 20% — a mesma do
//    cabeçalho v1.40, agora aplicada por interpolação)
int    GATE_W[5]  = {16,24,32,48,64};
double GATE_HI[5] = {2.896,2.511,2.350,2.205,2.134};
double GATE_LO[5] = {1.692,1.527,1.460,1.397,1.280};

//--- interpolação linear entre os nós; abaixo de 16 não existe (o piso
//    WFLOOR impede); acima de 64 mantém o nó 64 (curva assintótica)
double GateFor(int w,bool low)
{
   if(w<=GATE_W[0]) return low? GATE_LO[0]:GATE_HI[0];
   if(w>=GATE_W[4]) return low? GATE_LO[4]:GATE_HI[4];
   for(int i=0;i<4;i++)
      if(w<=GATE_W[i+1])
      {
         double f=(double)(w-GATE_W[i])/(double)(GATE_W[i+1]-GATE_W[i]);
         return low? GATE_LO[i]+f*(GATE_LO[i+1]-GATE_LO[i])
                   : GATE_HI[i]+f*(GATE_HI[i+1]-GATE_HI[i]);
      }
   return low? GATE_LO[4]:GATE_HI[4];
}

//--- função central: parâmetros efetivos de um TF qualquer
void WinFor(ENUM_TIMEFRAMES tf,SWin &o)
{
   if(InpWindowMode==WM_BARS)
   {
      o.wMid=InpWMid; o.wFast=InpWFast; o.zWin=InpZWin;
      o.layer=-1; o.tGate=InpTGate; o.tLow=InpTLow;
      return;
   }
   double tf_h=PeriodSeconds(Rtf(tf))/3600.0;
   int bars_det=(int)MathRound(InpHorizonHours/tf_h);
   if(bars_det>=WFLOOR){ o.wMid=(int)MathMin(bars_det,96); o.layer=WLAYER_DET; }
   else
   {
      int bars_ctx=(int)MathRound(InpContextHours/tf_h);
      if(bars_ctx>=WFLOOR){ o.wMid=(int)MathMin(bars_ctx,96); o.layer=WLAYER_CTX; }
      else                { o.wMid=64;                        o.layer=WLAYER_STR; }
   }
   o.wFast=MathMax(4,o.wMid/4);
   o.zWin=(int)MathMin(MathMax(8.0*o.wMid,150.0),500.0);
   if(InpAutoGates){ o.tGate=GateFor(o.wMid,false); o.tLow=GateFor(o.wMid,true); }
   else            { o.tGate=InpTGate;              o.tLow=InpTLow; }
}
string LayerSfx(int layer)
{
   if(layer==WLAYER_DET) return ShortToString(0x1D48);   // sobrescrito d
   if(layer==WLAYER_CTX) return ShortToString(0x1D9C);   // sobrescrito c
   if(layer==WLAYER_STR) return ShortToString(0x02E2);   // sobrescrito s
   return "";
}
string LayerName(int layer)
{
   if(layer==WLAYER_DET) return "DETECCAO";
   if(layer==WLAYER_CTX) return "CONTEXTO";
   if(layer==WLAYER_STR) return "ESTRUTURAL";
   return "BARS";
}

//+------------------------------------------------------------------+
//| Features (janela k..k+w-1 da série de índices; j=0..w-1 velho->novo)
//+------------------------------------------------------------------+
double IdxAt(int c,int k){ return gIdx[c*gLi+k]; }

//--- t da média dos RETORNOS, erro-padrão Newey-West (Bartlett, L=3)
//    v1.20: substitui o t de slope sobre níveis (regressão espúria: 84% de
//    falsos positivos em random walk; NW sobre níveis não conserta).
//    Esta versão calibra em ~5-7% em ruído puro (nominal).
//    v1.40: núcleo extraído p/ série arbitrária (reuso pelo motor por par,
//    sem duplicar a matemática); TStat(c,k,w) é wrapper idêntico ao v1.30.
double TStatSer(const double &ser[],int off,int len,int k,int w)
{
   if(k+w>=len) return 0.0;
   double mu=0;
   for(int m=k;m<k+w;m++) mu+=ser[off+m]-ser[off+m+1];
   mu/=w;
   double g0=0,g1=0,g2=0,g3=0;
   for(int m=k;m<k+w;m++)
   {
      double e0=ser[off+m]-ser[off+m+1]-mu;
      g0+=e0*e0;
      if(m+1<k+w){ double e1=ser[off+m+1]-ser[off+m+2]-mu; g1+=e0*e1; }
      if(m+2<k+w){ double e2=ser[off+m+2]-ser[off+m+3]-mu; g2+=e0*e2; }
      if(m+3<k+w){ double e3=ser[off+m+3]-ser[off+m+4]-mu; g3+=e0*e3; }
   }
   g0/=w; g1/=(w-1); g2/=(w-2); g3/=(w-3);
   double v=g0+2.0*(0.75*g1+0.50*g2+0.25*g3);
   v=MathMax(v,0.1*g0);                     // piso: autocov. negativa
   double se=MathSqrt(v/w);
   return (se>0)? mu/se : 0.0;
}
double TStat(int c,int k,int w){ return TStatSer(gIdx,c*gLi,gLi,k,w); }
double EffRatioSer(const double &ser[],int off,int len,int k,int w)
{
   if(k+w>=len) return 0.0;
   double net=MathAbs(ser[off+k]-ser[off+k+w]), path=0;
   for(int m=k;m<k+w;m++) path+=MathAbs(ser[off+m]-ser[off+m+1]);
   return (path>0)? net/path : 0.0;
}
double EffRatio(int c,int k,int w){ return EffRatioSer(gIdx,c*gLi,gLi,k,w); }
double VolMom(int c,int k,int w)
{
   if(k+w>=gLi) return 0.0;
   double s=0,s2=0; int n=0;
   for(int m=k;m<k+w;m++){ double d=IdxAt(c,m)-IdxAt(c,m+1); s+=d; s2+=d*d; n++; }
   if(n<2) return 0.0;
   double mean=s/n, var=s2/n-mean*mean;
   double sd=(var>0)?MathSqrt(var*n/(n-1)):0.0;
   return (IdxAt(c,k)-IdxAt(c,k+w))/(sd*MathSqrt((double)w)+1e-12);
}
double Persist(int c,int k,int w)
{
   if(k+w>=gLi) return 0.0;
   int up=0,dn=0;
   for(int m=k;m<k+w;m++){ double d=IdxAt(c,m)-IdxAt(c,m+1); if(d>0)up++; else if(d<0)dn++; }
   double net=IdxAt(c,k)-IdxAt(c,k+w);
   return (net>=0)? (double)up/w : (double)dn/w;
}
double Convex(int c,int k,int w)
{
   if(k+w>=gLi) return 0.0;
   double jm=(w-1)/2.0, mu2=0;
   for(int j=0;j<w;j++){ double u=j-jm; mu2+=u*u; }
   mu2/=w;
   double num=0,den=0;
   for(int j=0;j<w;j++){ double u=j-jm, p2=u*u-mu2; num+=IdxAt(c,k+w-1-j)*p2; den+=p2*p2; }
   if(den<=0) return 0.0;
   double cq=num/den, s=0,s2=0; int n=0;
   for(int m=k;m<k+w;m++){ double d=IdxAt(c,m)-IdxAt(c,m+1); s+=d; s2+=d*d; n++; }
   double mean=s/n, var=s2/n-mean*mean;
   double sd=(var>0)?MathSqrt(var*n/(n-1)):0.0;
   return cq*((double)w*w)/(sd+1e-12);
}
double SerStd(const double &ser[], int c,int len,int k,int w)
{
   int hi=MathMin(k+w,len), n=hi-k;
   if(n<8) return 0.0;
   double s=0,s2=0;
   for(int m=k;m<hi;m++){ double v=ser[c*len+m]; s+=v; s2+=v*v; }
   double mean=s/n, var=s2/n-mean*mean;
   return (var>0)?MathSqrt(var*n/(n-1)):0.0;
}

//+------------------------------------------------------------------+
int StateAt(int c,int k)
{
   double t=gTmid[c*gLf+k], at=MathAbs(t);
   double dir=(t>0?1.0:(t<0?-1.0:0.0));
   double sdC=SerStd(gConv,c,gLf,k,gZWin);
   double sdA=SerStd(gAcc, c,gLf,k,gZWin);
   double cxz=(sdC>0)? gConv[c*gLf+k]/sdC : 0.0;
   double acz=(sdA>0)? gAcc[c*gLf+k]/sdA : 0.0;
   if(k==0) gAccZ0[c]=acz;
   double cx=cxz*dir, ac=acz*dir, pers=gPers[c*gLf+k];

   int st=ST_NOISE;
   bool emerging=(at<gTGate && at>=gTLow && MathAbs(acz)>=InpAccEmg &&
                  ((gAcc[c*gLf+k]>0 && gMomF[c*gLf+k]>0)||(gAcc[c*gLf+k]<0 && gMomF[c*gLf+k]<0)));
   bool mature  =(at>=gTGate && pers>=InpPersist);
   bool exhaust =(at>=gTGate && cx<=InpCxExh && ac<=InpAcExh);
   if(emerging) st=ST_EMERGING;
   if(mature)   st=ST_MATURE;
   if(exhaust)  st=ST_EXHAUSTED;
   return st;
}

//+------------------------------------------------------------------+
bool Compute()
{
   ENUM_TIMEFRAMES tf=Rtf(InpTF);
   gLs=InpBars;
   gLf=InpBars+gZWin;
   gLi=gLf+gWMid+2;
   int W=gLi+2;

   ArrayResize(gIdx,8*gLi); ArrayInitialize(gIdx,0.0);
   double ret[]; ArrayResize(ret,8*(gLi-1)); ArrayInitialize(ret,0.0);
   int cnt[8]; ArrayInitialize(cnt,0);

   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      double cl[]; ArraySetAsSeries(cl,true);
      int copied=CopyClose(gPair[p],tf,1,W,cl);   // só barras fechadas
      if(copied<W) continue;
      good++;
      int bi=gBaseIdx[p], qi=gQuoteIdx[p];
      for(int k=0;k<gLi-1;k++)
      {
         if(cl[k+1]<=0||cl[k]<=0) continue;
         double r=MathLog(cl[k]/cl[k+1]);
         ret[bi*(gLi-1)+k]+=r;
         ret[qi*(gLi-1)+k]-=r;
      }
      cnt[bi]++; cnt[qi]++;
   }
   if(good<gPairsN/2) return false;

   for(int c=0;c<8;c++)
   {
      if(cnt[c]<1) continue;
      gIdx[c*gLi+(gLi-1)]=0.0;
      for(int k=gLi-2;k>=0;k--)
         gIdx[c*gLi+k]=gIdx[c*gLi+k+1]+ret[c*(gLi-1)+k]/cnt[c];
   }

   ArrayResize(gTmid,8*gLf); ArrayResize(gER,8*gLf);
   ArrayResize(gMomF,8*gLf); ArrayResize(gMomM,8*gLf);
   ArrayResize(gPers,8*gLf); ArrayResize(gConv,8*gLf);
   ArrayResize(gAcc,8*gLf);  ArrayResize(gM,8*gLf);
   ArrayResize(gStateSer,8*gLs); ArrayResize(gDirSer,8*gLs);

   for(int c=0;c<8;c++)
   {
      for(int k=gLf-1;k>=0;k--)
      {
         gTmid[c*gLf+k]=TStat(c,k,gWMid);
         gER[c*gLf+k]  =EffRatio(c,k,gWMid);
         gMomF[c*gLf+k]=VolMom(c,k,gWFast);
         gMomM[c*gLf+k]=VolMom(c,k,gWMid);
         gPers[c*gLf+k]=Persist(c,k,gWMid);
         gConv[c*gLf+k]=Convex(c,k,gWMid);
         double t=gTmid[c*gLf+k];
         gM[c*gLf+k]=(t>0?1.0:(t<0?-1.0:0.0))*MathMin(MathAbs(t)/2.0,1.0)*gER[c*gLf+k];
      }
      double alpha=2.0/(InpAccSpan+1.0);
      double ema=gMomF[c*gLf+(gLf-1)]-gMomM[c*gLf+(gLf-1)];
      gAcc[c*gLf+(gLf-1)]=ema;
      for(int k=gLf-2;k>=0;k--)
      {
         double x=gMomF[c*gLf+k]-gMomM[c*gLf+k];
         ema=alpha*x+(1.0-alpha)*ema;
         gAcc[c*gLf+k]=ema;
      }
      // estados históricos (k=0..gLs-1) + direção
      for(int k=gLs-1;k>=0;k--)
      {
         gStateSer[c*gLs+k]=StateAt(c,k);
         double t0=gTmid[c*gLf+k];
         gDirSer[c*gLs+k]=(t0>0?1:(t0<0?-1:0));
      }
      // idade do estado atual
      int st0=gStateSer[c*gLs+0], age=1;
      for(int k=1;k<gLs;k++){ if(gStateSer[c*gLs+k]==st0) age++; else break; }
      gAge[c]=age;
   }
   return true;
}

//+------------------------------------------------------------------+
//| v1.40 — CAMADA RELACIONAL (descritiva; ver cabeçalho)             |
//| Motor por par: t NW + ER sobre o log-preço de cada par, com a     |
//| MESMA disciplina anti-repaint do Compute(): CopyClose(...,1,W).   |
//| Estado do par (enxuto, sem z-features): Madura |t|>=InpPairGate;  |
//| Emergindo-lite InpPairGateLow<=|t|<gate; Ruído resto. Exausta     |
//| fica fora da célula (exigiria z-win por par) — limitação no       |
//| cabeçalho. Antissimetria: célula(A,B) = espelho exato de (B,A),   |
//| verificada em SelfTestAntisym() na 1ª barra calculada.            |
//+------------------------------------------------------------------+
bool RelActive(){ return (InpRelational && gRelOk && !gRelSlow); }

int FindPair(int a,int b)
{
   for(int p=0;p<gPairsN;p++)
      if((gBaseIdx[p]==a && gQuoteIdx[p]==b)||(gBaseIdx[p]==b && gQuoteIdx[p]==a))
         return p;
   return -1;
}
//--- t orientado da célula (a,b): símbolo A+B usa t como está; B+A inverte
double PairCellT(int a,int b,int k)
{
   int p=FindPair(a,b);
   if(p<0 || !gPairOk[p]) return 0.0;
   return (gBaseIdx[p]==a)? gPairT[p*gLp+k] : -gPairT[p*gLp+k];
}
bool PairCellOk(int a,int b)
{
   int p=FindPair(a,b);
   return (p>=0 && gPairOk[p]);
}
int PairStateAbs(double t)
{
   double at=MathAbs(t);
   if(at>=gPairGate) return ST_MATURE;
   if(at>=gPairLow)  return ST_EMERGING;
   return ST_NOISE;
}
bool Spurious(int c,int k)
{
   if(!RelActive()) return false;
   return (MathAbs(gTmid[c*gLf+k])>=gTGate && gBrHard[c*gLs+k]<3.0/7.0);
}

void SelfTestAntisym()
{
   int tested=0; bool ok=true;
   for(int p=0;p<gPairsN && tested<3;p++)
   {
      if(!gPairOk[p]) continue;
      int a=gBaseIdx[p], b=gQuoteIdx[p];
      double tab=PairCellT(a,b,0), tba=PairCellT(b,a,0);
      if(MathAbs(tab+tba)>1e-12)
      {
         ok=false;
         Print(StringFormat("CSSM v1.41: ANTISSIMETRIA FALHOU em %s: t(%s,%s)=%.6f t(%s,%s)=%.6f",
               gPair[p],cur[a],cur[b],tab,cur[b],cur[a],tba));
      }
      tested++;
   }
   if(ok) Print(StringFormat("CSSM v1.41: antissimetria OK (%d pares amostrados).",tested));
}

bool ComputePairs()
{
   ulong us0=GetMicrosecondCount();
   gLp=gLs+gWMid+2;
   int W=gLp+2;
   ArrayResize(gPairT,  gPairsN*gLp); ArrayInitialize(gPairT,0.0);
   ArrayResize(gPairER, gPairsN*gLp); ArrayInitialize(gPairER,0.0);
   ArrayResize(gPairLog,gPairsN*gLp); ArrayInitialize(gPairLog,0.0);
   ArrayResize(gPairOk, gPairsN);
   ENUM_TIMEFRAMES tf=Rtf(InpTF);
   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      gPairOk[p]=false;
      double cl[]; ArraySetAsSeries(cl,true);
      int copied=CopyClose(gPair[p],tf,1,W,cl);      // só barras FECHADAS
      if(copied<W) continue;
      bool bad=false;
      for(int k=0;k<gLp;k++)
      {
         if(cl[k]<=0){ bad=true; break; }
         gPairLog[p*gLp+k]=MathLog(cl[k]);
      }
      if(bad) continue;
      for(int k=0;k<gLs;k++)
      {
         gPairT[p*gLp+k] =TStatSer(gPairLog,p*gLp,gLp,k,gWMid);
         gPairER[p*gLp+k]=EffRatioSer(gPairLog,p*gLp,gLp,k,gWMid);
      }
      gPairOk[p]=true; good++;
   }
   if(good<gPairsN/2)
   {
      gRelMs=(GetMicrosecondCount()-us0)/1000.0;
      return false;
   }

   // breadth por moeda: direção de referência = sinal do t do ÍNDICE (gTmid)
   ArrayResize(gBrSoft,8*gLs); ArrayInitialize(gBrSoft,0.0);
   ArrayResize(gBrHard,8*gLs); ArrayInitialize(gBrHard,0.0);
   for(int c=0;c<8;c++)
      for(int k=0;k<gLs;k++)
      {
         double ti=gTmid[c*gLf+k];
         double d=(ti>0?1.0:(ti<0?-1.0:0.0));
         int n=0,ns=0,nh=0;
         for(int p=0;p<gPairsN;p++)
         {
            if(!gPairOk[p]) continue;
            double tor;
            if(gBaseIdx[p]==c)       tor= gPairT[p*gLp+k];
            else if(gQuoteIdx[p]==c) tor=-gPairT[p*gLp+k];
            else continue;
            n++;
            if(d!=0.0 && tor*d>0){ ns++; if(tor*d>=gPairGate) nh++; }
         }
         if(n>0)
         {
            gBrSoft[c*gLs+k]=(double)ns/n;
            gBrHard[c*gLs+k]=(double)nh/n;
         }
      }

   gRelMs=(GetMicrosecondCount()-us0)/1000.0;
   if(!gRelLogged)
   {
      Print(StringFormat("CSSM v1.41: ComputePairs() em %.1f ms (%d pares, w=%d, gate=%.3f/%.3f).",
            gRelMs,good,gWMid,gPairGate,gPairLow));
      gRelLogged=true;
   }
   if(gRelMs>200.0)
   {
      gRelSlow=true;   // desliga a camada nas próximas barras; aviso no painel
      Print("CSSM v1.41: camada relacional DESLIGADA (ComputePairs > 200 ms).");
   }
   return true;
}

//--- alerta de amplitude: reconhecimento de tendência EM CURSO, não
//    previsão (pesquisa a11/v2: continuação pós-reconhecimento testada e
//    NULA). Só em transição, só barra fechada — mesmo padrão do CheckAlerts.
void CheckBreadthAlerts()
{
   if(!RelActive()){ gPrevBHInit=false; return; }
   if(InpAlertBreadth && gPrevBHInit)
      for(int c=0;c<8;c++)
      {
         bool high=(gBrHard[c*gLs+0]>=6.0/7.0-1e-9);
         if(high && !gPrevBHHigh[c])
         {
            int h=(int)MathRound(gBrHard[c*gLs+0]*7.0);
            Alert(StringFormat("CSSM: %s tendencia ampla %s (%d/7 confirmados)",
                  cur[c],gDirSer[c*gLs+0]>0?"ALTA":"BAIXA",h));
         }
      }
   for(int c=0;c<8;c++) gPrevBHHigh[c]=(gBrHard[c*gLs+0]>=6.0/7.0-1e-9);
   gPrevBHInit=true;
}

//+------------------------------------------------------------------+
//| Grade MTF: estado atual (k=0) das 8 moedas num TF arbitrário.    |
//| Reusa gIdx/gLi como rascunho e as funções de feature. O z-score  |
//| se adapta ao histórico disponível; abaixo do mínimo => sem dado. |
//+------------------------------------------------------------------+
bool ComputeGridTF(int gi)
{
   ENUM_TIMEFRAMES tf=gGTF[gi];
   // v1.41: janela efetiva do PRÓPRIO TF (antes a grade herdava o
   // InpWMid único do gráfico e comparava horizontes incomparáveis)
   SWin gw; WinFor(tf,gw);
   // disponibilidade: menor histórico entre os pares utilizáveis
   int minA=2147483647, okp=0;
   for(int p=0;p<gPairsN;p++)
   {
      int b=Bars(gPair[p],tf);
      if(b>=gw.wMid+160){ okp++; if(b<minA) minA=b; }
   }
   if(okp<gPairsN/2) return false;
   int zw=MathMin(gw.zWin, minA-gw.wMid-10);
   if(zw<150) return false;

   int Lf=zw, Li=Lf+gw.wMid+2, W=Li+2;
   gLi=Li;   // funções de feature leem gIdx/gLi
   ArrayResize(gIdx,8*Li); ArrayInitialize(gIdx,0.0);
   double ret[]; ArrayResize(ret,8*(Li-1)); ArrayInitialize(ret,0.0);
   int cnt[8]; ArrayInitialize(cnt,0);
   int good=0;
   for(int p=0;p<gPairsN;p++)
   {
      double cl[]; ArraySetAsSeries(cl,true);
      int copied=CopyClose(gPair[p],tf,1,W,cl);
      if(copied<W) continue;
      good++;
      int bi=gBaseIdx[p], qi=gQuoteIdx[p];
      for(int k=0;k<Li-1;k++)
      {
         if(cl[k+1]<=0||cl[k]<=0) continue;
         double r=MathLog(cl[k]/cl[k+1]);
         ret[bi*(Li-1)+k]+=r;
         ret[qi*(Li-1)+k]-=r;
      }
      cnt[bi]++; cnt[qi]++;
   }
   if(good<gPairsN/2) return false;
   for(int c=0;c<8;c++)
   {
      if(cnt[c]<1) continue;
      gIdx[c*Li+(Li-1)]=0.0;
      for(int k=Li-2;k>=0;k--)
         gIdx[c*Li+k]=gIdx[c*Li+k+1]+ret[c*(Li-1)+k]/cnt[c];
   }

   // séries locais p/ z-score (convexidade e aceleração)
   double cv[],ac[],mf[],mm[];
   ArrayResize(cv,8*Lf); ArrayResize(ac,8*Lf);
   ArrayResize(mf,8*Lf); ArrayResize(mm,8*Lf);
   double alpha=2.0/(InpAccSpan+1.0);
   for(int c=0;c<8;c++)
   {
      for(int k=Lf-1;k>=0;k--)
      {
         cv[c*Lf+k]=Convex(c,k,gw.wMid);
         mf[c*Lf+k]=VolMom(c,k,gw.wFast);
         mm[c*Lf+k]=VolMom(c,k,gw.wMid);
      }
      double ema=mf[c*Lf+(Lf-1)]-mm[c*Lf+(Lf-1)];
      ac[c*Lf+(Lf-1)]=ema;
      for(int k=Lf-2;k>=0;k--)
      {
         double x=mf[c*Lf+k]-mm[c*Lf+k];
         ema=alpha*x+(1.0-alpha)*ema;
         ac[c*Lf+k]=ema;
      }
   }
   // estado k=0 por moeda (mesma lógica do TF principal)
   for(int c=0;c<8;c++)
   {
      double t=TStat(c,0,gw.wMid), at=MathAbs(t);
      double dir=(t>0?1.0:(t<0?-1.0:0.0));
      double pers=Persist(c,0,gw.wMid);
      double sdC=SerStd(cv,c,Lf,0,zw), sdA=SerStd(ac,c,Lf,0,zw);
      double cxz=(sdC>0)? cv[c*Lf+0]/sdC : 0.0;
      double acz=(sdA>0)? ac[c*Lf+0]/sdA : 0.0;
      double cx=cxz*dir, a2=acz*dir;
      int stt=ST_NOISE;
      bool emerging=(at<gw.tGate && at>=gw.tLow && MathAbs(acz)>=InpAccEmg &&
                     ((ac[c*Lf+0]>0 && mf[c*Lf+0]>0)||(ac[c*Lf+0]<0 && mf[c*Lf+0]<0)));
      bool mature  =(at>=gw.tGate && pers>=InpPersist);
      bool exhaust =(at>=gw.tGate && cx<=InpCxExh && a2<=InpAcExh);
      if(emerging) stt=ST_EMERGING;
      if(mature)   stt=ST_MATURE;
      if(exhaust)  stt=ST_EXHAUSTED;
      gGridSt[gi*8+c]=stt;
      gGridDir[gi*8+c]=(int)dir;
   }
   return true;
}

//--- atualiza os TFs da grade que fecharam barra nova
void UpdateGrid()
{
   if(!InpMTF) return;
   for(int i=0;i<6;i++)
   {
      datetime t0=iTime(_Symbol,gGTF[i],0);
      if(t0==gGridLast[i] && gGridOk[i]) continue;
      gGridOk[i]=ComputeGridTF(i);
      gGridLast[i]=t0;
   }
}

//+------------------------------------------------------------------+
//| Buffers (mapeia k -> barras do gráfico; correto se InpTF==TF)    |
//+------------------------------------------------------------------+
void SetM(int c,int idx,double v)
{
   switch(c)
   {
      case 0: BM0[idx]=v; break; case 1: BM1[idx]=v; break;
      case 2: BM2[idx]=v; break; case 3: BM3[idx]=v; break;
      case 4: BM4[idx]=v; break; case 5: BM5[idx]=v; break;
      case 6: BM6[idx]=v; break; case 7: BM7[idx]=v; break;
   }
}
void SetSD(int c,int idx,double s,double d)
{
   switch(c)
   {
      case 0: BS0[idx]=s; BD0[idx]=d; break; case 1: BS1[idx]=s; BD1[idx]=d; break;
      case 2: BS2[idx]=s; BD2[idx]=d; break; case 3: BS3[idx]=s; BD3[idx]=d; break;
      case 4: BS4[idx]=s; BD4[idx]=d; break; case 5: BS5[idx]=s; BD5[idx]=d; break;
      case 6: BS6[idx]=s; BD6[idx]=d; break; case 7: BS7[idx]=s; BD7[idx]=d; break;
   }
}
void SetBr(int c,int idx,double h,double s)   // v1.40: buffers 24-39
{
   switch(c)
   {
      case 0: BH0[idx]=h; BB0[idx]=s; break; case 1: BH1[idx]=h; BB1[idx]=s; break;
      case 2: BH2[idx]=h; BB2[idx]=s; break; case 3: BH3[idx]=h; BB3[idx]=s; break;
      case 4: BH4[idx]=h; BB4[idx]=s; break; case 5: BH5[idx]=h; BB5[idx]=s; break;
      case 6: BH6[idx]=h; BB6[idx]=s; break; case 7: BH7[idx]=h; BB7[idx]=s; break;
   }
}
void FillBuffers(int total)
{
   int lo=MathMax(0,total-2-InpBars);
   for(int c=0;c<8;c++)
   {
      for(int i=lo;i<total;i++)
      { SetM(c,i,EMPTY_VALUE); SetSD(c,i,EMPTY_VALUE,EMPTY_VALUE); SetBr(c,i,EMPTY_VALUE,EMPTY_VALUE); }
      for(int k=0;k<InpBars && k<gLs;k++)
      {
         int idx=total-2-k; if(idx<0) break;
         SetM(c,idx,gM[c*gLf+k]);
         SetSD(c,idx,(double)gStateSer[c*gLs+k],(double)gDirSer[c*gLs+k]);
         if(gRelOk)
         {
            double dr=(double)gDirSer[c*gLs+k];
            SetBr(c,idx,gBrHard[c*gLs+k]*dr,gBrSoft[c*gLs+k]*dr);
         }
      }
      // barra em formação repete o último valor FECHADO (cabeçalho útil,
      // linha sem gap, anti-repaint preservado)
      if(total-1>=0 && gLs>0)
      {
         SetM(c,total-1,gM[c*gLf+0]);
         SetSD(c,total-1,(double)gStateSer[c*gLs+0],(double)gDirSer[c*gLs+0]);
         if(gRelOk)
         {
            double dr0=(double)gDirSer[c*gLs+0];
            SetBr(c,total-1,gBrHard[c*gLs+0]*dr0,gBrSoft[c*gLs+0]*dr0);
         }
      }
   }
}

//+------------------------------------------------------------------+
//| Objetos: helpers                                                  |
//+------------------------------------------------------------------+
void Lbl(string nm,int win,int x,int y,string txt,color clv)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_LABEL,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetString (0,nm,OBJPROP_TEXT,txt);
   ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
   ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,InpFont);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,clv);
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}
void Rect(string nm,int win,int x,int y,int w,int hgt,color bg,color border)
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
   ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
}

//+------------------------------------------------------------------+
//| Foco: destaca moedas do par do gráfico                            |
//+------------------------------------------------------------------+
void DetectFocusPair()
{
   gFocA=CurIdx(SymbolInfoString(_Symbol,SYMBOL_CURRENCY_BASE));
   gFocB=CurIdx(SymbolInfoString(_Symbol,SYMBOL_CURRENCY_PROFIT));
}
bool FocusActive(){ return (gFocus && gFocA>=0 && gFocB>=0 && gFocA!=gFocB); }

void ApplyFocus()
{
   bool f=FocusActive();
   for(int p=0;p<8;p++)
   {
      bool hot=(!f || p==gFocA || p==gFocB);
      PlotIndexSetInteger(p,PLOT_LINE_COLOR,hot?colArr[p]:COL_DIM);
      PlotIndexSetInteger(p,PLOT_LINE_WIDTH,hot?(f?3:2):1);
   }
}
void DrawBtn(int win)
{
   string nm=PFX+"btnFocus";
   if(ObjectFind(0,nm)<0)
   {
      ObjectCreate(0,nm,OBJ_BUTTON,win,0,0);
      ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,6);
      ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,4);
      ObjectSetInteger(0,nm,OBJPROP_XSIZE,120);
      ObjectSetInteger(0,nm,OBJPROP_YSIZE,18);
      ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
      ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,8);
      ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
   }
   if(FocusActive())
   {
      ObjectSetString (0,nm,OBJPROP_TEXT,"[ FOCO: "+cur[gFocA]+"/"+cur[gFocB]+" ]");
      ObjectSetInteger(0,nm,OBJPROP_COLOR,clrBlack);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,clrLimeGreen);
   }
   else
   {
      ObjectSetString (0,nm,OBJPROP_TEXT,"[ 8 MOEDAS ]");
      ObjectSetInteger(0,nm,OBJPROP_COLOR,clrWhite);
      ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,C'50,50,65');
      ObjectSetInteger(0,nm,OBJPROP_STATE,false);
   }

   // v1.40: botão MTX (aba matriz) — mesma infraestrutura do FOCO
   if(!InpRelational) return;
   string nx=PFX+"btnMtx";
   if(ObjectFind(0,nx)<0)
   {
      ObjectCreate(0,nx,OBJ_BUTTON,win,0,0);
      ObjectSetInteger(0,nx,OBJPROP_CORNER,CORNER_LEFT_UPPER);
      ObjectSetInteger(0,nx,OBJPROP_XDISTANCE,132);
      ObjectSetInteger(0,nx,OBJPROP_YDISTANCE,4);
      ObjectSetInteger(0,nx,OBJPROP_XSIZE,52);
      ObjectSetInteger(0,nx,OBJPROP_YSIZE,18);
      ObjectSetString (0,nx,OBJPROP_FONT,"Consolas");
      ObjectSetInteger(0,nx,OBJPROP_FONTSIZE,8);
      ObjectSetInteger(0,nx,OBJPROP_SELECTABLE,false);
   }
   if(gMtx)
   {
      ObjectSetString (0,nx,OBJPROP_TEXT,"[ MTX ]");
      ObjectSetInteger(0,nx,OBJPROP_COLOR,clrBlack);
      ObjectSetInteger(0,nx,OBJPROP_BGCOLOR,clrGoldenrod);
   }
   else
   {
      ObjectSetString (0,nx,OBJPROP_TEXT,"[ MTX ]");
      ObjectSetInteger(0,nx,OBJPROP_COLOR,clrWhite);
      ObjectSetInteger(0,nx,OBJPROP_BGCOLOR,C'50,50,65');
      ObjectSetInteger(0,nx,OBJPROP_STATE,false);
   }
}

//+------------------------------------------------------------------+
//| Rótulos na ponta das linhas                                       |
//+------------------------------------------------------------------+
void DrawEndLabels(int win)
{
   if(!InpEndLabels) return;
   ENUM_TIMEFRAMES ctf=(ENUM_TIMEFRAMES)_Period;
   datetime tEnd=iTime(_Symbol,ctf,0)+PeriodSeconds(ctf);
   bool f=FocusActive();

   // anti-colisão: ordena por M desc e impõe separação mínima vertical
   int ord[8]; for(int i=0;i<8;i++) ord[i]=i;
   for(int i=0;i<7;i++) for(int j=i+1;j<8;j++)
      if(gM[ord[j]*gLf+0]>gM[ord[i]*gLf+0]){ int t=ord[i]; ord[i]=ord[j]; ord[j]=t; }

   // separação mínima em unidades de preço: altura do texto em px -> preço
   int hpx=(int)ChartGetInteger(0,CHART_HEIGHT_IN_PIXELS,win);
   double range=1.2;                       // janela fixa -0.6..0.6
   double minSep=(hpx>0)? range*(InpFont+5)/(double)hpx : 0.05;

   double ypos[8];
   for(int r=0;r<8;r++)
   {
      double want=gM[ord[r]*gLf+0];
      if(r>0 && ypos[r-1]-want<minSep) want=ypos[r-1]-minSep;
      ypos[r]=want;
   }

   for(int r=0;r<8;r++)
   {
      int c=ord[r];
      string nm=PFX+"end"+cur[c];
      double v=gM[c*gLf+0];
      bool hot=(!f || c==gFocA || c==gFocB);
      if(ObjectFind(0,nm)<0)
      {
         ObjectCreate(0,nm,OBJ_TEXT,win,tEnd,v);
         ObjectSetString (0,nm,OBJPROP_FONT,"Consolas");
         ObjectSetInteger(0,nm,OBJPROP_ANCHOR,ANCHOR_LEFT);
         ObjectSetInteger(0,nm,OBJPROP_SELECTABLE,false);
      }
      ObjectSetInteger(0,nm,OBJPROP_TIME,tEnd);
      ObjectSetDouble (0,nm,OBJPROP_PRICE,ypos[r]);
      ObjectSetString (0,nm,OBJPROP_TEXT," "+cur[c]+StringFormat(" %+.2f",v));
      ObjectSetInteger(0,nm,OBJPROP_FONTSIZE,hot?InpFont:InpFont-1);
      ObjectSetInteger(0,nm,OBJPROP_COLOR,hot?colArr[c]:COL_DIM);
   }
}

//+------------------------------------------------------------------+
//| Painel v1.1                                                       |
//+------------------------------------------------------------------+
void DrawPanel()
{
   if(!InpPanel) return;
   int win=ChartWindowFind(); if(win<0) return;

   bool rel=RelActive();                    // v1.40: camada relacional ativa
   bool lens=(InpWindowMode==WM_HOURS && gLens!="");   // v1.41: linha da lente
   static int prevLayout=-1;                // -1 nunca; bit0 rel, bit1 lente
   int layout=(rel?1:0)+(lens?2:0);
   if(prevLayout!=-1 && prevLayout!=layout) ObjectsDeleteAll(0,PPFX);
   prevLayout=layout;

   int rh=InpFont+9;
   int colName=0, colBar=36, colState=116;
   int barW=72, stW=82;
   int ampW=(rel?48:0);                     // v1.40: coluna "amp" após o estado
   int colAmp=colState+stW+6;
   int colRest=204+ampW;
   int cellW=20;
   int colGrid=colRest+196;
   int colAlin=colGrid+6*cellW+8;
   int colW=(InpMTF? colAlin+40 : colRest+206);
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int x=cw-InpPanelX-colW+6; if(x<6) x=6;
   int y=InpPanelY;
   int chpx=(InpFont*7)/9; if(chpx<5) chpx=5;   // avanço aprox. Consolas

   bool foot2=(rel || (InpRelational && gRelSlow));
   int nrows=11+(foot2?1:0)+(lens?1:0);
   Rect(PPFX+"bg",win,x-6,y-6,colW,rh*nrows+16,C'24,24,32',C'80,80,90');
   string hdr=StringFormat("CSSM CONTEXTO  %s",TfStr(InpTF));
   if(InpWindowMode==WM_HOURS) hdr+=StringFormat("  w=%d%s",gWMid,LayerSfx(gLayer));
   Lbl(PPFX+"hd",win,x,y,hdr,clrWhiteSmoke);
   Lbl(PPFX+"hd2",win,x+colRest,y+rh," DIR    M      t   pers acc",C'150,150,150');
   Lbl(PPFX+"hd3",win,x+colState,y+rh,"ESTADO(idade)",C'150,150,150');
   if(rel) Lbl(PPFX+"hdA",win,x+colAmp,y+rh,"amp",C'150,150,150');
   if(InpMTF)
   {
      // v1.41: cabeçalho por coluna com marcador de camada (sufixo d/c/s
      // sobrescrito + texto progressivamente mais apagado). Um TF
      // ESTRUTURAL nunca deve ser lido como se detectasse o horizonte.
      for(int i=0;i<6;i++)
      {
         SWin hw; WinFor(gGTF[i],hw);
         color hc=C'150,150,150';
         if(hw.layer==WLAYER_CTX)      hc=C'122,122,130';
         else if(hw.layer==WLAYER_STR) hc=C'96,96,104';
         Lbl(PPFX+"hd4_"+(string)i,win,x+colGrid+i*cellW,y+rh,
             TfShort(gGTF[i])+LayerSfx(hw.layer),hc);
      }
      Lbl(PPFX+"hd5",win,x+colAlin,y+rh,"alin",C'150,150,150');
   }

   // ranking por M
   int ord[8]; for(int i=0;i<8;i++) ord[i]=i;
   for(int i=0;i<7;i++) for(int j=i+1;j<8;j++)
      if(gM[ord[j]*gLf+0]>gM[ord[i]*gLf+0]){ int t=ord[i]; ord[i]=ord[j]; ord[j]=t; }

   // maior |M| p/ escala das barras
   double mMax=0.05;
   for(int c=0;c<8;c++) mMax=MathMax(mMax,MathAbs(gM[c*gLf+0]));

   for(int r=0;r<8;r++)
   {
      int c=ord[r];
      int yy=y+rh*(r+2);
      double m=gM[c*gLf+0], t=gTmid[c*gLf+0], pe=gPers[c*gLf+0];
      int st=gStateSer[c*gLs+0], dr=gDirSer[c*gLs+0];
      bool spur=(rel && Spurious(c,0));

      // v1.40: marcador de força espúria (índice ativo sem confirmação <3/7)
      if(rel)
         Lbl(PPFX+"wr"+(string)r,win,x+colName,yy,
             spur? ShortToString(0x26A0):" ",clrOrange);

      // nome na cor da linha (desloca p/ dar lugar ao ⚠ quando rel)
      Lbl(PPFX+"nm"+(string)r,win,x+colName+(rel?13:0),yy,cur[c],colArr[c]);

      // barra de força: trilho + preenchimento a partir do centro
      int cx0=x+colBar, cy=yy+2, half=barW/2;
      Rect(PPFX+"tr"+(string)r,win,cx0,cy,barW,InpFont+2,C'38,38,46',C'55,55,62');
      int fill=(int)MathRound(half*MathMin(MathAbs(m)/mMax,1.0));
      if(fill<1) fill=1;
      int fx=(m>=0)? cx0+half : cx0+half-fill;
      color fc=(m>=0)? C'46,160,90' : C'190,60,50';
      Rect(PPFX+"fl"+(string)r,win,fx,cy,fill,InpFont+2,fc,fc);

      // estado: célula com fundo + idade
      Rect(PPFX+"sr"+(string)r,win,x+colState,yy,stW,InpFont+6,stBg[st],stBg[st]);
      Lbl(PPFX+"st"+(string)r,win,x+colState+4,yy+1,
          StringFormat("%s %d",stName[st],MathMin(gAge[c],99)),stTxt[st]);

      // v1.40: coluna amp — hard como número principal, soft apagado
      if(rel)
      {
         int hN=(int)MathRound(gBrHard[c*gLs+0]*7.0);
         int sN=(int)MathRound(gBrSoft[c*gLs+0]*7.0);
         color hc=(hN==0)? C'120,120,120' :
                  ((dr>0)? C'90,200,130' : C'230,120,105');
         Lbl(PPFX+"ah"+(string)r,win,x+colAmp,yy,
             StringFormat("%d/7",hN),hc);
         Lbl(PPFX+"as"+(string)r,win,x+colAmp+26,yy,
             ShortToString(0x2022)+IntegerToString(sN),C'110,110,118');
      }

      // resto da linha: DIR | M (colorível p/ espúria) | t pers acc
      string dirs=(dr>0)?"ALTA ":((dr<0)?"BAIXA":" --  ");
      Lbl(PPFX+"rw"+(string)r,win,x+colRest,yy,dirs,C'205,205,210');
      Lbl(PPFX+"rm"+(string)r,win,x+colRest+6*chpx,yy,
          StringFormat("%+5.2f",m),spur? C'130,130,135':C'205,205,210');
      Lbl(PPFX+"rx"+(string)r,win,x+colRest+12*chpx,yy,
          StringFormat("%+6.1f %4.2f  %s",t,pe,Arr(gAccZ0[c])),C'205,205,210');

      // grade MTF
      if(InpMTF)
      {
         int nUp=0,nDn=0;
         for(int i=0;i<6;i++)
         {
            string nc=PPFX+"g"+(string)r+"_"+(string)i;
            string nl=PPFX+"gl"+(string)r+"_"+(string)i;
            int gx=x+colGrid+i*cellW;
            if(!gGridOk[i])
            {
               Rect(nc,win,gx,yy,cellW-3,InpFont+6,C'40,40,46',C'40,40,46');
               Lbl(nl,win,gx+5,yy+1,".",C'120,120,120');
               continue;
            }
            int gs=gGridSt[i*8+c], gd=gGridDir[i*8+c];
            if(gs>=ST_EMERGING){ if(gd>0) nUp++; else if(gd<0) nDn++; }
            Rect(nc,win,gx,yy,cellW-3,InpFont+6,stBg[gs],stBg[gs]);
            string arrow=(gd>0)?ShortToString(0x25B2):((gd<0)?ShortToString(0x25BC):"-");
            Lbl(nl,win,gx+4,yy+1,arrow,stTxt[gs]);
         }
         int amax=MathMax(nUp,nDn);
         string atx=(amax==0)? " - " : StringFormat("%d/6%s",amax,
                     (nUp>=nDn)?ShortToString(0x25B2):ShortToString(0x25BC));
         color acl=(amax==0)? C'120,120,120' : ((nUp>=nDn)? C'90,200,130' : C'230,120,105');
         Lbl(PPFX+"al"+(string)r,win,x+colAlin,yy,atx,acl);
      }
   }
   Lbl(PPFX+"ft",win,x,y+rh*10+4,"contexto, nao e sinal de entrada",C'150,120,120');
   int fr=11;
   if(rel)
   {
      Lbl(PPFX+"ft2",win,x,y+rh*fr+4,
          ShortToString(0x26A0)+" = indice ativo sem confirmacao dos pares (<3/7)",
          C'150,120,120');
      fr++;
   }
   else if(InpRelational && gRelSlow)
   {
      Lbl(PPFX+"ft2",win,x,y+rh*fr+4,
          "camada relacional OFF (ComputePairs > 200 ms)",clrOrange);
      fr++;
   }
   // v1.41: lente efetiva — o que cada TF da grade realmente enxerga
   if(lens)
      Lbl(PPFX+"ft3",win,x,y+rh*fr+4,"lente: "+gLens,C'120,140,160');
}

//+------------------------------------------------------------------+
//| v1.40 — Aba MATRIZ 8x8 (alternada pelo botão MTX)                 |
//| Célula (a,b) = estado do PAR orientado: fundo na cor do estado,   |
//| texto M↑/M↓/E↑/E↓/· . Só recalculada/redesenhada quando visível   |
//| e em barra fechada (Recalc controla via gMtxDirty).               |
//+------------------------------------------------------------------+
void DrawMatrix()
{
   if(!InpPanel || !RelActive()) return;
   int win=ChartWindowFind(); if(win<0) return;

   int rh=InpFont+9;
   int cellw=30, hdrw=36;
   int colW=hdrw+8*cellw+16;
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int x=cw-InpPanelX-colW+6; if(x<6) x=6;
   int y=InpPanelY;
   string up=ShortToString(0x2191), dn=ShortToString(0x2193);

   Rect(MPFX+"bg",win,x-6,y-6,colW,rh*12+16,C'24,24,32',C'80,80,90');
   Lbl(MPFX+"hd",win,x,y,
       StringFormat("CSSM MATRIZ 8x8  %s  (t do PAR, w=%d)",TfStr(InpTF),gWMid),
       clrWhiteSmoke);

   for(int b=0;b<8;b++)
      Lbl(MPFX+"ch"+(string)b,win,x+hdrw+b*cellw+3,y+rh,cur[b],colArr[b]);

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
            Lbl(nl,win,gx+9,yy+1,"-",C'90,90,96');
            continue;
         }
         if(!PairCellOk(a,b))
         {
            Rect(nc,win,gx,yy,cellw-3,InpFont+6,C'40,40,46',C'40,40,46');
            Lbl(nl,win,gx+9,yy+1,"?",C'120,120,120');
            continue;
         }
         double t=PairCellT(a,b,0);
         int st=PairStateAbs(t);
         if(st==ST_NOISE)
         {
            Rect(nc,win,gx,yy,cellw-3,InpFont+6,C'40,40,46',C'40,40,46');
            Lbl(nl,win,gx+9,yy+1,ShortToString(0x00B7),C'150,150,150');
         }
         else
         {
            string txt=((st==ST_MATURE)?"M":"E")+((t>0)?up:dn);
            Rect(nc,win,gx,yy,cellw-3,InpFont+6,stBg[st],stBg[st]);
            Lbl(nl,win,gx+5,yy+1,txt,stTxt[st]);
         }
      }
   }

   // rodapé: líder por breadth_hard + decomposição de dominância (top-3)
   int lead=-1; double bh=-1.0;
   for(int c=0;c<8;c++)
      if(gDirSer[c*gLs+0]!=0 && gBrHard[c*gLs+0]>bh){ bh=gBrHard[c*gLs+0]; lead=c; }
   string foot="sem lider";
   if(lead>=0)
   {
      int hN=(int)MathRound(bh*7.0);
      // dominância: retorno log orientado de cada par do líder em gWMid barras (janela efetiva)
      double rets[8]; int  vsIdx[8]; int nd=0; double tot=0.0;
      for(int p=0;p<gPairsN;p++)
      {
         if(!gPairOk[p]) continue;
         int o=-1; double sgn=0.0;
         if(gBaseIdx[p]==lead){ o=gQuoteIdx[p]; sgn=1.0; }
         else if(gQuoteIdx[p]==lead){ o=gBaseIdx[p]; sgn=-1.0; }
         else continue;
         if(gWMid>=gLp) continue;
         double r=sgn*(gPairLog[p*gLp+0]-gPairLog[p*gLp+gWMid]);
         rets[nd]=r; vsIdx[nd]=o; nd++; tot+=MathAbs(r);
      }
      for(int i=0;i<nd-1;i++) for(int j=i+1;j<nd;j++)
         if(rets[j]>rets[i])
         { double tr=rets[i]; rets[i]=rets[j]; rets[j]=tr;
           int ti=vsIdx[i]; vsIdx[i]=vsIdx[j]; vsIdx[j]=ti; }
      foot=StringFormat("%s%s %d/7 | dom:",cur[lead],
                        (gDirSer[lead*gLs+0]>0)?up:dn,hN);
      for(int i=0;i<3 && i<nd;i++)
         foot+=StringFormat(" %s %+.0fbp %.0f%%%s",cur[vsIdx[i]],rets[i]*1e4,
               (tot>0)?100.0*MathAbs(rets[i])/tot:0.0,(i<2 && i<nd-1)?" ·":"");
   }
   Lbl(MPFX+"ft",win,x,y+rh*10+4,foot,C'200,200,205');
   Lbl(MPFX+"ft2",win,x,y+rh*11+4,
       "M=|t|>=gate  E=|t|>=low  |  leitura descritiva, nao e sinal",
       C'150,120,120');
}

//+------------------------------------------------------------------+
void CheckAlerts()
{
   if(!InpAlerts){ for(int c=0;c<8;c++) gPrevState[c]=gStateSer[c*gLs+0]; gPrevInit=true; return; }
   if(gPrevInit)
      for(int c=0;c<8;c++)
      {
         int st=gStateSer[c*gLs+0];
         if(st!=gPrevState[c] && (st==ST_MATURE||st==ST_EXHAUSTED))
            Alert(StringFormat("CSSM %s: %s -> %s (dir %s)",
                  TfStr(InpTF),cur[c],stName[st],gDirSer[c*gLs+0]>0?"ALTA":"BAIXA"));
      }
   for(int c=0;c<8;c++) gPrevState[c]=gStateSer[c*gLs+0];
   gPrevInit=true;
}

//+------------------------------------------------------------------+
int OnInit()
{
   SetIndexBuffer(0,BM0,INDICATOR_DATA);  SetIndexBuffer(1,BM1,INDICATOR_DATA);
   SetIndexBuffer(2,BM2,INDICATOR_DATA);  SetIndexBuffer(3,BM3,INDICATOR_DATA);
   SetIndexBuffer(4,BM4,INDICATOR_DATA);  SetIndexBuffer(5,BM5,INDICATOR_DATA);
   SetIndexBuffer(6,BM6,INDICATOR_DATA);  SetIndexBuffer(7,BM7,INDICATOR_DATA);
   SetIndexBuffer(8,BS0,INDICATOR_CALCULATIONS);  SetIndexBuffer(9,BS1,INDICATOR_CALCULATIONS);
   SetIndexBuffer(10,BS2,INDICATOR_CALCULATIONS); SetIndexBuffer(11,BS3,INDICATOR_CALCULATIONS);
   SetIndexBuffer(12,BS4,INDICATOR_CALCULATIONS); SetIndexBuffer(13,BS5,INDICATOR_CALCULATIONS);
   SetIndexBuffer(14,BS6,INDICATOR_CALCULATIONS); SetIndexBuffer(15,BS7,INDICATOR_CALCULATIONS);
   SetIndexBuffer(16,BD0,INDICATOR_CALCULATIONS); SetIndexBuffer(17,BD1,INDICATOR_CALCULATIONS);
   SetIndexBuffer(18,BD2,INDICATOR_CALCULATIONS); SetIndexBuffer(19,BD3,INDICATOR_CALCULATIONS);
   SetIndexBuffer(20,BD4,INDICATOR_CALCULATIONS); SetIndexBuffer(21,BD5,INDICATOR_CALCULATIONS);
   SetIndexBuffer(22,BD6,INDICATOR_CALCULATIONS); SetIndexBuffer(23,BD7,INDICATOR_CALCULATIONS);
   // v1.40: 24-31 breadth_hard*dir | 32-39 breadth_soft*dir
   SetIndexBuffer(24,BH0,INDICATOR_CALCULATIONS); SetIndexBuffer(25,BH1,INDICATOR_CALCULATIONS);
   SetIndexBuffer(26,BH2,INDICATOR_CALCULATIONS); SetIndexBuffer(27,BH3,INDICATOR_CALCULATIONS);
   SetIndexBuffer(28,BH4,INDICATOR_CALCULATIONS); SetIndexBuffer(29,BH5,INDICATOR_CALCULATIONS);
   SetIndexBuffer(30,BH6,INDICATOR_CALCULATIONS); SetIndexBuffer(31,BH7,INDICATOR_CALCULATIONS);
   SetIndexBuffer(32,BB0,INDICATOR_CALCULATIONS); SetIndexBuffer(33,BB1,INDICATOR_CALCULATIONS);
   SetIndexBuffer(34,BB2,INDICATOR_CALCULATIONS); SetIndexBuffer(35,BB3,INDICATOR_CALCULATIONS);
   SetIndexBuffer(36,BB4,INDICATOR_CALCULATIONS); SetIndexBuffer(37,BB5,INDICATOR_CALCULATIONS);
   SetIndexBuffer(38,BB6,INDICATOR_CALCULATIONS); SetIndexBuffer(39,BB7,INDICATOR_CALCULATIONS);

   for(int p=0;p<8;p++)
   {
      PlotIndexSetString(p,PLOT_LABEL,cur[p]);
      PlotIndexSetDouble(p,PLOT_EMPTY_VALUE,EMPTY_VALUE);
      PlotIndexSetInteger(p,PLOT_LINE_WIDTH,2);
   }

   gPairsN=0;
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
      gPairsN++; seen[key]=true;
   }
   Print("CSSM_Contexto v1.41: ",gPairsN," pares detectados.");

   DetectFocusPair();
   gFocus=InpFocusStart;
   gMtx=false; gMtxDirty=false;
   gRelOk=false; gRelSlow=false; gRelLogged=false; gPerfLogged=false;
   gPrevBHInit=false;
   for(int c=0;c<8;c++) gPrevBHHigh[c]=false;

   gGTF[0]=InpGT1; gGTF[1]=InpGT2; gGTF[2]=InpGT3;
   gGTF[3]=InpGT4; gGTF[4]=InpGT5; gGTF[5]=InpGT6;
   for(int i=0;i<6;i++){ gGridOk[i]=false; gGridLast[i]=0; }
   ArrayInitialize(gGridSt,0); ArrayInitialize(gGridDir,0);

   // v1.41: parâmetros efetivos do motor do gráfico (em WM_BARS recebem
   // os inputs legados — critério de aceite nº 1: v1.40 byte a byte)
   SWin wc; WinFor(InpTF,wc);
   gWMid=wc.wMid; gWFast=wc.wFast; gZWin=wc.zWin; gLayer=wc.layer;
   gTGate=wc.tGate; gTLow=wc.tLow;
   if(InpWindowMode==WM_HOURS && InpAutoGates)
   { gPairGate=GateFor(gWMid,false); gPairLow=GateFor(gWMid,true); }
   else
   { gPairGate=InpPairGate; gPairLow=InpPairGateLow; }

   // lente efetiva da grade (linha de status do painel)
   gLens="";
   if(InpWindowMode==WM_HOURS)
   {
      string det="",ctx="",str="";
      for(int i=0;i<6;i++)
      {
         SWin gw; WinFor(gGTF[i],gw);
         string nm=TfShort(gGTF[i]);
         if(gw.layer==WLAYER_DET)      det+=(det==""?"":" ")+nm+":"+IntegerToString(gw.wMid);
         else if(gw.layer==WLAYER_CTX) ctx+=(ctx==""?"":" ")+nm+":"+IntegerToString(gw.wMid);
         else                          str+=(str==""?"":" ")+nm;
      }
      gLens=StringFormat("%gh -> %s",InpHorizonHours,(det=="")?"(nenhum)":det);
      if(ctx!="") gLens+=StringFormat(" | ctx%gh -> %s",InpContextHours,ctx);
      if(str!="") gLens+=" | estr: "+str;
   }

   // v1.41: Journal — tabela de conversão (critério nº 2) e verificação
   // do GateFor (critério nº 3), impressas uma vez no init
   if(InpWindowMode==WM_HOURS)
   {
      Print(StringFormat("CSSM v1.41: modo HORAS — deteccao %gh, contexto %gh, piso %d barras.",
            InpHorizonHours,InpContextHours,WFLOOR));
      Print(StringFormat("CSSM v1.41: motor do grafico %s: w_mid=%d w_fast=%d z_win=%d camada=%s t=%.3f/%.3f par=%.3f/%.3f",
            TfStr(InpTF),gWMid,gWFast,gZWin,LayerName(gLayer),gTGate,gTLow,gPairGate,gPairLow));
      ENUM_TIMEFRAMES vtf[7]={PERIOD_M15,PERIOD_M30,PERIOD_H1,PERIOD_H4,PERIOD_D1,PERIOD_W1,PERIOD_MN1};
      for(int i=0;i<7;i++)
      {
         SWin w; WinFor(vtf[i],w);
         Print(StringFormat("CSSM v1.41:   %-3s w_mid=%2d w_fast=%2d z_win=%3d t_gate=%.3f t_low=%.3f [%s]",
               TfStr(vtf[i]),w.wMid,w.wFast,w.zWin,w.tGate,w.tLow,LayerName(w.layer)));
      }
      bool nodes=true;
      for(int i=0;i<5;i++)
         if(MathAbs(GateFor(GATE_W[i],false)-GATE_HI[i])>1e-12 ||
            MathAbs(GateFor(GATE_W[i],true )-GATE_LO[i])>1e-12) nodes=false;
      bool mono=true; double ph=99.0,pl=99.0;
      for(int w=WFLOOR;w<=96;w++)
      {
         double h=GateFor(w,false), l=GateFor(w,true);
         if(h>ph+1e-12 || l>pl+1e-12) mono=false;
         ph=h; pl=l;
      }
      Print(StringFormat("CSSM v1.41: GateFor — nos exatos: %s | interpolacao monotona 16..96: %s.",
            nodes?"OK":"FALHOU",mono?"OK":"FALHOU"));
      Print("CSSM v1.41: lente da grade: "+gLens);
   }
   else
      Print("CSSM v1.41: modo BARRAS — janelas e portoes dos inputs (comportamento v1.40 exato).");

   IndicatorSetDouble(INDICATOR_MINIMUM,-0.6);
   IndicatorSetDouble(INDICATOR_MAXIMUM, 0.6);
   IndicatorSetInteger(INDICATOR_LEVELS,3);
   IndicatorSetDouble (INDICATOR_LEVELVALUE,0, 0.25);
   IndicatorSetDouble (INDICATOR_LEVELVALUE,1, 0.0);
   IndicatorSetDouble (INDICATOR_LEVELVALUE,2,-0.25);
   IndicatorSetInteger(INDICATOR_LEVELSTYLE,0,STYLE_DOT);
   IndicatorSetInteger(INDICATOR_LEVELSTYLE,1,STYLE_SOLID);
   IndicatorSetInteger(INDICATOR_LEVELSTYLE,2,STYLE_DOT);
   IndicatorSetInteger(INDICATOR_LEVELWIDTH,0,1);
   IndicatorSetInteger(INDICATOR_LEVELWIDTH,1,2);
   IndicatorSetInteger(INDICATOR_LEVELWIDTH,2,1);
   IndicatorSetInteger(INDICATOR_LEVELCOLOR,0,C'90,90,100');
   IndicatorSetInteger(INDICATOR_LEVELCOLOR,1,C'120,120,132');
   IndicatorSetInteger(INDICATOR_LEVELCOLOR,2,C'90,90,100');
   IndicatorSetString (INDICATOR_SHORTNAME,"CSSM Contexto");
   IndicatorSetInteger(INDICATOR_DIGITS,3);
   EventSetTimer(2);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0,PFX);
   Comment("");
}

//+------------------------------------------------------------------+
void Recalc(int total,bool force=false)
{
   datetime t0=iTime(_Symbol,Rtf(InpTF),0);
   bool mainNew=(t0!=gLastBar) || !gPrevInit || force;
   bool gridNew=false;
   if(InpMTF && !mainNew)
      for(int i=0;i<6;i++)
         if(iTime(_Symbol,gGTF[i],0)!=gGridLast[i] || !gGridOk[i]){ gridNew=true; break; }
   if(!mainNew && !gridNew) return;

   ulong usR=GetMicrosecondCount();   // v1.41: tempo total do 1º Recalc
   bool didMain=false;
   if(mainNew)
   {
      if(!Compute())
      {
         Comment("CSSM: aguardando historico dos pares...");
         return;
      }
      didMain=true;
      Comment("");
      gLastBar=t0;
      // v1.40: camada relacional ANTES do FillBuffers (buffers 24-39 a
      // dependem); usa gTmid recém-calculado
      gRelOk=false;
      if(InpRelational && !gRelSlow)
      {
         gRelOk=ComputePairs();
         if(gRelOk && !gPrevBHInit) SelfTestAntisym();
         gMtxDirty=true;                    // matriz só redesenha em barra nova
      }
      FillBuffers(total);
   }
   UpdateGrid();
   if(didMain && !gPerfLogged)
   {
      gPerfLogged=true;
      Print(StringFormat("CSSM v1.41: Recalc inicial em %.1f ms (motor w=%d + pares + buffers + grade MTF).",
            (GetMicrosecondCount()-usR)/1000.0,gWMid));
   }
   ApplyFocus();
   int win=ChartWindowFind();
   if(win>=0){ DrawBtn(win); DrawEndLabels(win); }
   // v1.40: aba MATRIZ alterna com o painel-normal
   static int prevView=-1;                  // 0 painel, 1 matriz
   int view=(gMtx && RelActive())?1:0;
   if(prevView!=-1 && prevView!=view)
      ObjectsDeleteAll(0,(view==1)?PPFX:MPFX);
   prevView=view;
   if(view==1)
   {
      if(gMtxDirty){ DrawMatrix(); gMtxDirty=false; }
   }
   else DrawPanel();
   if(mainNew){ CheckAlerts(); CheckBreadthAlerts(); }
   ChartRedraw();
}

//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,const int prev_calculated,
                const datetime &time[],const double &open[],
                const double &high[],const double &low[],
                const double &close[],const long &tick_volume[],
                const long &volume[],const int &spread[])
{
   if(prev_calculated==0)
   {
      ArrayInitialize(BM0,EMPTY_VALUE); ArrayInitialize(BM1,EMPTY_VALUE);
      ArrayInitialize(BM2,EMPTY_VALUE); ArrayInitialize(BM3,EMPTY_VALUE);
      ArrayInitialize(BM4,EMPTY_VALUE); ArrayInitialize(BM5,EMPTY_VALUE);
      ArrayInitialize(BM6,EMPTY_VALUE); ArrayInitialize(BM7,EMPTY_VALUE);
      ArrayInitialize(BS0,EMPTY_VALUE); ArrayInitialize(BS1,EMPTY_VALUE);
      ArrayInitialize(BS2,EMPTY_VALUE); ArrayInitialize(BS3,EMPTY_VALUE);
      ArrayInitialize(BS4,EMPTY_VALUE); ArrayInitialize(BS5,EMPTY_VALUE);
      ArrayInitialize(BS6,EMPTY_VALUE); ArrayInitialize(BS7,EMPTY_VALUE);
      ArrayInitialize(BD0,EMPTY_VALUE); ArrayInitialize(BD1,EMPTY_VALUE);
      ArrayInitialize(BD2,EMPTY_VALUE); ArrayInitialize(BD3,EMPTY_VALUE);
      ArrayInitialize(BD4,EMPTY_VALUE); ArrayInitialize(BD5,EMPTY_VALUE);
      ArrayInitialize(BD6,EMPTY_VALUE); ArrayInitialize(BD7,EMPTY_VALUE);
      ArrayInitialize(BH0,EMPTY_VALUE); ArrayInitialize(BH1,EMPTY_VALUE);
      ArrayInitialize(BH2,EMPTY_VALUE); ArrayInitialize(BH3,EMPTY_VALUE);
      ArrayInitialize(BH4,EMPTY_VALUE); ArrayInitialize(BH5,EMPTY_VALUE);
      ArrayInitialize(BH6,EMPTY_VALUE); ArrayInitialize(BH7,EMPTY_VALUE);
      ArrayInitialize(BB0,EMPTY_VALUE); ArrayInitialize(BB1,EMPTY_VALUE);
      ArrayInitialize(BB2,EMPTY_VALUE); ArrayInitialize(BB3,EMPTY_VALUE);
      ArrayInitialize(BB4,EMPTY_VALUE); ArrayInitialize(BB5,EMPTY_VALUE);
      ArrayInitialize(BB6,EMPTY_VALUE); ArrayInitialize(BB7,EMPTY_VALUE);
      gLastBar=0; gPrevInit=false;
   }
   // barra em formação: repete o último valor fechado a cada tick (o MT5
   // cria o elemento novo como 0.0 a cada barra; sem isto o cabeçalho da
   // janela mostra 0.000 até o próximo recálculo)
   int last=rates_total-1;
   if(last>=0 && gLs>0 && ArraySize(gM)>0)
   {
      for(int c=0;c<8;c++)
      {
         SetM(c,last,gM[c*gLf+0]);
         SetSD(c,last,(double)gStateSer[c*gLs+0],(double)gDirSer[c*gLs+0]);
         if(gRelOk && ArraySize(gBrHard)>=8*gLs)   // v1.40: cópia cosmética
         {
            double dr0=(double)gDirSer[c*gLs+0];
            SetBr(c,last,gBrHard[c*gLs+0]*dr0,gBrSoft[c*gLs+0]*dr0);
         }
      }
   }
   Recalc(rates_total);
   return rates_total;
}

//+------------------------------------------------------------------+
void OnTimer()
{
   int total=Bars(_Symbol,PERIOD_CURRENT);
   if(total>0) Recalc(total);
}

//+------------------------------------------------------------------+
void OnChartEvent(const int id,const long &lparam,const double &dparam,const string &sparam)
{
   if(id==CHARTEVENT_OBJECT_CLICK && sparam==PFX+"btnFocus")
   {
      gFocus=!gFocus;
      DetectFocusPair();
      ApplyFocus();
      int win=ChartWindowFind();
      if(win>=0){ DrawBtn(win); DrawEndLabels(win); }
      ObjectSetInteger(0,PFX+"btnFocus",OBJPROP_STATE,false);
      ChartRedraw();
   }
   // v1.40: alterna painel-normal <-> matriz (persiste como o FOCO)
   if(id==CHARTEVENT_OBJECT_CLICK && sparam==PFX+"btnMtx")
   {
      gMtx=!gMtx;
      int win=ChartWindowFind();
      if(win>=0) DrawBtn(win);
      if(gMtx && RelActive())
      {
         ObjectsDeleteAll(0,PPFX);
         DrawMatrix();
         gMtxDirty=false;
      }
      else
      {
         ObjectsDeleteAll(0,MPFX);
         DrawPanel();
      }
      ObjectSetInteger(0,PFX+"btnMtx",OBJPROP_STATE,false);
      ChartRedraw();
   }
}
//+------------------------------------------------------------------+
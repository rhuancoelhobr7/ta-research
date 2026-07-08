//+------------------------------------------------------------------+
//|                                     CurrencySlopeStrength.mq5     |
//|   Forca de moeda por slope de TMA, estilo Anderson Bonoto.       |
//|   - Linhas (TF do grafico) + box +/-0.2                          |
//|   - Painel com 3 timeframes lado a lado (ranking forte->fraca)   |
//|   - Sinal: moeda fora da box (|val|>box) = impulso.              |
//|     Topo fora por cima + fundo fora por baixo = trend novo.      |
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
#property version   "2.32"
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

input int    InpMAPeriod = 20;   // periodo da TMA (original: 20)
input int    InpSlope    = 1;    // lookback do slope (original CSS: 1)
input int    InpVolWin   = 20;   // janela p/ normalizar pela volatilidade (legado)
input int    InpATRPeriod= 100;  // ATR p/ normalizar slope (original: 100)
input bool   InpUseATR   = true; // usar ATR(100) em vez de stdev (modo original)
input double InpScale    = 0.40; // escala (afine ate bater a faixa do Anderson)
input double InpBox      = 0.20; // box +/- (LevelCrossValue)
input double InpScaleMax = 1.00; // escala fixa da janela (+/-): enquadra a box
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
input double InpExtLevel = 0.50; // nivel exaustao (a19: SEM base empirica; ver InpShowExt)
input bool   InpShowExt  = false;// mostrar linhas 0.50? (a19 Q1b: transicao real ~0.17, nao 0.50)
input double InpTrigger  = 0.20; // trigger p/ cores de estado (modo par)
input int    InpPanelX   = 12;   // painel: margem a partir da DIREITA
input int    InpPanelY   = 16;   // painel Y
input int    InpFont     = 9;    // fonte do painel
input bool   InpAlerts   = false; // alertas de cruzamento da box (ligue se quiser)
input double InpDiffThr  = 0.0;  // distancia minima de forca (regra de ouro)
input bool   InpAddSunday= true; // somar candle de domingo na segunda
input int    InpPesoK    = 3;    // k (barras fechadas do TF) p/ dpeso — pre-registro a13

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
string PFX = "CSS_";
bool   gSingle = false; // estado do botao linha unica
bool   gBoxPrev[8];     // estado anterior: estava fora da box?
bool   gHide[8];        // moeda oculta? (toggle pelo painel)
int    gRowCur[8];      // linha r do painel (col A) -> indice da moeda
bool   gAlertInit=false;

//+------------------------------------------------------------------+
int CurIdx(string code){ for(int i=0;i<8;i++) if(cur[i]==code) return i; return -1; }
ENUM_TIMEFRAMES Rtf(ENUM_TIMEFRAMES tf){ return (tf==PERIOD_CURRENT)?(ENUM_TIMEFRAMES)_Period:tf; }
string TfStr(ENUM_TIMEFRAMES tf){ string s=EnumToString(Rtf(tf)); StringReplace(s,"PERIOD_",""); return s; }
double Clamp(double v,double lo,double hi){ return (v<lo?lo:(v>hi?hi:v)); }

//+------------------------------------------------------------------+
//| Desvio-padrao dos retornos (cl em serie: cl[0]=atual)            |
double Vol(const double &cl[], int n)
{
   int m=0; double s=0,s2=0;
   for(int i=0;i<n;i++){ if(cl[i+1]==0) continue; double r=(cl[i]-cl[i+1])/cl[i+1]; s+=r; s2+=r*r; m++; }
   if(m<2) return 0;
   double mean=s/m, var=s2/m-mean*mean;
   return (var>0)?MathSqrt(var):0;
}
//+------------------------------------------------------------------+
//| ATR em pontos do par, normalizado pelo proprio preco (cl serie). |
//| Retorna ATR relativo (ATR/preco) para escala comparavel.         |
double ATRrel(const double &cl[], int copied, int per)
{
   // Formula original CSS: ATR(100) deslocando +10 candles, dividido por 10.
   // addSundayToMonday: corretoras com candle de domingo deslocam +1.
   int shift=10 + (InpAddSunday?1:0);
   int n=MathMin(per,copied-1-shift);
   if(n<2) return 0;
   double s=0; int m=0;
   for(int i=shift;i<shift+n;i++)
   {
      if(i+1>=copied) break;
      double tr=MathAbs(cl[i]-cl[i+1]);
      s+=tr; m++;
   }
   if(m<1) return 0;
   double atr=(s/m)/10.0;            // divisao por 10 (original)
   double price=cl[0]; if(price==0) return 0;
   return atr/price;                 // relativo ao preco
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
//| Valor de forca por moeda na barra de shift k p/ um TF.           |
//| k=0: barra em formacao (painel legado). k>=1: barra FECHADA —    |
//| e o que a camada de peso do v2.30 usa (sem repaint).             |
int ComputeAt(ENUM_TIMEFRAMES tf, int kShift, double &out[])
{
   double acc[8]; ArrayInitialize(acc,0);
   int good=0;
   int W = 2*InpMAPeriod + InpSlope + MathMax(InpVolWin,InpATRPeriod) + 16;
   double rs = MathSqrt((double)InpSlope);

   // Ancora temporal p/ backtest (alinha o painel com a barra do grafico)
   datetime anchor=0; bool useAnchor=false;
   if(InpSyncBars)
   {
      datetime tt[];
      if(CopyTime(_Symbol,tf,0,1,tt)==1){ anchor=tt[0]; useAnchor=true; }
   }

   for(int p=0;p<gPairsN;p++)
   {
      double cl[]; ArraySetAsSeries(cl,true);
      int copied;
      if(useAnchor) copied=CopyClose(gPair[p],tf,anchor,W,cl);
      else          copied=CopyClose(gPair[p],tf,0,W,cl);
      if(copied < InpMAPeriod+InpSlope+kShift+3) continue;
      double norm;
      if(InpUseATR) norm=ATRrel(cl,copied,InpATRPeriod)*rs;
      else          norm=Vol(cl, MathMin(InpVolWin,copied-1))*rs;
      double tma[]; TMA(cl,copied,InpMAPeriod,tma);
      if(kShift+InpSlope>copied-1) continue;
      double prev=tma[kShift+InpSlope]; if(prev==0) continue;
      double price=cl[kShift]; if(price==0) continue;
      double z=((tma[kShift]-prev)/price)/(norm+1e-12);
      acc[gBaseIdx[p]]  += Clamp(z*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
      acc[gQuoteIdx[p]] -= Clamp(z*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
      good++;
   }
   for(int c=0;c<8;c++) out[c]=(cnt[c]>0)?acc[c]/cnt[c]:0;
   return good;
}
int ComputeNow(ENUM_TIMEFRAMES tf, double &out[]) { return ComputeAt(tf,0,out); }
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
   for(int k=0;k<kbars;k++)
   {
      int idx=total-1-k; if(idx<0) break;
      buf[idx]=S[c*kbars+k]/cnt[c];
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
      int idx=total-1-k; if(idx<0) continue;
      double vb=S[iBase *kbars+k]/cnt[iBase];
      double vq=S[iQuote*kbars+k]/cnt[iQuote];
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
         int idx=total-1-k; if(idx<0) break;
         double v=EMPTY_VALUE;
         if(cnt[c]>0 && k+InpPesoK<kbars)
            v=MathAbs(S[c*kbars+k]/cnt[c])-MathAbs(S[c*kbars+k+InpPesoK]/cnt[c]);
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
   if(total<InpMAPeriod+InpSlope+MathMax(InpVolWin,InpATRPeriod)+6 || gPairsN<1) return false;
   int kbars=MathMin(InpBars,total-2);
   double S[]; ArrayResize(S,8*kbars); ArrayInitialize(S,0);
   int W=kbars+2*InpMAPeriod+InpSlope+MathMax(InpVolWin,InpATRPeriod)+16;
   double rs=MathSqrt((double)InpSlope);
   int good=0;
   ENUM_TIMEFRAMES tf=Rtf(InpLineTF);

   // Ancora temporal: no backtest/historico, usa o tempo da barra atual
   // do grafico para alinhar as linhas com as barras antigas.
   datetime anchor=0;
   bool useAnchor=false;
   if(InpSyncBars)
   {
      datetime tt[];
      if(CopyTime(_Symbol,tf,0,1,tt)==1){ anchor=tt[0]; useAnchor=true; }
   }

   for(int p=0;p<gPairsN;p++)
   {
      double cl[]; ArraySetAsSeries(cl,true);
      int copied;
      if(useAnchor)
         copied=CopyClose(gPair[p],tf,anchor,W,cl);  // ancorado no tempo
      else
         copied=CopyClose(gPair[p],tf,0,W,cl);
      if(copied < InpMAPeriod+InpSlope+3) continue;
      good++;
      double norm;
      if(InpUseATR) norm=ATRrel(cl,copied,InpATRPeriod)*rs;
      else          norm=Vol(cl, MathMin(InpVolWin,copied-1))*rs;
      double tma[]; TMA(cl,copied,InpMAPeriod,tma);
      int bi=gBaseIdx[p], qi=gQuoteIdx[p];
      for(int k=0;k<kbars;k++)
      {
         if(k+InpSlope>copied-1) break;
         double prev=tma[k+InpSlope]; if(prev==0) continue;
         double price=cl[k]; if(price==0) continue;
         double z=((tma[k]-prev)/price)/(norm+1e-12);
         double val=Clamp(z*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
         S[bi*kbars+k]+=val; S[qi*kbars+k]-=val;
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
void Rect(string nm,int win,int x,int y,int w,int hgt,color bg)
{
   if(ObjectFind(0,nm)<0) ObjectCreate(0,nm,OBJ_RECTANGLE_LABEL,win,0,0);
   ObjectSetInteger(0,nm,OBJPROP_XDISTANCE,x);
   ObjectSetInteger(0,nm,OBJPROP_YDISTANCE,y);
   ObjectSetInteger(0,nm,OBJPROP_XSIZE,w);
   ObjectSetInteger(0,nm,OBJPROP_YSIZE,hgt);
   ObjectSetInteger(0,nm,OBJPROP_BGCOLOR,bg);
   ObjectSetInteger(0,nm,OBJPROP_BORDER_TYPE,BORDER_FLAT);
   ObjectSetInteger(0,nm,OBJPROP_COLOR,C'80,80,90');
   ObjectSetInteger(0,nm,OBJPROP_CORNER,CORNER_LEFT_UPPER);
   ObjectSetInteger(0,nm,OBJPROP_BACK,false);
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
}

void DrawBox(int win)
{
   HLine(PFX+"bxhi", win,  InpBox,     clrForestGreen, 2);
   HLine(PFX+"bxlo", win, -InpBox,     clrFireBrick,   2);
   HLine(PFX+"bxmid",win,  0.0,        C'70,70,80',    1);
   // Linhas de exaustao 0.50: DESLIGADAS por padrao (a19 Q1b — a
   // transicao exaustao->fraqueza real ocorre perto de ~0.17, nao 0.50)
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
   // header com horizonte real da TMA (v2.31/WM_HOURS)
   Lbl(PFX+cid+"h",win,x,y, TfStr(tf)+ShortToString(0x00B7)+HorizonStr(tf)+mark,
       (trend&&hasGas)?clrGold:clrWhiteSmoke);
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
      Rect(PFX+cid+"cell"+(string)r,win,x-2,y+rh*(r+1)-1,colW-4,rh-1,cellBg);
      // barra de forca proporcional (|V| / ScaleMax) na base da celula
      int wmax=colW-8;
      int wbar=(int)MathRound(wmax*MathMin(MathAbs(V[c])/InpScaleMax,1.0));
      color barc=(V[c]>=0)?C'70,190,90':C'220,90,80';
      if(gHide[c]) barc=C'70,70,70';
      Rect(PFX+cid+"bar"+(string)r,win,x,y+rh*(r+1)+rh-4,MathMax(wbar,1),2,barc);
      // seta de direcao (k=3 barras fechadas; leitura do ciclo a19)
      string ar=(dir[c]>0)?up:((dir[c]<0)?dn:ShortToString(0x00B7));
      color shown = gHide[c] ? C'90,90,90' : colArr[c];
      string vis  = gHide[c] ? " (off)" : "";
      string lblName=PFX+cid+(string)r;
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
void DrawPanel(const double &V1[],const double &V2[],const double &V3[],
               const double &V4[],const double &V5[])
{
   if(!InpPanel) return;
   int win=ChartWindowFind(); if(win<0) return;
   int rh=InpFont+9, colW=94, y=InpPanelY;
   int panelW=colW*5+12;
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   // Ancora pela direita. Se nao couber, fica preso na borda esquerda.
   int x=cw-InpPanelX-panelW+6; if(x<6) x=6;
   Rect(PFX+"bg",win,x-6,y-6, panelW, rh*11+12, C'24,24,32');
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
   Lbl(PFX+"leg",win,x,y+rh*9,
       " verde=forca verm=fraqueza cinza=box | verde+"+dn+"=exaustao cinza+"+up+"=expansao",
       C'150,150,150');
   Lbl(PFX+"leg2",win,x,y+rh*10,
       " ciclo=LEITURA, nao sinal (a19: 40% falsa exaustao; a20: confluencia MTF nula)",
       C'150,150,150');
}
//+------------------------------------------------------------------+
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
   bool ok = ComputeSeries();
   double V1[8],V2[8],V3[8];
   int g1=ComputeNow(Rtf(InpTF1),V1);
   int g2=ComputeNow(Rtf(InpTF2),V2);
   int g3=ComputeNow(Rtf(InpTF3),V3);
   double V4[8],V5[8];
   int g4=ComputeNow(Rtf(InpTF4),V4);
   int g5=ComputeNow(Rtf(InpTF5),V5);
   // Alertas usam o TF do grafico (coluna 1 do painel = mais rapido)
   double Vlinha[8]; ComputeNow(Rtf(InpLineTF),Vlinha);
   CheckAlerts(Vlinha);
   int win=ChartWindowFind();
   if(win>=0){ DrawBox(win); DrawBtn(win); }
   DrawPanel(V1,V2,V3,V4,V5);
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

   IndicatorSetInteger(INDICATOR_LEVELS,0);
   IndicatorSetDouble(INDICATOR_MINIMUM,-InpScaleMax);
   IndicatorSetDouble(INDICATOR_MAXIMUM, InpScaleMax);
   IndicatorSetString(INDICATOR_SHORTNAME,"Currency Slope Strength (TMA)");
   IndicatorSetInteger(INDICATOR_DIGITS,3);
   EventSetTimer(2);
   return INIT_SUCCEEDED;
}
//+------------------------------------------------------------------+
void OnDeinit(const int reason){ EventKillTimer(); Comment(""); ObjectsDeleteAll(0,PFX); }
//+------------------------------------------------------------------+
void OnTimer(){ static int tr=0; if(!gReady){ gReady=Compute(); if(++tr>15) gReady=true; } }
//+------------------------------------------------------------------+
void OnChartEvent(const int id, const long &lparam,
                  const double &dparam, const string &sparam)
{
   if(id!=CHARTEVENT_OBJECT_CLICK) return;

   // Botao linha unica
   if(sparam==PFX+"btnSingle")
   {
      gSingle = !gSingle;
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

   // Clique num label da coluna A (PFX+"a"+r): alterna a moeda daquela linha
   string prefA=PFX+"a";
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
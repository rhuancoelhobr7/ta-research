//+------------------------------------------------------------------+
//|                                              CSSM_Contexto.mq5   |
//|  Painel de CONTEXTO por índices sintéticos G8 — v1.30            |
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
//|  IMPORTANTE: este indicador NÃO gera sinal de entrada.           |
//|  Estudo de evento (26k eventos) rejeitou continuação nestes      |
//|  horizontes. Painel = contexto; decisão de entrada é do trader.  |
//|                                                                  |
//|  Buffers p/ iCustom:                                             |
//|   0-7  M por moeda | 8-15 estado (0-3) | 16-23 direção (+1/-1)   |
//|  Ordem: USD,EUR,GBP,JPY,CHF,CAD,AUD,NZD. Ler com shift>=1.       |
//+------------------------------------------------------------------+
#property copyright "Carlos — motor CSSM (validado por estudo de evento)"
#property version   "1.30"
#property indicator_separate_window
#property indicator_buffers 24
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

//--- inputs: motor
input ENUM_TIMEFRAMES InpTF      = PERIOD_CURRENT; // TF do cálculo (= TF do gráfico p/ linhas alinhadas)
input int    InpWFast   = 16;    // janela rápida (barras)
input int    InpWMid    = 64;    // janela média (barras) — base das features
input int    InpZWin    = 500;   // janela do z-score adaptativo
input int    InpBars    = 300;   // barras a plotar
input int    InpAccSpan = 8;     // suavização EMA da aceleração
//--- inputs: máquina de estados
input double InpTGate   = 2.0;   // t mínimo p/ Madura
input double InpTLow    = 1.0;   // t mínimo p/ Emergindo
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

string   PFX="CSSM_";
datetime gLastBar=0;

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
//| Features (janela k..k+w-1 da série de índices; j=0..w-1 velho->novo)
//+------------------------------------------------------------------+
double IdxAt(int c,int k){ return gIdx[c*gLi+k]; }

//--- t da média dos RETORNOS, erro-padrão Newey-West (Bartlett, L=3)
//    v1.20: substitui o t de slope sobre níveis (regressão espúria: 84% de
//    falsos positivos em random walk; NW sobre níveis não conserta).
//    Esta versão calibra em ~5-7% em ruído puro (nominal).
double TStat(int c,int k,int w)
{
   if(k+w>=gLi) return 0.0;
   double mu=0;
   for(int m=k;m<k+w;m++) mu+=IdxAt(c,m)-IdxAt(c,m+1);
   mu/=w;
   double g0=0,g1=0,g2=0,g3=0;
   for(int m=k;m<k+w;m++)
   {
      double e0=IdxAt(c,m)-IdxAt(c,m+1)-mu;
      g0+=e0*e0;
      if(m+1<k+w){ double e1=IdxAt(c,m+1)-IdxAt(c,m+2)-mu; g1+=e0*e1; }
      if(m+2<k+w){ double e2=IdxAt(c,m+2)-IdxAt(c,m+3)-mu; g2+=e0*e2; }
      if(m+3<k+w){ double e3=IdxAt(c,m+3)-IdxAt(c,m+4)-mu; g3+=e0*e3; }
   }
   g0/=w; g1/=(w-1); g2/=(w-2); g3/=(w-3);
   double v=g0+2.0*(0.75*g1+0.50*g2+0.25*g3);
   v=MathMax(v,0.1*g0);                     // piso: autocov. negativa
   double se=MathSqrt(v/w);
   return (se>0)? mu/se : 0.0;
}
double EffRatio(int c,int k,int w)
{
   if(k+w>=gLi) return 0.0;
   double net=MathAbs(IdxAt(c,k)-IdxAt(c,k+w)), path=0;
   for(int m=k;m<k+w;m++) path+=MathAbs(IdxAt(c,m)-IdxAt(c,m+1));
   return (path>0)? net/path : 0.0;
}
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
   double sdC=SerStd(gConv,c,gLf,k,InpZWin);
   double sdA=SerStd(gAcc, c,gLf,k,InpZWin);
   double cxz=(sdC>0)? gConv[c*gLf+k]/sdC : 0.0;
   double acz=(sdA>0)? gAcc[c*gLf+k]/sdA : 0.0;
   if(k==0) gAccZ0[c]=acz;
   double cx=cxz*dir, ac=acz*dir, pers=gPers[c*gLf+k];

   int st=ST_NOISE;
   bool emerging=(at<InpTGate && at>=InpTLow && MathAbs(acz)>=InpAccEmg &&
                  ((gAcc[c*gLf+k]>0 && gMomF[c*gLf+k]>0)||(gAcc[c*gLf+k]<0 && gMomF[c*gLf+k]<0)));
   bool mature  =(at>=InpTGate && pers>=InpPersist);
   bool exhaust =(at>=InpTGate && cx<=InpCxExh && ac<=InpAcExh);
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
   gLf=InpBars+InpZWin;
   gLi=gLf+InpWMid+2;
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
         gTmid[c*gLf+k]=TStat(c,k,InpWMid);
         gER[c*gLf+k]  =EffRatio(c,k,InpWMid);
         gMomF[c*gLf+k]=VolMom(c,k,InpWFast);
         gMomM[c*gLf+k]=VolMom(c,k,InpWMid);
         gPers[c*gLf+k]=Persist(c,k,InpWMid);
         gConv[c*gLf+k]=Convex(c,k,InpWMid);
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
//| Grade MTF: estado atual (k=0) das 8 moedas num TF arbitrário.    |
//| Reusa gIdx/gLi como rascunho e as funções de feature. O z-score  |
//| se adapta ao histórico disponível; abaixo do mínimo => sem dado. |
//+------------------------------------------------------------------+
bool ComputeGridTF(int gi)
{
   ENUM_TIMEFRAMES tf=gGTF[gi];
   // disponibilidade: menor histórico entre os pares utilizáveis
   int minA=2147483647, okp=0;
   for(int p=0;p<gPairsN;p++)
   {
      int b=Bars(gPair[p],tf);
      if(b>=InpWMid+160){ okp++; if(b<minA) minA=b; }
   }
   if(okp<gPairsN/2) return false;
   int zw=MathMin(InpZWin, minA-InpWMid-10);
   if(zw<150) return false;

   int Lf=zw, Li=Lf+InpWMid+2, W=Li+2;
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
         cv[c*Lf+k]=Convex(c,k,InpWMid);
         mf[c*Lf+k]=VolMom(c,k,InpWFast);
         mm[c*Lf+k]=VolMom(c,k,InpWMid);
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
      double t=TStat(c,0,InpWMid), at=MathAbs(t);
      double dir=(t>0?1.0:(t<0?-1.0:0.0));
      double pers=Persist(c,0,InpWMid);
      double sdC=SerStd(cv,c,Lf,0,zw), sdA=SerStd(ac,c,Lf,0,zw);
      double cxz=(sdC>0)? cv[c*Lf+0]/sdC : 0.0;
      double acz=(sdA>0)? ac[c*Lf+0]/sdA : 0.0;
      double cx=cxz*dir, a2=acz*dir;
      int stt=ST_NOISE;
      bool emerging=(at<InpTGate && at>=InpTLow && MathAbs(acz)>=InpAccEmg &&
                     ((ac[c*Lf+0]>0 && mf[c*Lf+0]>0)||(ac[c*Lf+0]<0 && mf[c*Lf+0]<0)));
      bool mature  =(at>=InpTGate && pers>=InpPersist);
      bool exhaust =(at>=InpTGate && cx<=InpCxExh && a2<=InpAcExh);
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
void FillBuffers(int total)
{
   int lo=MathMax(0,total-2-InpBars);
   for(int c=0;c<8;c++)
   {
      for(int i=lo;i<total;i++){ SetM(c,i,EMPTY_VALUE); SetSD(c,i,EMPTY_VALUE,EMPTY_VALUE); }
      for(int k=0;k<InpBars && k<gLs;k++)
      {
         int idx=total-2-k; if(idx<0) break;
         SetM(c,idx,gM[c*gLf+k]);
         SetSD(c,idx,(double)gStateSer[c*gLs+k],(double)gDirSer[c*gLs+k]);
      }
      // barra em formação repete o último valor FECHADO (cabeçalho útil,
      // linha sem gap, anti-repaint preservado)
      if(total-1>=0 && gLs>0)
      {
         SetM(c,total-1,gM[c*gLf+0]);
         SetSD(c,total-1,(double)gStateSer[c*gLs+0],(double)gDirSer[c*gLs+0]);
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

   int rh=InpFont+9;
   int colName=0, colBar=36, colState=116, colRest=204;
   int barW=72, stW=82;
   int cellW=20;
   int colGrid=colRest+196;
   int colAlin=colGrid+6*cellW+8;
   int colW=(InpMTF? colAlin+40 : colRest+206);
   int cw=(int)ChartGetInteger(0,CHART_WIDTH_IN_PIXELS);
   int x=cw-InpPanelX-colW+6; if(x<6) x=6;
   int y=InpPanelY;

   Rect(PFX+"bg",win,x-6,y-6,colW,rh*11+16,C'24,24,32',C'80,80,90');
   Lbl(PFX+"hd",win,x,y,StringFormat("CSSM CONTEXTO  %s",TfStr(InpTF)),clrWhiteSmoke);
   Lbl(PFX+"hd2",win,x+colRest,y+rh," DIR    M      t   pers acc",C'150,150,150');
   Lbl(PFX+"hd3",win,x+colState,y+rh,"ESTADO(idade)",C'150,150,150');
   if(InpMTF)
   {
      string gh="";
      for(int i=0;i<6;i++) gh+=StringFormat("%-3s",TfShort(gGTF[i]));
      Lbl(PFX+"hd4",win,x+colGrid,y+rh,gh,C'150,150,150');
      Lbl(PFX+"hd5",win,x+colAlin,y+rh,"alin",C'150,150,150');
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

      // nome na cor da linha
      Lbl(PFX+"nm"+(string)r,win,x+colName,yy,cur[c],colArr[c]);

      // barra de força: trilho + preenchimento a partir do centro
      int cx0=x+colBar, cy=yy+2, half=barW/2;
      Rect(PFX+"tr"+(string)r,win,cx0,cy,barW,InpFont+2,C'38,38,46',C'55,55,62');
      int fill=(int)MathRound(half*MathMin(MathAbs(m)/mMax,1.0));
      if(fill<1) fill=1;
      int fx=(m>=0)? cx0+half : cx0+half-fill;
      color fc=(m>=0)? C'46,160,90' : C'190,60,50';
      Rect(PFX+"fl"+(string)r,win,fx,cy,fill,InpFont+2,fc,fc);

      // estado: célula com fundo + idade
      Rect(PFX+"sr"+(string)r,win,x+colState,yy,stW,InpFont+6,stBg[st],stBg[st]);
      Lbl(PFX+"st"+(string)r,win,x+colState+4,yy+1,
          StringFormat("%s %d",stName[st],MathMin(gAge[c],99)),stTxt[st]);

      // resto da linha
      string dirs=(dr>0)?"ALTA ":((dr<0)?"BAIXA":" --  ");
      Lbl(PFX+"rw"+(string)r,win,x+colRest,yy,
          StringFormat("%s %+5.2f %+6.1f %4.2f  %s",dirs,m,t,pe,Arr(gAccZ0[c])),
          C'205,205,210');

      // grade MTF
      if(InpMTF)
      {
         int nUp=0,nDn=0;
         for(int i=0;i<6;i++)
         {
            string nc=PFX+"g"+(string)r+"_"+(string)i;
            string nl=PFX+"gl"+(string)r+"_"+(string)i;
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
         Lbl(PFX+"al"+(string)r,win,x+colAlin,yy,atx,acl);
      }
   }
   Lbl(PFX+"ft",win,x,y+rh*10+4,"contexto, nao e sinal de entrada",C'150,120,120');
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
   Print("CSSM_Contexto v1.30: ",gPairsN," pares detectados.");

   DetectFocusPair();
   gFocus=InpFocusStart;

   gGTF[0]=InpGT1; gGTF[1]=InpGT2; gGTF[2]=InpGT3;
   gGTF[3]=InpGT4; gGTF[4]=InpGT5; gGTF[5]=InpGT6;
   for(int i=0;i<6;i++){ gGridOk[i]=false; gGridLast[i]=0; }
   ArrayInitialize(gGridSt,0); ArrayInitialize(gGridDir,0);

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

   if(mainNew)
   {
      if(!Compute())
      {
         Comment("CSSM: aguardando historico dos pares...");
         return;
      }
      Comment("");
      gLastBar=t0;
      FillBuffers(total);
   }
   UpdateGrid();
   ApplyFocus();
   int win=ChartWindowFind();
   if(win>=0){ DrawBtn(win); DrawEndLabels(win); }
   DrawPanel();
   if(mainNew) CheckAlerts();
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
}
//+------------------------------------------------------------------+
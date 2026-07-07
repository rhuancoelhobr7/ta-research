//+------------------------------------------------------------------+
//|                                          Export_CSS_Parity.mq5   |
//|  Paridade CSS da tela x pesquisa (css_screen.py).                |
//|                                                                  |
//|  POR QUE NAO LE OS BUFFERS DO INDICADOR: as linhas historicas do |
//|  v2.20 usam TMA CENTRADA (ate 20 barras futuras = repaint). O    |
//|  porte css_screen.py reproduz a LEITURA AO VIVO (barra corrente, |
//|  sem futuro). Para comparar como-com-como, este script recalcula |
//|  a leitura ao vivo em cada barra historica: CopyClose ancorado   |
//|  no tempo da barra + a MESMA aritmetica do v2.20 (TMA Gernard,   |
//|  ATRrel(100) shift 10+1, /10, z*0.40 clamp +/-0.98, media por    |
//|  moeda). Formulas copiadas verbatim do indicador.                |
//|                                                                  |
//|  USO: anexar ao grafico no TF desejado (script roda no TF do     |
//|  grafico). CSV sai em MQL5\Files\css_parity_{TF}.csv com as 8    |
//|  moedas por barra (ts = ABERTURA da barra, cronologico).         |
//|  No repo: python p2_css_parity.py --csv css_parity_H1.csv        |
//|  Universo: todos os pares G8 do Market Watch (= OnInit do v2.20).|
//|  Rode o p2 com --pares all28 para casar o universo.              |
//+------------------------------------------------------------------+
#property script_show_inputs
#property version "1.00"

input int  InpNBars     = 200;   // barras a exportar (a partir da ultima fechada)
input int  InpMAPeriod  = 20;    // TMA Gernard (fixo 20 na formula)
input int  InpSlope     = 1;     // lookback do slope
input int  InpATRPeriod = 100;   // ATRrel
input double InpScale   = 0.40;  // escala
input double InpScaleMax= 1.00;  // clamp +/-(max-0.02)
input bool InpAddSunday = true;  // shift ATR +1

string cur[8]={"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};
string gPair[]; int gBaseIdx[], gQuoteIdx[]; int gPairsN=0; int cnt[8];

int CurIdx(string c){ for(int i=0;i<8;i++) if(cur[i]==c) return i; return -1; }
double Clamp(double v,double lo,double hi){ return (v<lo?lo:(v>hi?hi:v)); }

// --- copias verbatim do CurrencySlopeStrength v2.20 ---------------
double ATRrel(const double &cl[], int copied, int per)
{
   int shift=10 + (InpAddSunday?1:0);
   int n=MathMin(per,copied-1-shift);
   if(n<2) return 0;
   double s=0; int m=0;
   for(int i=shift;i<shift+n;i++)
   {
      if(i+1>=copied) break;
      s+=MathAbs(cl[i]-cl[i+1]); m++;
   }
   if(m<1) return 0;
   double atr=(s/m)/10.0;
   double price=cl[0]; if(price==0) return 0;
   return atr/price;
}
void TMA(const double &cl[], int copied, int N, double &out[])
{
   ArrayResize(out,copied); ArraySetAsSeries(out,true);
   for(int i=0;i<copied;i++)
   {
      double dblSum=cl[i]*21.0, dblSumw=21.0;
      for(int jnx=1,knx=20; jnx<=20; jnx++,knx--)
      {
         int back=i+jnx;
         if(back<copied){ dblSum+=cl[back]*knx; dblSumw+=knx; }
         if(jnx<=i){ int fwd=i-jnx; if(fwd>=0){ dblSum+=cl[fwd]*knx; dblSumw+=knx; } }
      }
      out[i]=(dblSumw>0)? dblSum/dblSumw : cl[i];
   }
}
// -------------------------------------------------------------------

void OnStart()
{
   // universo: todos os pares G8 do Market Watch (igual OnInit do v2.20)
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
   Print("Export_CSS_Parity: ",gPairsN," pares.");

   ENUM_TIMEFRAMES tf=(ENUM_TIMEFRAMES)_Period;
   string tfs=EnumToString(tf); StringReplace(tfs,"PERIOD_","");
   int W=2*InpMAPeriod+InpSlope+InpATRPeriod+16;
   double rs=MathSqrt((double)InpSlope);

   datetime tm[]; ArraySetAsSeries(tm,true);
   if(CopyTime(_Symbol,tf,1,InpNBars,tm)<InpNBars)
   { Print("CopyTime falhou — aguarde o historico e rode de novo"); return; }

   string fn=StringFormat("css_parity_%s.csv",tfs);
   int f=FileOpen(fn,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(f==INVALID_HANDLE){ Print("FileOpen falhou"); return; }
   FileWrite(f,"ts","USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD");

   for(int k=InpNBars-1;k>=0;k--)      // cronologico; leitura AO VIVO na barra k
   {
      double acc[8]; ArrayInitialize(acc,0);
      for(int p=0;p<gPairsN;p++)
      {
         double cl[]; ArraySetAsSeries(cl,true);
         int copied=CopyClose(gPair[p],tf,tm[k],W,cl);   // ancorado no tempo da barra
         if(copied<InpMAPeriod+InpSlope+3) continue;
         double norm=ATRrel(cl,copied,InpATRPeriod)*rs;
         double tma[]; TMA(cl,copied,InpMAPeriod,tma);
         double prev=tma[InpSlope]; if(prev==0) continue;
         double price=cl[0]; if(price==0) continue;
         double z=((tma[0]-prev)/price)/(norm+1e-12);
         double val=Clamp(z*InpScale,-(InpScaleMax-0.02),(InpScaleMax-0.02));
         acc[gBaseIdx[p]]+=val; acc[gQuoteIdx[p]]-=val;
      }
      FileWrite(f,TimeToString(tm[k],TIME_DATE|TIME_MINUTES),
         DoubleToString(cnt[0]>0?acc[0]/cnt[0]:0,8),
         DoubleToString(cnt[1]>0?acc[1]/cnt[1]:0,8),
         DoubleToString(cnt[2]>0?acc[2]/cnt[2]:0,8),
         DoubleToString(cnt[3]>0?acc[3]/cnt[3]:0,8),
         DoubleToString(cnt[4]>0?acc[4]/cnt[4]:0,8),
         DoubleToString(cnt[5]>0?acc[5]/cnt[5]:0,8),
         DoubleToString(cnt[6]>0?acc[6]/cnt[6]:0,8),
         DoubleToString(cnt[7]>0?acc[7]/cnt[7]:0,8));
   }
   FileClose(f);
   Print("exportado: MQL5\\Files\\",fn," (",InpNBars," barras, leitura ao vivo)");
}
//+------------------------------------------------------------------+

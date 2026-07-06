//+------------------------------------------------------------------+
//|                                        Export_CSSM_Parity.mq5    |
//|  Paridade indicador x pesquisa (critério de aceite 6 do v1.40):  |
//|  lê os buffers 24-39 do CSSM_Contexto via iCustom e exporta CSV  |
//|  (moeda x 50 barras) p/ comparar com relational_H1_w64.parquet   |
//|  do repo ta-research (a11).                                      |
//|                                                                  |
//|  USO: anexar a um gráfico H1; ajustar InpCur; o CSV sai em       |
//|  MQL5\Files\cssm_parity_{CUR}.csv. No repo:                      |
//|    python - <<EOF                                                |
//|    import pandas as pd                                           |
//|    mt = pd.read_csv("cssm_parity_USD.csv", parse_dates=["ts"])   |
//|    br = pd.read_parquet("data/features/relational_H1_w64.parquet")|
//|    br = br[br.currency=="USD"].set_index("ts")                   |
//|    j = mt.set_index("ts").join(br, rsuffix="_py").dropna()       |
//|    print((j.breadth_hard_mt - j.breadth_hard*j["dir"]).abs().max())|
//|    EOF                                                           |
//|  NOTA: passe InpPairGate=2.137276 (gate exato da pesquisa) p/    |
//|  breadth idêntico; o default 2.13 do indicador é arredondado.    |
//|                                                                  |
//|  v1.01: (a) corrige o alinhamento POSICIONAL do iCustom — a      |
//|  chamada antiga pulava os 7 inputs visuais e o gate 2.137276     |
//|  caía em InpEndLabels (bool), nunca chegando em InpPairGate,     |
//|  que ficava no default 2.13; (b) adapta à ordem do Cssm v1.41    |
//|  (4 inputs de modo na frente), forçando WM_BARS — a pesquisa     |
//|  usa w=64 fixo, então a paridade é contra o modo legado.         |
//+------------------------------------------------------------------+
#property script_show_inputs
#property version "1.01"

input string InpCur      = "USD";     // moeda a exportar
input int    InpNBars    = 50;        // barras (a partir da última fechada)
input double InpPairGate = 2.137276;  // gate do PAR (exato da pesquisa)
input int    InpWMid     = 64;

string curArr[8]={"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};

void OnStart()
{
   int c=-1;
   for(int i=0;i<8;i++) if(curArr[i]==InpCur) c=i;
   if(c<0){ Print("moeda invalida: ",InpCur); return; }

   int h=iCustom(_Symbol,PERIOD_H1,"Cssm",
                 0,18.0,120.0,false,                    // v1.41: WM_BARS (w fixo, como a pesquisa)
                 PERIOD_H1,16,InpWMid,500,300,8,        // motor
                 2.0,1.0,0.55,0.75,-1.0,-0.75,          // estados
                 true,true,false,12,16,9,false,         // visual (não afeta buffers)
                 true,InpPairGate,1.28,false,           // camada relacional
                 false);                                // MTF off (não afeta buffers)
   if(h==INVALID_HANDLE){ Print("iCustom falhou"); return; }

   double bh[],bs[];
   if(CopyBuffer(h,24+c,1,InpNBars,bh)<InpNBars ||
      CopyBuffer(h,32+c,1,InpNBars,bs)<InpNBars)
   { Print("CopyBuffer falhou (aguarde o calculo e rode de novo)"); return; }
   ArraySetAsSeries(bh,true); ArraySetAsSeries(bs,true);

   datetime tm[]; CopyTime(_Symbol,PERIOD_H1,1,InpNBars,tm);
   ArraySetAsSeries(tm,true);

   string fn=StringFormat("cssm_parity_%s.csv",InpCur);
   int f=FileOpen(fn,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(f==INVALID_HANDLE){ Print("FileOpen falhou"); return; }
   FileWrite(f,"ts","breadth_hard_mt","breadth_soft_mt");
   for(int k=InpNBars-1;k>=0;k--)     // cronológico; ts = FECHAMENTO da barra
      FileWrite(f,TimeToString(tm[k]+PeriodSeconds(PERIOD_H1),
                               TIME_DATE|TIME_MINUTES),
                DoubleToString(bh[k],6),DoubleToString(bs[k],6));
   FileClose(f);
   Print("exportado: MQL5\\Files\\",fn," (",InpNBars," barras, ",InpCur,")");
   IndicatorRelease(h);
}
//+------------------------------------------------------------------+

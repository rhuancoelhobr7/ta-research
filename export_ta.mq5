//+------------------------------------------------------------------+
//|                                                    export_ta.mq5  |
//|  TAREFA -1 da agenda a22-a26: exporta OHLC + tick_volume + spread |
//|  dos 28 pares G8 em M15 (fallback H1 por par) para CSV, mais um   |
//|  broker_info.csv com fuso do servidor e metadados de normalizacao |
//|  de pips.                                                          |
//|                                                                    |
//|  USO (3 linhas):                                                   |
//|   1) copie este arquivo para <TerminalData>\MQL5\Scripts\ e       |
//|      compile no MetaEditor (F7);                                   |
//|   2) arraste "export_ta" para QUALQUER grafico com o terminal      |
//|      LOGADO e deixe rodar (baixa historico; pode levar minutos);   |
//|   3) quando o log imprimir "export_ta: DONE", devolva a pasta      |
//|      <TerminalData>\MQL5\Files\ta_export\ inteira.                 |
//|                                                                    |
//|  Saida: MQL5\Files\ta_export\{SYMBOL}_{TF}.csv  (um por par)       |
//|         MQL5\Files\ta_export\broker_info.csv    (meta long-format) |
//|  Idempotente: reescreve tudo se rodar de novo.                     |
//|                                                                    |
//|  Convencoes herdadas do repo ta-research:                          |
//|   - `time` em EPOCH SECONDS no fuso do SERVIDOR (Python faz        |
//|     pd.to_datetime(time, unit="s"); o offset esta no broker_info). |
//|   - barra em formacao (a mais recente) descartada.                 |
//|   - G8 na ordem canonica; testa {XY} e {YX} p/ achar o simbolo.    |
//+------------------------------------------------------------------+
#property script_show_inputs
#property version   "1.00"
#property strict

input bool InpExportM15    = true;   // exportar M15 (base). DESLIGUE p/ so M5 (rapido)
input int  InpYears        = 10;     // anos de historico M15 (min util ~5)
input int  InpMinBarsM15   = 30000;  // se M15 vier abaixo disto, cai p/ H1 no par
input int  InpM5Years      = 3;      // >0 exporta M5 desses ultimos anos (a29/a30); 0 = pula
input int  InpMaxLoadTries = 40;     // tentativas de espera do download assincrono
input int  InpLoadSleepMs  = 400;    // pausa entre tentativas (ms)

string G8[8] = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};

//--- handle global do broker_info (long format: scope,key,value) ----
int g_meta = INVALID_HANDLE;

void MetaRow(string scope,string key,string value)
{
   if(g_meta!=INVALID_HANDLE) FileWrite(g_meta,scope,key,value);
}

//--- nome do TF p/ arquivo/manifesto -------------------------------
string TfName(ENUM_TIMEFRAMES tf)
{
   if(tf==PERIOD_M5)  return "M5";
   if(tf==PERIOD_M15) return "M15";
   if(tf==PERIOD_H1)  return "H1";
   return EnumToString(tf);
}

//--- forca o download assincrono e devolve o nro de barras ---------
//    repete ate a contagem ESTABILIZAR (duas leituras iguais) ou
//    esgotar as tentativas. rates fica em ordem cronologica (0=antiga).
int LoadRates(string sym,ENUM_TIMEFRAMES tf,datetime from,datetime to,MqlRates &rates[])
{
   ArraySetAsSeries(rates,false);
   int prev=-1;
   for(int t=0;t<InpMaxLoadTries;t++)
   {
      int got=CopyRates(sym,tf,from,to,rates);
      if(got>0 && got==prev) return got;   // estabilizou
      prev=got;
      Sleep(InpLoadSleepMs);
   }
   return prev; // ultima contagem conhecida (pode ser <=0)
}

//--- exporta um par num TF; retorna barras escritas (0 = falhou) ----
int ExportPair(string sym,ENUM_TIMEFRAMES tf,datetime from,datetime to)
{
   MqlRates rates[];
   int got=LoadRates(sym,tf,from,to,rates);
   if(got<=1) return 0;   // precisa de ao menos 1 barra alem da em formacao

   int dg=(int)SymbolInfoInteger(sym,SYMBOL_DIGITS);
   string fname="ta_export\\"+sym+"_"+TfName(tf)+".csv";
   int f=FileOpen(fname,FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(f==INVALID_HANDLE){ Print("export_ta: FileOpen falhou p/ ",fname); return 0; }

   FileWrite(f,"time","open","high","low","close","tick_volume","spread");
   // descarta a ultima barra (mais recente = em formacao)
   int last=got-1;
   for(int i=0;i<last;i++)
   {
      FileWrite(f,
         (string)(long)rates[i].time,
         DoubleToString(rates[i].open ,dg),
         DoubleToString(rates[i].high ,dg),
         DoubleToString(rates[i].low  ,dg),
         DoubleToString(rates[i].close,dg),
         (string)(long)rates[i].tick_volume,
         (string)rates[i].spread);
   }
   FileClose(f);

   // manifesto no broker_info: cobertura + normalizacao de pips
   MetaRow(sym,"tf",TfName(tf));
   MetaRow(sym,"bars",(string)last);
   MetaRow(sym,"first_epoch",(string)(long)rates[0].time);
   MetaRow(sym,"last_epoch",(string)(long)rates[last-1].time);
   MetaRow(sym,"point",DoubleToString(SymbolInfoDouble(sym,SYMBOL_POINT),10));
   MetaRow(sym,"tick_size",DoubleToString(SymbolInfoDouble(sym,SYMBOL_TRADE_TICK_SIZE),10));
   MetaRow(sym,"digits",(string)dg);
   return last;
}

void OnStart()
{
   if(!FolderCreate("ta_export"))
   { Print("export_ta: FolderCreate(ta_export) falhou err=",GetLastError()); return; }

   g_meta=FileOpen("ta_export\\broker_info.csv",FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(g_meta==INVALID_HANDLE){ Print("export_ta: nao abriu broker_info.csv"); return; }
   FileWrite(g_meta,"scope","key","value");

   // --- meta global: broker + fuso (p/ inferir offset servidor<->GMT) ---
   datetime now  = TimeCurrent();
   datetime gmt  = TimeGMT();
   long     off  = (long)now-(long)gmt;   // offset do servidor vs GMT (segundos)
   MetaRow("global","broker",AccountInfoString(ACCOUNT_COMPANY));
   MetaRow("global","server",AccountInfoString(ACCOUNT_SERVER));
   MetaRow("global","time_current_epoch",(string)(long)now);
   MetaRow("global","time_current_str",TimeToString(now,TIME_DATE|TIME_MINUTES|TIME_SECONDS));
   MetaRow("global","time_gmt_epoch",(string)(long)gmt);
   MetaRow("global","time_gmt_str",TimeToString(gmt,TIME_DATE|TIME_MINUTES|TIME_SECONDS));
   MetaRow("global","server_gmt_offset_sec",(string)off);
   MetaRow("global","export_years",(string)InpYears);

   datetime from   = now-(datetime)((long)InpYears*365*24*60*60);
   datetime fromM5 = (InpM5Years>0) ? now-(datetime)((long)InpM5Years*365*24*60*60) : 0;

   int okM15=0, okH1=0, okM5=0, missing=0;
   for(int i=0;i<8;i++)
     for(int j=i+1;j<8;j++)
     {
        // resolve o simbolo real do broker (XY ou YX)
        string cand[2]={ G8[i]+G8[j], G8[j]+G8[i] };
        string sym="";
        for(int k=0;k<2;k++)
          if(SymbolSelect(cand[k],true)){ sym=cand[k]; break; }
        if(sym==""){ Print("export_ta: par ausente ",cand[0],"/",cand[1]); missing++; continue; }

        // M15 primeiro (se InpExportM15); se historico raso, cai p/ H1 nesse par
        if(InpExportM15)
        {
           int wrote=ExportPair(sym,PERIOD_M15,from,now);
           if(wrote>=InpMinBarsM15){ okM15++; }
           else
           {
              if(wrote>0) Print("export_ta: ",sym," M15 raso (",wrote," barras) -> fallback H1");
              int wh=ExportPair(sym,PERIOD_H1,from,now);
              if(wh>0){ okH1++; MetaRow(sym,"m15_fallback","H1"); }
              else { Print("export_ta: ",sym," sem M15 nem H1 utilizavel"); missing++; continue; }
           }
        }

        if(InpM5Years>0)
        {
           int wm5=ExportPair(sym,PERIOD_M5,fromM5,now);
           if(wm5>0) okM5++;
        }
        Print("export_ta: ",sym," ok (",i*8+j,")");
     }

   MetaRow("global","pairs_m15",(string)okM15);
   MetaRow("global","pairs_h1_fallback",(string)okH1);
   MetaRow("global","pairs_m5",(string)okM5);
   MetaRow("global","pairs_missing",(string)missing);
   FileClose(g_meta);

   Print("export_ta: DONE  M15=",okM15," H1fallback=",okH1,
         " M5=",okM5," ausentes=",missing,
         "  -> MQL5\\Files\\ta_export\\  (devolva a pasta inteira)");
}
//+------------------------------------------------------------------+

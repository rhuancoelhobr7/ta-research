//+------------------------------------------------------------------+
//|                                          s1_export_calendar.mq5  |
//|  Exporta o calendario economico do MT5 (CalendarValueHistory)    |
//|  para CSV — insumo do a18 (calendario x rotulos).                |
//|                                                                  |
//|  USO: script; rodar em qualquer grafico com o terminal LOGADO    |
//|  (o calendario exige conexao). Saida: MQL5\Files\calendar_mt5.csv|
//|  Copiar para o repo em data/calendar/calendar_mt5.csv e rodar    |
//|  `python a18_calendar.py --ingest` (que verifica o FUSO e grava  |
//|  o _meta.json; se a verificacao falhar, o a18 PARA e reporta).   |
//|                                                                  |
//|  Colunas: event_id,time_server,country,currency,name,importance, |
//|           actual,forecast,previous                               |
//|  - moeda pelo MqlCalendarCountry.currency (zona do euro -> EUR   |
//|    automaticamente); paises fora do G8 descartados.              |
//|  - LIMITACAO (pre-registro): `actual` e o valor ATUAL no         |
//|    provedor (revisoes nao reconstruiveis). Uso preditivo em T0   |
//|    so pode usar a AGENDA (evento, moeda, horario, importancia);  |
//|    actual/forecast so em descritivo pos-evento.                  |
//+------------------------------------------------------------------+
#property script_show_inputs
#property version "1.00"

input datetime InpFrom = D'2024.07.01 00:00'; // inicio da cobertura

string G8[8] = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};
bool IsG8(string c){ for(int i=0;i<8;i++) if(G8[i]==c) return true; return false; }

string ImpStr(ENUM_CALENDAR_EVENT_IMPORTANCE imp)
{
   if(imp==CALENDAR_IMPORTANCE_HIGH)     return "HIGH";
   if(imp==CALENDAR_IMPORTANCE_MODERATE) return "MODERATE";
   if(imp==CALENDAR_IMPORTANCE_LOW)      return "LOW";
   return "NONE";
}
// numero com sentinela de vazio -> string ("" se vazio)
string NumOrEmpty(bool has, double v)
{ return has ? DoubleToString(v,6) : ""; }

void OnStart()
{
   MqlCalendarCountry countries[];
   int nc=CalendarCountries(countries);
   if(nc<=0){ Print("s1: CalendarCountries falhou (terminal offline?) err=",GetLastError()); return; }

   int f=FileOpen("calendar_mt5.csv",FILE_WRITE|FILE_CSV|FILE_ANSI,',');
   if(f==INVALID_HANDLE){ Print("s1: FileOpen falhou"); return; }
   FileWrite(f,"event_id","time_server","country","currency","name",
             "importance","actual","forecast","previous");

   datetime now=TimeCurrent();
   int total=0, skipped=0;
   for(int i=0;i<nc;i++)
   {
      string ccy=countries[i].currency;
      if(!IsG8(ccy)){ skipped++; continue; }   // fora do G8: descarta

      MqlCalendarValue vals[];
      int nv=CalendarValueHistory(vals,InpFrom,now,countries[i].code);
      if(nv<=0) continue;

      for(int v=0;v<nv;v++)
      {
         MqlCalendarEvent ev;
         if(!CalendarEventById(vals[v].event_id,ev)) continue;
         string nm=ev.name;
         StringReplace(nm,",",";");            // protege o CSV
         StringReplace(nm,"\"","'");
         FileWrite(f,
            (string)vals[v].event_id,
            TimeToString(vals[v].time,TIME_DATE|TIME_MINUTES|TIME_SECONDS),
            countries[i].name, ccy, nm, ImpStr(ev.importance),
            NumOrEmpty(vals[v].HasActualValue(),  vals[v].GetActualValue()),
            NumOrEmpty(vals[v].HasForecastValue(),vals[v].GetForecastValue()),
            NumOrEmpty(vals[v].HasPreviousValue(),vals[v].GetPreviousValue()));
         total++;
      }
   }
   FileClose(f);
   Print("s1: ",total," eventos exportados (",skipped," paises fora do G8 "
         "descartados) -> MQL5\\Files\\calendar_mt5.csv");
   Print("s1: copie para data/calendar/ e rode `python a18_calendar.py --ingest`");
}
//+------------------------------------------------------------------+

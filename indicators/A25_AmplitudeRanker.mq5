//+------------------------------------------------------------------+
//|                                        A25_AmplitudeRanker.mq5   |
//|  Painel do PRODUTO do ta-research (a25/a42/a43): ranqueia os 28  |
//|  pares G8 por AMPLITUDE esperada e por EFICIENCIA range/spread.  |
//|                                                                  |
//|  MODO AMPLITUDE (a25): score = mediana dos ranges diarios dos    |
//|    ultimos 20 dias FECHADOS (causal). Valida: captura ~80 pips   |
//|    liq/dia no top-1, ~80% do teto, 30% de acerto do maior-range  |
//|    (acaso 3.6%), bate estatico e aleatorio (a25/a33/a40/a42).    |
//|  MODO EFICIENCIA (z-ATR, a42): score = quao ATIPICO o ATR do par |
//|    esta p/ os padroes DELE (z vs 120d). Menos pips, mas melhor   |
//|    razao range/spread (160 vs 136) — seleciona par calmo em dia  |
//|    atipico com spread proporcionalmente menor. CANDIDATO (a39).  |
//|                                                                  |
//|  HONESTIDADE (a38/a43): isto seleciona AMPLITUDE, NAO direcao    |
//|  nem lucro. "Folga" = range tipico / spread atual (quantos       |
//|  spreads cabem no movimento). Direcao e gestao sao do trader.    |
//|  Nada aqui e sinal de entrada.                                    |
//|                                                                  |
//|  USO: compilar (F7) e arrastar em QUALQUER grafico. O painel     |
//|  atualiza a cada InpRefreshS segundos (valores mudam 1x/dia;     |
//|  o spread/folga e ao vivo). Primeira carga pode demorar ate o    |
//|  terminal baixar D1 dos 28 pares (mostra o progresso).           |
//+------------------------------------------------------------------+
#property indicator_chart_window
#property indicator_plots 0
#property version   "1.00"
#property strict

input int              InpAtrDays  = 20;   // janela do ATR (a25 CONGELADO: 20 dias)
input int              InpZWin     = 120;  // janela historica do z-ATR (a42: 60/120/250)
input int              InpTop      = 3;    // pares exibidos por modo
input ENUM_BASE_CORNER InpCorner   = CORNER_LEFT_UPPER; // canto do painel
input int              InpX        = 10;   // margem X (px)
input int              InpY        = 22;   // margem Y (px)
input int              InpFont     = 9;    // tamanho da fonte
input int              InpRefreshS = 60;   // refresh (segundos)

string G8[8] = {"USD","EUR","GBP","JPY","CHF","CAD","AUD","NZD"};
#define PFX "A25RK_"

struct Row { string sym; double atr; double z; double eff; double spread; };
Row  g_rows[28];
int  g_n = 0;
int  g_missing = 0;

//--- mediana de a[from..from+count-1] ------------------------------
double MedianOf(const double &a[], int from, int count)
{
   double tmp[]; ArrayResize(tmp, count);
   for(int i = 0; i < count; i++) tmp[i] = a[from + i];
   ArraySort(tmp);
   int m = count / 2;
   return (count % 2 == 1) ? tmp[m] : 0.5 * (tmp[m - 1] + tmp[m]);
}

//--- coleta um par: atr(a25), z(a42), spread, folga ----------------
bool ScanPair(const string sym, Row &row)
{
   double point = SymbolInfoDouble(sym, SYMBOL_POINT);
   if(point <= 0) return false;
   double pip = point * 10.0;

   int need = InpZWin + InpAtrDays + 5;
   MqlRates r[];
   ArraySetAsSeries(r, false);                       // r[0] = mais antigo
   int got = CopyRates(sym, PERIOD_D1, 1, need, r);  // shift 1 = so dias FECHADOS
   if(got < InpAtrDays + 10) return false;           // historico raso: tenta depois

   double rng[]; ArrayResize(rng, got);
   for(int i = 0; i < got; i++) rng[i] = (r[i].high - r[i].low) / pip;

   // serie causal de base_atr: mediana de InpAtrDays terminando em cada dia
   int nba = got - InpAtrDays + 1;
   double ba[]; ArrayResize(ba, nba);
   for(int k = 0; k < nba; k++) ba[k] = MedianOf(rng, k, InpAtrDays);
   row.atr = ba[nba - 1];                            // o score do a25 p/ HOJE

   // z-ATR (a42): (atr_hoje - media_prior) / desvio_prior (ddof=1, so anteriores)
   row.z = EMPTY_VALUE;
   int nprior = MathMin(InpZWin, nba - 1);
   if(nprior >= 30)
   {
      double s = 0, s2 = 0;
      for(int k = nba - 1 - nprior; k < nba - 1; k++) { s += ba[k]; s2 += ba[k] * ba[k]; }
      double mean = s / nprior;
      double var  = (s2 / nprior - mean * mean) * nprior / (nprior - 1);
      if(var > 0) row.z = (row.atr - mean) / MathSqrt(var);
   }

   row.spread = (double)SymbolInfoInteger(sym, SYMBOL_SPREAD) / 10.0;  // points->pips
   if(row.spread < 0.1) row.spread = 0.1;            // piso (como costs.py)
   row.eff = row.atr / row.spread;                   // "folga": spreads no movimento
   row.sym = sym;
   return true;
}

//--- varre os 28 pares (resolve XY/YX) ------------------------------
void Recalc()
{
   g_n = 0; g_missing = 0;
   for(int i = 0; i < 8; i++)
      for(int j = i + 1; j < 8; j++)
      {
         string cand[2] = { G8[i] + G8[j], G8[j] + G8[i] };
         string sym = "";
         for(int k = 0; k < 2; k++)
            if(SymbolSelect(cand[k], true)) { sym = cand[k]; break; }
         if(sym == "") { g_missing++; continue; }
         Row row;
         if(ScanPair(sym, row)) g_rows[g_n++] = row;
         else g_missing++;                            // sem D1 ainda: proximo tick
      }
}

//--- ordena indices por chave desc ----------------------------------
void SortIdx(int &idx[], int n, const bool by_z)
{
   for(int i = 1; i < n; i++)
   {
      int cur = idx[i]; int j = i - 1;
      double kc = by_z ? g_rows[cur].z : g_rows[cur].atr;
      while(j >= 0)
      {
         double kj = by_z ? g_rows[idx[j]].z : g_rows[idx[j]].atr;
         if(kj >= kc) break;
         idx[j + 1] = idx[j]; j--;
      }
      idx[j + 1] = cur;
   }
}

//--- desenha uma linha do painel ------------------------------------
void Put(const string name, const int line, const string text, const color clr)
{
   string obj = PFX + name;
   if(ObjectFind(0, obj) < 0)
   {
      ObjectCreate(0, obj, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, obj, OBJPROP_CORNER, InpCorner);
      ObjectSetInteger(0, obj, OBJPROP_XDISTANCE, InpX);
      ObjectSetInteger(0, obj, OBJPROP_SELECTABLE, false);
      ObjectSetInteger(0, obj, OBJPROP_HIDDEN, true);
      ObjectSetString (0, obj, OBJPROP_FONT, "Consolas");
   }
   ObjectSetInteger(0, obj, OBJPROP_YDISTANCE, InpY + line * (InpFont + 7));
   ObjectSetInteger(0, obj, OBJPROP_FONTSIZE, InpFont);
   ObjectSetInteger(0, obj, OBJPROP_COLOR, clr);
   ObjectSetString (0, obj, OBJPROP_TEXT, text);
}

//--- painel ----------------------------------------------------------
void Render()
{
   int line = 0;
   Put("h0", line++, "A25 AMPLITUDE RANKER  (ta-research a25/a42/a43)", clrGoldenrod);

   if(g_n < 20)
   {
      Put("h1", line++, StringFormat("carregando historico D1... %d/28 pares", g_n),
          clrSilver);
      ChartRedraw();
      return;
   }
   ObjectDelete(0, PFX + "h1");

   int idxA[28], idxZ[28]; int nz = 0;
   for(int i = 0; i < g_n; i++) idxA[i] = i;
   SortIdx(idxA, g_n, false);
   for(int i = 0; i < g_n; i++) if(g_rows[i].z != EMPTY_VALUE) idxZ[nz++] = i;
   SortIdx(idxZ, nz, true);

   Put("a0", line++, "-- AMPLITUDE (a25: ATR20 mediana, pips) --", clrDodgerBlue);
   int topA = MathMin(InpTop, g_n);
   for(int k = 0; k < topA; k++)
   {
      Row r = g_rows[idxA[k]];
      Put("a" + IntegerToString(k + 1), line++,
          StringFormat("%d. %-7s atr %4.0f   folga %3.0fx",
                       k + 1, r.sym, r.atr, r.eff),
          k == 0 ? clrWhite : clrSilver);
   }

   Put("z0", line++, StringFormat("-- EFICIENCIA (a42: z-ATR %dd, candidato) --", InpZWin),
       clrMediumSeaGreen);
   int topZ = MathMin(InpTop, nz);
   for(int k = 0; k < topZ; k++)
   {
      Row r = g_rows[idxZ[k]];
      Put("z" + IntegerToString(k + 1), line++,
          StringFormat("%d. %-7s z %+4.1f  atr %4.0f  folga %3.0fx",
                       k + 1, r.sym, r.z, r.atr, r.eff),
          k == 0 ? clrWhite : clrSilver);
   }

   Put("f0", line++, "AMPLITUDE, NAO direcao. Probabilistico; nao e sinal.", clrGray);
   Put("f1", line++, StringFormat("atualizado %s  spreads ao vivo  pares %d/28",
       TimeToString(TimeCurrent(), TIME_MINUTES), g_n), clrDimGray);
   ChartRedraw();
}

//--- ciclo -----------------------------------------------------------
void Update() { Recalc(); Render(); }

int OnInit()
{
   EventSetTimer(MathMax(10, InpRefreshS));
   Update();
   return INIT_SUCCEEDED;
}

void OnTimer() { Update(); }

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectsDeleteAll(0, PFX);
}

int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[])
{
   return rates_total;
}
//+------------------------------------------------------------------+
